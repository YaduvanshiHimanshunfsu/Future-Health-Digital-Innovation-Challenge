"""The router decides who answers. Arabic samples are Roman letters, with their meanings, since
project files hold no Arabic script. Native speakers still need to write the real evaluation set."""

import pytest

from app.explain.router import route
from app.models.enums import Boundary


@pytest.mark.parametrize(
    ("question", "language"),
    [
        (
            "madha ya'ni annani hamil lil-jin?",
            "ar",
        ),  # "what does it mean that I'm a carrier of the gene?"
        ("ana hamila lil marad?", "ar"),  # "am I a carrier of the condition?"
        ("What does being a carrier mean?", "en"),
        ("How does inheritance work?", "en"),
        ("वाहक होने का मतलब क्या है?", "hi"),  # "what does being a carrier mean?"
        ("vahak hone ka matlab kya hai", "hi"),
    ],
)
def test_carrier_questions_are_education(question: str, language: str) -> None:
    """V4.3.1 and V4.3.10. The original spec sent the Arabic one to the clinical path."""
    assert route(question, language).boundary is Boundary.EDUCATION


@pytest.mark.parametrize(
    ("question", "language"),
    [
        ("ana hamil fi al-shahr al-thalith", "ar"),  # "I'm three months pregnant"
        ("hiya hamil", "ar"),  # "she is pregnant": no carrier context, so read as pregnancy
        ("I'm 12 weeks pregnant, what should I do?", "en"),
        ("What medicine should my son take?", "en"),
        ("Is my baby sick?", "en"),
        ("मैं गर्भवती हूँ, क्या करूँ?", "hi"),  # "I'm pregnant, what should I do?"
        ("main garbhvati hoon", "hi"),
    ],
)
def test_clinical_questions_go_to_a_person(question: str, language: str) -> None:
    """V4.3.2 and V4.3.10."""
    assert route(question, language).boundary is Boundary.CLINICAL_ADVICE


def test_pregnancy_is_noticed_for_triage() -> None:
    assert route("ana hamil fi al-shahr al-thalith", "ar").pregnant
    assert route("I am pregnant", "en").pregnant
    assert not route("What does being a carrier mean?", "en").pregnant


@pytest.mark.parametrize(
    ("question", "language"),
    [
        ("I can't go on like this", "en"),
        ("I want to die", "en"),
        ("मैं मरना चाहती हूँ", "hi"),  # "I want to die"
        ("abi amoot", "ar"),  # "I want to die"
    ],
)
def test_distress_is_caught_first(question: str, language: str) -> None:
    assert route(question, language).boundary is Boundary.DISTRESS


@pytest.mark.parametrize(
    ("question", "language"),
    [
        ("My family is forcing me to show them my result", "en"),
        ("My in-laws insist I share it", "en"),
        ("ससुराल वाले ज़बरदस्ती कर रहे हैं", "hi"),  # "my in-laws are forcing me"
        ("abuya yijburni atazawaj", "ar"),  # "my father forces me to marry"
    ],
)
def test_coercion_reaches_a_person(question: str, language: str) -> None:
    """V4.3.12 and C10."""
    assert route(question, language).boundary is Boundary.COERCION


def test_the_most_careful_reading_wins() -> None:
    """Distress beats a clinical question, which beats an options question."""
    assert route("I'm pregnant and I want to die", "en").boundary is Boundary.DISTRESS
    assert route("I'm pregnant, what are my options?", "en").boundary is Boundary.CLINICAL_ADVICE


def test_options_questions_are_decision_support() -> None:
    assert route("What are my options?", "en").boundary is Boundary.DECISION_SUPPORT
    assert route("Should we still marry?", "en").boundary is Boundary.DECISION_SUPPORT


def test_arabic_script_goes_to_a_person_until_it_can_be_read() -> None:
    letters = "".join(chr(code) for code in range(0x0628, 0x062D))
    result = route(letters, "ar")
    assert result.boundary is Boundary.CLINICAL_ADVICE
    assert result.reasons == ("unsupported_script",)
