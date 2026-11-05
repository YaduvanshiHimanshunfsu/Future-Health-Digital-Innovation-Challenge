"""The facts an answer may draw on: the person's own, and nothing about anyone else.

Couple facts reach a person only through the couple check, which has its own consent and view. Chat
doesn't recompute them, so a partner's private finding can't reach the chat or its AI context (C7).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.country_packs.loader import CountryPack
from app.models.person import Person
from app.privacy.crypto import FieldCipher
from app.repositories.genetic import load_record, person_sex
from app.risk_engine.engine import person_facts
from app.risk_engine.types import RiskFact


async def own_facts(
    db: AsyncSession, cipher: FieldCipher, person: Person, pack: CountryPack
) -> list[RiskFact]:
    # Someone who chose not to know gets no facts here either.
    if person.results_withheld_at is not None:
        return []
    record = await load_record(db, cipher, person.id)
    return person_facts(record.findings, await person_sex(cipher, person), pack.gene_table)


def conditions_of(facts: list[RiskFact], pack: CountryPack) -> list[str]:
    genes = pack.panel.genes
    return sorted({c for fact in facts if fact.gene in genes for c in genes[fact.gene].conditions})
