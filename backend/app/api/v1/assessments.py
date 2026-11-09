"""Understanding checks, owner only. Answers are scored on the server.

A passed teach-back after reading the result moves the journey to COMPREHENSION_CHECKED. A second
missed teach-back opens or raises a P3 case, so a counsellor offers help (V5.3.3). Scores feed the
metrics as events with no answers in them, only the score.
"""

from http import HTTPStatus

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.events import emit
from app.api.deps import (
    current_person,
    get_audit,
    get_cipher,
    get_db,
    get_packs,
    require_service_consent,
)
from app.assessments.instruments import OFFERED, PASS_MARK, language_for
from app.assessments.scoring import BadAnswers, paired_change, score
from app.core.config import decode_key
from app.core.errors import ApiError
from app.core.security import Principal, get_principal
from app.country_packs.loader import PackRegistry
from app.models.assessment import Assessment
from app.models.case import CareCase
from app.models.enums import AssessmentPhase, CaseState, Instrument
from app.models.person import Person
from app.pathway.service import advance
from app.privacy.audit import AuditTrail
from app.privacy.crypto import FieldCipher
from app.schemas.assessments import AnswersIn, InstrumentOut, ItemOut, MyScoresOut, ScoreOut
from app.triage.scoring import score as triage_score
from app.triage.service import open_or_escalate

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/mine", response_model=list[MyScoresOut])
async def my_scores(
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
) -> list[MyScoresOut]:
    require_service_consent(person)
    rows = (
        await db.scalars(
            select(Assessment)
            .where(Assessment.person_id == person.id)
            .order_by(Assessment.created_at)
        )
    ).all()
    summary: list[MyScoresOut] = []
    for instrument in OFFERED:
        mine = [row for row in rows if row.instrument == instrument.value]
        pre = next((r.score for r in mine if r.phase == AssessmentPhase.PRE.value), None)
        post = next(
            (r.score for r in reversed(mine) if r.phase == AssessmentPhase.POST.value), None
        )
        summary.append(
            MyScoresOut(
                instrument=instrument.value,
                pre=pre,
                post=post,
                change=paired_change(pre, post),
                last_at=mine[-1].created_at if mine else None,
            )
        )
    return summary


@router.get("/{instrument}", response_model=InstrumentOut)
async def questions(
    instrument: Instrument,
    lang: str = Query(default="en", max_length=8),
    person: Person = Depends(current_person),
) -> InstrumentOut:
    """The questions without the answers."""
    require_service_consent(person)
    found = OFFERED.get(instrument)
    if found is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "instrument_not_offered")
    used = language_for(lang)
    return InstrumentOut(
        instrument=found.key.value,
        status=found.status,
        citation=found.citation,
        language_used=used,
        items=[ItemOut(id=i.id, text=i.text[used], options=i.options[used]) for i in found.items],
    )


@router.post("/{instrument}", response_model=ScoreOut, status_code=HTTPStatus.CREATED)
async def answer(
    request: Request,
    instrument: Instrument,
    body: AnswersIn,
    lang: str = Query(default="en", max_length=8),
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> ScoreOut:
    require_service_consent(person)
    found = OFFERED.get(instrument)
    if found is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "instrument_not_offered")
    used = language_for(lang)
    try:
        result = score(found, body.answers, used)
    except BadAnswers:
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "invalid_answers") from None

    pack = packs.require(person.pack_code)
    db.add(
        Assessment(
            person_id=person.id,
            instrument=instrument.value,
            phase=body.phase.value,
            lang=used,
            score=result.score,
        )
    )
    support = False
    if instrument is Instrument.TEACH_BACK:
        key = decode_key(request.app.state.settings.analytics_hmac_key, "ANALYTICS_HMAC_KEY")
        emit(db, key, f"comprehension_{body.phase.value}", person, value=result.score)
        case = await db.scalar(
            select(CareCase)
            .where(CareCase.subject_id == person.id, CareCase.state != CaseState.CLOSED.value)
            .order_by(CareCase.created_at.desc())
            .limit(1)
            .with_for_update()
        )
        understood = result.passed and case is not None
        if understood and case is not None and case.state == CaseState.EDUCATION_VIEWED.value:
            await advance(db, case, CaseState.COMPREHENSION_CHECKED, actor=principal.sub, pack=pack)
        if not result.passed:
            await db.flush()
            missed = await db.scalar(
                select(func.count()).where(
                    Assessment.person_id == person.id,
                    Assessment.instrument == Instrument.TEACH_BACK.value,
                    Assessment.score < PASS_MARK,
                )
            )
            triaged = triage_score([], teach_back_failures=int(missed or 0))
            if triaged is not None:
                await open_or_escalate(
                    db, cipher, audit, person=person, pack=pack, result=triaged, actor=principal.sub
                )
                support = True
    await audit.append(
        db,
        actor=principal.sub,
        action="assessment.submit",
        resource=f"person:{person.id}",
        meta={"mode": instrument.value},
    )
    await db.commit()
    return ScoreOut(
        instrument=instrument.value,
        phase=body.phase.value,
        score=result.score,
        passed=result.passed,
        support_offered=support,
    )
