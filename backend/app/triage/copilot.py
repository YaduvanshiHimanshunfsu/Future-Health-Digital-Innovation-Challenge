"""A case summary for the counsellor, built only from structured data.

No AI writes any of it, so it can't add a clinical claim. It says "verify before use", because the
facts come from rules no clinician has reviewed yet, and it never writes to the clinical record.
"""

from dataclasses import dataclass

from app.risk_engine.types import RiskFact


@dataclass(frozen=True, slots=True)
class SummaryFact:
    scenario: str
    gene: str | None
    label: str
    percent: str | None


@dataclass(frozen=True, slots=True)
class CaseSummary:
    facts: tuple[SummaryFact, ...]
    values: dict[str, str] | None
    verify_before_use: bool = True


def summarise(facts: list[RiskFact], values: dict[str, str] | None) -> CaseSummary:
    return CaseSummary(
        facts=tuple(SummaryFact(f.scenario.value, f.gene, f.label.value, f.percent) for f in facts),
        values=values,
    )
