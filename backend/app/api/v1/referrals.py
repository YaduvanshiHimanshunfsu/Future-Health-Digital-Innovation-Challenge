"""Referrals from counselling to confirmatory testing or reproductive genetics.

Only the counsellor a case is assigned to can create or move its referrals, checked against the
authorisation store. Sending one moves the case along the pathway and records the FHIR reference on
that step, so the hand-off is traceable from the result to the referral (V5.2.5).
"""

import hashlib
import hmac
import uuid
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_person, deny, get_audit, get_authz, get_db, get_packs
from app.core.config import decode_key
from app.core.errors import ApiError
from app.core.security import Principal, require_role
from app.country_packs.loader import PackRegistry
from app.models.case import CareCase
from app.models.enums import CaseState, ReferralKind, ReferralStatus
from app.models.person import Person
from app.models.referral import Referral
from app.pathway import fhir_mapper
from app.pathway.service import advance, commit_or_conflict
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz
from app.schemas.booking import ReferralIn, ReferralOut

router = APIRouter(tags=["referrals"])

# Sending a referral of each kind is this step on the pathway.
_SENT_STATE = {
    ReferralKind.CONFIRMATORY_LAB.value: CaseState.CONFIRMATORY_TEST_ORDERED,
    ReferralKind.REPRODUCTIVE_GENOMICS.value: CaseState.REPRO_GENOMICS_REFERRED,
}


def _pseudonym(key: bytes, purpose: str, ident: uuid.UUID) -> str:
    # A separate derivation per purpose, so a referral's pseudonym can't be joined to analytics.
    return hmac.new(key, f"{purpose}|".encode() + ident.bytes, hashlib.sha256).hexdigest()[:32]


def _out(request: Request, referral: Referral, case: CareCase) -> ReferralOut:
    key = decode_key(request.app.state.settings.analytics_hmac_key, "ANALYTICS_HMAC_KEY")
    names = {
        "subject_pseudonym": _pseudonym(key, "fhir-subject", case.subject_id),
        "requester_pseudonym": _pseudonym(key, "fhir-staff", referral.created_by),
    }
    return ReferralOut(
        id=referral.id,
        case_id=case.id,
        kind=referral.kind,
        destination=referral.destination,
        status=referral.status,
        created_at=referral.created_at,
        service_request=fhir_mapper.service_request(referral, **names),
        task=fhir_mapper.task(referral, **names),
    )


async def _assigned_case(
    db: AsyncSession,
    authz: Authz,
    audit: AuditTrail,
    principal: Principal,
    person: Person,
    case_id: UUID,
) -> CareCase:
    case = await db.get(CareCase, case_id, with_for_update=True)
    assigned = case is not None and await authz.check(
        f"user:{person.id}", "assigned", f"care_case:{case_id}"
    )
    if case is None or not assigned:
        await deny(audit, principal.sub, f"case:{case_id}", meta={"actor_kind": "counsellor"})
    return case


@router.post(
    "/cases/{case_id}/referrals", response_model=ReferralOut, status_code=HTTPStatus.CREATED
)
async def create_referral(
    request: Request,
    case_id: UUID,
    body: ReferralIn,
    principal: Principal = Depends(require_role("counsellor")),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
) -> ReferralOut:
    case = await _assigned_case(db, authz, audit, principal, person, case_id)
    referral = Referral(
        case_id=case.id,
        created_by=person.id,
        kind=body.kind.value,
        destination=body.destination.strip(),
        status=ReferralStatus.DRAFT.value,
    )
    db.add(referral)
    await db.flush()
    await db.refresh(referral)
    await audit.append(
        db,
        actor=principal.sub,
        action="referral.create",
        resource=f"case:{case.id}",
        meta={"mode": body.kind.value},
    )
    await db.commit()
    return _out(request, referral, case)


@router.get("/cases/{case_id}/referrals", response_model=list[ReferralOut])
async def list_referrals(
    request: Request,
    case_id: UUID,
    principal: Principal = Depends(require_role("counsellor")),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
) -> list[ReferralOut]:
    case = await _assigned_case(db, authz, audit, principal, person, case_id)
    rows = (
        await db.scalars(
            select(Referral).where(Referral.case_id == case.id).order_by(Referral.created_at)
        )
    ).all()
    return [_out(request, row, case) for row in rows]


async def _move(
    request: Request,
    referral_id: UUID,
    to_status: ReferralStatus,
    principal: Principal,
    person: Person,
    db: AsyncSession,
    audit: AuditTrail,
    authz: Authz,
    packs: PackRegistry,
) -> ReferralOut:
    referral = await db.get(Referral, referral_id, with_for_update=True)
    if referral is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    case = await _assigned_case(db, authz, audit, principal, person, referral.case_id)
    allowed = {
        ReferralStatus.SENT: {ReferralStatus.DRAFT.value},
        ReferralStatus.ACCEPTED: {ReferralStatus.SENT.value},
        ReferralStatus.CANCELLED: {ReferralStatus.DRAFT.value, ReferralStatus.SENT.value},
    }
    if referral.status not in allowed[to_status]:
        raise ApiError(HTTPStatus.CONFLICT, "invalid_referral_status")
    subject = await db.get(Person, case.subject_id)
    pack = (packs.get(subject.pack_code) if subject else None) or packs.default

    async def work() -> None:
        referral.status = to_status.value
        next_state = None
        if to_status is ReferralStatus.SENT:
            referral.fhir_ref = f"ServiceRequest/{referral.id}"
            next_state = _SENT_STATE[referral.kind]
        elif (
            to_status is ReferralStatus.ACCEPTED
            and referral.kind == ReferralKind.REPRODUCTIVE_GENOMICS.value
        ):
            next_state = CaseState.REFERRAL_ACCEPTED
        if next_state is not None:
            await advance(
                db,
                case,
                next_state,
                actor=principal.sub,
                pack=pack,
                fhir_ref=f"ServiceRequest/{referral.id}",
            )
        await audit.append(
            db,
            actor=principal.sub,
            action=f"referral.{to_status.value}",
            resource=f"case:{case.id}",
            meta={"mode": referral.kind},
        )

    await commit_or_conflict(db, work)
    await db.refresh(referral)
    return _out(request, referral, case)


def _route(to_status: ReferralStatus):  # type: ignore[no-untyped-def]
    async def handler(
        request: Request,
        referral_id: UUID,
        principal: Principal = Depends(require_role("counsellor")),
        person: Person = Depends(current_person),
        db: AsyncSession = Depends(get_db),
        audit: AuditTrail = Depends(get_audit),
        authz: Authz = Depends(get_authz),
        packs: PackRegistry = Depends(get_packs),
    ) -> ReferralOut:
        return await _move(
            request, referral_id, to_status, principal, person, db, audit, authz, packs
        )

    return handler


for _status, _verb in (
    (ReferralStatus.SENT, "send"),
    (ReferralStatus.ACCEPTED, "accept"),
    (ReferralStatus.CANCELLED, "cancel"),
):
    router.add_api_route(
        f"/referrals/{{referral_id}}/{_verb}",
        _route(_status),
        methods=["POST"],
        response_model=ReferralOut,
        name=f"referral_{_verb}",
    )
