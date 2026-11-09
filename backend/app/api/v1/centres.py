"""Where screening and counselling are offered, from the country pack's own list.

Public: finding a centre needs no account and no result on file (V5.2.6). Each entry shows its
source and the date it was checked. An empty list is shown as empty, with the pack's honest status,
rather than filled with guesses: a wrong address is worse than none.
"""

from datetime import date
from http import HTTPStatus

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_packs
from app.core.errors import ApiError
from app.country_packs.loader import PackRegistry
from app.schemas.booking import CentreOut, CentresOut

router = APIRouter(prefix="/centres", tags=["centres"])


@router.get("", response_model=CentresOut)
async def centres(
    pack: str | None = Query(default=None, max_length=32),
    region: str | None = Query(default=None, max_length=32),
    packs: PackRegistry = Depends(get_packs),
) -> CentresOut:
    chosen = packs.get(pack) if pack else packs.default
    if chosen is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "unknown_country_pack")
    listed = [c for c in chosen.services.centres if region is None or c.region == region]
    checked = [date.fromisoformat(c.checked_on) for c in listed]
    return CentresOut(
        pack=chosen.code,
        pack_reviewed=chosen.is_reviewed,
        qualified_human=chosen.services.qualified_human,
        centres=[CentreOut.model_validate(c, from_attributes=True) for c in listed],
        funding_notes=list(chosen.services.funding_notes),
        as_of=min(checked) if checked else None,
    )
