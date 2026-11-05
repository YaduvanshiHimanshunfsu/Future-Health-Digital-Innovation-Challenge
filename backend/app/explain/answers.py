"""Builds the approved answer for a fact set. Used directly in template mode, and as the fallback."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.risk_engine.types import RiskFact

_DIR = Path(__file__).parent / "templates"
FALLBACK_LANGUAGE = "en"


@lru_cache
def _load(language: str) -> dict[str, Any]:
    path = _DIR / f"{language}.yaml"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        loaded: dict[str, Any] = yaml.safe_load(handle)
    return loaded


def texts(language: str) -> tuple[dict[str, Any], str]:
    """The language's templates, or English with the language that was actually used."""
    own = _load(language)
    return (own, language) if own else (_load(FALLBACK_LANGUAGE), FALLBACK_LANGUAGE)


@dataclass(frozen=True, slots=True)
class Draft:
    text: str
    # Which fact each placeholder stands for, by label, for the binding check.
    labels: dict[str, str]
    fact_ids: tuple[str, ...]


def fact_sentence(fact: RiskFact, catalogue: dict[str, Any]) -> str:
    words: dict[str, str] = catalogue["fact"]
    gene = fact.gene or catalogue["gene_hidden"]
    if fact.has_number:
        key = "carrier_chance" if fact.label.value == "carrier" else fact.label.value
        return words[key].replace("{fact}", f"{{fact:{fact.id}}}")
    return words[fact.label.value].replace("{gene}", gene)


def draft_for(facts: list[RiskFact], language: str) -> Draft:
    catalogue, _ = texts(language)
    if not facts:
        return Draft(catalogue["no_facts"], {}, ())
    lines = [fact_sentence(fact, catalogue) for fact in facts]
    if any(fact.has_number for fact in facts):
        lines.append(catalogue["memory"])
    return Draft(
        " ".join(lines),
        {fact.id: fact.label.value for fact in facts if fact.has_number},
        tuple(fact.id for fact in facts),
    )


def fill(text: str, facts: list[RiskFact]) -> str:
    """The only place a number enters an answer, and it comes from the risk engine."""
    by_id = {fact.id: fact for fact in facts}
    for fact_id, fact in by_id.items():
        if fact.percent is None:
            continue
        figure = f"{fact.percent}% (1 in {fact.one_in})" if fact.one_in else f"{fact.percent}%"
        text = text.replace(f"{{fact:{fact_id}}}", figure)
    return text
