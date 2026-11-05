import re
from fractions import Fraction

import pytest

from app.core.config import DEFAULT_PACKS_DIR
from app.country_packs.loader import load_pack
from app.privacy import redaction
from app.privacy.redaction import (
    NUMBER_PLACEHOLDER,
    WORD_PLACEHOLDER,
    LlmRequest,
    RedactionError,
    build_llm_facts,
    call_llm_guarded,
    redact,
)
from app.risk_engine.engine import _fact
from app.risk_engine.types import Label, Scenario

ARABIC_INDIC = "".join(chr(0x0660 + digit) for digit in (9, 8, 7, 6, 5, 4, 3, 2))
DEVANAGARI_DIGITS = "".join(chr(0x0966 + digit) for digit in (9, 8, 7, 6, 5, 4, 3, 2))
# Letters from the Arabic block with no meaning, since project files hold no Arabic words.
ARABIC_LETTERS = "".join(chr(code) for code in range(0x0628, 0x0630))


@pytest.mark.parametrize(
    ("language", "text", "secrets"),
    [
        ("en", "My name is Priya Sharma and I worry about my baby", ["Priya", "Sharma"]),
        ("en", "Dr Khalid at Mafraq Hospital told my wife Fatima", ["Khalid", "Mafraq", "Fatima"]),
        ("en", "Email me at someone.real@example.com please", ["someone", "example.com"]),
        ("en", "Call +91 98765 43210 or 050-123-4567", ["98765", "43210", "123-4567"]),
        ("en", "see https://example.com/profile/42", ["example.com", "profile"]),
        ("hi", "मेरा नाम प्रिया शर्मा है", ["प्रिया", "शर्मा"]),
        ("hi", "मेरे पति राहुल की रिपोर्ट", ["राहुल"]),
        ("hi", "mera naam Priya Sharma hai", ["Priya", "Sharma"]),
        ("hi", f"मेरा नंबर {DEVANAGARI_DIGITS} है", [DEVANAGARI_DIGITS]),
        # Arabic in Roman letters and Gulf dialect, with the meaning given: "my name is Fatima, my
        # husband Khalid", and "she is pregnant, her name is Noura".
        ("ar", "ismi Fatima, zawji Khalid", ["Fatima", "Khalid", "ismi", "zawji"]),
        ("ar", "hiya hamil, ismaha Noura", ["Noura", "ismaha", "hamil"]),
        ("ar", ARABIC_LETTERS, [ARABIC_LETTERS]),
        ("ar", f"raqmi {ARABIC_INDIC}", [ARABIC_INDIC]),
    ],
)
def test_identifying_details_are_removed(language: str, text: str, secrets: list[str]) -> None:
    """V3.5.4. Samples by the author: a native speaker still has to write the real ones."""
    cleaned = redact(text, language)
    for secret in secrets:
        assert secret not in cleaned


def test_ordinary_questions_survive_in_english() -> None:
    question = "What does being a carrier mean for my children?"
    assert redact(question, "en") == question


def test_ordinary_questions_survive_in_hindi() -> None:
    question = "वाहक होने का मतलब क्या है?"
    assert redact(question, "hi") == question


def test_hindi_words_stay_whole_despite_their_vowel_signs() -> None:
    """Python's \\w treats these signs as breaks, which would leave pieces of a name behind."""
    assert redact("प्रिया", "hi") == WORD_PLACEHOLDER


def test_short_numbers_stay_since_they_identify_nobody() -> None:
    assert redact("my 2 children", "en") == "my 2 children"


def test_a_language_with_no_word_list_loses_every_word() -> None:
    """Poor answers beat leaked names. Arabic stays here until someone writes its word list."""
    assert not re.search(r"[A-Za-z]", redact("hello there my friend", "ar").replace("WORD", ""))


def test_country_formats_come_from_the_pack() -> None:
    pack = load_pack(DEFAULT_PACKS_DIR / "ae-abu-dhabi")
    cleaned = redact(
        "my id is 784-1990-1234567-1", "en", patterns=[pack.identity.national_id_pattern]
    )
    assert "1234567" not in cleaned
    assert NUMBER_PLACEHOLDER in cleaned


def test_genes_from_the_panel_are_allowed_through() -> None:
    assert redact("What is HBB?", "en", genes=["HBB"]) == "What is HBB?"
    assert "HBB" not in redact("What is HBB?", "en")


@pytest.mark.parametrize("language", ["../../secrets", "EN", "", "en-US"])
def test_a_strange_language_code_is_refused(language: str) -> None:
    with pytest.raises(RedactionError):
        redact("hello", language)


class RecordingLlm:
    def __init__(self) -> None:
        self.requests: list[LlmRequest] = []

    async def __call__(self, request: LlmRequest) -> str:
        self.requests.append(request)
        return "answer"


async def test_if_redaction_fails_no_llm_call_happens(monkeypatch: pytest.MonkeyPatch) -> None:
    """V3.5.3."""

    def explode(_: str) -> frozenset[str]:
        raise RuntimeError("word list broke")

    monkeypatch.setattr(redaction, "_vocabulary", explode)
    llm = RecordingLlm()
    with pytest.raises(RedactionError):
        await call_llm_guarded(llm, "My name is Priya", "en", [])
    assert llm.requests == []


async def test_only_listed_fields_reach_the_llm() -> None:
    """V3.5.5."""
    fact = _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.TWO_COPIES, Fraction(1, 4), "citation")
    llm = RecordingLlm()
    await call_llm_guarded(llm, "My name is Priya, what is this?", "en", [fact], genes=["HBB"])
    request = llm.requests[0]
    assert "Priya" not in request.question
    assert set(request.facts[0]) == {
        "id", "scenario", "gene", "label", "percent", "one_in", "has_number",
    }  # fmt: skip
    assert request.facts[0]["percent"] == "25"


def test_llm_facts_carry_no_flags_or_citations() -> None:
    fact = _fact(Scenario.REFER, "HBB", Label.REFER, None, "citation")
    built = build_llm_facts([fact])[0]
    assert built["has_number"] is False
    assert "citation" not in built
    assert "flags" not in built


def test_a_pack_format_the_generic_rules_miss_is_still_removed() -> None:
    """Some countries use IDs with letters, or numbers too short for the generic rule."""
    pattern = r"\bAB-[A-Z]{3}\b"
    genes = ["AB", "QXZ"]
    assert "AB-QXZ" in redact("ref AB-QXZ", "en", genes=genes), "the generic rules alone miss it"
    assert "AB-QXZ" not in redact("ref AB-QXZ", "en", patterns=[pattern], genes=genes)
