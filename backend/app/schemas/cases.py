from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import Out, StrictIn


class CaseOut(Out):
    id: UUID
    priority: str
    state: str
    step_due: datetime
    reasons: list[str]
    through_break_glass: bool


class BreakGlassIn(StrictIn):
    reason: str = Field(min_length=10, max_length=500)


class BreakGlassOut(Out):
    event_id: UUID
    expires_at: datetime
    access_ready: bool


class BreakGlassEventOut(Out):
    id: UUID
    case_id: UUID
    actor_id: UUID
    reason: str
    expires_at: datetime
    created_at: datetime
