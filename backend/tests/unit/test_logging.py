import json
import logging
import sys

import pytest

from app.core.logging import PhiSafeJsonFormatter, register_scrub_patterns, scrub


def formatted(message: str, *args: object, **extra: object) -> dict[str, object]:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, message, args, None)
    for key, value in extra.items():
        setattr(record, key, value)
    return json.loads(PhiSafeJsonFormatter().format(record))


@pytest.mark.parametrize(
    ("text", "secret"),
    [
        ("national id 784-1990-1234567-1", "1234567"),
        ("called +971 50 123 4567 today", "123 4567"),
        ("mobile 9876543210", "9876543210"),
        ("contact person@example.org", "person@example.org"),
        ("aadhaar 1234 5678 9012", "5678"),
        # The same number written in Devanagari and Arabic-Indic digits.
        ("number ९८७६५४३२१०", "९८७"),
        ("number ٩٨٧٦٥٤٣٢١٠", "٩٨٧"),
        ("token eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl", "eyJhbGci"),
    ],
)
def test_identifiers_are_scrubbed(text: str, secret: str) -> None:
    assert secret not in scrub(text)


@pytest.mark.parametrize(
    "text",
    [
        "request finished in 125 ms",
        "status 404 on route /v1/cases",
        "version 3.12.13",
        "retry 2 of 5",
    ],
)
def test_ordinary_numbers_survive(text: str) -> None:
    assert scrub(text) == text


def test_country_pack_formats_can_be_added() -> None:
    assert "ABCDE1234F" in scrub("pan card ABCDE1234F")
    register_scrub_patterns([(r"\b[A-Z]{5}\d{4}[A-Z]\b", "[TAX_ID]")])
    assert scrub("pan card ABCDE1234F") == "pan card [TAX_ID]"


def test_message_text_is_scrubbed_after_formatting() -> None:
    entry = formatted("lookup for %s failed", "784-1990-1234567-1")
    assert "1234567" not in str(entry["msg"])


@pytest.mark.parametrize(
    "key", ["gene", "hgvs", "name", "email", "token", "Authorization", "answer"]
)
def test_sensitive_context_keys_are_redacted(key: str) -> None:
    entry = formatted("event", ctx={key: "HBB c.20A>T", "request_id": "abc"})
    assert entry["ctx"] == {key: "[REDACTED]", "request_id": "abc"}


def test_nested_context_is_redacted_too() -> None:
    entry = formatted("event", ctx={"details": {"gene": "HBB", "phone": ["+971501234567"]}})
    assert entry["ctx"] == {"details": {"gene": "[REDACTED]", "phone": "[REDACTED]"}}


def test_context_values_are_scrubbed_under_innocent_keys() -> None:
    entry = formatted("event", ctx={"note": "reach me at +971 50 123 4567"})
    assert "123 4567" not in str(entry["ctx"])


def test_exception_message_never_reaches_the_log() -> None:
    try:
        raise ValueError("HBB c.20A>T for person 784-1990-1234567-1")
    except ValueError:
        exc_info = sys.exc_info()
    record = logging.LogRecord("t", logging.ERROR, __file__, 1, "failed", (), exc_info)
    output = PhiSafeJsonFormatter().format(record)
    assert json.loads(output)["exc_type"] == "ValueError"
    assert "HBB" not in output
    assert "c.20A" not in output
    assert "Traceback" not in output


def test_output_is_one_line_of_json() -> None:
    line = PhiSafeJsonFormatter().format(
        logging.LogRecord("t", logging.INFO, __file__, 1, "two\nlines", (), None)
    )
    assert "\n" not in line
    json.loads(line)
