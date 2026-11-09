"""Programme metrics for a programme administrator. Aggregates only: no person, case or ID appears
in any response, and every count of people under the minimum cell size arrives as null."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.metrics import overview
from app.api.deps import get_audit, get_db, get_packs
from app.core.security import Principal, require_role
from app.country_packs.loader import PackRegistry
from app.privacy.audit import AuditTrail
from app.schemas.analytics import AnalyticsOut

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOut)
async def programme_overview(
    principal: Principal = Depends(require_role("program_admin")),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> AnalyticsOut:
    result = await overview(db, packs.default)
    await audit.append(
        db, actor=principal.sub, action="analytics.view", resource="analytics:overview"
    )
    await db.commit()
    return result
