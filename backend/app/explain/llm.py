"""The seam where an AI model plugs in.

A provider implements `LlmClient` and only ever sees what the privacy layer lets through: the
redacted question, the listed fact fields, and approved knowledge-base passages. Every draft it
writes is validated before anyone reads it, and any failure falls back to the reviewed template.

`TemplateOnly` never calls anything. The providers live in `app/explain/providers.py`.
"""

from typing import Protocol

from app.models.enums import Boundary
from app.privacy.redaction import LlmRequest


class LlmUnavailable(Exception):
    """No answer in time, no provider, or an answer that couldn't be read. The template is used."""


class LlmClient(Protocol):
    """Two jobs, both narrow. It has no tools and no database access: it receives one request."""

    name: str

    async def draft(self, request: LlmRequest, passages: list[str], language: str) -> str:
        """An explanation that may hold {fact:ID} placeholders and no figures of its own."""
        ...

    async def classify(self, question: str, language: str) -> Boundary:
        """Which kind of question a redacted question is. Used only to escalate, never to relax."""
        ...


class TemplateOnly:
    """The default. Never calls anything, so the template and the rules decide everything."""

    name = "template"

    async def draft(self, request: LlmRequest, passages: list[str], language: str) -> str:
        raise LlmUnavailable("template mode")

    async def classify(self, question: str, language: str) -> Boundary:
        raise LlmUnavailable("template mode")
