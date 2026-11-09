import asyncio
from fractions import Fraction

import pytest

from app.core.config import DEFAULT_PACKS_DIR
from app.country_packs.loader import load_pack
from app.explain.graph import answer
from app.explain.llm import LlmUnavailable, TemplateOnly
from app.models.enums import AnswerSource, Boundary
from app.privacy.redaction import LlmRequest
from app.risk_engine.engine import _fact
from app.risk_engine.types import Label, Scenario

PACK = load_pack(DEFAULT_PACKS_DIR / "ae-abu-dhabi")
CARRIER = [_fact(Scenario.CARRIER_SELF, "HBB", Label.CARRIER, None, "c")]
SHARED = [
    _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.TWO_COPIES, Fraction(1, 4), "c"),
    _fact(Scenario.COUPLE_SHARED_AR, "HBB", Label.CARRIER, Fraction(1, 2), "c"),
]


class Scripted:
    """Stands in for a model, returning a fixed draft and recording what it was given."""

    name = "scripted"

    def __init__(self, draft: str = "", delay: float = 0.0, label: Boundary | None = None) -> None:
        self.text, self.delay, self.label = draft, delay, label
        self.requests: list[LlmRequest] = []
        self.classified: list[str] = []

    async def draft(self, request: LlmRequest, passages: list[str], language: str) -> str:
        self.requests.append(request)
        await asyncio.sleep(self.delay)
        return self.text

    async def classify(self, question: str, language: str) -> Boundary:
        self.classified.append(question)
        if self.label is None:
            raise LlmUnavailable("no opinion scripted")
        return self.label


async def test_template_mode_answers_with_no_model() -> None:
    """V4.3.7."""
    result = await answer(
        "What does being a carrier mean?", "en", "simple", CARRIER, PACK, TemplateOnly()
    )
    assert result.boundary is Boundary.EDUCATION
    assert result.source is AnswerSource.TEMPLATE
    assert "HBB" in result.text
    assert "usually doesn't cause illness" in result.text


async def test_numbers_in_an_answer_come_from_the_risk_engine() -> None:
    result = await answer(
        "What are the chances for our children?", "en", "simple", SHARED, PACK, TemplateOnly()
    )
    assert "25% (1 in 4)" in result.text
    assert "50%" in result.text


async def test_a_good_model_draft_is_used_with_figures_filled_by_code() -> None:
    draft = f"In each pregnancy there is a {{fact:{SHARED[0].id}}} chance that a child inherits two copies."
    model = Scripted(draft)
    result = await answer("What are the chances?", "en", "standard", SHARED, PACK, model)
    assert result.source is AnswerSource.LLM
    assert "25% (1 in 4)" in result.text


@pytest.mark.parametrize(
    "draft",
    [
        "You should not have children.",
        "There is a 25% chance of two copies.",
        f"There is a {{fact:{SHARED[1].id}}} chance that a child inherits two copies.",
        "You are healthy, nothing to worry about.",
    ],
)
async def test_an_unsafe_model_draft_falls_back_to_the_template(draft: str) -> None:
    """V4.2 and C5. The flags are kept, without the text, for the safety dashboard."""
    result = await answer("What are the chances?", "en", "standard", SHARED, PACK, Scripted(draft))
    assert result.source is AnswerSource.TEMPLATE
    assert result.flags
    assert draft not in result.text


async def test_a_stalled_model_gives_the_template_in_time() -> None:
    """V4.3.5. A 30 s stall, against a short deadline, so the test stays fast."""
    started = asyncio.get_running_loop().time()
    result = await answer(
        "What does this mean?", "en", "simple", CARRIER, PACK, Scripted("x", delay=30), deadline=0.2
    )
    assert result.source is AnswerSource.TEMPLATE
    assert asyncio.get_running_loop().time() - started < 2


async def test_the_model_sees_no_names_or_ids() -> None:
    model = Scripted("A short answer.")
    await answer(
        "My name is Priya and my id is 784-1990-1234567-1, what is HBB?",
        "en",
        "simple",
        CARRIER,
        PACK,
        model,
    )
    sent = model.requests[0]
    assert "Priya" not in sent.question
    assert "1234567" not in sent.question
    assert "HBB" in sent.question


@pytest.mark.parametrize(
    ("question", "boundary"),
    [
        ("I'm 12 weeks pregnant, what should I do?", Boundary.CLINICAL_ADVICE),
        ("I want to die", Boundary.DISTRESS),
        ("My family is forcing me to share my result", Boundary.COERCION),
        ("What are my options?", Boundary.DECISION_SUPPORT),
    ],
)
async def test_hard_questions_never_reach_the_model(question: str, boundary: Boundary) -> None:
    model = Scripted("anything")
    result = await answer(question, "en", "simple", CARRIER, PACK, model)
    assert result.boundary is boundary
    assert model.requests == []
    assert result.source is AnswerSource.TEMPLATE


async def test_distress_never_shows_a_guessed_number() -> None:
    """The pack lists no verified contacts, so none are shown and nothing is made up."""
    result = await answer("I want to die", "en", "simple", CARRIER, PACK, TemplateOnly())
    assert result.contacts == ()
    assert "local emergency services" in result.text
    assert not any(ch.isdigit() for ch in result.text)


@pytest.mark.parametrize(
    "facts",
    [
        [_fact(Scenario.UNCERTAIN_VUS, "CYP21A2", Label.UNCERTAIN, None, "c")],
        [_fact(Scenario.XL_CARRIER_FEMALE, "DMD", Label.SON_AFFECTED, Fraction(1, 2), "c")],
    ],
)
async def test_uncertain_and_x_linked_never_get_the_general_carrier_text(facts: list) -> None:
    """V4.3.8. "Usually doesn't cause illness" would be false reassurance for these."""
    result = await answer(
        "What does being a carrier mean?", "en", "simple", facts, PACK, TemplateOnly()
    )
    assert "usually doesn't cause illness" not in result.text
    assert "carrier_basics" not in result.passage_ids


async def test_hindi_gets_a_hindi_answer() -> None:
    result = await answer("वाहक होने का मतलब क्या है?", "hi", "simple", CARRIER, PACK, TemplateOnly())
    assert "वाहक" in result.text
    assert result.language_used == "hi"


async def test_arabic_gets_english_and_says_why() -> None:
    result = await answer(
        "madha ya'ni annani hamil lil-jin?", "ar", "simple", CARRIER, PACK, TemplateOnly()
    )
    assert result.boundary is Boundary.EDUCATION
    assert result.language_used == "en"
    assert result.text.startswith("Answers in Arabic are waiting for review")


async def test_a_message_the_router_cannot_place_goes_to_a_person_with_support_shown() -> None:
    """Education is never the fallback. A statement naming no topic could be distress in words the
    rules don't know, so a person reads it, and the safety line is shown as for distress."""
    model = Scripted("anything")
    result = await answer("Nobody would notice if I was gone", "en", "simple", CARRIER, PACK, model)
    assert result.boundary is Boundary.CLINICAL_ADVICE
    assert result.route.reasons == ("unclear",)
    assert model.requests == []
    # This pack has no verified contacts, so the emergency-services line is shown, and no number.
    assert "local emergency services" in result.text
    assert not any(ch.isdigit() for ch in result.text)
