from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Body, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_audit, get_cipher, get_db, get_packs
from app.core.config import decode_key
from app.core.errors import ApiError
from app.core.rate_limit import rate_limit
from app.core.security import Principal, require_role
from app.country_packs.loader import PackRegistry
from app.ingestion.service import IngestContext, ingest_bundle
from app.models.enums import Attestation
from app.privacy.audit import AuditTrail
from app.privacy.crypto import FieldCipher

router = APIRouter(tags=["reports"])


@router.post("/reports:ingest", status_code=HTTPStatus.CREATED)
async def ingest(
    request: Request,
    response: Response,
    bundle: Any = Body(...),
    pack_code: str = Header(alias="X-Country-Pack", max_length=32),
    principal: Principal = Depends(require_role("lab_service")),
    _: None = Depends(rate_limit("ingest", 600, 60)),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> dict[str, Any]:
    pack = packs.get(pack_code)
    if pack is None:
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "unknown_country_pack")
    settings = request.app.state.settings
    result = await ingest_bundle(
        db,
        IngestContext(
            national_id_key=decode_key(settings.national_id_hmac_key, "NATIONAL_ID_HMAC_KEY"),
            cipher=cipher,
            audit=audit,
            attestation=Attestation(settings.lab_attestation),
        ),
        bundle=bundle,
        pack=pack,
        source_lab=principal.sub,
        actor=principal.sub,
    )
    await db.commit()
    if result.replayed:
        response.status_code = HTTPStatus.OK
    return {"report_id": str(result.report.id), "replayed": result.replayed}
