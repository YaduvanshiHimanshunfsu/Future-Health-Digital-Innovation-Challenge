from collections.abc import Iterable
from dataclasses import dataclass

from app.models.enums import Priority
from app.risk_engine.types import Flag, RiskFact


@dataclass(frozen=True, slots=True)
class TriageResult:
    priority: Priority
    reasons: tuple[str, ...]


def score(
    facts: Iterable[RiskFact],
    *,
    distress: bool = False,
    pregnant: bool = False,
    teach_back_failures: int = 0,
    asked_for_human: bool = False,
    asked_about_extended_testing: bool = False,
) -> TriageResult | None:
    """Transparent rules. The highest matching priority wins, and each case records why."""
    collected = list(facts)
    flags = {flag for fact in collected for flag in fact.flags}
    shared_genes = {fact.gene for fact in collected if Flag.SHARED_AR in fact.flags}
    needs_review = Flag.REVIEW_NEEDED in flags
    has_shared_finding = bool(shared_genes) or needs_review or Flag.XL_COUPLE in flags

    urgent: list[str] = []
    if distress:
        urgent.append("distress")
    if pregnant and (has_shared_finding or Flag.XL_FEMALE in flags):
        urgent.append("pregnant_with_finding")
    if Flag.POSSIBLE_AFFECTED in flags:
        urgent.append("possibly_affected")
    if urgent:
        return TriageResult(Priority.P1, tuple(urgent))

    high: list[str] = []
    if shared_genes:
        high.append("shared_finding")
    if len(shared_genes) >= 2:
        high.append("several_shared_findings")
    if needs_review:
        high.append("couple_review")
    if Flag.XL_FEMALE in flags:
        high.append("x_linked_carrier")
    if Flag.XL_COUPLE in flags:
        high.append("x_linked_couple")
    if high:
        return TriageResult(Priority.P2, tuple(high))

    standard: list[str] = []
    if Flag.VUS in flags:
        standard.append("uncertain_finding")
    if Flag.UNKNOWN_GENE in flags or Flag.INCONSISTENT_DATA in flags:
        standard.append("needs_clinical_check")
    if Flag.POSSIBLE_AFFECTED_ROUTINE in flags:
        standard.append("possibly_affected_routine")
    if Flag.CONSANGUINEOUS in flags and asked_about_extended_testing:
        standard.append("extended_testing_question")
    if teach_back_failures >= 2:
        standard.append("understanding_support")
    if standard:
        return TriageResult(Priority.P3, tuple(standard))

    return TriageResult(Priority.P4, ("asked_for_a_person",)) if asked_for_human else None
