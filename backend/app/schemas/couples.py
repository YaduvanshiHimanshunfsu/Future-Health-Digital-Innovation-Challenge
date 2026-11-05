from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.risk_engine.types import Relationship
from app.schemas.common import Out, StrictIn
from app.schemas.results import FactOut


class CoupleCreateIn(StrictIn):
    relationship: Relationship = Relationship.UNKNOWN


class CoupleCreatedOut(Out):
    id: UUID
    # Shown once. Only its hash is stored.
    invite_code: str
    expires_at: datetime | None


class CoupleJoinIn(StrictIn):
    invite_code: str = Field(min_length=16, max_length=64)
    relationship: Relationship = Relationship.UNKNOWN


class MatchConsentIn(StrictIn):
    reveal_level: Literal["yes_no", "genes"] = "yes_no"
    terms_version: str = Field(min_length=1, max_length=16)
    # What a "yes" reveals has to be read and accepted, because it isn't fully blind (issue S8).
    understood_what_a_result_reveals: Literal[True]


class FollowUpOut(Out):
    case_id: UUID
    state: str


class CoupleOut(Out):
    """Holds this person's own choices only. Nothing here shows what the partner has decided."""

    id: UUID
    partner_joined: bool
    my_consent_id: UUID | None
    my_reveal_level: str | None
    what_a_result_reveals: str
    follow_up: FollowUpOut | None


class MatchIn(StrictIn):
    """Takes nothing. It exists so that a request carrying a gene list is refused, not ignored."""


class MatchOut(Out):
    outcome: Literal["shared", "none_shared", "cannot_determine"]
    reveal_level: Literal["yes_no", "genes"]
    # Null unless both partners chose to see gene names.
    shared_genes: list[str] | None
    facts: list[FactOut]
    visuals: list[dict[str, object]]
    follow_up_case_id: UUID | None
    notice: str
