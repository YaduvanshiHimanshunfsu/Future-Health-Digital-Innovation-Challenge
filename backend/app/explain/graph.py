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
# The check runs beside the draft, so it can take nearly as long without slowing the answer.
CHECK_SECONDS = 15.0
# Most careful first. A second opinion may only move a question up this list.
_CAREFUL = [
    Boundary.DISTRESS,
    Boundary.COERCION,
    Boundary.CLINICAL_ADVICE,
    Boundary.DECISION_SUPPORT,
    Boundary.EDUCATION,
]
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
    # A message the router couldn't place may be distress in words it doesn't know, so it gets the
    # same support contacts. The early evaluation found exactly that kind of message. A message in a
    # script no rule reads, Arabic script included, could be distress too, so it gets them as well.
    unclear = "unclear" in found.reasons or "unsupported_script" in found.reasons
    if boundary is Boundary.DISTRESS or unclear:
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
            text = f"{text} {catalogue['unclear_contacts' if unclear else 'distress_contacts']}"
        else:
            text = f"{text} {catalogue['distress_no_contacts']}"
    if used != language:
        text = f"{catalogue['script_pending']} {text}"
    return Answer(
        text, boundary, AnswerSource.TEMPLATE, route=found, language_used=used, contacts=contacts
    )


async def second_opinion(
    question: str, language: str, found: Route, pack: CountryPack, llm: LlmClient
) -> Route:
    """Asks the model to classify the redacted question, and keeps whichever reading is more careful.

    Rules can't recognise distress they haven't seen (docs/evaluation/router_early_eval.md), so a
    model double-checks them. It can only escalate: if it says "education" where the rules said
    "clinical", the rules win. If it fails or is slow, the rules' answer stands.
    """
    if found.boundary is Boundary.DISTRESS:
        return found
    # When the rules have already sent a question to a person, the model may only add the crisis
    # reading. A small model once relabelled "I'm three months pregnant" as coercion, which would
    # have shown the wrong message; the person was reached either way.
    reached = found.boundary in _ESCALATE and found.reasons != ("unclear",)
    try:
        redacted = build_llm_request(
            question,
            language,
            [],
            patterns=[pack.identity.national_id_pattern],
            genes=pack.gene_table.genes,
        ).question
        opinion = await asyncio.wait_for(llm.classify(redacted, language), timeout=CHECK_SECONDS)
    except (LlmUnavailable, RedactionError, TimeoutError):
        return found
    if _CAREFUL.index(opinion) >= _CAREFUL.index(found.boundary):
        return found
    # The check exists to bring in a person. "Decision" brings in nobody, so a model saying it only
    # costs someone their explanation: a small model once called "what does carrier mean?" a decision.
    if opinion not in _ESCALATE:
        return found
    if reached and opinion is not Boundary.DISTRESS:
        return found
    return Route(opinion, (*found.reasons, "model_check"), found.pregnant)


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
    rules = route(question, language)
    if rules.boundary is not Boundary.EDUCATION:
        return _for_a_person(
            await second_opinion(question, language, rules, pack, llm), language, pack
        )

    # For education, the model's check and the draft run side by side, so a slow model costs the
    # time of one call, not two. If the check escalates, the draft is simply never shown.
    check = asyncio.create_task(second_opinion(question, language, rules, pack, llm))
    try:
        educated = await _educate(question, language, level, facts, pack, llm, deadline, rules)
    finally:
        found = await check
    if found.boundary is Boundary.EDUCATION:
        return educated
    return _for_a_person(found, language, pack)


def _for_a_person(found: Route, language: str, pack: CountryPack) -> Answer:
    keys = {
        Boundary.DISTRESS: "distress",
        Boundary.COERCION: "coercion",
        Boundary.CLINICAL_ADVICE: "clinical",
        Boundary.DECISION_SUPPORT: "decision",
    }
    return _fixed(keys[found.boundary], found.boundary, language, found, pack)


async def _educate(
    question: str,
    language: str,
    level: str,
    facts: list[RiskFact],
    pack: CountryPack,
    llm: LlmClient,
    deadline: float,
    found: Route,
) -> Answer:
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
