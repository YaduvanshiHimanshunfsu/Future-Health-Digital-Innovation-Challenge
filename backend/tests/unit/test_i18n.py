import json
from pathlib import Path

import pytest

from app.core.i18n import negotiate_language, translate

SUPPORTED = ["en", "ar", "hi"]
MESSAGES = Path(__file__).resolve().parents[2] / "app" / "core" / "messages"


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, "en"),
        ("", "en"),
        ("hi", "hi"),
        ("hi-IN", "hi"),
        ("ar-AE,ar;q=0.9,en;q=0.8", "ar"),
        ("en;q=0.5,hi;q=0.9", "hi"),
        ("fr,de", "en"),
        ("hi;q=0,en", "en"),
        ("hi;q=not-a-number,en", "en"),
        ("HI", "hi"),
        ("x" * 300, "en"),
    ],
)
def test_language_negotiation(header: str | None, expected: str) -> None:
    assert negotiate_language(header, SUPPORTED, "en") == expected


def test_missing_translation_falls_back_to_english() -> None:
    assert translate("error.not_found", "ar") == translate("error.not_found", "en")


def test_unknown_key_returns_the_key_rather_than_nothing() -> None:
    assert translate("error.nonexistent", "en") == "error.nonexistent"


def test_language_tag_cannot_read_arbitrary_files() -> None:
    assert translate("error.not_found", "../../secrets") == translate("error.not_found", "en")


def test_hindi_covers_every_english_message() -> None:
    english = json.loads((MESSAGES / "en.json").read_text("utf-8"))
    hindi = json.loads((MESSAGES / "hi.json").read_text("utf-8"))
    assert set(hindi) == set(english)
