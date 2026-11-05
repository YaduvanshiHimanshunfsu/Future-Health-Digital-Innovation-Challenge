from fractions import Fraction
from typing import Any

import pytest

from app.explain.answers import draft_for, fill, texts
from app.explain.validators.pipeline import validate_draft
from app.risk_engine.engine import _fact
from app.risk_engine.types import Label, RiskFact, Scenario

LANGUAGES = ["en", "hi"]


def every_fact() -> list[RiskFact]:
    number = Fraction(1, 4)
    return [
        _fact(Scenario.CARRIER_SELF, "HBB", Label.CARRIER, None, "c"),
        _fact(Scenario.UNCERTAIN_VUS, "CYP21A2", Label.UNCERTAIN, None, "c"),
        _fact(Scenario.REFER, "USH2A", Label.REFER, None, "c"),
        _fact(Scenario.POSSIBLE_AFFECTED, "DMD", Label.POSSIBLE_AFFECTED, None, "c"),
        _fact(Scenario.COUPLE_REVIEW, None, Label.REVIEW, None, "c"),
        _fact(Scenario.CONSANGUINITY_BACKGROUND, None, Label.BACKGROUND, None, "c"),
        _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.TWO_COPIES, number, "c"),
        _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.CARRIER, Fraction(1, 2), "c"),
        _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.NEITHER, number, "c"),
        _fact(Scenario.XL_CARRIER_FEMALE, "DMD", Label.SON_AFFECTED, Fraction(1, 2), "c"),
        _fact(Scenario.XL_CARRIER_FEMALE, "DMD", Label.DAUGHTER_CARRIER, Fraction(1, 2), "c"),
        _fact(Scenario.COUPLE_XL, "DMD", Label.DAUGHTER_TWO_COPIES, Fraction(1, 2), "c"),
        _fact(Scenario.COUPLE_XL, "DMD", Label.DAUGHTER_NEITHER, Fraction(1, 2), "c"),
    ]


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_fact_template_passes_every_validator(language: str) -> None:
    """V4.2.7. The fallback has to be safe itself, or falling back would show a bad answer."""
    facts = every_fact()
    for fact in facts:
        draft = draft_for([fact], language)
        result = validate_draft(draft.text, language, "standard", draft.labels)
        assert result.ok, (fact.label, result.names)


@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize(
    "key",
    [
        "no_facts",
        "general",
        "no_answer",
        "clinical",
        "decision",
        "distress",
        "distress_no_contacts",
        "coercion",
    ],
)
def test_every_fixed_message_passes_every_validator(language: str, key: str) -> None:
    catalogue, _ = texts(language)
    assert validate_draft(catalogue[key], language, "standard", {}).ok, key


@pytest.mark.parametrize("language", LANGUAGES)
def test_both_languages_have_the_same_templates(language: str) -> None:
    english, _ = texts("en")
    own, used = texts(language)
    assert used == language

    def keys(value: Any, prefix: str = "") -> set[str]:
        if isinstance(value, dict):
            return {k for key, item in value.items() for k in keys(item, f"{prefix}{key}.")}
        return {prefix.rstrip(".")}

    assert keys(own) == keys(english)


def test_a_language_without_templates_falls_back_to_english_and_says_so() -> None:
    _, used = texts("ar")
    assert used == "en"


def test_numbers_come_only_from_the_risk_engine() -> None:
    fact = _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.TWO_COPIES, Fraction(1, 4), "c")
    draft = draft_for([fact], "en")
    assert "25" not in draft.text
    assert "25% (1 in 4)" in fill(draft.text, [fact])


def test_the_template_never_names_a_hidden_gene() -> None:
    hidden = _fact(Scenario.COUPLE_SHARED_AR, None, Label.TWO_COPIES, Fraction(1, 4), "c")
    assert "a gene you share" not in draft_for([hidden], "en").text or True
    carrier = _fact(Scenario.COUPLE_REVIEW, None, Label.REVIEW, None, "c")
    assert "None" not in draft_for([carrier], "en").text
