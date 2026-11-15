"""Where screening and counselling are offered, from the country pack's own list.

Public: finding a centre needs no account and no result on file (V5.2.6). A real entry shows its
source and the date it was checked. A demo entry is marked fictional, carries no contact details,
and the pack loader refuses one in a reviewed pack. An empty list is shown as empty.

The order is fixed: by the pack's regions, then city, then name. Nothing can buy a higher place,
and nothing here ranks one centre as better than another.
"""

from datetime import date
from http import HTTPStatus

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_packs
from app.core.errors import ApiError
from app.country_packs.loader import PackRegistry
from app.country_packs.schema import Centre, CentreService, VisitMode
from app.schemas.booking import CentreOut, CentresOut

router = APIRouter(prefix="/centres", tags=["centres"])


def _matches(
    centre: Centre,
    *,
    words: list[str],
    region: str | None,
    service: str | None,
    mode: str | None,
    step_free: bool | None,
) -> bool:
    searchable = f"{centre.name} {centre.city}".casefold()
    return (
        all(word in searchable for word in words)
        and (region is None or centre.region == region)
        and (service is None or service in centre.services)
        and (mode is None or mode in centre.modes)
        # Only an explicit "yes" counts. "Not checked" isn't step-free.
        and (step_free is not True or centre.step_free is True)
    )


@router.get("", response_model=CentresOut)
async def centres(
    pack: str | None = Query(default=None, max_length=32),
    q: str | None = Query(default=None, max_length=60),
    region: str | None = Query(default=None, max_length=32),
    service: CentreService | None = None,
    mode: VisitMode | None = None,
    step_free: bool | None = None,
    packs: PackRegistry = Depends(get_packs),
) -> CentresOut:
    chosen = packs.get(pack) if pack else packs.default
    if chosen is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "unknown_country_pack")
    every = chosen.services.centres
    order = {name: index for index, name in enumerate(chosen.strata.regions)}
    words = (q or "").casefold().split()
    listed = sorted(
        (
            centre
            for centre in every
            if _matches(
                centre,
                words=words,
                region=region,
                service=service,
                mode=mode,
                step_free=step_free,
            )
        ),
        key=lambda c: (order.get(c.region, len(order)), c.city, c.name),
    )
    checked = [date.fromisoformat(c.checked_on) for c in listed if c.checked_on]
    present = {centre.region for centre in every}
    return CentresOut(
        pack=chosen.code,
        pack_name=chosen.manifest.name,
        pack_reviewed=chosen.is_reviewed,
        qualified_human=chosen.services.qualified_human,
        total=len(every),
        fictional_count=sum(centre.fictional for centre in every),
        regions=[name for name in chosen.strata.regions if name in present],
        region_names=dict(chosen.strata.region_names),
        centres=[CentreOut.model_validate(c, from_attributes=True) for c in listed],
        funding_notes=list(chosen.services.funding_notes),
        as_of=min(checked) if checked else None,
    )
