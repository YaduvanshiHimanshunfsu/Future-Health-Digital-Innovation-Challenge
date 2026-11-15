"""Booking, referral and centre contracts. Inputs refuse unknown fields; outputs list theirs."""

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from app.models.enums import AppointmentMode, ReferralKind
from app.schemas.common import LanguageCode, Out, StrictIn


class SlotIn(StrictIn):
    starts_at: datetime
    minutes: Literal[30, 45, 60] = 30
    mode: AppointmentMode = AppointmentMode.VIDEO
    lang: LanguageCode = "en"


class SlotOut(Out):
    """When, how, and with which counsellor.

    The counsellor was hidden until booking at first. The user chose on 15 Nov 2026 to show the team
    and their availability, as booking services do. What stays hidden is anything about another
    client: a busy counsellor is shown as busy, never with whom.
    """

    id: UUID
    counsellor_id: UUID
    starts_at: datetime
    ends_at: datetime
    mode: str
    lang: str


class CounsellorOut(Out):
    id: UUID
    display_name: str
    role: str
    languages: list[str]
    fictional: bool
    # in_session, free_soon (within a day), free_later or no_times. From their calendar only.
    status: str
    next_open: datetime | None
    # This counsellor already has the person's case, so only their times are offered.
    yours: bool


class BookIn(StrictIn):
    case_id: UUID


class AppointmentOut(SlotOut):
    status: str


class StaffAppointmentOut(AppointmentOut):
    case_id: UUID | None


class ReferralIn(StrictIn):
    kind: ReferralKind
    # Where it's going, such as a laboratory or clinic. Not a person's details.
    destination: str = Field(min_length=2, max_length=128)


class ReferralOut(Out):
    id: UUID
    case_id: UUID
    kind: str
    destination: str
    status: str
    created_at: datetime
    # FHIR R5 ServiceRequest and Task, with the minimum necessary fields.
    service_request: dict[str, Any]
    task: dict[str, Any]


class CentreOut(Out):
    id: str
    # True for an invented demo entry. Screens must say so on the entry itself.
    fictional: bool
    name: str
    city: str
    region: str
    kind: str
    services: list[str]
    modes: list[str]
    step_free: bool | None
    lat: float
    lon: float
    contact: str | None
    source_url: str | None
    checked_on: str | None


class CentresOut(Out):
    pack: str
    pack_name: str
    pack_reviewed: bool
    # Who counts as the qualified person in this country, or "none" if nobody has checked one.
    qualified_human: str
    # How many the pack lists before any filter, and how many of those are invented.
    total: int
    fictional_count: int
    # The pack's regions that have at least one centre, in the pack's own order.
    regions: list[str]
    # The pack's own names for regions that are proper names. Others are translated on screen.
    region_names: dict[str, str]
    centres: list[CentreOut]
    funding_notes: list[str]
    # The oldest check date among the real centres shown. None when none of them is real.
    as_of: date | None
