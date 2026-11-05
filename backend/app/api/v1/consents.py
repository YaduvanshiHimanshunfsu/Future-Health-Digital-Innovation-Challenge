from datetime import timedelta
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    current_person,
    deny,
    get_audit,
    get_authz,
    get_db,
    get_redis,
    require_service_consent,
)
from app.core.config import decode_key
from app.core.errors import ApiError
from app.core.rate_limit import rate_limit
from app.core.security import Principal, get_principal
from app.models.consent import Consent
from app.models.enums import ConsentKind
from app.models.person import Person
from app.privacy import consent_service
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz
from app.privacy.outbox import drain_quietly
from app.schemas.consent import ConsentListOut, ConsentOut, GrantedOut, GrantIn, ReceiveCodeOut

router = APIRouter(prefix="/consents", tags=["consents"])


def _invite_key(request: Request) -> bytes:
    return decode_key(request.app.state.settings.invite_hmac_key, "INVITE_HMAC_KEY")


def _out(consent: Consent, authz: Authz) -> ConsentOut:
    return ConsentOut(
        id=consent.id,
        kind=consent.kind,
        purpose=consent.purpose,
        reveal_level=consent.reveal_level,
        expires_at=consent.expires_at,
        revoked_at=consent.revoked_at,
        created_at=consent.created_at,
        active=consent_service.is_live(consent, authz.clock()),
    )


@router.post(
    "/receive-code",
    response_model=ReceiveCodeOut,
    dependencies=[Depends(rate_limit("receive_code", 10, 3600))],
)
async def receive_code(
    request: Request,
    person: Person = Depends(current_person),
    redis: Redis = Depends(get_redis),
    authz: Authz = Depends(get_authz),
) -> ReceiveCodeOut:
    code = await consent_service.create_receive_code(redis, _invite_key(request), person)
    return ReceiveCodeOut(
        code=code,
        expires_at=authz.clock() + timedelta(seconds=consent_service.RECEIVE_CODE_SECONDS),
    )


@router.get("", response_model=ConsentListOut)
async def list_consents(
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    authz: Authz = Depends(get_authz),
) -> ConsentListOut:
    rows = (
        await db.scalars(
            select(Consent)
            .where(or_(Consent.grantor_id == person.id, Consent.grantee_id == person.id))
            .order_by(Consent.created_at.desc())
        )
    ).all()
    now = authz.clock()
    return ConsentListOut(
        given=[_out(row, authz) for row in rows if row.grantor_id == person.id],
        received=[
            _out(row, authz)
            for row in rows
            if row.grantee_id == person.id and consent_service.is_live(row, now)
        ],
    )


@router.post(
    "",
    status_code=HTTPStatus.CREATED,
    response_model=GrantedOut,
    dependencies=[Depends(rate_limit("consent_grant", 20, 3600))],
)
async def grant(
    request: Request,
    body: GrantIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
    redis: Redis = Depends(get_redis),
) -> GrantedOut:
    require_service_consent(person)
    if person.results_withheld_at is not None:
        raise ApiError(HTTPStatus.CONFLICT, "results_withheld")
    if body.purpose not in consent_service.SHARE_PURPOSES:
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_purpose")

    grantee_id = await consent_service.take_receive_code(
        redis, _invite_key(request), body.grantee_code
    )
    if grantee_id is None or grantee_id == person.id:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")

    consent = await consent_service.grant_share(
        db,
        audit,
        actor=principal.sub,
        owner=person,
        grantee_id=grantee_id,
        kind=ConsentKind(body.kind),
        purpose=body.purpose,
        terms_version=body.terms_version,
        duration=timedelta(days=body.duration_days),
        now=authz.clock(),
    )
    await db.commit()
    await db.refresh(consent)
    await drain_quietly(request.app.state.session_factory, authz)
    ready = await authz.check(
        f"user:{grantee_id}",
        consent_service.VIEW_RELATION[consent.kind],
        f"report:{person.id}",
    )
    return GrantedOut(**_out(consent, authz).model_dump(), access_ready=ready)


@router.delete("/{consent_id}", status_code=HTTPStatus.NO_CONTENT)
async def revoke(
    request: Request,
    consent_id: UUID,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
) -> None:
    revoked = await consent_service.revoke(
        db, authz, audit, actor=principal.sub, owner=person, consent_id=consent_id
    )
    if not revoked:
        await db.rollback()
        await deny(audit, principal.sub, f"consent:{consent_id}")
    await db.commit()
    await drain_quietly(request.app.state.session_factory, authz)
