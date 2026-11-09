"""Scores, worked out on the server from the answers alone, so a client can't claim a score.

- Teach-back: the share of items answered correctly, 0 to 1. A pass is PASS_MARK or more.
- SURE: the number of "yes" answers, 0 to 4. Under 4 suggests decisional conflict, which is a
  reason to offer support, never a judgement of the person.
- Paired change: a person's post score minus their own pre score, so groups are compared on how
  much the explanation helped, not on where people started (S7).
"""

from dataclasses import dataclass

from app.assessments.instruments import PASS_MARK, InstrumentDef
from app.models.enums import Instrument


class BadAnswers(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Scored:
    score: float
    passed: bool


def score(instrument: InstrumentDef, answers: list[int], language: str) -> Scored:
    if len(answers) != len(instrument.items):
        raise BadAnswers("one answer per item")
    for item, answer in zip(instrument.items, answers, strict=True):
        if not 0 <= answer < len(item.options[language]):
            raise BadAnswers(f"no option {answer} for {item.id}")
    if instrument.key is Instrument.SURE:
        yes = sum(1 for answer in answers if answer == 0)
        return Scored(score=float(yes), passed=yes == len(answers))
    right = sum(
        1 for item, answer in zip(instrument.items, answers, strict=True) if item.correct == answer
    )
    share = right / len(instrument.items)
    return Scored(score=share, passed=share >= PASS_MARK)


def paired_change(pre: float | None, post: float | None) -> float | None:
    """None unless both exist: an unpaired score says nothing about what the explanation did."""
    if pre is None or post is None:
        return None
    return post - pre
