from datetime import datetime
from typing import Literal
from uuid import UUID

from app.models.enums import CaseState
from app.schemas.common import Out, StrictIn


class JourneyStepOut(Out):
    state: str
    at: datetime
    # Who made the change, as a kind, never a name or an account ID.
    by: Literal["you", "care_team", "system"]


class JourneyOut(Out):
    case_id: UUID
    state: str
    step_due: datetime
    with_partner: bool
    steps: list[JourneyStepOut]
    # What the person can do next themselves, such as asking for counselling or stepping back.
    next_steps: list[str]
    reminders_off: bool


class StepIn(StrictIn):
    to_state: CaseState


class RemindersIn(StrictIn):
    opt_out: bool
