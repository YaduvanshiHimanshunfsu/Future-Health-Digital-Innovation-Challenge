"""Moving a care case along its pathway. Everything here goes through `state_machine.transition`.

Each move sets the next step's deadline from the country pack (O5.1.4) and clears the step's reminder.
The step row `transition` writes is the measurement: pathway metrics read those rows, so there is one
source for them, not two. Two people changing one case at once can't both win: the case row is
versioned, and the loser gets 409 (V5.1.7).
"""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from http import HTTPStatus

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.core.errors import ApiError
from app.country_packs.loader import CountryPack
from app.models.case import CareCase
from app.models.enums import CaseState as S
from app.pathway.state_machine import TRANSITIONS, transition
from app.triage.service import sla_hours

# No deadline applies once a case has ended, or while a person has stepped back.
RESTING = frozenset({S.CLOSED, S.DECLINED_BY_USER, S.LOST_TO_FOLLOW_UP})
# Steps a person can take themselves. The rest belong to the care team.
PERSON_MAY = frozenset({S.EDUCATION_VIEWED, S.COUNSELLING_REQUESTED, S.DECLINED_BY_USER})
# Steps a counsellor takes. Booking is done through the booking routes, so it isn't here.
STAFF_MAY = frozenset(
    {
        S.COUNSELLING_DONE,
        S.CONFIRMATORY_TEST_ORDERED,
        S.CONFIRMED,
        S.NOT_CONFIRMED,
        S.REPRO_GENOMICS_REFERRED,
        S.REFERRAL_ACCEPTED,
        S.LOST_TO_FOLLOW_UP,
        S.CLOSED,
    }
)


def next_due(pack: CountryPack, priority: str, state: S, now: datetime) -> datetime:
    """A fresh window for every step, so advancing never leaves a case instantly overdue (V5.1.5)."""
    if state in RESTING:
        return now
    return now + timedelta(hours=sla_hours(pack, priority))


async def advance(
    db: AsyncSession,
    case: CareCase,
    to_state: S,
    *,
    actor: str,
    pack: CountryPack,
    now: datetime | None = None,
    fhir_ref: str | None = None,
) -> None:
    moment = now or datetime.now(UTC)
    await transition(
        db,
        case,
        to_state,
        actor=actor,
        step_due=next_due(pack, case.priority, to_state, moment),
        fhir_ref=fhir_ref,
    )
    case.reminded_at = None


def can_move(case: CareCase, to_state: S) -> bool:
    return to_state in TRANSITIONS[S(case.state)]


async def commit_or_conflict(db: AsyncSession, work: Callable[[], Awaitable[None]]) -> None:
    """Runs a change and commits it. If someone else changed the case first, nothing is kept."""
    try:
        await work()
        await db.commit()
    except StaleDataError:
        await db.rollback()
        raise ApiError(HTTPStatus.CONFLICT, "case_changed") from None
