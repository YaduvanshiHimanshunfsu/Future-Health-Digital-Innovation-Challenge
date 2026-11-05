from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import Out, StrictIn


class SummaryFactOut(Out):
    scenario: str
    gene: str | None
    label: str
    percent: str | None


class CaseSummaryOut(Out):
    facts: list[SummaryFactOut]
    # Only what the person chose to share with this case.
    values: dict[str, str] | None
    verify_before_use: bool


class CaseOut(Out):
    id: UUID
    priority: str
    state: str
    step_due: datetime
    reasons: list[str]
    through_break_glass: bool
    summary: CaseSummaryOut | None = None


class QueueItemOut(Out):
    """No identity, and no genetic detail, until a counsellor takes the case on."""

    id: UUID
    priority: str
    state: str
    step_due: datetime
    reasons: list[str]
    assigned_to_me: bool


class AssignIn(StrictIn):
    counsellor_id: UUID


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
