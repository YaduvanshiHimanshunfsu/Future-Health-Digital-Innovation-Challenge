from fastapi import APIRouter, Depends

from app.api.deps import current_person, get_packs, require_service_consent
from app.country_packs.loader import PackRegistry
from app.decision.options import options_for
from app.models.person import Person
from app.schemas.options import OptionOut, OptionsOut

router = APIRouter(tags=["options"])


@router.get("/options", response_model=OptionsOut)
async def list_options(
    person: Person = Depends(current_person),
    packs: PackRegistry = Depends(get_packs),
) -> OptionsOut:
    require_service_consent(person)
    cards = options_for(packs.require(person.pack_code))
    return OptionsOut(
        options=[
            OptionOut(key=c.key, title=c.title, source=c.source, note=c.note, reviewed=c.reviewed)
            for c in cards
        ]
    )
