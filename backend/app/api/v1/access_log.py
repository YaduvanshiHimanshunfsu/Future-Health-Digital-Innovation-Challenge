from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_person, get_db
from app.core.i18n import translate
from app.core.security import Principal, get_principal
from app.models.audit import AuditLog
from app.models.case import CareCase
from app.models.couple import Couple
from app.models.person import Person
from app.schemas.consent import AccessEntryOut, AccessLogOut

router = APIRouter(prefix="/me", tags=["privacy"])

_MAX_ENTRIES = 200
_AUTOMATIC = {"report.ingest": "lab", "case.triage": "system", "invitation.redeem": "system"}


@router.get("/access-log", response_model=AccessLogOut)
async def access_log(
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
) -> AccessLogOut:
    """Who has done what with this person's data. Login IDs never appear, only what kind of actor."""
    couples = (
        await db.scalars(
            select(Couple).where(or_(Couple.person_a == person.id, Couple.person_b == person.id))
        )
    ).all()
    partner_ids = {
        partner
        for couple in couples
        for partner in (couple.person_a, couple.person_b)
        if partner is not None and partner != person.id
    }
    partner_subs: set[str] = set()
    if partner_ids:
        subs = await db.scalars(select(Person.keycloak_sub).where(Person.id.in_(partner_ids)))
        partner_subs = {sub for sub in subs if sub}

    case_ids = (await db.scalars(select(CareCase.id).where(CareCase.subject_id == person.id))).all()
    resources = [
        f"person:{person.id}",
        *(f"couple:{couple.id}" for couple in couples),
        *(f"case:{case_id}" for case_id in case_ids),
    ]
    rows = (
        await db.scalars(
            select(AuditLog)
            .where(AuditLog.resource.in_(resources))
            .order_by(AuditLog.seq.desc())
            .limit(_MAX_ENTRIES)
        )
    ).all()

    def who(row: AuditLog) -> str:
        if row.actor == principal.sub:
            return "you"
        if row.actor in partner_subs:
            return "partner"
        kind = row.meta.get("actor_kind")
        if isinstance(kind, str):
            return kind
        return _AUTOMATIC.get(row.action, "someone_else")

    language = person.preferred_lang
    return AccessLogOut(
        entries=[
            AccessEntryOut(
                at=row.at,
                who=who(row),
                action=row.action,
                summary=translate(f"access.{row.action}", language),
                outcome=row.outcome,
                flagged=row.meta.get("flagged") is True,
            )
            for row in rows
        ]
    )
