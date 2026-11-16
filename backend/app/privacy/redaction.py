"""What may reach an LLM. Nothing does unless it's on a list, and any failure means no call.

Finding names in free text is unreliable in any language, and there's no model we could trust for
Arabic names. So this works the other way round: a word survives only if it's on the
language's vocabulary list, and everything else becomes a placeholder. A language with no list yet,
such as Arabic for now, loses every word. That makes for poor answers, never for leaked names.

Limit: a name that's also an everyday word on a list would survive, so names are kept off the lists.
"""

import re
import unicodedata
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.risk_engine.types import RiskFact

WORD_PLACEHOLDER = "[WORD]"
NUMBER_PLACEHOLDER = "[NUMBER]"
EMAIL_PLACEHOLDER = "[EMAIL]"
LINK_PLACEHOLDER = "[LINK]"
_VOCABULARY_DIR = Path(__file__).parent / "safe_words"
_LANGUAGE = re.compile(r"[a-z]{2,3}")
_APOSTROPHES = "'\u2019"
_EMAIL = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
_LINK = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
# \d matches every script's digits, so Arabic-Indic numbers are caught too.
_LONG_NUMBER = re.compile(r"\+?\d(?:[\s().\-/]*\d){4,}")


class RedactionError(Exception):
    """Redaction couldn't finish, so the text must not go anywhere."""


@dataclass(frozen=True, slots=True)
class LlmRequest:
    question: str
    facts: tuple[dict[str, Any], ...]


@lru_cache
def _vocabulary(language: str) -> frozenset[str]:
    path = _VOCABULARY_DIR / f"{language}.txt"
    if not path.is_file():
        return frozenset()
    lines = path.read_text("utf-8").splitlines()
    return frozenset(
        word.casefold() for line in lines if not line.startswith("#") for word in line.split()
    )


def _is_word_character(character: str) -> bool:
    # Some scripts write vowel signs as combining marks, and \w would split a word at each one.
    return unicodedata.category(character)[0] in ("L", "M")


def _tokens(text: str) -> Iterable[tuple[str, bool]]:
    """Splits into runs of word and non-word characters, keeping an apostrophe inside a word."""
    start = 0
    position = 0
    in_word = False
    length = len(text)
    while position < length:
        character = text[position]
        inner_apostrophe = (
            in_word
            and character in _APOSTROPHES
            and position + 1 < length
            and _is_word_character(text[position + 1])
        )
        is_word = _is_word_character(character) or inner_apostrophe
        if is_word != in_word and position > start:
            yield text[start:position], in_word
            start = position
        in_word = is_word
        position += 1
    if start < length:
        yield text[start:], in_word


def redact_identifiers(text: str, patterns: Iterable[str] = ()) -> str:
    """Emails, links, long numbers and any country-specific formats, leaving ordinary words."""
    for pattern in patterns:
        text = re.sub(pattern, NUMBER_PLACEHOLDER, text)
    text = _EMAIL.sub(EMAIL_PLACEHOLDER, text)
    text = _LINK.sub(LINK_PLACEHOLDER, text)
    return _LONG_NUMBER.sub(NUMBER_PLACEHOLDER, text)


_PLACEHOLDER_WORDS = frozenset(
    placeholder.strip("[]").casefold()
    for placeholder in (WORD_PLACEHOLDER, NUMBER_PLACEHOLDER, EMAIL_PLACEHOLDER, LINK_PLACEHOLDER)
)


def redact(
    text: str,
    language: str,
    *,
    patterns: Iterable[str] = (),
    genes: Iterable[str] = (),
) -> str:
    """Raises RedactionError rather than ever returning something half-processed."""
    if not _LANGUAGE.fullmatch(language):
        raise RedactionError("unknown language")
    try:
        allowed = _vocabulary(language) | _PLACEHOLDER_WORDS
        gene_names = {gene.casefold() for gene in genes}
        cleaned = redact_identifiers(text, patterns)
        return "".join(
            (
                token
                if not is_word or token.casefold() in allowed or token.casefold() in gene_names
                else WORD_PLACEHOLDER
            )
            for token, is_word in _tokens(cleaned)
        )
    except Exception as exc:
        raise RedactionError(type(exc).__name__) from None


def build_llm_facts(facts: Iterable[RiskFact]) -> tuple[dict[str, Any], ...]:
    """A list of fields, not a filter: a field added to RiskFact later stays out until named here."""
    return tuple(
        {
            "id": fact.id,
            "scenario": fact.scenario.value,
            "gene": fact.gene,
            "label": fact.label.value,
            "percent": fact.percent,
            "one_in": fact.one_in,
            "has_number": fact.has_number,
        }
        for fact in facts
    )


def build_llm_request(
    question: str,
    language: str,
    facts: Iterable[RiskFact],
    *,
    patterns: Iterable[str] = (),
    genes: Iterable[str] = (),
) -> LlmRequest:
    return LlmRequest(
        question=redact(question, language, patterns=patterns, genes=genes),
        facts=build_llm_facts(facts),
    )


async def call_llm_guarded[Result](
    send: Callable[[LlmRequest], Awaitable[Result]],
    question: str,
    language: str,
    facts: Iterable[RiskFact],
    *,
    patterns: Iterable[str] = (),
    genes: Iterable[str] = (),
) -> Result:
    """The only route to a model. If the request can't be made safe, `send` is never called."""
    request = build_llm_request(question, language, facts, patterns=patterns, genes=genes)
    return await send(request)
