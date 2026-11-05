from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import Out, StrictIn
from app.schemas.results import FactOut, PackInfo


class ReceiveCodeOut(Out):
    code: str
    expires_at: datetime


class GrantIn(StrictIn):
    grantee_code: str = Field(min_length=16, max_length=64)
    kind: Literal["share_summary", "share_full"]
    purpose: str = Field(max_length=32)
    terms_version: str = Field(min_length=1, max_length=16)
    duration_days: int = Field(ge=1, le=365)


class ConsentOut(Out):
    id: UUID
    kind: str
    purpose: str
    reveal_level: str | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    active: bool


class GrantedOut(ConsentOut):
    # False means the share is saved and access will follow shortly. It's never true early.
    access_ready: bool


class ConsentListOut(Out):
    given: list[ConsentOut]
    # Only live ones: someone who was shared with isn't shown a record of being cut off.
    received: list[ConsentOut]


class SummaryFactOut(Out):
    gene: str | None
    label: str


class SharedSummaryOut(Out):
    scope: Literal["summary"] = "summary"
    has_report: bool
    facts: list[SummaryFactOut]
    pack: PackInfo


class SharedFullOut(Out):
    scope: Literal["full"] = "full"
    has_report: bool
    facts: list[FactOut]
    visuals: list[dict[str, object]]
    pack: PackInfo


class AccessEntryOut(Out):
    at: datetime
    who: str
    action: str
    summary: str
    outcome: str
    flagged: bool


class AccessLogOut(Out):
    entries: list[AccessEntryOut]
