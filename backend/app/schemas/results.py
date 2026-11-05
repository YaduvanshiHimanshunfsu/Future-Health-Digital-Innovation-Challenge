from datetime import datetime
from typing import Any
from uuid import UUID

from app.risk_engine.types import RiskFact
from app.schemas.common import Out


class FactOut(Out):
    id: str
    scenario: str
    gene: str | None
    label: str
    percent: str | None
    one_in: int | None
    has_number: bool
    citation: str

    @classmethod
    def from_fact(cls, fact: RiskFact) -> "FactOut":
        return cls(
            id=fact.id,
            scenario=fact.scenario.value,
            gene=fact.gene,
            label=fact.label.value,
            percent=fact.percent,
            one_in=fact.one_in,
            has_number=fact.has_number,
            citation=fact.citation,
        )


class PackInfo(Out):
    code: str
    status: str
    # Shown on screen, so an unreviewed country can't look like a supported one.
    reviewed: bool


class MyResultsOut(Out):
    has_report: bool
    facts: list[FactOut]
    panels: list[str]
    # Condition keys per gene in this person's own facts, from the country pack.
    conditions: dict[str, list[str]] = {}
    pack: PackInfo
    # The person has chosen not to know. Facts stay empty until they change their mind.
    withheld: bool = False
    # A counsellor will be in touch. Says nothing about why.
    human_contact_required: bool = False


class MyRiskOut(Out):
    has_report: bool
    facts: list[FactOut]
    visuals: list[dict[str, Any]]
    pack: PackInfo
    withheld: bool = False
    human_contact_required: bool = False


class CareStepOut(Out):
    """A person's own follow-up. Priority and reasons stay with the counsellor."""

    case_id: UUID
    state: str
    step_due: datetime
    with_partner: bool
