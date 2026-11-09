from datetime import datetime
from http import HTTPStatus

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.case import CareCase, PathwayStep
from app.models.enums import CaseState as S

# A person can decline from any active step. It's a valid choice, and it's why every active state
# below lists it. Withdrawing from care must never be a dead end.
_ACTIVE: dict[S, set[S]] = {
    S.RESULT_RELEASED: {S.EDUCATION_VIEWED, S.COUNSELLING_REQUESTED},
    S.EDUCATION_VIEWED: {S.COMPREHENSION_CHECKED, S.COUNSELLING_REQUESTED},
    S.COMPREHENSION_CHECKED: {S.COUNSELLING_REQUESTED, S.CLOSED},
    S.COUNSELLING_REQUESTED: {S.COUNSELLING_BOOKED},
    # Back to requested when an appointment is cancelled, so it can be booked again.
    S.COUNSELLING_BOOKED: {S.COUNSELLING_DONE, S.COUNSELLING_REQUESTED},
    S.COUNSELLING_DONE: {S.CONFIRMATORY_TEST_ORDERED, S.CLOSED},
    S.CONFIRMATORY_TEST_ORDERED: {S.CONFIRMED, S.NOT_CONFIRMED},
    S.CONFIRMED: {S.REPRO_GENOMICS_REFERRED, S.CLOSED},
    S.NOT_CONFIRMED: {S.COUNSELLING_REQUESTED, S.CLOSED},
    S.REPRO_GENOMICS_REFERRED: {S.REFERRAL_ACCEPTED},
    S.REFERRAL_ACCEPTED: {S.CLOSED},
}
TRANSITIONS: dict[S, set[S]] = {
    **{
        state: {*allowed, S.DECLINED_BY_USER, S.LOST_TO_FOLLOW_UP}
        for state, allowed in _ACTIVE.items()
    },
    S.DECLINED_BY_USER: {S.COUNSELLING_REQUESTED, S.CLOSED},
    S.LOST_TO_FOLLOW_UP: {S.COUNSELLING_REQUESTED, S.CLOSED},
    S.CLOSED: set(),
}


async def record_opening(db: AsyncSession, case: CareCase, *, actor: str) -> None:
    db.add(PathwayStep(case_id=case.id, from_state=None, to_state=case.state, actor=actor))
    await db.flush()


async def transition(
    db: AsyncSession,
    case: CareCase,
    to_state: S,
    *,
    actor: str,
    step_due: datetime,
    fhir_ref: str | None = None,
) -> None:
    """The only place a case changes state, so every change leaves a step behind.

    Time-to-referral is measured from those steps. A change that skipped this would drop the case
    out of the metric, and the most urgent cases are the ones that move fastest.
    """
    current = S(case.state)
    if to_state not in TRANSITIONS[current]:
        raise ApiError(HTTPStatus.CONFLICT, "invalid_transition")
    case.state = to_state.value
    case.step_due = step_due
    case.stalled = False
    db.add(
        # Steps are insert-only for the app's database role, so the FHIR reference goes in now.
        PathwayStep(
            case_id=case.id,
            from_state=current.value,
            to_state=to_state.value,
            actor=actor,
            fhir_ref=fhir_ref,
        )
    )
    await db.flush()
