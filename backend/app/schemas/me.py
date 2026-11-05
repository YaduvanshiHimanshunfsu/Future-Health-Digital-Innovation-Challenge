from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import ReadingLevel
from app.schemas.common import LanguageCode, Out, StrictIn


class ProvisionIn(StrictIn):
    # Which country's rules to use when no report has linked the person to one yet.
    pack_code: str | None = Field(default=None, max_length=32)


class ProfilePatch(StrictIn):
    preferred_lang: LanguageCode | None = None
    literacy_level: ReadingLevel | None = None
    region: str | None = Field(default=None, max_length=32)
    age_band: str | None = Field(default=None, max_length=8)
    gender: str | None = Field(default=None, max_length=16)


class ServiceConsentIn(StrictIn):
    terms_version: str = Field(min_length=1, max_length=16)
    accepted: bool


class ResultsPreferenceIn(StrictIn):
    withhold: bool
    terms_version: str = Field(min_length=1, max_length=16)


class ProfileOut(Out):
    id: UUID
    pack_code: str
    preferred_lang: str
    literacy_level: str
    region: str | None
    age_band: str | None
    gender: str | None
    service_consent_at: datetime | None
    results_withheld: bool
    # False means no lab report has been matched to this person.
    linked_to_national_id: bool
