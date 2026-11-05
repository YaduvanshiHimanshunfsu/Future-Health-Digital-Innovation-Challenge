from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    current_person,
    deny,
    get_audit,
    get_authz,
    get_cipher,
    get_db,
    get_packs,
    require_service_consent,
)
from app.core.config import decode_key
from app.core.errors import ApiError
from app.core.i18n import translate
from app.core.rate_limit import rate_limit
from app.core.security import Principal, get_principal
from app.country_packs.loader import PackRegistry
from app.models.consent import Consent
from app.models.couple import Couple
from app.models.enums import ConsentKind, OutboxOperation
from app.models.person import Person
from app.privacy import matching
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz, RelationTuple
from app.privacy.crypto import FieldCipher
from app.privacy.outbox import drain_quietly, enqueue
from app.risk_engine.visuals import visuals_for
from app.schemas.couples import (
    CoupleCreatedOut,
    CoupleCreateIn,
    CoupleJoinIn,
    CoupleOut,
    FollowUpOut,
    MatchConsentIn,
    MatchIn,
    MatchOut,
)
from app.schemas.results import FactOut

router = APIRouter(prefix="/couples", tags=["couples"])


def _invite_key(request: Request) -> bytes:
    return decode_key(request.app.state.settings.invite_hmac_key, "INVITE_HMAC_KEY")


def _membership(person: Person, couple_id: UUID) -> RelationTuple:
    return RelationTuple(f"user:{person.id}", "member", f"couple:{couple_id}")


async def _my_couple(
    couple_id: UUID,
    principal: Principal,
    person: Person,
    db: AsyncSession,
    audit: AuditTrail,
    authz: Authz,
) -> Couple:
    couple = await db.get(Couple, couple_id)
    allowed = (
        couple is not None
        and person.id in (couple.person_a, couple.person_b)
        and await authz.check(f"user:{person.id}", "member", f"couple:{couple_id}")
    )
    if not allowed or couple is None:
        await deny(audit, principal.sub, f"couple:{couple_id}")
    return couple


async def _couple_out(db: AsyncSession, couple: Couple, person: Person) -> CoupleOut:
    consent = await matching.live_match_consent(db, person.id, couple.id)
    case = await matching.open_case_for(db, person.id, couple.id)
    return CoupleOut(
        id=couple.id,
        partner_joined=couple.person_b is not None,
        my_consent_id=consent.id if consent else None,
        my_reveal_level=consent.reveal_level if consent else None,
        what_a_result_reveals=translate("match.what_a_result_reveals", person.preferred_lang),
        follow_up=FollowUpOut(case_id=case.id, state=case.state) if case else None,
    )


@router.post(
    "",
    status_code=HTTPStatus.CREATED,
    response_model=CoupleCreatedOut,
    dependencies=[Depends(rate_limit("couple_create", 10, 86400))],
)
async def create(
    request: Request,
    body: CoupleCreateIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
) -> CoupleCreatedOut:
    require_service_consent(person)
    couple, code = await matching.create_couple(
        db,
        cipher,
        audit,
        actor=principal.sub,
        person=person,
        relationship=body.relationship,
        key=_invite_key(request),
        now=authz.clock(),
    )
    enqueue(db, OutboxOperation.WRITE, _membership(person, couple.id))
    expires_at = couple.invite_expires_at
    couple_id = couple.id
    await db.commit()
    await drain_quietly(request.app.state.session_factory, authz)
    return CoupleCreatedOut(id=couple_id, invite_code=code, expires_at=expires_at)


@router.get("", response_model=list[CoupleOut])
async def list_mine(
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
) -> list[CoupleOut]:
    couples = (
        await db.scalars(
            select(Couple).where(or_(Couple.person_a == person.id, Couple.person_b == person.id))
        )
    ).all()
    return [await _couple_out(db, couple, person) for couple in couples]


@router.post(
    "/join",
    response_model=CoupleOut,
    dependencies=[Depends(rate_limit("couple_join", 10, 3600))],
)
async def join(
    request: Request,
    body: CoupleJoinIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
) -> CoupleOut:
    require_service_consent(person)
    couple = await matching.join_couple(
        db,
        cipher,
        audit,
        actor=principal.sub,
        person=person,
        code=body.invite_code,
        relationship=body.relationship,
        key=_invite_key(request),
        now=authz.clock(),
    )
    if couple is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    enqueue(db, OutboxOperation.WRITE, _membership(person, couple.id))
    await db.commit()
    await drain_quietly(request.app.state.session_factory, authz)
    return await _couple_out(db, couple, person)


@router.get("/{couple_id}", response_model=CoupleOut)
async def read(
    couple_id: UUID,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
) -> CoupleOut:
    couple = await _my_couple(couple_id, principal, person, db, audit, authz)
    return await _couple_out(db, couple, person)


@router.post("/{couple_id}/consent", response_model=CoupleOut)
async def give_consent(
    couple_id: UUID,
    body: MatchConsentIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
) -> CoupleOut:
    require_service_consent(person)
    if person.results_withheld_at is not None:
        raise ApiError(HTTPStatus.CONFLICT, "results_withheld")
    couple = await _my_couple(couple_id, principal, person, db, audit, authz)
    # Changing a choice keeps the old row: the ledger shows what was agreed, and when.
    existing = await matching.live_match_consent(db, person.id, couple.id)
    if existing is not None:
        existing.revoked_at = authz.clock()
        await db.flush()
    consent = Consent(
        grantor_id=person.id,
        couple_id=couple.id,
        kind=ConsentKind.COUPLE_MATCH.value,
        reveal_level=body.reveal_level,
        purpose="couple_match",
        terms_version=body.terms_version,
    )
    db.add(consent)
    await db.flush()
    # Filed under the person, not the couple, so the partner's log doesn't show their choices.
    await audit.append(
        db,
        actor=principal.sub,
        action="consent.couple",
        resource=f"person:{person.id}",
        meta={"consent_id": str(consent.id), "reveal": body.reveal_level},
    )
    await db.commit()
    return await _couple_out(db, couple, person)


@router.delete("/{couple_id}/consent", status_code=HTTPStatus.NO_CONTENT)
async def withdraw_consent(
    couple_id: UUID,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
) -> None:
    couple = await _my_couple(couple_id, principal, person, db, audit, authz)
    consent = await matching.live_match_consent(db, person.id, couple.id)
    if consent is None:
        return
    consent.revoked_at = authz.clock()
    await db.flush()
    await audit.append(
        db,
        actor=principal.sub,
        action="consent.couple_withdraw",
        resource=f"person:{person.id}",
        meta={"consent_id": str(consent.id)},
    )
    await db.commit()


@router.post(
    "/{couple_id}/match",
    response_model=MatchOut,
    dependencies=[Depends(rate_limit("couple_match", 20, 3600))],
)
async def match(
    couple_id: UUID,
    _: MatchIn | None = None,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
    packs: PackRegistry = Depends(get_packs),
) -> MatchOut:
    """Takes no input beyond the couple's ID, so nobody can test a list of genes against a partner."""
    require_service_consent(person)
    couple = await _my_couple(couple_id, principal, person, db, audit, authz)
    try:
        result = await matching.match_couple(
            db, cipher, audit, packs, actor=principal.sub, couple=couple, viewer=person
        )
    except matching.MatchNotReady:
        raise ApiError(HTTPStatus.CONFLICT, "match_not_ready") from None
    await db.commit()
    facts = list(result.facts)
    return MatchOut(
        outcome=result.outcome.value,
        reveal_level=result.reveal.value,
        shared_genes=list(result.shared_genes) if result.shared_genes is not None else None,
        facts=[FactOut.from_fact(fact) for fact in facts],
        visuals=visuals_for(facts),
        follow_up_case_id=result.case_id,
        notice=translate(f"match.{result.outcome.value}", person.preferred_lang),
    )
