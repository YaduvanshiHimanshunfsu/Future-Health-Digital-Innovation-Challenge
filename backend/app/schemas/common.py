from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.models.enums import ReadingLevel

# A shape check only. The active country pack decides which languages are actually on offer.
LanguageCode = Annotated[str, StringConstraints(pattern=r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})?$")]
Level = ReadingLevel


class StrictIn(BaseModel):
    """Base for request bodies. Unknown fields are refused, which stops mass assignment."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)
