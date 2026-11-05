from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import ApiError
from app.models.case import CareCase, PathwayStep
from app.models.enums import CaseState as S
from app.models.person import Person
from app.pathway.state_machine import TRANSITIONS, record_opening, transition

ACTIVE = [state for state in S if state not in (S.CLOSED, S.DECLINED_BY_USER, S.LOST_TO_FOLLOW_UP)]


@pytest.mark.parametrize("state", ACTIVE)
def test_a_person_can_decline_from_every_active_step(state: S) -> None:
    """V5.1.3, early. The original spec had dead ends once a test or referral was ordered."""
    assert S.DECLINED_BY_USER in TRANSITIONS[state]


def test_someone_who_declined_can_change_their_mind() -> None:
    assert S.COUNSELLING_REQUESTED in TRANSITIONS[S.DECLINED_BY_USER]


def test_a_test_that_does_not_confirm_the_finding_is_its_own_outcome() -> None:
    assert S.NOT_CONFIRMED in TRANSITIONS[S.CONFIRMATORY_TEST_ORDERED]


def test_every_state_has_an_entry() -> None:
    assert set(TRANSITIONS) == set(S)
    assert TRANSITIONS[S.CLOSED] == set()


@pytest.mark.db
async def test_every_change_writes_a_step_and_resets_the_deadline(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        person = Person(keycloak_sub="x", pack_code="ae-abu-dhabi", preferred_lang="en")
        session.add(person)
        await session.flush()
        case = CareCase(
            subject_id=person.id,
            priority="P4",
            reasons_enc=b"x",
            step_due=datetime.now(UTC) - timedelta(days=1),
            stalled=True,
        )
        session.add(case)
        await session.flush()
        await record_opening(session, case, actor="system")
        later = datetime.now(UTC) + timedelta(days=3)
        await transition(session, case, S.COUNSELLING_REQUESTED, actor="system", step_due=later)

        steps = (await session.scalars(select(PathwayStep).order_by(PathwayStep.at))).all()
        states = {(step.from_state, step.to_state) for step in steps}
        assert states == {
            (None, S.RESULT_RELEASED.value),
            (S.RESULT_RELEASED.value, S.COUNSELLING_REQUESTED.value),
        }
        assert case.step_due == later
        assert case.stalled is False


@pytest.mark.db
async def test_invalid_transition_is_refused(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        person = Person(keycloak_sub="y", pack_code="ae-abu-dhabi", preferred_lang="en")
        session.add(person)
        await session.flush()
        case = CareCase(
            subject_id=person.id, priority="P4", reasons_enc=b"x", step_due=datetime.now(UTC)
        )
        session.add(case)
        await session.flush()
        with pytest.raises(ApiError) as caught:
            await transition(session, case, S.CLOSED, actor="a", step_due=datetime.now(UTC))
        assert caught.value.status == 409
