"""Answers a question. Each step runs in order, and no step can be skipped.

redact, route, then for education only: retrieve, draft, validate, fill. Anything that fails falls
back to the reviewed template. Numbers enter only at the last step, from the risk engine.
"""

import asyncio
from dataclasses import dataclass, field

from app.country_packs.loader import CountryPack
from app.explain import answers
from app.explain.llm import LlmClient, LlmUnavailable
from app.explain.retriever import retrieve
from app.explain.router import Route, route
from app.explain.validators.pipeline import validate_draft
from app.models.enums import AnswerSource, Boundary
from app.privacy.redaction import RedactionError, build_llm_request
from app.risk_engine.types import RiskFact

DEADLINE_SECONDS = 20.0
_ESCALATE = frozenset({Boundary.CLINICAL_ADVICE, Boundary.DISTRESS, Boundary.COERCION})


@dataclass(frozen=True, slots=True)
class Answer:
    text: str
    boundary: Boundary
    source: AnswerSource
    fact_ids: tuple[str, ...] = ()
    passage_ids: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()
    route: Route | None = None
    language_used: str = "en"
    contacts: tuple[dict[str, str], ...] = field(default_factory=tuple)

    @property
    def escalate(self) -> bool:
        return self.boundary in _ESCALATE


def _fixed(key: str, boundary: Boundary, language: str, found: Route, pack: CountryPack) -> Answer:
    catalogue, used = answers.texts(language)
    text = catalogue[key]
    contacts: tuple[dict[str, str], ...] = ()
    if boundary is Boundary.DISTRESS:
        # Only contacts the pack lists as checked. A guessed crisis number could cost a life.
        listed = [
            c
            for c in pack.support_contacts.contacts
            if language in c.languages or "en" in c.languages
        ]
        if listed:
            contacts = tuple(
                {"service": c.service, "contact": c.contact, "hours": c.hours} for c in listed
            )
            text = f"{text} {catalogue['distress_contacts']}"
        else:
            text = f"{text} {catalogue['distress_no_contacts']}"
    if used != language:
        text = f"{catalogue['script_pending']} {text}"
    return Answer(
        text, boundary, AnswerSource.TEMPLATE, route=found, language_used=used, contacts=contacts
    )


async def answer(
    question: str,
    language: str,
    level: str,
    facts: list[RiskFact],
    pack: CountryPack,
    llm: LlmClient,
    *,
    deadline: float = DEADLINE_SECONDS,
) -> Answer:
    found = route(question, language)
    if found.boundary is Boundary.DISTRESS:
        return _fixed("distress", found.boundary, language, found, pack)
    if found.boundary is Boundary.COERCION:
        return _fixed("coercion", found.boundary, language, found, pack)
    if found.boundary is Boundary.CLINICAL_ADVICE:
        return _fixed("clinical", found.boundary, language, found, pack)
    if found.boundary is Boundary.DECISION_SUPPORT:
        return _fixed("decision", found.boundary, language, found, pack)

    catalogue, used = answers.texts(language)
    excluded = _not_for(facts)
    passages = [
        p
        for p in retrieve(question, used, "simple", _conditions(facts, pack), limit=4)
        if p.id not in excluded
    ][:2]
    template = answers.draft_for(facts, used)
    flags: tuple[str, ...] = ()
    text, source = template.text, AnswerSource.TEMPLATE

    try:
        request = build_llm_request(
            question,
            language,
            facts,
            patterns=[pack.identity.national_id_pattern],
            genes=pack.gene_table.genes,
        )
        draft = await asyncio.wait_for(
            llm.draft(request, [p.text for p in passages], used), timeout=deadline
        )
        result = validate_draft(draft, used, level, template.labels)
        flags = tuple(result.names)
        if result.ok:
            text, source = draft, AnswerSource.LLM
    except (LlmUnavailable, RedactionError, TimeoutError):
        # Any of these means the reviewed template, never a half-checked answer.
        pass

    if source is AnswerSource.TEMPLATE and passages:
        text = f"{text} {catalogue['general']} {passages[0].text}"
    if used != language:
        text = f"{catalogue['script_pending']} {text}"
    return Answer(
        text=answers.fill(text, facts),
        boundary=Boundary.EDUCATION,
        source=source,
        fact_ids=template.fact_ids,
        passage_ids=tuple(p.id for p in passages),
        flags=flags,
        route=found,
        language_used=used,
    )


_NOT_A_PLAIN_CARRIER = frozenset({"uncertain", "refer", "possible_affected", "review"})


def _not_for(facts: list[RiskFact]) -> frozenset[str]:
    """General carrier text would be wrong, and falsely reassuring, for these results (V4.3.8)."""
    unusual = any(fact.label.value in _NOT_A_PLAIN_CARRIER for fact in facts)
    x_linked = any(fact.scenario.value.startswith(("xl_", "couple_xl")) for fact in facts)
    if unusual or x_linked:
        return frozenset({"carrier_basics", "recessive_inheritance"})
    return frozenset()


def _conditions(facts: list[RiskFact], pack: CountryPack) -> list[str]:
    genes = pack.panel.genes
    return sorted({c for fact in facts if fact.gene in genes for c in genes[fact.gene].conditions})
