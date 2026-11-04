import hashlib
import hmac
import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit import AuditLog

log = logging.getLogger("samvid.audit")

GENESIS_HASH = "0" * 64
# Arbitrary, but every writer must use the same number: it serialises appends to the chain.
_CHAIN_LOCK_ID = 7_302_011
_VERIFY_BATCH = 1_000
_MAX_META_VALUE_CHARS = 200

# An allowlist, so a careless caller can't put health data in the permanent log.
ALLOWED_META_KEYS = frozenset(
    {
        "boundary",
        "case_id",
        "consent_id",
        "count",
        "mode",
        "priority",
        "reason",
        "reveal",
        "route",
        "rule_version",
        "state",
    }
)


@dataclass(frozen=True, slots=True)
class ChainReport:
    rows_checked: int
    head_hash: str
    broken_at_seq: int | None = None

    @property
    def intact(self) -> bool:
        return self.broken_at_seq is None


def _clean_meta(meta: Mapping[str, Any] | None) -> dict[str, Any]:
    if not meta:
        return {}
    unknown = set(meta) - ALLOWED_META_KEYS
    if unknown:
        raise ValueError(f"audit meta keys not allowed: {sorted(unknown)}")
    for key, value in meta.items():
        if not isinstance(value, str | int | float | bool) and value is not None:
            raise ValueError(f"audit meta value for {key!r} must be a scalar")
        if isinstance(value, str) and len(value) > _MAX_META_VALUE_CHARS:
            raise ValueError(f"audit meta value for {key!r} is too long")
    return dict(meta)


def _canonical(
    *,
    seq: int,
    at: datetime,
    actor: str,
    action: str,
    resource: str,
    outcome: str,
    meta: Mapping[str, Any],
) -> bytes:
    return json.dumps(
        {
            "seq": seq,
            "at": at.astimezone(UTC).isoformat(),
            "actor": actor,
            "action": action,
            "resource": resource,
            "outcome": outcome,
            "meta": meta,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()


class AuditTrail:
    """Tamper-evident log of who did what to whose data.

    The hash covers the columns themselves, not a stored copy of them. The access log and every
    report read the columns, so those are what must be impossible to alter unnoticed.
    """

    def __init__(self, key: bytes, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._key = key
        self._session_factory = session_factory

    def _digest(self, prev_hash: str, canonical: bytes) -> str:
        return hmac.new(self._key, prev_hash.encode() + canonical, hashlib.sha256).hexdigest()

    async def append(
        self,
        session: AsyncSession,
        *,
        actor: str,
        action: str,
        resource: str,
        outcome: str = "ok",
        meta: Mapping[str, Any] | None = None,
    ) -> None:
        """Add a row to the caller's transaction, so the action and its record commit together.

        This takes a lock held until commit. Call it after any network work in the transaction, so
        one slow external call can't stall every writer in the system.
        """
        clean_meta = _clean_meta(meta)
        await session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": _CHAIN_LOCK_ID}
        )
        last = (
            await session.execute(
                select(AuditLog.seq, AuditLog.hash).order_by(AuditLog.seq.desc()).limit(1)
            )
        ).first()
        seq = last.seq + 1 if last else 1
        prev_hash = last.hash if last else GENESIS_HASH
        at = datetime.now(UTC)
        canonical = _canonical(
            seq=seq,
            at=at,
            actor=actor,
            action=action,
            resource=resource,
            outcome=outcome,
            meta=clean_meta,
        )
        session.add(
            AuditLog(
                seq=seq,
                at=at,
                actor=actor,
                action=action,
                resource=resource,
                outcome=outcome,
                meta=clean_meta,
                prev_hash=prev_hash,
                hash=self._digest(prev_hash, canonical),
            )
        )
        await session.flush()

    async def record_independently(
        self,
        *,
        actor: str,
        action: str,
        resource: str,
        outcome: str,
        meta: Mapping[str, Any] | None = None,
    ) -> bool:
        """Write in a separate transaction, for events that must outlive a rolled-back request.

        A denied attempt ends in an error, which rolls back the request's own transaction and would
        take the audit row with it. If this write fails, the attempt stays denied regardless.
        """
        try:
            async with self._session_factory() as session, session.begin():
                # If the caller's own open transaction already holds the chain lock, this would
                # otherwise wait on itself until the statement timeout.
                await session.execute(text("SET LOCAL lock_timeout = '2s'"))
                await self.append(
                    session,
                    actor=actor,
                    action=action,
                    resource=resource,
                    outcome=outcome,
                    meta=meta,
                )
        except (SQLAlchemyError, OSError) as exc:
            log.error("audit_write_failed", extra={"ctx": {"error": type(exc).__name__}})
            return False
        return True

    async def verify_chain(self, session: AsyncSession) -> ChainReport:
        """Walk the chain in batches, returning the first row that doesn't check out.

        A chain can't reveal that its newest rows were cut off. Compare `head_hash` with a copy
        stored outside this database to catch that.
        """
        prev_hash = GENESIS_HASH
        expected_seq = 1
        checked = 0
        after_seq = 0
        while True:
            rows = (
                await session.scalars(
                    select(AuditLog)
                    .where(AuditLog.seq > after_seq)
                    .order_by(AuditLog.seq)
                    .limit(_VERIFY_BATCH)
                )
            ).all()
            if not rows:
                return ChainReport(rows_checked=checked, head_hash=prev_hash)
            for row in rows:
                canonical = _canonical(
                    seq=row.seq,
                    at=row.at,
                    actor=row.actor,
                    action=row.action,
                    resource=row.resource,
                    outcome=row.outcome,
                    meta=row.meta,
                )
                valid = (
                    row.seq == expected_seq
                    and row.prev_hash == prev_hash
                    and hmac.compare_digest(row.hash, self._digest(prev_hash, canonical))
                )
                if not valid:
                    return ChainReport(
                        rows_checked=checked, head_hash=prev_hash, broken_at_seq=row.seq
                    )
                prev_hash = row.hash
                expected_seq += 1
                checked += 1
            after_seq = rows[-1].seq
            session.expunge_all()
