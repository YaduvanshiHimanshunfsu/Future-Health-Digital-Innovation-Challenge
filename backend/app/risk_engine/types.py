from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction


class Classification(StrEnum):
    PATHOGENIC = "P"
    LIKELY_PATHOGENIC = "LP"
    UNCERTAIN = "VUS"


class Zygosity(StrEnum):
    HETEROZYGOUS = "het"
    HOMOZYGOUS = "hom"
    HEMIZYGOUS = "hemi"


class Inheritance(StrEnum):
    AUTOSOMAL_RECESSIVE = "AR"
    X_LINKED = "XL"


class Sex(StrEnum):
    FEMALE = "F"
    MALE = "M"
    UNKNOWN = "U"


class Relationship(StrEnum):
    DOUBLE_FIRST_COUSINS = "double_first_cousins"
    FIRST_COUSINS = "first_cousins"
    FIRST_COUSINS_ONCE_REMOVED = "first_cousins_once_removed"
    SECOND_COUSINS = "second_cousins"
    UNRELATED = "unrelated"
    UNKNOWN = "unknown"


class Scenario(StrEnum):
    CARRIER_SELF = "carrier_self"
    POSSIBLE_AFFECTED = "possible_affected"
    UNCERTAIN_VUS = "uncertain_vus"
    REFER = "refer"
    XL_CARRIER_FEMALE = "xl_carrier_female"
    XL_TWO_COPIES_FEMALE = "xl_two_copies_female"
    XL_FATHER = "xl_father"
    COUPLE_XL = "couple_xl"
    COUPLE_SHARED_AR = "couple_shared_ar"
    COUPLE_REVIEW = "couple_review"
    COUPLE_ONE_CARRIER_TESTED_NEGATIVE = "couple_one_carrier_tested_negative"
    COUPLE_ONE_CARRIER_UNTESTED = "couple_one_carrier_untested"
    CONSANGUINITY_BACKGROUND = "consanguinity_background"


class Flag(StrEnum):
    """What triage needs to know. Facts carry these so triage never re-derives clinical logic."""

    POSSIBLE_AFFECTED = "possible_affected"
    POSSIBLE_AFFECTED_ROUTINE = "possible_affected_routine"
    VUS = "vus"
    SHARED_AR = "shared_ar"
    XL_FEMALE = "xl_female"
    XL_COUPLE = "xl_couple"
    REVIEW_NEEDED = "review_needed"
    UNKNOWN_GENE = "unknown_gene"
    INCONSISTENT_DATA = "inconsistent_data"
    CONSANGUINEOUS = "consanguineous"


class Label(StrEnum):
    CARRIER = "carrier"
    TWO_COPIES = "two_copies"
    NEITHER = "neither"
    UNCERTAIN = "uncertain"
    REFER = "refer"
    POSSIBLE_AFFECTED = "possible_affected"
    SON_AFFECTED = "son_affected"
    DAUGHTER_CARRIER = "daughter_carrier"
    DAUGHTER_TWO_COPIES = "daughter_two_copies"
    DAUGHTER_NEITHER = "daughter_neither"
    REVIEW = "review"
    BACKGROUND = "background"


class Viewer(StrEnum):
    A = "a"
    B = "b"


class Reveal(StrEnum):
    YES_NO = "yes_no"
    GENES = "genes"


@dataclass(frozen=True, slots=True)
class Finding:
    gene: str
    classification: Classification
    zygosity: Zygosity
    variant: str = ""

    @property
    def is_pathogenic(self) -> bool:
        return self.classification is not Classification.UNCERTAIN


@dataclass(frozen=True, slots=True)
class RiskFact:
    id: str
    scenario: Scenario
    gene: str | None
    label: Label
    value: Fraction | None
    citation: str
    rule_version: str
    flags: frozenset[Flag] = field(default_factory=frozenset)

    @property
    def percent(self) -> str | None:
        if self.value is None:
            return None
        percent = self.value * 100
        if percent.denominator == 1:
            return str(percent.numerator)
        return f"{float(percent):.2g}"

    @property
    def one_in(self) -> int | None:
        if not self.value:
            return None
        return round(1 / self.value)

    @property
    def has_number(self) -> bool:
        return self.value is not None


@dataclass(frozen=True, slots=True)
class PartnerRecord:
    findings: tuple[Finding, ...]
    sex: Sex
    # Genes on the panel this partner was tested with. None means no report exists at all.
    tested_genes: frozenset[str] | None


@dataclass(frozen=True, slots=True)
class CoupleFact:
    fact: RiskFact
    visible_to: frozenset[Viewer]


@dataclass(frozen=True, slots=True)
class CoupleAssessment:
    """Holds both partners' information, so it must never be returned or logged as it stands.

    Everything that leaves the engine goes through `partner_view`.
    """

    facts: tuple[CoupleFact, ...]
    shared_genes: frozenset[str]
    review_needed: bool

    @property
    def any_shared(self) -> bool:
        return bool(self.shared_genes) or self.review_needed

    def __repr__(self) -> str:
        return "CoupleAssessment(<withheld>)"
