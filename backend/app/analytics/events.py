"""Measurement events: what happened, to which kind of person, never who or why in their words.

Every event has a kind from a fixed list, a pseudonymous subject (a keyed hash of the person's ID,
so one person's pre and post scores pair up without naming them), and the person's reporting
groups. There is no free-text column, and `emit` has no parameter that could carry any (V5.4.5).

No event ever records a marriage decision or any one reproductive choice as an outcome (V5.4.8).
"""

import hashlib
import hmac
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Event
from app.models.person import Person

# Each kind and what `value` means for it, if anything. Care-pathway changes aren't here: each one
# already writes a `pathway_step` row, and pathway metrics read those, so there is one source.
KINDS: dict[str, str] = {
    "comprehension_pre": "score from 0 to 1",
    "comprehension_post": "score from 0 to 1",
    "case_stalled": "",
    "reminder_sent": "",
    "chat_answer": "1 if written by a model and validated, 0 if the reviewed template",
    "chat_escalated": "",
    "validator_flag": "number of rules a model draft broke",
    "share_revoked": "milliseconds until access was removed",
    "access_denied": "",
}


class UnknownEvent(ValueError):
    pass


def pseudonym(key: bytes, person_id: uuid.UUID) -> str:
    return hmac.new(key, person_id.bytes, hashlib.sha256).hexdigest()[:32]


def emit(
    db: AsyncSession,
    key: bytes,
    kind: str,
    person: Person | None,
    *,
    value: float | None = None,
    at: datetime | None = None,
) -> None:
    """Adds one event to the caller's transaction, so it commits or rolls back with the change."""
    if kind not in KINDS:
        raise UnknownEvent(kind)
    event = Event(
        subject=pseudonym(key, person.id) if person is not None else None,
        kind=kind,
        pack_code=person.pack_code if person else None,
        lang=person.preferred_lang if person else None,
        literacy=person.literacy_level if person else None,
        region=person.region if person else None,
        age_band=person.age_band if person else None,
        gender=person.gender if person else None,
        value=value,
    )
    if at is not None:
        event.at = at
    db.add(event)
