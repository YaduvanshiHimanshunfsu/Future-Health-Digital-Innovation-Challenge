from collections.abc import Iterable

from app.country_packs.loader import CountryPack
from app.risk_engine.types import Flag, RiskFact


def can_withhold(pack: CountryPack) -> bool:
    return pack.legal.right_not_to_know


def human_contact_required(facts: Iterable[RiskFact], pack: CountryPack) -> bool:
    """Some laws require telling someone anyway. That's a counsellor's conversation, never a screen.

    "Possibly affected" stands in for "threatens life" until a clinician defines the real rule.
    """
    return pack.legal.must_inform_if_life_threatening and any(
        Flag.POSSIBLE_AFFECTED in fact.flags for fact in facts
    )
