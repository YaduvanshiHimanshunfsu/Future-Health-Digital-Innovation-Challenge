from fractions import Fraction
from math import floor
from typing import Any

from app.risk_engine.types import Label, RiskFact, Scenario

_SMALLEST_ICON_ARRAY_CHANCE = Fraction(1, 1000)
_ALLELE_PAIRS = {
    Fraction(1, 4): (["A", "a"], ["A", "a"]),
    Fraction(1, 2): (["a", "a"], ["A", "a"]),
    Fraction(1): (["a", "a"], ["a", "a"]),
}
_CELL_LABEL = {
    "AA": Label.NEITHER.value,
    "Aa": Label.CARRIER.value,
    "aA": Label.CARRIER.value,
    "aa": Label.TWO_COPIES.value,
}
# A dominant square uses the usual genetics convention, where the capital letter is the changed
# copy, so the letters mean the opposite of the recessive square above. The two squares therefore
# carry a `pattern`, and each screen explains its own letters rather than sharing one sentence.
_DOMINANT_CELL_LABEL = {
    "Aa": Label.INHERITS_CHANGE.value,
    "aA": Label.INHERITS_CHANGE.value,
    "aa": Label.DOES_NOT_INHERIT.value,
    "AA": Label.INHERITS_CHANGE.value,
}


def split_counts(outcomes: dict[str, Fraction], total: int) -> dict[str, int]:
    """Whole icons per group that always add up to the total, using largest remainders."""
    exact = {key: value * total for key, value in outcomes.items()}
    counts = {key: floor(value) for key, value in exact.items()}
    shortfall = total - sum(counts.values())
    for key in sorted(exact, key=lambda k: exact[k] - counts[k], reverse=True)[:shortfall]:
        counts[key] += 1
    return counts


def icon_array(outcomes: dict[str, Fraction], total: int) -> dict[str, Any]:
    counts = split_counts(outcomes, total)
    return {
        "type": "icon_array",
        "total": total,
        "groups": [{"key": key, "count": count} for key, count in counts.items()],
    }


def punnett(two_copies_chance: Fraction) -> dict[str, Any] | None:
    pair = _ALLELE_PAIRS.get(two_copies_chance)
    if pair is None:
        return None
    parent_a, parent_b = pair
    cells = [[a + b for b in parent_b] for a in parent_a]
    return {
        "type": "punnett",
        "pattern": "recessive",
        "parent_a": parent_a,
        "parent_b": parent_b,
        "cells": cells,
        "legend": {cell: _CELL_LABEL[cell] for row in cells for cell in row},
    }


def dominant_punnett(passes_on: Fraction) -> dict[str, Any] | None:
    """One parent with the change, one without: Aa x aa, or AA x aa when both copies are changed.

    The other parent's genotype is not a guess about a real person. A dominant change needs only
    the one parent, so the square shows what this person alone can pass on.
    """
    if passes_on == Fraction(1, 2):
        parent_a = ["A", "a"]
    elif passes_on == Fraction(1):
        parent_a = ["A", "A"]
    else:
        return None
    parent_b = ["a", "a"]
    cells = [[a + b for b in parent_b] for a in parent_a]
    return {
        "type": "punnett",
        "pattern": "dominant",
        "parent_a": parent_a,
        "parent_b": parent_b,
        "cells": cells,
        "legend": {cell: _DOMINANT_CELL_LABEL[cell] for row in cells for cell in row},
    }


def x_linked_diagram(facts: list[RiskFact]) -> dict[str, Any]:
    return {
        "type": "x_linked",
        "children": [
            {"key": fact.label.value, "percent": fact.percent}
            for fact in facts
            if fact.value is not None
        ],
    }


def visuals_for(facts: list[RiskFact]) -> list[dict[str, Any]]:
    """Picks the visual each scenario calls for.

    A carrier on their own gets none: a 25% square means nothing without a partner who shares the
    finding, and showing one would suggest a risk they don't have.
    """
    by_key: dict[tuple[Scenario, str | None], list[RiskFact]] = {}
    for fact in facts:
        # With gene names hidden, each shared gene still needs its own picture. The ID keeps them
        # apart ("couple_shared_ar:shared-1:carrier") with no name in the output.
        gene_key = fact.gene or fact.id.split(":")[1]
        by_key.setdefault((fact.scenario, gene_key), []).append(fact)

    visuals: list[dict[str, Any]] = []
    for (scenario, _), group in by_key.items():
        gene = group[0].gene
        if scenario is Scenario.COUPLE_SHARED_AR:
            visuals.extend(_shared_visuals(gene, group))
        elif scenario is Scenario.AD_SELF:
            visuals.extend(_dominant_visuals(gene, group))
        elif scenario in (
            Scenario.XLD_SELF,
            Scenario.XL_CARRIER_FEMALE,
            Scenario.XL_TWO_COPIES_FEMALE,
            Scenario.XL_FATHER,
            Scenario.COUPLE_XL,
        ):
            visuals.append({**x_linked_diagram(group), "gene": gene})
        elif scenario in (
            Scenario.COUPLE_ONE_CARRIER_TESTED_NEGATIVE,
            Scenario.COUPLE_ONE_CARRIER_UNTESTED,
        ):
            visuals.extend(_residual_visual(gene, group[0]))
    return visuals


def _dominant_visuals(gene: str | None, group: list[RiskFact]) -> list[dict[str, Any]]:
    outcomes = {fact.label.value: fact.value for fact in group if fact.value is not None}
    passes_on = outcomes.get(Label.INHERITS_CHANGE.value)
    if passes_on is None:
        return []
    visuals: list[dict[str, Any]] = [{**icon_array(outcomes, 100), "gene": gene}]
    square = dominant_punnett(passes_on)
    if square:
        visuals.append({**square, "gene": gene})
    return visuals


def _shared_visuals(gene: str | None, group: list[RiskFact]) -> list[dict[str, Any]]:
    outcomes = {fact.label.value: fact.value for fact in group if fact.value is not None}
    visuals: list[dict[str, Any]] = [{**icon_array(outcomes, 100), "gene": gene}]
    square = punnett(outcomes[Label.TWO_COPIES.value])
    if square:
        visuals.append({**square, "gene": gene})
    return visuals


def _residual_visual(gene: str | None, fact: RiskFact) -> list[dict[str, Any]]:
    chance = fact.value
    # Below 1 in 1000 even the larger grid would show nothing, so it stays as words.
    if chance is None or chance < _SMALLEST_ICON_ARRAY_CHANCE:
        return []
    total = 1000 if chance < Fraction(1, 100) else 100
    outcomes = {Label.TWO_COPIES.value: chance, "other": 1 - chance}
    return [{**icon_array(outcomes, total), "gene": gene}]
