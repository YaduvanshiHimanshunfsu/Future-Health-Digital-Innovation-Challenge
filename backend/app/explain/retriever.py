"""Picks the knowledge-base passages that fit a question.

Plain word overlap over a small, reviewed set, instead of an embedding model: it gives the same
answer every time, runs offline, and needs no model download (issue H15). With a few dozen passages,
this is enough. Passages only ever come from the person's own language and level, never another.
"""

import re
from collections.abc import Iterable

from app.explain.validators.text import normalise
from app.kb.ingest import Passage, load_all

# Devanagari vowel signs are marks, which \w alone would treat as breaks inside a Hindi word.
_WORD = re.compile(r"(?:[^\W\d_]|[ऀ-ॿ]){3,}", re.UNICODE)
_STOP = frozenset(
    {
        "the",
        "and",
        "what",
        "does",
        "this",
        "that",
        "for",
        "with",
        "are",
        "you",
        "your",
        "can",
        "how",
        "mean",
        "means",
    }
)


def _words(text: str) -> set[str]:
    return {word for word in _WORD.findall(normalise(text)) if word not in _STOP}


def retrieve(
    question: str,
    language: str,
    level: str,
    conditions: Iterable[str] = (),
    *,
    limit: int = 2,
    passages: Iterable[Passage] | None = None,
) -> list[Passage]:
    pool = [
        passage
        for passage in (passages if passages is not None else load_all())
        if passage.lang == language and passage.level == level
    ]
    wanted = set(conditions)
    asked = _words(question)

    def score(passage: Passage) -> tuple[int, int, str]:
        overlap = len(asked & _words(passage.title + " " + passage.text))
        about_their_result = 1 if passage.condition in wanted else 0
        return (overlap + 3 * about_their_result, about_their_result, passage.id)

    ranked = sorted(pool, key=score, reverse=True)
    return [passage for passage in ranked[:limit] if score(passage)[0] > 0]
