"""Reading one case. The counsellor queue and actions on a case arrive in sub-phase 4.5."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_person, deny, get_audit, get_authz, get_cipher, get_db
from app.core.security import Principal, require_role
from app.models.case import CareCase
from app.models.person import Person
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz
from app.privacy.crypto import FieldCipher
from app.schemas.cases import CaseOut
from app.triage.service import reasons_aad

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
        through_break_glass=not assigned,
    )
