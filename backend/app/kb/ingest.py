"""Loads the knowledge base from markdown files, refusing any file that breaks the content rules."""

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.explain.validators import rules

CONTENT_DIR = Path(__file__).parent / "content"
REQUIRED = ("id", "condition", "lang", "level", "version", "status", "source", "title")
STATUSES = frozenset({"draft", "reviewed"})
# Figures written into content must be one of these general facts, which hold for every
# recessive condition. Anything personal comes from the risk engine instead.
APPROVED_FIGURES = re.compile(r"\b1 in (4|2)\b")
_FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


class ContentError(ValueError):
    """A content file is incomplete or breaks a wording rule."""


@dataclass(frozen=True, slots=True)
class Passage:
    id: str
    condition: str
    lang: str
    level: str
    title: str
    text: str
    status: str
    source: str
    version: int


def parse(path: Path) -> Passage:
    found = _FRONT_MATTER.match(path.read_text("utf-8").replace("\r\n", "\n"))
    if not found:
        raise ContentError(f"{path.name}: no front matter")
    meta = yaml.safe_load(found.group(1)) or {}
    missing = [key for key in REQUIRED if meta.get(key) in (None, "")]
    if missing:
        raise ContentError(f"{path.name}: missing {missing}")
    if meta["status"] not in STATUSES:
        raise ContentError(f"{path.name}: unknown status {meta['status']!r}")
    if meta["status"] == "reviewed" and not meta.get("reviewed_by"):
        raise ContentError(f"{path.name}: reviewed with no reviewer named")
    body = found.group(2).strip()
    problems = _wording_problems(body, str(meta["lang"]))
    if problems:
        raise ContentError(f"{path.name}: {problems}")
    return Passage(
        id=str(meta["id"]),
        condition=str(meta["condition"]),
        lang=str(meta["lang"]),
        level=str(meta["level"]),
        title=str(meta["title"]),
        text=body,
        status=str(meta["status"]),
        source=str(meta["source"]),
        version=int(meta["version"]),
    )


def _wording_problems(text: str, language: str) -> list[str]:
    flags = (
        rules.directive(text, language)
        + rules.certainty(text, language)
        + rules.stigma(text, language)
    )
    flags += rules.free_numbers(APPROVED_FIGURES.sub(" ", text), language)
    return sorted({flag.rule for flag in flags})


@lru_cache
def load_all(directory: Path = CONTENT_DIR) -> tuple[Passage, ...]:
    return tuple(parse(path) for path in sorted(directory.glob("*/*.md")))
