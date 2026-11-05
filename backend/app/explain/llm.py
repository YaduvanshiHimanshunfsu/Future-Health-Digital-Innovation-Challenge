"""The seam where an AI model would plug in.

No provider is configured yet: the choice of model service is the user's (see brain.md). Until one
is, every answer comes from the reviewed templates, which the plan allows ("ship with templates only
and say so"). A provider implements `LlmClient`, and only ever sees what `call_llm_guarded` lets
through: redacted question, listed fact fields, and approved passages.
"""

from typing import Protocol

from app.privacy.redaction import LlmRequest


class LlmUnavailable(Exception):
    """No answer in time, or no provider. The pipeline falls back to the template."""


class LlmClient(Protocol):
    """Gets a draft that may hold {fact:ID} placeholders and no figures of its own.

    It has no tools and no database access, by construction: it receives one request object.
    """

    async def draft(self, request: LlmRequest, passages: list[str], language: str) -> str: ...


class TemplateOnly:
    """The default. Never calls anything, so the template is always used."""

    async def draft(self, request: LlmRequest, passages: list[str], language: str) -> str:
        raise LlmUnavailable("template mode")
