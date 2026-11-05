from uuid import UUID

from pydantic import Field

from app.schemas.common import Out, StrictIn


class ChatIn(StrictIn):
    message: str = Field(min_length=1, max_length=1000)
    conversation_id: UUID | None = None


class ContactOut(Out):
    service: str
    contact: str
    hours: str


class ChatOut(Out):
    conversation_id: UUID
    # Plain text. Screens must show it as text, never as HTML.
    answer: str
    boundary: str
    source: str
    # Only the asker's own facts, so nothing here can point at a partner's finding.
    fact_ids: list[str]
    escalated: bool
    contacts: list[ContactOut]
