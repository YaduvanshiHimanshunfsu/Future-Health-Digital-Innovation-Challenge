from dataclasses import dataclass
import re

from app.explain.validators import patterns
from app.explain.validators.text import loose, normalise, sentences

_DIGITS = re.compile(r"\d")
PLACEHOLDER = re.compile(r"\{fact:([A-Za-z0-9_:\-]+)\}")


@dataclass(frozen=True, slots=True)
class Flag:
    rule: str
    detail: str = ""


def _scan(text: str, table: patterns.Patterns, language: str, rule: str) -> list[Flag]:
    # Hindi speakers mix in English, and Arabic speakers often type in Roman letters, so English
    # checks always run as well as the language's own.
    found: list[Flag] = []
    for lang in {language, "en"}:
        target = loose(text) if lang == "ar" else normalise(text)
        for pattern in table.get(lang, []):
            if pattern.search(target):
                found.append(Flag(rule, f"{lang}:{pattern.pattern[:40]}"))
    return found


def directive(text: str, language: str) -> list[Flag]:
    return _scan(text, patterns.DIRECTIVE, language, "directive")


def certainty(text: str, language: str) -> list[Flag]:
    return _scan(text, patterns.CERTAINTY, language, "certainty")


def stigma(text: str, language: str) -> list[Flag]:
    return _scan(text, patterns.STIGMA, language, "stigma")


def free_numbers(text: str, language: str) -> list[Flag]:
    """A draft answer may not contain any number of its own. Numbers only enter as placeholders.

    Code fills the placeholders from the risk engine afterwards, so a model can never state a figure.
    """
    without = PLACEHOLDER.sub(" ", text)
    found = [Flag("number", "digit")] if _DIGITS.search(without) else []
    return found + _scan(without, patterns.NUMBER_WORDS, language, "number")


def bindings(text: str, language: str, labels: dict[str, str]) -> list[Flag]:
    """Each placeholder must sit in a sentence about its own outcome, and no other one.

    Swapping "25" and "50" between "two copies" and "carrier" is the mistake this exists for.
    """
    words = patterns.LABEL_WORDS.get(language, patterns.LABEL_WORDS["en"])
    found: list[Flag] = []
    for sentence in sentences(text):
        for fact_id in PLACEHOLDER.findall(sentence):
            label = labels.get(fact_id)
            if label is None:
                found.append(Flag("unknown_fact", fact_id))
                continue
            own = words.get(label)
            if own and not re.search(own, sentence, re.IGNORECASE):
                found.append(Flag("binding", label))
            others = [
                other
                for other, pattern in words.items()
                if other != label and pattern != own and re.search(pattern, sentence, re.IGNORECASE)
            ]
            if others and own and not _only_shared_words(label, others):
                found.append(Flag("binding", f"{label} beside {others[0]}"))
    return found


def _only_shared_words(label: str, others: list[str]) -> bool:
    # "Daughter" fits all three daughter labels, so naming a daughter isn't a contradiction.
    return label.startswith("daughter") and all(other.startswith("daughter") for other in others)


def readability(text: str, level: str) -> list[Flag]:
    """A rough length check per level. It flags, and doesn't block on its own."""
    limit = {"simple": 22, "standard": 30, "detailed": 40}.get(level, 30)
    long_ones = [s for s in sentences(text) if len(s.split()) > limit]
    return [Flag("readability", f"{len(long_ones)} long")] if long_ones else []
