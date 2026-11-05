"""Option cards, straight from the country pack's signed-off table.

Every card has the same fields, and the order is the pack's own, never a ranking. Nothing here reads
what a person said matters to them: values reflect back to the person and never change the options.
"""

from dataclasses import dataclass

from app.country_packs.loader import CountryPack


@dataclass(frozen=True, slots=True)
class OptionCard:
    key: str
    title: str
    source: str
    note: str | None
    reviewed: bool


def options_for(pack: CountryPack) -> list[OptionCard]:
    return [
        OptionCard(
            key=option.key,
            title=option.title,
            source=option.source,
            note=option.note,
            reviewed=option.reviewed_by is not None,
        )
        for option in pack.options.options
    ]
