"""Checks every answer must pass. Samples in Hindi and Roman-letter Arabic are the team's own, and
need native speakers to write the real ones (V4.2.8). Arabic meanings are given beside each sample."""

from fractions import Fraction

import pytest

from app.explain.validators.pipeline import validate_draft
from app.explain.validators.rules import bindings, free_numbers
from app.risk_engine.engine import _fact
from app.risk_engine.types import Label, Scenario

TWO = _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.TWO_COPIES, Fraction(1, 4), "c")
ONE = _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.CARRIER, Fraction(1, 2), "c")
LABELS = {TWO.id: "two_copies", ONE.id: "carrier"}


def rules_fired(text: str, language: str = "en", level: str = "standard") -> set[str]:
    return set(validate_draft(text, language, level, LABELS).names)


def test_swapped_figures_are_blocked() -> None:
    """V4.2.1. The original spec passed this, because it only checked that the numbers existed."""
    swapped = f"There is a {{fact:{ONE.id}}} chance that a child inherits two copies."
    assert "binding" in rules_fired(swapped)
    right = f"There is a {{fact:{TWO.id}}} chance that a child inherits two copies."
    assert "binding" not in rules_fired(right)


def test_a_sentence_mixing_two_outcomes_for_one_figure_is_blocked() -> None:
    text = f"A {{fact:{TWO.id}}} chance of two copies, so most children will be carriers."
    assert "binding" in rules_fired(text)


def test_a_daughters_figure_may_use_its_own_words_and_no_one_elses() -> None:
    daughter = _fact(Scenario.XL_CARRIER_FEMALE, "DMD", Label.DAUGHTER_CARRIER, Fraction(1, 2), "c")
    labels = {daughter.id: "daughter_carrier"}
    right = f"Each daughter has a {{fact:{daughter.id}}} chance of one copy, as a carrier."
    wrong = f"Each daughter has a {{fact:{daughter.id}}} chance of two copies."
    assert bindings(right, "en", labels) == []
    assert [flag.rule for flag in bindings(wrong, "en", labels)] == ["binding"]


def test_a_placeholder_for_a_fact_the_person_cant_see_is_blocked() -> None:
    assert {flag.rule for flag in bindings("Two copies: {fact:someone_elses}.", "en", LABELS)} == {
        "unknown_fact"
    }


@pytest.mark.parametrize(
    "text",
    [
        "There is a 25% chance of two copies.",
        "Half of your children will inherit it.",
        "One in four children inherits two copies.",
        "About twenty five per cent.",
    ],
)
def test_a_draft_cannot_state_a_number_itself(text: str) -> None:
    """Numbers enter only through placeholders, which code fills from the risk engine."""
    assert "number" in rules_fired(text)


def test_half_your_children_in_gulf_dialect_is_blocked() -> None:
    """V4.2.2: nisf atfalikuma sayusabun, "half of your children will be affected"."""
    fired = rules_fired("nisf atfalikuma sayusabun", "ar")
    assert {"number", "certainty"} <= fired


@pytest.mark.parametrize(
    "text",
    [
        "You carry one changed copy of this gene.",
        "Each parent passes on one copy, by chance.",
        "Two copies of a gene, one from each parent.",
        "Being a carrier usually doesn't cause illness.",
    ],
)
def test_ordinary_carrier_wording_passes(text: str) -> None:
    """V4.2.3. "One copy" is a description, not a statistic."""
    assert validate_draft(text, "en", "standard", LABELS).ok


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("lazim tsawwun al-fahs", "ar"),  # "you must do the test"
        ("It would be best to have IVF.", "en"),
        ("We recommend that you don't marry.", "en"),
        ("You should think about adoption.", "en"),
        ("The best option is prenatal testing.", "en"),
        ("आपको शादी नहीं करनी चाहिए।", "hi"),  # "you should not marry"
        ("सबसे अच्छा विकल्प आईवीएफ है।", "hi"),  # "the best option is IVF"
        ("apko test karana chahiye", "hi"),  # Hindi in Roman letters: "you should get tested"
        ("ahsan lak tatazawaj wahda thanya", "ar"),  # "better for you to marry someone else"
    ],
)
def test_directing_a_decision_is_flagged(text: str, language: str) -> None:
    """V4.2.4."""
    assert "directive" in rules_fired(text, language)


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("You are healthy.", "en"),
        ("Good news: there is no risk.", "en"),
        ("Your child will have thalassaemia.", "en"),
        ("This is 100% safe.", "en"),
        ("आप पूरी तरह स्वस्थ हैं।", "hi"),  # "you are completely healthy"
        ("कोई खतरा नहीं है।", "hi"),  # "there is no danger"
        ("anta salim, ma fi khatar", "ar"),  # "you are healthy, there's no danger"
    ],
)
def test_false_certainty_is_flagged(text: str, language: str) -> None:
    """V4.2.5."""
    assert "certainty" in rules_fired(text, language)


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("Your genes are defective.", "en"),
        ("You two are incompatible.", "en"),
        ("A child suffering from the condition.", "en"),
        ("आपके खराब जीन हैं।", "hi"),  # "you have bad genes"
        ("dam fasid", "ar"),  # "corrupt blood"
    ],
)
def test_stigmatising_words_are_flagged(text: str, language: str) -> None:
    assert "stigma" in rules_fired(text, language)


def test_hindi_number_words_are_caught() -> None:
    """V4.2.8, in part: a Hindi speaker still has to write the full sample set."""
    assert "number" in rules_fired("आपके आधे बच्चों को यह मिलेगा।", "hi")  # "half your children"


def test_arabic_script_cannot_pass_until_it_can_be_checked() -> None:
    letters = "".join(chr(code) for code in range(0x0628, 0x062D))
    assert "unreadable_script" in rules_fired(letters, "ar")


def test_readability_is_noted_and_does_not_block_on_its_own() -> None:
    long = " ".join(["word"] * 40) + "."
    result = validate_draft(long, "en", "simple", LABELS)
    assert "readability" in result.names
    assert result.ok


def test_digits_inside_placeholders_are_not_free_numbers() -> None:
    assert free_numbers(f"Two copies: {{fact:{TWO.id}}}.", "en") == []
