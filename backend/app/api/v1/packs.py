from fastapi import APIRouter, Depends

from app.api.deps import get_packs
from app.country_packs.loader import PackRegistry
from app.schemas.common import Out

router = APIRouter(prefix="/packs", tags=["packs"])


class PackOut(Out):
    code: str
    name: str
    languages: list[str]
    default_language: str
    status: str
    # Shown beside the name, so an unreviewed country can't look like a supported one.
    reviewed: bool


@router.get("", response_model=list[PackOut])
async def list_packs(packs: PackRegistry = Depends(get_packs)) -> list[PackOut]:
    """Public, because someone chooses their country before they have an account."""
    found = (packs.require(code) for code in sorted(packs.codes))
    return [
        PackOut(
            code=pack.code,
            name=pack.manifest.name,
            languages=pack.manifest.languages,
            default_language=pack.manifest.default_language,
            status=pack.manifest.status.value,
            reviewed=pack.is_reviewed,
        )
        for pack in found
    ]
