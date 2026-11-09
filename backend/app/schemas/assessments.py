from datetime import datetime

from pydantic import Field

from app.models.enums import AssessmentPhase
from app.schemas.common import Out, StrictIn


class ItemOut(Out):
    id: str
    text: str
    options: list[str]


class InstrumentOut(Out):
    instrument: str
    # Shown on screen next to the questions, so nobody mistakes a draft for a validated tool.
    status: str
    citation: str
    language_used: str
    items: list[ItemOut]


class AnswersIn(StrictIn):
    phase: AssessmentPhase
    answers: list[int] = Field(min_length=1, max_length=20)


class ScoreOut(Out):
    instrument: str
    phase: str
    score: float
    passed: bool
    # True after a second missed check: a counsellor has been asked to help.
    support_offered: bool


class MyScoresOut(Out):
    instrument: str
    pre: float | None
    post: float | None
    change: float | None
    last_at: datetime | None
