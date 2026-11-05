from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    current_person,
    get_audit,
    get_cipher,
    get_db,
    get_packs,
    require_service_consent,
)
from app.core.security import Principal, get_principal
from app.country_packs.loader import CountryPack, PackRegistry
from app.models.case import CareCase
from app.models.person import Person
from app.privacy.audit import AuditTrail
from app.privacy.crypto import FieldCipher
from app.privacy.right_not_to_know import human_contact_required
from app.repositories.genetic import load_record, person_sex
from app.risk_engine.engine import person_facts
from app.risk_engine.types import RiskFact
from app.risk_engine.visuals import visuals_for
from app.schemas.results import CareStepOut, FactOut, MyResultsOut, MyRiskOut, PackInfo

router = APIRouter(prefix="/me", tags=["results"])


def _pack_info(pack: CountryPack) -> PackInfo:
    return PackInfo(code=pack.code, status=pack.manifest.status.value, reviewed=pack.is_reviewed)


def _conditions_of(facts: list[RiskFact], pack: CountryPack) -> dict[str, list[str]]:
    genes = pack.panel.genes
    return {
        fact.gene: list(genes[fact.gene].conditions)
        for fact in facts
        if fact.gene is not None and fact.gene in genes
    }


@router.get("/results", response_model=MyResultsOut)
async def my_results(
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> MyResultsOut:
    require_service_consent(person)
    pack = packs.require(person.pack_code)
    record = await load_record(db, cipher, person.id)
    facts = person_facts(record.findings, await person_sex(cipher, person), pack.gene_table)
    withheld = person.results_withheld_at is not None
    await audit.append(
        db,
        actor=principal.sub,
        action="results.view",
        resource=f"person:{person.id}",
        meta={"mode": "withheld"} if withheld else None,
    )
    await db.commit()
    return MyResultsOut(
        has_report=record.has_report,
        facts=[] if withheld else [FactOut.from_fact(fact) for fact in facts],
        panels=sorted(record.panel_versions),
        conditions={} if withheld else _conditions_of(facts, pack),
        pack=_pack_info(pack),
        withheld=withheld,
        human_contact_required=withheld and human_contact_required(facts, pack),
    )


@router.get("/risk", response_model=MyRiskOut)
async def my_risk(
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> MyRiskOut:
    """This person's own risk facts. Couple facts arrive in sub-phase 3.3, behind match consent."""
    require_service_consent(person)
    pack = packs.require(person.pack_code)
    record = await load_record(db, cipher, person.id)
    facts = person_facts(record.findings, await person_sex(cipher, person), pack.gene_table)
    withheld = person.results_withheld_at is not None
    await audit.append(
        db,
        actor=principal.sub,
        action="risk.view",
        resource=f"person:{person.id}",
        meta={"mode": "withheld"} if withheld else None,
    )
    await db.commit()
    return MyRiskOut(
        has_report=record.has_report,
        facts=[] if withheld else [FactOut.from_fact(fact) for fact in facts],
        visuals=[] if withheld else visuals_for(facts),
        pack=_pack_info(pack),
        withheld=withheld,
        human_contact_required=withheld and human_contact_required(facts, pack),
    )


@router.get("/care", response_model=list[CareStepOut])
async def my_care(
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
) -> list[CareStepOut]:
    """Holds no genetic detail, so it works whatever someone has chosen about seeing results."""
    require_service_consent(person)
    cases = (
        await db.scalars(
            select(CareCase)
            .where(CareCase.subject_id == person.id)
            .order_by(CareCase.created_at.desc())
        )
    ).all()
    return [
        CareStepOut(
            case_id=case.id,
            state=case.state,
            step_due=case.step_due,
            with_partner=case.couple_id is not None,
        )
        for case in cases
    ]
