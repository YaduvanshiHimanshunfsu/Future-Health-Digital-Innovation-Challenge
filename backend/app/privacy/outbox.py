import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.break_glass import BreakGlassEvent
from app.models.consent import Consent
from app.models.enums import OutboxOperation
from app.models.outbox import AuthzOutbox
from app.privacy.authz import Authz, AuthzRejected, AuthzUnavailable, RelationTuple

log = logging.getLogger("samvid.authz")

_MAX_ATTEMPTS = 5
_GRANT_PREFIX = "grant:"
_GRANT_RELATION = "holder"


def enqueue(db: AsyncSession, operation: OutboxOperation, relation_tuple: RelationTuple) -> None:
    """Commits with the row that caused it, so access can't exist unless that row does."""
    db.add(
        AuthzOutbox(
            operation=operation.value,
            subject=relation_tuple.user,
            relation=relation_tuple.relation,
            object=relation_tuple.object,
            expires_at=relation_tuple.expires_at,
        )
    )


async def drain(
    session_factory: async_sessionmaker[AsyncSession], authz: Authz, *, limit: int = 100
) -> int:
    """Apply pending changes, one transaction each, stopping as soon as OpenFGA is out of reach."""
    applied = 0
    for _ in range(limit):
        async with session_factory() as session, session.begin():
            row = await session.scalar(
                select(AuthzOutbox)
                .where(AuthzOutbox.applied_at.is_(None), AuthzOutbox.attempts < _MAX_ATTEMPTS)
                .order_by(AuthzOutbox.created_at)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if row is None:
                return applied
            relation_tuple = RelationTuple(row.subject, row.relation, row.object, row.expires_at)
            try:
                if row.operation == OutboxOperation.WRITE.value:
                    await authz.write(relation_tuple)
                else:
                    await authz.delete(relation_tuple)
            except AuthzUnavailable:
                return applied
            except AuthzRejected:
                row.attempts += 1
                log.error("authz_outbox_rejected", extra={"ctx": {"relation": row.relation}})
                continue
            row.applied_at = datetime.now(UTC)
            applied += 1
    return applied


async def drain_quietly(session_factory: async_sessionmaker[AsyncSession], authz: Authz) -> None:
    """After a commit, try to apply straight away. The worker picks up anything left behind."""
    try:
        await drain(session_factory, authz, limit=10)
    except (SQLAlchemyError, OSError) as exc:
        log.warning("authz_outbox_deferred", extra={"ctx": {"error": type(exc).__name__}})


async def reconcile(session_factory: async_sessionmaker[AsyncSession], authz: Authz) -> int:
    """Remove any grant tuple with no live record behind it. Deleting is always the safe direction.

    It never re-creates a missing tuple. A live consent without one is either still in the outbox,
    or left by a revocation whose commit failed, and restoring that would undo what someone asked.
    """
    removed = 0
    now = authz.clock()
    async with session_factory() as session:
        async for relation_tuple in authz.tuples():
            if relation_tuple.relation != _GRANT_RELATION:
                continue
            if not relation_tuple.object.startswith(_GRANT_PREFIX):
                continue
            grant_id = uuid.UUID(relation_tuple.object.removeprefix(_GRANT_PREFIX))
            consent = await session.get(Consent, grant_id)
            event = None if consent else await session.get(BreakGlassEvent, grant_id)
            if consent is not None:
                live = consent.revoked_at is None and (
                    consent.expires_at is None or consent.expires_at > now
                )
            else:
                live = event is not None and event.expires_at > now
            if not live:
                await authz.delete(relation_tuple)
                removed += 1
    if removed:
        log.warning("authz_orphans_removed", extra={"ctx": {"count": removed}})
    return removed
