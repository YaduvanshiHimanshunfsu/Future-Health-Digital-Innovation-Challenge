from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _Strict(BaseModel):
    # A pack may only set what's defined here. That's what stops one from carrying something like
    # "disable_validators: true": unknown keys fail at load, and no safety switch exists to set.
    model_config = ConfigDict(extra="forbid", frozen=True)


class PackStatus(StrEnum):
    REVIEWED = "reviewed"
    REFERENCE = "reference"
    ILLUSTRATIVE = "illustrative"
    DRAFT = "draft"


class Manifest(_Strict):
    code: str = Field(pattern=r"^[a-z]{2}-[a-z0-9-]{1,28}$")
    name: str
    status: PackStatus
    reviewers: list[str] = []
    languages: list[str] = Field(min_length=1)
    default_language: str

    @field_validator("default_language")
    @classmethod
    def _default_is_offered(cls, value: str, info: object) -> str:
        languages = getattr(info, "data", {}).get("languages", [])
        if value not in languages:
            raise ValueError("default_language must be one of languages")
        return value


class Option(_Strict):
    key: str
    title: str
    source: str
    reviewed_by: str | None = None
    note: str | None = None


class OptionsFile(_Strict):
    options: list[Option] = []


class Legal(_Strict):
    """Every default is the most restrictive reading, so a missing rule can't loosen anything."""

    hosting_region: str | None = None
    data_may_leave_region: bool = False
    # Years to keep health records. None means nothing may be deleted until someone decides.
    health_record_retention_years: int | None = None
    right_not_to_know: bool = True
    must_inform_if_life_threatening: bool = True
    # Treated as restricted until a reviewer says otherwise.
    sex_selection_restricted: bool = True
    licensed_partner_required: bool = True
    notes: list[str] = []


class GeneEntry(_Strict):
    inheritance: Literal["AR", "XL"]
    carrier_frequency: float = Field(gt=0, lt=1)
    detection_rate: float = Field(ge=0, le=1)
    conditions: list[str] = []
    risk_group: str | None = None
    routine_when_hemizygous: bool = False
    source: str


class Panel(_Strict):
    values_status: Literal["placeholder", "reviewed"]
    panels: dict[str, list[str]]
    genes: dict[str, GeneEntry]


class Centre(_Strict):
    name: str
    region: str
    services: str
    contact: str | None = None
    source_url: str
    checked_on: str


class Services(_Strict):
    # Who counts as the qualified human here. "none" makes the app say so, and AI never fills in.
    qualified_human: Literal["counsellor", "tele_genetics", "trained_clinician", "none"] = "none"
    centres: list[Centre] = []
    funding_notes: list[str] = []


class SupportContact(_Strict):
    service: str
    contact: str
    hours: str
    languages: list[str]
    source_url: str
    checked_on: str
    checked_by: str


class SupportContacts(_Strict):
    contacts: list[SupportContact] = []


class Identity(_Strict):
    national_id_label: str
    national_id_pattern: str
    national_id_fhir_system: str
    # Characters ignored when comparing IDs, such as hyphens in a formatted number.
    national_id_ignore: str = "- "
    phone_pattern: str | None = None
    sign_in_adapter: str = "demo"
    records_adapter: str = "none"


class Lexicon(_Strict):
    lists: dict[str, list[str]] = {}


class SlaHours(_Strict):
    P1: int = Field(default=24, gt=0)
    P2: int = Field(default=72, gt=0)
    P3: int = Field(default=168, gt=0)
    P4: int = Field(default=336, gt=0)


class Strata(_Strict):
    regions: list[str] = []
    age_bands: list[str] = []
    genders: list[str] = []
    sla_hours: SlaHours = SlaHours()
