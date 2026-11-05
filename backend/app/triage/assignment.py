"""Who looks after a case. Nothing here decides anything about the person, only who's responsible.

The database records the assignment, and OpenFGA gets the matching tuple through the outbox, so the
two can't disagree for long and a failed commit leaves no access behind (H7).
"""

import uuid
from http import HTTPStatus

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.case import CareCase
from app.models.enums import OutboxOperation
from app.privacy.audit import AuditTrail
from app.privacy.authz import RelationTuple
from app.privacy.outbox import enqueue


def assigned_tuple(counsellor_id: uuid.UUID, case_id: uuid.UUID) -> RelationTuple:
    return RelationTuple(f"user:{counsellor_id}", "assigned", f"care_case:{case_id}")


async def claim(
    db: AsyncSession, audit: AuditTrail, *, actor: str, case: CareCase, counsellor_id: uuid.UUID
) -> None:
    if case.counsellor_id is not None:
        raise ApiError(HTTPStatus.CONFLICT, "already_assigned")
    case.counsellor_id = counsellor_id
    enqueue(db, OutboxOperation.WRITE, assigned_tuple(counsellor_id, case.id))
    await db.flush()
    await audit.append(
        db,
        actor=actor,
        action="case.claim",
        resource=f"case:{case.id}",
        meta={"actor_kind": "counsellor"},
    )


async def assign(
    db: AsyncSession, audit: AuditTrail, *, actor: str, case: CareCase, counsellor_id: uuid.UUID
) -> None:
    """A coordinator moving a case. The previous counsellor loses access in the same change."""
    if case.counsellor_id == counsellor_id:
        return
    if case.counsellor_id is not None:
        enqueue(db, OutboxOperation.DELETE, assigned_tuple(case.counsellor_id, case.id))
    case.counsellor_id = counsellor_id
    enqueue(db, OutboxOperation.WRITE, assigned_tuple(counsellor_id, case.id))
    await db.flush()
    await audit.append(
        db,
        actor=actor,
        action="case.assign",
        resource=f"case:{case.id}",
        meta={"actor_kind": "coordinator"},
    )
