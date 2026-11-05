from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    current_person,
    deny,
    get_audit,
    get_authz,
    get_cipher,
    get_db,
    get_packs,
    require_service_consent,
)
from app.core.security import Principal, get_principal
from app.country_packs.loader import PackRegistry
from app.models.consent import Consent
from app.models.enums import ConsentKind
from app.models.person import Person
from app.privacy import consent_service
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz
from app.privacy.crypto import FieldCipher
from app.repositories.genetic import load_record, person_sex
from app.risk_engine.engine import person_facts
from app.risk_engine.visuals import visuals_for
from app.schemas.consent import SharedFullOut, SharedSummaryOut, SummaryFactOut
from app.schemas.results import FactOut, PackInfo

router = APIRouter(prefix="/shared", tags=["shared"])


@router.get("/{consent_id}", response_model=SharedFullOut | SharedSummaryOut)
async def read_shared(
    request: Request,
    consent_id: UUID,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
    packs: PackRegistry = Depends(get_packs),
) -> SharedFullOut | SharedSummaryOut:
    """A share has to be live in the ledger and in OpenFGA. If either says no, the answer is no."""
    require_service_consent(person)
    consent = await db.get(Consent, consent_id)
    owner = await db.get(Person, consent.grantor_id) if consent else None
    allowed = (
        consent is not None
        and owner is not None
        and consent.grantee_id == person.id
        and consent.kind in consent_service.SHARE_KINDS
        and consent_service.is_live(consent, authz.clock())
        # Someone who has chosen not to know keeps their result out of circulation too.
        and owner.results_withheld_at is None
        and await authz.check(
            f"user:{person.id}",
            consent_service.VIEW_RELATION[consent.kind],
            f"report:{owner.id}",
        )
    )
    if not allowed or consent is None or owner is None:
        # An attempt on a real share goes in the owner's own access log.
        resource = f"person:{owner.id}" if owner else f"consent:{consent_id}"
        await deny(audit, principal.sub, resource, meta={"actor_kind": "shared_with"})

    pack = packs.require(owner.pack_code)
    record = await load_record(db, cipher, owner.id)
    facts = person_facts(record.findings, await person_sex(cipher, owner), pack.gene_table)
    await audit.append(
        db,
        actor=principal.sub,
        action="shared.view",
        resource=f"person:{owner.id}",
        meta={"consent_id": str(consent.id), "mode": consent.kind, "actor_kind": "shared_with"},
    )
    await db.commit()
    pack_info = PackInfo(
        code=pack.code, status=pack.manifest.status.value, reviewed=pack.is_reviewed
    )
    if consent.kind == ConsentKind.SHARE_FULL.value:
        return SharedFullOut(
            has_report=record.has_report,
            facts=[FactOut.from_fact(fact) for fact in facts],
            visuals=visuals_for(facts),
            pack=pack_info,
        )
    return SharedSummaryOut(
        has_report=record.has_report,
        facts=[SummaryFactOut(gene=fact.gene, label=fact.label.value) for fact in facts],
        pack=pack_info,
    )
