from datetime import date
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    # AR and XL (X-linked recessive) are carrier patterns. AD and XLD are dominant: one changed
    # copy is enough, so nobody is a carrier and the person themselves may be affected.
    inheritance: Literal["AR", "XL", "AD", "XLD"]
    # How often the changed copy is seen. For a dominant gene there are no carriers, so this is
    # the frequency of the change itself, and the engine never uses it to work out a couple's risk.
    carrier_frequency: float = Field(gt=0, lt=1)
    detection_rate: float = Field(ge=0, le=1)
    conditions: list[str] = []
    # Known variants and the one condition each causes, by HGVS. One gene can cause different
    # conditions: in HBB, c.20A>T is the sickle cell change and c.92+5G>C a beta thalassaemia one.
    # A variant missing from here is shown with every condition the gene can cause, and says so.
    variants: dict[str, str] = {}
    risk_group: str | None = None
    routine_when_hemizygous: bool = False
    source: str

    @model_validator(mode="after")
    def _variants_name_known_conditions(self) -> Self:
        stray = set(self.variants.values()) - set(self.conditions)
        if stray:
            raise ValueError(f"variants name conditions the gene doesn't list: {sorted(stray)}")
        return self


class Panel(_Strict):
    values_status: Literal["placeholder", "reviewed"]
    panels: dict[str, list[str]]
    genes: dict[str, GeneEntry]


CentreService = Literal[
    "genetic_counselling",
    "carrier_screening",
    "confirmatory_testing",
    "prenatal_diagnosis",
    "haemoglobin_clinic",
    "family_testing",
]
VisitMode = Literal["in_person", "video"]


class Centre(_Strict):
    id: str = Field(pattern=r"^[a-z0-9-]{3,48}$")
    # Required, with no default: nobody can add a centre without saying whether it is real.
    fictional: bool
    name: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=60)
    region: str
    kind: Literal["public_hospital", "private_hospital", "academic", "community_clinic"]
    services: list[CentreService] = Field(min_length=1)
    modes: list[VisitMode] = Field(min_length=1)
    # None means nobody has checked, which is not the same as "no".
    step_free: bool | None = None
    # A city's position, for the schematic map. Never a street address.
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    contact: str | None = None
    source_url: str | None = None
    checked_on: str | None = None

    @model_validator(mode="after")
    def _real_or_plainly_invented(self) -> Self:
        if len(set(self.services)) != len(self.services) or len(set(self.modes)) != len(self.modes):
            raise ValueError(f"{self.id}: a service or visit mode is listed twice")
        if self.fictional:
            # An invented centre gets no phone, website or check date, so it can never send
            # anyone to a real number or a real door.
            if self.contact or self.source_url or self.checked_on:
                raise ValueError(f"{self.id}: a fictional centre carries no contact or source")
        else:
            if not (self.source_url and self.checked_on):
                raise ValueError(f"{self.id}: a real centre needs source_url and checked_on")
            date.fromisoformat(self.checked_on)
        return self


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
    # Display names for regions that are proper names, such as a city. Generic ones like "north"
    # are translated by the screens; a proper name belongs to its country, so it lives here.
    region_names: dict[str, str] = {}
    age_bands: list[str] = []
    genders: list[str] = []
    sla_hours: SlaHours = SlaHours()

    @model_validator(mode="after")
    def _names_are_for_listed_regions(self) -> Self:
        stray = set(self.region_names) - set(self.regions)
        if stray:
            raise ValueError(f"region_names for regions not listed: {sorted(stray)}")
        return self
