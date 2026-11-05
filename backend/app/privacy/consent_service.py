import hashlib
import hmac
import secrets
import time
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.consent import Consent
from app.models.enums import ConsentKind, OutboxOperation
from app.models.outbox import AuthzOutbox
from app.models.person import Person
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz, AuthzRejected, AuthzUnavailable, RelationTuple
from app.privacy.outbox import enqueue

# A vocabulary written for family sharing. DUO is meant for research data, not this (issue H19).
SHARE_PURPOSES = frozenset(
    {"partner_support", "family_planning", "clinical_care", "family_support"}
)
SHARE_KINDS = frozenset({ConsentKind.SHARE_SUMMARY.value, ConsentKind.SHARE_FULL.value})
RECEIVE_CODE_SECONDS = 900

_REPORT_RELATION = {
    ConsentKind.SHARE_SUMMARY.value: "summary_grant",
    ConsentKind.SHARE_FULL.value: "full_grant",
}
VIEW_RELATION = {
    ConsentKind.SHARE_SUMMARY.value: "can_view_summary",
    ConsentKind.SHARE_FULL.value: "can_view_full",
}


def holder_tuple(consent: Consent) -> RelationTuple:
    return RelationTuple(
        f"user:{consent.grantee_id}", "holder", f"grant:{consent.id}", consent.expires_at
    )


def report_tuple(consent: Consent) -> RelationTuple:
    return RelationTuple(
        f"grant:{consent.id}#holder",
        _REPORT_RELATION[consent.kind],
        f"report:{consent.grantor_id}",
    )


def is_live(consent: Consent, now: datetime) -> bool:
    if consent.revoked_at is not None:
        return False
    return consent.expires_at is None or consent.expires_at > now


def _code_key(key: bytes, code: str) -> str:
    digest = hmac.new(key, code.encode(), hashlib.sha256).hexdigest()
    return f"receive-code:{digest}"


async def create_receive_code(redis: Redis, key: bytes, person: Person) -> str:
    """The person receiving a share creates this and passes it on themselves.

    So nobody can look someone up by name or number to find out whether they use the service, and
    no result can arrive for someone who didn't ask to receive it.
    """
    code = secrets.token_urlsafe(16)
    try:
        await redis.set(_code_key(key, code), str(person.id), ex=RECEIVE_CODE_SECONDS)
    except RedisError:
        raise ApiError(HTTPStatus.SERVICE_UNAVAILABLE, "service_unavailable") from None
    return code


async def take_receive_code(redis: Redis, key: bytes, code: str) -> uuid.UUID | None:
    try:
        found = await redis.getdel(_code_key(key, code))
    except RedisError:
        raise ApiError(HTTPStatus.SERVICE_UNAVAILABLE, "service_unavailable") from None
    return uuid.UUID(found) if found else None


async def grant_share(
    db: AsyncSession,
    audit: AuditTrail,
    *,
    actor: str,
    owner: Person,
    grantee_id: uuid.UUID,
    kind: ConsentKind,
    purpose: str,
    terms_version: str,
    duration: timedelta,
    now: datetime,
) -> Consent:
    consent = Consent(
        id=uuid.uuid4(),
        grantor_id=owner.id,
        grantee_id=grantee_id,
        kind=kind.value,
        purpose=purpose,
        terms_version=terms_version,
        expires_at=now + duration,
    )
    db.add(consent)
    await db.flush()
    # Access is created only after this commits, so a failed commit leaves none behind (H7).
    enqueue(db, OutboxOperation.WRITE, holder_tuple(consent))
    enqueue(db, OutboxOperation.WRITE, report_tuple(consent))
    await db.flush()
    await audit.append(
        db,
        actor=actor,
        action="consent.grant",
        resource=f"person:{owner.id}",
        meta={"consent_id": str(consent.id), "mode": kind.value},
    )
    return consent


async def revoke(
    db: AsyncSession,
    authz: Authz,
    audit: AuditTrail,
    *,
    actor: str,
    owner: Person,
    consent_id: uuid.UUID,
) -> bool:
    """Access goes first. If that can't happen, nothing changes and the consent stays active.

    Returns False if this person has no such live consent.
    """
    started = time.perf_counter()
    consent = await db.scalar(
        select(Consent)
        .where(Consent.id == consent_id, Consent.grantor_id == owner.id)
        .with_for_update()
    )
    if consent is None or consent.revoked_at is not None:
        return False

    if consent.kind in SHARE_KINDS:
        holder = holder_tuple(consent)
        # A grant still waiting in the outbox must not be applied after this revocation. Taking its
        # row lock here also waits out a worker applying it right now, so the delete comes last.
        await db.execute(
            update(AuthzOutbox)
            .where(
                AuthzOutbox.object == holder.object,
                AuthzOutbox.operation == OutboxOperation.WRITE.value,
                AuthzOutbox.applied_at.is_(None),
            )
            .values(applied_at=authz.clock())
        )
        try:
            await authz.delete(holder)
        except (AuthzUnavailable, AuthzRejected):
            raise ApiError(HTTPStatus.SERVICE_UNAVAILABLE, "revoke_unavailable") from None
        enqueue(db, OutboxOperation.DELETE, report_tuple(consent))
    elif consent.kind == ConsentKind.SERVICE.value:
        owner.service_consent_at = None

    consent.revoked_at = authz.clock()
    await db.flush()
    await audit.append(
        db,
        actor=actor,
        action="consent.revoke",
        resource=f"person:{owner.id}",
        meta={
            "consent_id": str(consent.id),
            "mode": consent.kind,
            "latency_ms": round((time.perf_counter() - started) * 1000),
        },
    )
    return True
