import uuid
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.country_packs.loader import CountryPack
from app.models.case import CareCase
from app.models.enums import CaseState, Priority
from app.models.person import Person
from app.pathway.state_machine import record_opening, transition
from app.privacy.audit import AuditTrail
from app.privacy.crypto import FieldCipher
from app.risk_engine.types import RiskFact
from app.triage.scoring import TriageResult, score

_CLOSED_STATES = (CaseState.CLOSED.value, CaseState.DECLINED_BY_USER.value)
# Priorities that shouldn't wait for someone to read their result first.
_STRAIGHT_TO_COUNSELLING = (Priority.P1.value, Priority.P2.value)
_EARLY_STATES = (
    CaseState.RESULT_RELEASED.value,
    CaseState.EDUCATION_VIEWED.value,
    CaseState.COMPREHENSION_CHECKED.value,
)
_NO_TRIGGER = TriageResult(Priority.P4, ("result_released",))


def _rank(priority: str) -> int:
    return int(priority.removeprefix("P"))


def reasons_aad(case: CareCase) -> str:
    return f"care_case:{case.id}:reasons"


def sla_hours(pack: CountryPack, priority: str) -> int:
    """How long the pack allows for a step at this priority."""
    hours: int = getattr(pack.strata.sla_hours, priority)
    return hours


def due_at(pack: CountryPack, priority: str) -> datetime:
    return datetime.now(UTC) + timedelta(hours=sla_hours(pack, priority))


async def triage_result(
    db: AsyncSession,
    cipher: FieldCipher,
    audit: AuditTrail,
    *,
    person: Person,
    pack: CountryPack,
    facts: Iterable[RiskFact],
    actor: str,
) -> CareCase:
    """Every result opens or updates a case, so nothing waits on the person starting a chat."""
    return await open_or_escalate(
        db, cipher, audit, person=person, pack=pack, result=score(facts) or _NO_TRIGGER, actor=actor
    )


async def open_or_escalate(
    db: AsyncSession,
    cipher: FieldCipher,
    audit: AuditTrail,
    *,
    person: Person,
    pack: CountryPack,
    result: TriageResult,
    actor: str,
    couple_id: uuid.UUID | None = None,
) -> CareCase:
    case = await db.scalar(
        select(CareCase)
        .where(CareCase.subject_id == person.id, CareCase.state.not_in(_CLOSED_STATES))
        .with_for_update()
    )
    priority = result.priority.value
    if case is not None and couple_id is not None and case.couple_id is None:
        case.couple_id = couple_id
    if case is None:
        case = CareCase(
            subject_id=person.id,
            couple_id=couple_id,
            priority=priority,
            reasons_enc=b"",
            state=CaseState.RESULT_RELEASED.value,
            step_due=due_at(pack, priority),
        )
        db.add(case)
        await db.flush()
        case.reasons_enc = await cipher.encrypt_json(list(result.reasons), aad=reasons_aad(case))
        await record_opening(db, case, actor=actor)
    elif _rank(priority) < _rank(case.priority):
        # Automatic triage only ever moves a case up. Lowering one is a person's decision.
        existing = await cipher.decrypt_json(case.reasons_enc, aad=reasons_aad(case))
        case.priority = priority
        case.reasons_enc = await cipher.encrypt_json(
            sorted({*existing, *result.reasons}), aad=reasons_aad(case)
        )
        case.step_due = min(case.step_due, due_at(pack, priority))
    else:
        await db.flush()
        return case

    if priority in _STRAIGHT_TO_COUNSELLING and case.state in _EARLY_STATES:
        await transition(
            db,
            case,
            CaseState.COUNSELLING_REQUESTED,
            actor=actor,
            step_due=case.step_due,
        )
    await db.flush()
    await audit.append(
        db,
        actor=actor,
        action="case.triage",
        resource=f"case:{case.id}",
        meta={"priority": case.priority},
    )
    return case
