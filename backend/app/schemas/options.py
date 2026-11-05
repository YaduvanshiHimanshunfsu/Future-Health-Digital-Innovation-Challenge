from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import Out, StrictIn


class OptionOut(Out):
    key: str
    title: str
    source: str
    note: str | None
    # False until a local clinician signs the option off. Screens say so.
    reviewed: bool


class OptionsOut(Out):
    options: list[OptionOut]
    # The order is the pack's own table, not a ranking, and screens must not imply one.
    order_is_not_a_ranking: bool = True


class ValuesIn(StrictIn):
    what_matters: str = Field(default="", max_length=500)
    worries: str = Field(default="", max_length=500)
    who_to_involve: str = Field(default="", max_length=500)
    timing: str = Field(default="", max_length=500)


class ValuesOut(Out):
    id: UUID
    answers: dict[str, str]
    shared_with_case: bool
    created_at: datetime


class ShareValuesIn(StrictIn):
    case_id: UUID
