from datetime import UTC, datetime
from http import HTTPStatus

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_person, get_audit, get_db, get_packs
from app.core.config import decode_key
from app.core.errors import ApiError
from app.core.security import Principal, get_principal
from app.country_packs.loader import PackRegistry
from app.ingestion.service import national_id_hash
from app.models.consent import Consent
from app.models.enums import ConsentKind
from app.models.person import Person
from app.privacy.audit import AuditTrail
from app.privacy.right_not_to_know import can_withhold
from app.schemas.me import (
    ProfileOut,
    ProfilePatch,
    ProvisionIn,
    ResultsPreferenceIn,
    ServiceConsentIn,
)

router = APIRouter(prefix="/me", tags=["me"])


def _profile(person: Person) -> ProfileOut:
    return ProfileOut(
        id=person.id,
        pack_code=person.pack_code,
        preferred_lang=person.preferred_lang,
        literacy_level=person.literacy_level,
        region=person.region,
        age_band=person.age_band,
        gender=person.gender,
        service_consent_at=person.service_consent_at,
        results_withheld=person.results_withheld_at is not None,
        linked_to_national_id=person.national_id_hash is not None,
    )


@router.post("", response_model=ProfileOut)
async def provision(
    request: Request,
    body: ProvisionIn,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> ProfileOut:
    """Called after first sign-in. Safe to repeat.

    The national ID comes only from the verified token, never the request, or anyone could claim
    someone else's results by typing their number.
    """
    existing = await db.scalar(select(Person).where(Person.keycloak_sub == principal.sub))
    if existing is not None:
        return _profile(existing)

    pack = packs.get(body.pack_code) if body.pack_code else packs.default
    if pack is None:
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "unknown_country_pack")

    person: Person | None = None
    id_hash: str | None = None
    if principal.national_id:
        key = decode_key(request.app.state.settings.national_id_hmac_key, "NATIONAL_ID_HMAC_KEY")
        id_hash = national_id_hash(key, pack, principal.national_id)
        person = await db.scalar(select(Person).where(Person.national_id_hash == id_hash))
        if person is not None and person.keycloak_sub is not None:
            raise ApiError(HTTPStatus.CONFLICT, "identity_already_linked")

    if person is None:
        person = Person(
            keycloak_sub=principal.sub,
            national_id_hash=id_hash,
            pack_code=pack.code,
            preferred_lang=pack.manifest.default_language,
        )
        db.add(person)
    else:
        person.keycloak_sub = principal.sub
    try:
        await db.flush()
    except IntegrityError:
        # Two tabs signing in together race here. If this login won the other request, it's a
        # repeat, not a conflict.
        await db.rollback()
        mine = await db.scalar(select(Person).where(Person.keycloak_sub == principal.sub))
        if mine is not None:
            return _profile(mine)
        raise ApiError(HTTPStatus.CONFLICT, "identity_already_linked") from None

    await audit.append(
        db, actor=principal.sub, action="person.link", resource=f"person:{person.id}"
    )
    await db.commit()
    await db.refresh(person)
    return _profile(person)


@router.get("", response_model=ProfileOut)
async def read(person: Person = Depends(current_person)) -> ProfileOut:
    return _profile(person)


@router.patch("", response_model=ProfileOut)
async def update(
    body: ProfilePatch,
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    packs: PackRegistry = Depends(get_packs),
) -> ProfileOut:
    pack = packs.require(person.pack_code)
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    allowed = {
        "preferred_lang": pack.manifest.languages,
        "region": pack.strata.regions,
        "age_band": pack.strata.age_bands,
        "gender": pack.strata.genders,
    }
    for field, options in allowed.items():
        if field in changes and changes[field] not in options:
            raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, f"invalid_{field}")
    for field, value in changes.items():
        setattr(person, field, value)
    await db.commit()
    await db.refresh(person)
    return _profile(person)


@router.post("/service-consent", response_model=ProfileOut)
async def service_consent(
    body: ServiceConsentIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
) -> ProfileOut:
    if not body.accepted:
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "consent_not_given")
    if person.service_consent_at is None:
        now = datetime.now(UTC)
        person.service_consent_at = now
        db.add(
            Consent(
                grantor_id=person.id,
                kind=ConsentKind.SERVICE.value,
                purpose="explain_my_result",
                terms_version=body.terms_version,
            )
        )
        await db.flush()
        await audit.append(
            db, actor=principal.sub, action="consent.service", resource=f"person:{person.id}"
        )
        await db.commit()
        await db.refresh(person)
    return _profile(person)


@router.post("/results-preference", response_model=ProfileOut)
async def results_preference(
    body: ResultsPreferenceIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> ProfileOut:
    """The right not to know. Triage still runs, so a serious finding still reaches a person."""
    if body.withhold and not can_withhold(packs.require(person.pack_code)):
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "right_not_to_know_unavailable")
    person.results_withheld_at = datetime.now(UTC) if body.withhold else None
    await db.flush()
    await audit.append(
        db,
        actor=principal.sub,
        action="results.preference",
        resource=f"person:{person.id}",
        meta={"mode": "withheld" if body.withhold else "shown"},
    )
    await db.commit()
    await db.refresh(person)
    return _profile(person)
