"""The care pathway: a person's own journey, the steps they can take, and a counsellor's moves.

A person reads only their own cases (404 for anyone else's, V5.1.9) and can always step back
(V5.1.3). A counsellor moves only a case assigned to them, checked against the authorisation store,
not a role alone. Every change goes through the state machine and leaves a step behind (V5.1.1).
"""

from http import HTTPStatus
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    current_person,
    deny,
    get_audit,
    get_authz,
    get_db,
    get_packs,
    require_service_consent,
)
from app.core.errors import ApiError
from app.core.security import Principal, get_principal, require_role
from app.country_packs.loader import PackRegistry
from app.models.case import CareCase, PathwayStep
from app.models.person import Person
from app.pathway.service import PERSON_MAY, STAFF_MAY, advance, can_move, commit_or_conflict
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz
from app.schemas.pathway import JourneyOut, JourneyStepOut, RemindersIn, StepIn

router = APIRouter(tags=["pathway"])


def _by(actor: str, me: str) -> Literal["you", "care_team", "system"]:
    if actor == me:
        return "you"
    return "system" if actor.startswith("system") or actor == "public" else "care_team"


@router.get("/me/journey", response_model=list[JourneyOut])
async def my_journey(
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
) -> list[JourneyOut]:
    """Holds no genetic detail, so it works whatever someone has chosen about seeing results."""
    require_service_consent(person)
    cases = (
        await db.scalars(
            select(CareCase)
            .where(CareCase.subject_id == person.id)
            .order_by(CareCase.created_at.desc())
        )
    ).all()
    journeys = []
    for case in cases:
        steps = (
            await db.scalars(
                select(PathwayStep).where(PathwayStep.case_id == case.id).order_by(PathwayStep.at)
            )
        ).all()
        journeys.append(
            JourneyOut(
                case_id=case.id,
                state=case.state,
                step_due=case.step_due,
                with_partner=case.couple_id is not None,
                steps=[
                    JourneyStepOut(
                        state=step.to_state, at=step.at, by=_by(step.actor, principal.sub)
                    )
                    for step in steps
                ],
                next_steps=sorted(s.value for s in PERSON_MAY if can_move(case, s)),
                reminders_off=person.reminders_opt_out,
            )
        )
    return journeys


async def _own_case(db: AsyncSession, person: Person, case_id: UUID) -> CareCase:
    case = await db.get(CareCase, case_id, with_for_update=True)
    if case is None or case.subject_id != person.id:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    return case


@router.post("/journey/{case_id}/steps", status_code=HTTPStatus.NO_CONTENT)
async def take_step(
    case_id: UUID,
    body: StepIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> Response:
    """Asking for counselling, or stepping back. Both are always the person's to choose."""
    require_service_consent(person)
    if body.to_state not in PERSON_MAY:
        raise ApiError(HTTPStatus.FORBIDDEN, "not_your_step")
    case = await _own_case(db, person, case_id)

    async def work() -> None:
        await advance(
            db, case, body.to_state, actor=principal.sub, pack=packs.require(person.pack_code)
        )
        await audit.append(
            db,
            actor=principal.sub,
            action="pathway.step",
            resource=f"case:{case.id}",
            meta={"state": body.to_state.value},
        )

    await commit_or_conflict(db, work)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.patch("/me/reminders", status_code=HTTPStatus.NO_CONTENT)
async def reminders(
    body: RemindersIn,
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
) -> Response:
    person.reminders_opt_out = body.opt_out
    await db.commit()
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.post("/cases/{case_id}/advance", status_code=HTTPStatus.NO_CONTENT)
async def advance_case(
    case_id: UUID,
    body: StepIn,
    principal: Principal = Depends(require_role("counsellor")),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
    packs: PackRegistry = Depends(get_packs),
) -> Response:
    """Only the counsellor the case is assigned to. Anyone else gets what looks like nothing there."""
    case = await db.get(CareCase, case_id, with_for_update=True)
    assigned = case is not None and await authz.check(
        f"user:{person.id}", "assigned", f"care_case:{case_id}"
    )
    if case is None or not assigned:
        await deny(audit, principal.sub, f"case:{case_id}", meta={"actor_kind": "counsellor"})
    if body.to_state not in STAFF_MAY:
        raise ApiError(HTTPStatus.FORBIDDEN, "not_a_staff_step")
    subject = await db.get(Person, case.subject_id)
    pack = (packs.get(subject.pack_code) if subject else None) or packs.default

    async def work() -> None:
        await advance(db, case, body.to_state, actor=principal.sub, pack=pack)
        await audit.append(
            db,
            actor=principal.sub,
            action="pathway.step",
            resource=f"case:{case.id}",
            meta={"state": body.to_state.value, "actor_kind": "counsellor"},
        )

    await commit_or_conflict(db, work)
    return Response(status_code=HTTPStatus.NO_CONTENT)
