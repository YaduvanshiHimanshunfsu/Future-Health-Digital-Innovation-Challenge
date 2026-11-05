import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.break_glass import BreakGlassEvent
from app.models.enums import OutboxOperation
from app.models.person import Person
from app.privacy.audit import AuditTrail
from app.privacy.authz import RelationTuple
from app.privacy.outbox import enqueue
from app.privacy.redaction import redact_identifiers

LIFETIME = timedelta(hours=1)


async def open_event(
    db: AsyncSession,
    audit: AuditTrail,
    *,
    actor: str,
    actor_person: Person,
    actor_kind: str,
    case_id: uuid.UUID,
    reason: str,
    now: datetime,
) -> BreakGlassEvent:
    event = BreakGlassEvent(
        id=uuid.uuid4(),
        actor_id=actor_person.id,
        case_id=case_id,
        # Reviewers need the reason in words, and it has no reason to hold a phone number or ID.
        reason=redact_identifiers(reason),
        expires_at=now + LIFETIME,
    )
    db.add(event)
    await db.flush()
    enqueue(
        db,
        OutboxOperation.WRITE,
        RelationTuple(f"user:{actor_person.id}", "holder", f"grant:{event.id}", event.expires_at),
    )
    enqueue(
        db,
        OutboxOperation.WRITE,
        RelationTuple(f"grant:{event.id}#holder", "emergency", f"care_case:{case_id}"),
    )
    await db.flush()
    await audit.append(
        db,
        actor=actor,
        action="break_glass.open",
        resource=f"case:{case_id}",
        meta={"actor_kind": actor_kind, "flagged": True},
    )
    return event
