"""The counsellor console: the queue, claiming and assigning, and reading one case."""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    current_person,
    deny,
    get_audit,
    get_authz,
    get_cipher,
    get_db,
    get_packs,
)
from app.core.security import Principal, require_role
from app.country_packs.loader import PackRegistry
from app.decision.values import QUESTIONS, values_aad
from app.explain.context import own_facts
from app.models.case import CareCase
from app.models.enums import CaseState
from app.models.person import Person
from app.models.values_note import ValuesNote
from app.pathway.service import STAFF_MAY, can_move
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz
from app.privacy.crypto import FieldCipher
from app.privacy.outbox import drain_quietly
from app.schemas.cases import AssignIn, CaseOut, CaseSummaryOut, QueueItemOut, SummaryFactOut
from app.triage import assignment
from app.triage.copilot import summarise
from app.triage.service import reasons_aad, sla_hours

router = APIRouter(prefix="/cases", tags=["cases"])

STAFF_ROLES = ("counsellor", "physician")


def staff_kind(principal: Principal) -> str:
    return next((role for role in STAFF_ROLES if role in principal.roles), "staff")


@router.get("/{case_id}", response_model=CaseOut)
async def read_case(
    case_id: UUID,
    principal: Principal = Depends(require_role(*STAFF_ROLES)),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
    packs: PackRegistry = Depends(get_packs),
) -> CaseOut:
    user, obj = f"user:{person.id}", f"care_case:{case_id}"
    case = await db.get(CareCase, case_id)
    assigned = case is not None and await authz.check(user, "assigned", obj)
    allowed = assigned or (case is not None and await authz.check(user, "can_view", obj))
    if not allowed or case is None:
        await deny(
            audit, principal.sub, f"case:{case_id}", meta={"actor_kind": staff_kind(principal)}
        )

    reasons = await cipher.decrypt_json(case.reasons_enc, aad=reasons_aad(case))
    subject = await db.get(Person, case.subject_id)
    summary = None
    if subject is not None:
        facts = await own_facts(db, cipher, subject, packs.require(subject.pack_code))
        summary = summarise(facts, await _shared_values(db, cipher, case))
    await audit.append(
        db,
        actor=principal.sub,
        action="case.view",
        resource=f"case:{case.id}",
        meta={"actor_kind": staff_kind(principal), "flagged": not assigned},
    )
    await db.commit()
    return CaseOut(
        id=case.id,
        priority=case.priority,
        state=case.state,
        step_due=case.step_due,
        reasons=reasons,
        window_hours=_window(packs, subject.pack_code if subject else None, case),
        through_break_glass=not assigned,
        next_steps=sorted(s.value for s in STAFF_MAY if can_move(case, s)) if assigned else [],
        summary=CaseSummaryOut(
            facts=[SummaryFactOut(**vars_of(f)) for f in summary.facts],
            values=summary.values,
            verify_before_use=summary.verify_before_use,
        )
        if summary
        else None,
    )


def _window(packs: PackRegistry, pack_code: str | None, case: CareCase) -> int:
    pack = packs.get(pack_code) if pack_code else None
    return sla_hours(pack or packs.default, case.priority)


async def _queue_item(
    cipher: FieldCipher, packs: PackRegistry, case: CareCase, pack_code: str | None, me: Person
) -> QueueItemOut:
    return QueueItemOut(
        id=case.id,
        priority=case.priority,
        state=case.state,
        step_due=case.step_due,
        reasons=await cipher.decrypt_json(case.reasons_enc, aad=reasons_aad(case)),
        window_hours=_window(packs, pack_code, case),
        assigned_to_me=case.counsellor_id == me.id,
    )


def vars_of(fact: object) -> dict[str, object]:
    return {name: getattr(fact, name) for name in ("scenario", "gene", "label", "percent")}


async def _shared_values(
    db: AsyncSession, cipher: FieldCipher, case: CareCase
) -> dict[str, str] | None:
    note = await db.scalar(
        select(ValuesNote)
        .where(ValuesNote.shared_with_case_id == case.id)
        .order_by(ValuesNote.created_at.desc())
        .limit(1)
    )
    if note is None:
        return None
    answers = await cipher.decrypt_json(note.answers_enc, aad=values_aad(note.id))
    return {key: str(answers.get(key, "")) for key in QUESTIONS}


_CLOSED = (
    CaseState.CLOSED.value,
    CaseState.DECLINED_BY_USER.value,
    CaseState.LOST_TO_FOLLOW_UP.value,
)


@router.get("", response_model=list[QueueItemOut])
async def queue(
    view: str = Query(default="pool", pattern="^(pool|mine)$"),
    principal: Principal = Depends(require_role("counsellor")),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    packs: PackRegistry = Depends(get_packs),
) -> list[QueueItemOut]:
    """The unassigned pool, or this counsellor's own cases. Most urgent first, then soonest due."""
    owner = (
        CareCase.counsellor_id.is_(None) if view == "pool" else CareCase.counsellor_id == person.id
    )
    cases = (
        await db.scalars(
            select(CareCase)
            .where(owner, CareCase.state.not_in(_CLOSED))
            .order_by(CareCase.priority, CareCase.step_due)
            .limit(200)
        )
    ).all()
    # One lookup for every case's country rules, rather than one query per case.
    codes = dict(
        (
            await db.execute(
                select(Person.id, Person.pack_code).where(
                    Person.id.in_({case.subject_id for case in cases})
                )
            )
        )
        .tuples()
        .all()
    )
    return [
        await _queue_item(cipher, packs, case, codes.get(case.subject_id), person) for case in cases
    ]


@router.post("/{case_id}/claim", response_model=QueueItemOut)
async def claim_case(
    request: Request,
    case_id: uuid.UUID,
    principal: Principal = Depends(require_role("counsellor")),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
    packs: PackRegistry = Depends(get_packs),
) -> QueueItemOut:
    case = await db.get(CareCase, case_id, with_for_update=True)
    if case is None:
        await deny(audit, principal.sub, f"case:{case_id}", meta={"actor_kind": "counsellor"})
    await assignment.claim(db, audit, actor=principal.sub, case=case, counsellor_id=person.id)
    subject = await db.get(Person, case.subject_id)
    item = await _queue_item(cipher, packs, case, subject.pack_code if subject else None, person)
    await db.commit()
    await drain_quietly(request.app.state.session_factory, authz)
    return item


@router.post("/{case_id}/assign", status_code=204)
async def assign_case(
    request: Request,
    case_id: uuid.UUID,
    body: AssignIn,
    principal: Principal = Depends(require_role("program_admin")),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
) -> None:
    case = await db.get(CareCase, case_id, with_for_update=True)
    counsellor = await db.get(Person, body.counsellor_id)
    if case is None or counsellor is None:
        await deny(audit, principal.sub, f"case:{case_id}", meta={"actor_kind": "coordinator"})
    await assignment.assign(db, audit, actor=principal.sub, case=case, counsellor_id=counsellor.id)
    await db.commit()
    await drain_quietly(request.app.state.session_factory, authz)
