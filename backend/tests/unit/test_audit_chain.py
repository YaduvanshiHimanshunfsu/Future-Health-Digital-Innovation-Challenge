import asyncio
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.models.audit import AuditLog
from app.privacy.audit import GENESIS_HASH, AuditTrail, _canonical

pytestmark = pytest.mark.db


async def write_rows(
    audit: AuditTrail, factory: async_sessionmaker[AsyncSession], count: int
) -> None:
    for number in range(count):
        async with factory() as session, session.begin():
            await audit.append(
                session,
                actor=f"actor-{number}",
                action="results.view",
                resource=f"person:{number}",
                meta={"count": number},
            )


async def tamper(owner_engine: AsyncEngine, statement: str) -> None:
    async with owner_engine.begin() as connection:
        await connection.execute(text("ALTER TABLE audit_log DISABLE TRIGGER USER"))
        await connection.execute(text(statement))
        await connection.execute(text("ALTER TABLE audit_log ENABLE TRIGGER USER"))


async def test_empty_chain_is_intact(
    audit: AuditTrail, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    async with session_factory() as session:
        report = await audit.verify_chain(session)
    assert report.intact
    assert report.rows_checked == 0
    assert report.head_hash == GENESIS_HASH


async def test_rows_link_to_one_another(
    audit: AuditTrail, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await write_rows(audit, session_factory, 5)
    async with session_factory() as session:
        rows = (await session.scalars(select(AuditLog).order_by(AuditLog.seq))).all()
        report = await audit.verify_chain(session)
    assert [row.seq for row in rows] == [1, 2, 3, 4, 5]
    assert rows[0].prev_hash == GENESIS_HASH
    assert all(
        later.prev_hash == earlier.hash for earlier, later in zip(rows, rows[1:], strict=False)
    )
    assert report.intact
    assert report.rows_checked == 5
    assert report.head_hash == rows[-1].hash


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE audit_log SET actor = 'x'",
        "DELETE FROM audit_log",
        "TRUNCATE audit_log",
    ],
)
async def test_app_role_cannot_change_history(
    audit: AuditTrail, session_factory: async_sessionmaker[AsyncSession], statement: str
) -> None:
    await write_rows(audit, session_factory, 1)
    async with session_factory() as session:
        with pytest.raises(ProgrammingError, match="permission denied"):
            await session.execute(text(statement))


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE audit_log SET actor = 'x'",
        "DELETE FROM audit_log",
        "TRUNCATE audit_log",
    ],
)
async def test_even_the_owner_is_stopped_by_the_triggers(
    audit: AuditTrail,
    session_factory: async_sessionmaker[AsyncSession],
    owner_engine: AsyncEngine,
    statement: str,
) -> None:
    await write_rows(audit, session_factory, 1)
    async with owner_engine.connect() as connection:
        with pytest.raises(DBAPIError, match="append-only"):
            await connection.execute(text(statement))


@pytest.mark.parametrize(
    ("statement", "broken_at"),
    [
        ("UPDATE audit_log SET actor = 'someone-else' WHERE seq = 3", 3),
        ("UPDATE audit_log SET action = 'nothing.happened' WHERE seq = 2", 2),
        ("UPDATE audit_log SET resource = 'person:999' WHERE seq = 4", 4),
        ("UPDATE audit_log SET outcome = 'denied' WHERE seq = 1", 1),
        ("""UPDATE audit_log SET meta = '{"count": 99}' WHERE seq = 3""", 3),
        ("UPDATE audit_log SET at = at + interval '1 second' WHERE seq = 2", 2),
        ("DELETE FROM audit_log WHERE seq = 3", 4),
        ("DELETE FROM audit_log WHERE seq = 1", 2),
    ],
)
async def test_tampering_with_any_column_is_detected(
    audit: AuditTrail,
    session_factory: async_sessionmaker[AsyncSession],
    owner_engine: AsyncEngine,
    statement: str,
    broken_at: int,
) -> None:
    await write_rows(audit, session_factory, 5)
    await tamper(owner_engine, statement)
    async with session_factory() as session:
        report = await audit.verify_chain(session)
    assert not report.intact
    assert report.broken_at_seq == broken_at


async def test_recomputing_a_hash_without_the_key_is_detected(
    audit: AuditTrail,
    session_factory: async_sessionmaker[AsyncSession],
    owner_engine: AsyncEngine,
) -> None:
    """An attacker with database access but not the key can't forge a consistent chain."""
    await write_rows(audit, session_factory, 3)
    forger = AuditTrail(b"guessed-key-that-is-not-the-real-one", session_factory)
    async with session_factory() as session:
        row = await session.scalar(select(AuditLog).where(AuditLog.seq == 3))
        assert row is not None
    forged = forger._digest(
        row.prev_hash,
        _canonical(
            seq=3,
            at=row.at,
            actor="someone-else",
            action=row.action,
            resource=row.resource,
            outcome=row.outcome,
            meta=row.meta,
        ),
    )
    await tamper(
        owner_engine,
        f"UPDATE audit_log SET actor = 'someone-else', hash = '{forged}' WHERE seq = 3",
    )
    async with session_factory() as session:
        assert (await audit.verify_chain(session)).broken_at_seq == 3


async def test_cutting_off_the_newest_rows_shows_in_the_head_hash(
    audit: AuditTrail,
    session_factory: async_sessionmaker[AsyncSession],
    owner_engine: AsyncEngine,
) -> None:
    await write_rows(audit, session_factory, 4)
    async with session_factory() as session:
        anchored_head = (await audit.verify_chain(session)).head_hash
    await tamper(owner_engine, "DELETE FROM audit_log WHERE seq = 4")
    async with session_factory() as session:
        report = await audit.verify_chain(session)
    assert report.intact  # why the head has to be compared with a copy kept elsewhere
    assert report.head_hash != anchored_head


async def test_a_rolled_back_write_leaves_no_gap(
    audit: AuditTrail, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await write_rows(audit, session_factory, 1)
    async with session_factory() as session:
        await audit.append(session, actor="a", action="abandoned", resource="r")
        await session.rollback()
    await write_rows(audit, session_factory, 1)
    async with session_factory() as session:
        seqs = (await session.scalars(select(AuditLog.seq).order_by(AuditLog.seq))).all()
        assert list(seqs) == [1, 2]
        assert (await audit.verify_chain(session)).intact


async def test_concurrent_writers_keep_one_linear_chain(
    audit: AuditTrail, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    async def writer(number: int) -> None:
        async with session_factory() as session, session.begin():
            await audit.append(session, actor=f"w{number}", action="write", resource="r")

    await asyncio.gather(*(writer(number) for number in range(20)))
    async with session_factory() as session:
        report = await audit.verify_chain(session)
        total = await session.scalar(select(func.count()).select_from(AuditLog))
    assert report.intact
    assert report.rows_checked == total == 20


async def test_verify_handles_more_rows_than_one_batch(
    audit: AuditTrail,
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.privacy.audit._VERIFY_BATCH", 2)
    await write_rows(audit, session_factory, 5)
    async with session_factory() as session:
        report = await audit.verify_chain(session)
    assert report.intact
    assert report.rows_checked == 5


async def test_chain_written_with_another_key_fails_verification(
    audit: AuditTrail, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await write_rows(audit, session_factory, 2)
    other = AuditTrail(b"x" * 32, session_factory)
    async with session_factory() as session:
        assert (await other.verify_chain(session)).broken_at_seq == 1


@pytest.mark.parametrize(
    "meta",
    [
        {"gene": "HBB"},
        {"notes": "anything"},
        {"reason": {"nested": "value"}},
        {"reason": ["a", "list"]},
        {"reason": "x" * 201},
    ],
)
async def test_meta_cannot_carry_health_data(
    audit: AuditTrail,
    session_factory: async_sessionmaker[AsyncSession],
    meta: dict[str, object],
) -> None:
    async with session_factory() as session:
        with pytest.raises(ValueError, match="audit meta"):
            await audit.append(session, actor="a", action="b", resource="c", meta=meta)


async def test_timestamps_in_another_zone_hash_the_same_instant(
    audit: AuditTrail, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """Postgres can hand a timestamp back in the session's zone. The hash must not care."""
    moment = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)
    elsewhere = moment.astimezone(timezone(timedelta(hours=5, minutes=30)))
    shared = {
        "seq": 1,
        "actor": "a",
        "action": "b",
        "resource": "c",
        "outcome": "ok",
        "meta": {},
    }
    assert _canonical(at=moment, **shared) == _canonical(at=elsewhere, **shared)


async def test_unicode_in_rows_survives_the_round_trip(
    audit: AuditTrail, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    async with session_factory() as session, session.begin():
        await audit.append(
            session, actor="a", action="b", resource="c", meta={"reason": "परिवार की अनुमति"}
        )
    async with session_factory() as session:
        assert (await audit.verify_chain(session)).intact
