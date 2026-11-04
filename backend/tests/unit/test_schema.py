import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import LargeBinary, inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

import app.models  # noqa: F401
from app.db.base import Base
from app.models.appointment import Appointment
from app.models.consent import Consent
from app.models.couple import Couple
from app.models.person import Person

CLASSIFICATION = (
    Path(__file__).resolve().parents[3] / "docs" / "security" / "data_classification.md"
)


def test_every_column_is_classified() -> None:
    """A new column can't slip in unclassified: this fails until someone documents the decision."""
    documented = set(
        re.findall(r"^\| `(\w+\.\w+)` \|", CLASSIFICATION.read_text("utf-8"), flags=re.M)
    )
    columns = {
        f"{table.name}.{column.name}"
        for table in Base.metadata.sorted_tables
        for column in table.columns
    }
    assert columns - documented == set(), "columns with no classification"
    assert documented - columns == set(), "documented columns that no longer exist"


def test_encrypted_columns_follow_the_naming_rule() -> None:
    for table in Base.metadata.sorted_tables:
        for column in table.columns:
            is_binary = isinstance(column.type, LargeBinary)
            assert is_binary == column.name.endswith("_enc"), f"{table.name}.{column.name}"


def test_care_case_is_not_named_case() -> None:
    names = {table.name for table in Base.metadata.sorted_tables}
    assert "care_case" in names
    assert "case" not in names


@pytest.mark.db
async def test_migrations_match_the_models_exactly(
    migrated: str, alembic_runner: Callable[..., Any]
) -> None:
    result = alembic_runner("check")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.db
async def test_downgrade_removes_everything_and_upgrade_restores_it(
    owner_engine: AsyncEngine, alembic_runner: Callable[..., Any]
) -> None:
    def table_names(connection: Any) -> set[str]:
        return set(inspect(connection).get_table_names())

    down = alembic_runner("downgrade", "base")
    assert down.returncode == 0, down.stdout + down.stderr
    async with owner_engine.connect() as connection:
        assert await connection.run_sync(table_names) == {"alembic_version"}

    up = alembic_runner("upgrade", "head")
    assert up.returncode == 0, up.stdout + up.stderr
    async with owner_engine.connect() as connection:
        found = await connection.run_sync(table_names)
    assert {table.name for table in Base.metadata.sorted_tables} <= found


@pytest.mark.db
@pytest.mark.parametrize(
    "statement",
    [
        "CREATE TABLE sneaky (id int)",
        "DROP TABLE person",
        "ALTER TABLE person ADD COLUMN sneaky int",
        "ALTER TABLE audit_log DISABLE TRIGGER USER",
    ],
)
async def test_api_role_cannot_change_the_schema(
    session_factory: async_sessionmaker[AsyncSession], statement: str
) -> None:
    async with session_factory() as session:
        with pytest.raises(ProgrammingError):
            await session.execute(text(statement))


@pytest.mark.db
@pytest.mark.parametrize(
    "statement",
    [
        "DELETE FROM consent",
        "DELETE FROM person",
        "DELETE FROM pathway_step",
        "UPDATE pathway_step SET actor = 'x'",
        "DELETE FROM event",
        "DELETE FROM carrier_finding",
    ],
)
async def test_records_of_what_happened_cannot_be_erased_by_the_api(
    session_factory: async_sessionmaker[AsyncSession], statement: str
) -> None:
    async with session_factory() as session:
        with pytest.raises(ProgrammingError, match="permission denied"):
            await session.execute(text(statement))


async def _person(session: AsyncSession) -> Person:
    person = Person(keycloak_sub=str(uuid.uuid4()), pack_code="ae-abu-dhabi", preferred_lang="en")
    session.add(person)
    await session.flush()
    return person


@pytest.mark.db
async def test_person_must_have_some_identity(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        session.add(Person(pack_code="ae-abu-dhabi", preferred_lang="en"))
        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.db
async def test_share_without_expiry_is_refused(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        owner = await _person(session)
        other = await _person(session)
        session.add(
            Consent(
                grantor_id=owner.id,
                grantee_id=other.id,
                kind="share_full",
                purpose="partner",
                terms_version="1",
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.db
async def test_one_live_match_consent_per_person_and_couple(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        owner = await _person(session)
        other = await _person(session)
        couple = Couple(person_a=owner.id, person_b=other.id)
        session.add(couple)
        await session.flush()

        def consent(**extra: Any) -> Consent:
            return Consent(
                grantor_id=owner.id,
                couple_id=couple.id,
                kind="couple_match",
                reveal_level="yes_no",
                purpose="couple_match",
                terms_version="1",
                **extra,
            )

        session.add(consent(revoked_at=datetime.now(UTC)))
        session.add(consent())
        await session.flush()  # a revoked consent doesn't block a new one

        session.add(consent())
        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.db
async def test_couple_partners_must_differ(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        owner = await _person(session)
        session.add(Couple(person_a=owner.id, person_b=owner.id))
        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.db
async def test_a_slot_cannot_be_double_booked_unless_cancelled(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    starts = datetime(2026, 12, 1, 9, tzinfo=UTC)

    def slot(counsellor: uuid.UUID, status: str = "booked") -> Appointment:
        return Appointment(
            counsellor_id=counsellor,
            starts_at=starts,
            ends_at=starts + timedelta(minutes=30),
            mode="video",
            lang="en",
            status=status,
        )

    async with session_factory() as session:
        counsellor = await _person(session)
        session.add(slot(counsellor.id, "cancelled"))
        session.add(slot(counsellor.id))
        await session.flush()
        session.add(slot(counsellor.id))
        with pytest.raises(IntegrityError):
            await session.flush()


@pytest.mark.db
async def test_invalid_enum_value_is_refused_by_the_database(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        with pytest.raises(DBAPIError):
            await session.execute(
                text(
                    "INSERT INTO person (id, keycloak_sub, pack_code, preferred_lang, literacy_level)"
                    " VALUES (gen_random_uuid(), 'x', 'p', 'en', 'nonsense')"
                )
            )
