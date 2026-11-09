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
    """What a person sees: when and how. Not who, until they've booked and met."""

    id: UUID
    starts_at: datetime
    ends_at: datetime
    mode: str
    lang: str


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
    name: str
    region: str
    services: str
    contact: str | None
    source_url: str
    checked_on: str


class CentresOut(Out):
    pack: str
    pack_reviewed: bool
    # Who counts as the qualified person in this country, or "none" if nobody has checked one.
    qualified_human: str
    centres: list[CentreOut]
    funding_notes: list[str]
    as_of: date | None
