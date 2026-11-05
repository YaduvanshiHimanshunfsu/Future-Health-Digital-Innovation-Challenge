from datetime import UTC, datetime
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_person, deny, get_audit, get_authz, get_db
from app.api.v1.cases import STAFF_ROLES, staff_kind
from app.core.errors import ApiError
from app.core.security import Principal, require_role
from app.models.break_glass import BreakGlassEvent
from app.models.case import CareCase
from app.models.person import Person
from app.privacy import break_glass
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz
from app.privacy.outbox import drain_quietly
from app.schemas.cases import BreakGlassEventOut, BreakGlassIn, BreakGlassOut

router = APIRouter(tags=["break-glass"])


@router.post(
    "/cases/{case_id}/break-glass",
    status_code=HTTPStatus.CREATED,
    response_model=BreakGlassOut,
)
async def open_break_glass(
    request: Request,
    case_id: UUID,
    body: BreakGlassIn,
    principal: Principal = Depends(require_role(*STAFF_ROLES)),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
) -> BreakGlassOut:
    if await db.get(CareCase, case_id) is None:
        await deny(audit, principal.sub, f"case:{case_id}")
    event = await break_glass.open_event(
        db,
        audit,
        actor=principal.sub,
        actor_person=person,
        actor_kind=staff_kind(principal),
        case_id=case_id,
        reason=body.reason,
        now=authz.clock(),
    )
    event_id, expires_at = event.id, event.expires_at
    await db.commit()
    await drain_quietly(request.app.state.session_factory, authz)
    ready = await authz.check(f"user:{person.id}", "can_view", f"care_case:{case_id}")
    return BreakGlassOut(event_id=event_id, expires_at=expires_at, access_ready=ready)


@router.get("/break-glass", response_model=list[BreakGlassEventOut])
async def review_list(
    _: Principal = Depends(require_role("auditor")),
    db: AsyncSession = Depends(get_db),
) -> list[BreakGlassEventOut]:
    events = (
        await db.scalars(
            select(BreakGlassEvent)
            .where(BreakGlassEvent.reviewed_at.is_(None))
            .order_by(BreakGlassEvent.created_at)
        )
    ).all()
    return [
        BreakGlassEventOut(
            id=event.id,
            case_id=event.case_id,
            actor_id=event.actor_id,
            reason=event.reason,
            expires_at=event.expires_at,
            created_at=event.created_at,
        )
        for event in events
    ]


@router.post("/break-glass/{event_id}/review", status_code=HTTPStatus.NO_CONTENT)
async def review(
    event_id: UUID,
    principal: Principal = Depends(require_role("auditor")),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
) -> None:
    event = await db.get(BreakGlassEvent, event_id, with_for_update=True)
    if event is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    if event.actor_id == person.id:
        raise ApiError(HTTPStatus.CONFLICT, "cannot_review_own_access")
    if event.reviewed_at is not None:
        return
    event.reviewed_by = person.id
    event.reviewed_at = datetime.now(UTC)
    await db.flush()
    await audit.append(
        db,
        actor=principal.sub,
        action="break_glass.review",
        resource=f"case:{event.case_id}",
        meta={"actor_kind": "auditor"},
    )
    await db.commit()
