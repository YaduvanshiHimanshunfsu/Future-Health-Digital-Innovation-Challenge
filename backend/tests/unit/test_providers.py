"""Model providers, tested against a fake HTTP service: the request each one sends, what it reads
back, and that every failure becomes LlmUnavailable rather than an error a person would see."""

import json
from collections.abc import Callable
from fractions import Fraction

import httpx
import pytest

from app.core.config import DEFAULT_PACKS_DIR
from app.country_packs.loader import load_pack
from app.explain.graph import answer, second_opinion
from app.explain.llm import LlmUnavailable, TemplateOnly
from app.explain.providers import (
    GeminiClient,
    OllamaClient,
    OpenAICompatClient,
    ProviderChain,
    build_llm,
    draft_messages,
    parse_label,
)
from app.explain.router import route
from app.models.enums import Boundary
from app.privacy.redaction import LlmRequest
from app.risk_engine.engine import _fact
from app.risk_engine.types import Label, Scenario
from tests.conftest import settings_for_tests
from tests.unit.test_config import production

KEY = "test-key-not-real-0123456789"
PACK = load_pack(DEFAULT_PACKS_DIR / "ae-abu-dhabi")
REQUEST = LlmRequest(
    question="what does carrier mean",
    facts=(
        {
            "id": "couple_shared_ar:HBB:two_copies",
            "scenario": "couple_shared_ar",
            "gene": "HBB",
            "label": "two_copies",
            "percent": "25",
            "one_in": 4,
            "has_number": True,
        },
    ),
)


def client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def gemini_reply(text: str, finish: str = "STOP") -> httpx.Response:
    return httpx.Response(
        200, json={"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": finish}]}
    )


async def test_gemini_sends_the_key_in_a_header_and_reads_the_text() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return gemini_reply("Carriers have one changed copy.")

    gemini = GeminiClient(client(handler), "gemini-test", KEY, 5)
    assert await gemini.draft(REQUEST, ["A passage."], "en") == "Carriers have one changed copy."
    sent = seen[0]
    assert sent.url.path.endswith("/models/gemini-test:generateContent")
    assert sent.headers["x-goog-api-key"] == KEY
    assert KEY not in str(sent.url)
    body = json.loads(sent.content)
    assert "English" in body["systemInstruction"]["parts"][0]["text"]


@pytest.mark.parametrize(
    "reply",
    [
        httpx.Response(429, json={"error": {"message": f"quota for key {KEY}"}}),
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"candidates": []}),
        gemini_reply("", "STOP"),
        gemini_reply("Something", "SAFETY"),
    ],
)
async def test_gemini_failures_become_unavailable_without_the_key(reply: httpx.Response) -> None:
    gemini = GeminiClient(client(lambda _: reply), "gemini-test", KEY, 5)
    with pytest.raises(LlmUnavailable) as caught:
        await gemini.draft(REQUEST, [], "en")
    assert KEY not in str(caught.value)


async def test_a_network_failure_becomes_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"cannot reach {request.url}", request=request)

    with pytest.raises(LlmUnavailable) as caught:
        await GeminiClient(client(handler), "m", KEY, 5).classify("hello", "en")
    assert str(caught.value) == "ConnectError"


async def test_ollama_uses_the_chat_endpoint_without_streaming() -> None:
    seen: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("http://127.0.0.1:11434/api/chat")
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "DISTRESS"}})

    ollama = OllamaClient(client(handler), "qwen2.5:3b", "http://127.0.0.1:11434/", 5)
    assert await ollama.classify("i do not want to live", "en") is Boundary.DISTRESS
    assert seen[0]["stream"] is False
    assert seen[0]["model"] == "qwen2.5:3b"


async def test_openai_compatible_services_get_a_bearer_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == f"Bearer {KEY}"
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(200, json={"choices": [{"message": {"content": "EDUCATION"}}]})

    compat = OpenAICompatClient(client(handler), "some-model", "https://llm.example/v1", KEY, 5)
    assert await compat.classify("what is a gene", "en") is Boundary.EDUCATION


def test_the_model_never_sees_a_figure_only_placeholders() -> None:
    system, user = draft_messages(REQUEST, ["passage"], "ar")
    payload = json.loads(user)
    assert payload["placeholders_you_may_use"] == ["{fact:couple_shared_ar:HBB:two_copies}"]
    assert "25" not in user
    assert all("percent" not in fact and "one_in" not in fact for fact in payload["facts"])
    assert "Arabic" in system


@pytest.mark.parametrize(
    ("reply", "label"),
    [
        ("DISTRESS", Boundary.DISTRESS),
        ("coercion.", Boundary.COERCION),
        ("Label: EDUCATION", Boundary.EDUCATION),
    ],
)
def test_labels_are_read_from_short_replies(reply: str, label: Boundary) -> None:
    assert parse_label(reply) is label


def test_an_unreadable_label_is_unavailable() -> None:
    with pytest.raises(LlmUnavailable):
        parse_label("I'm not sure what you mean")


def test_template_is_the_default_and_providers_need_their_settings() -> None:
    http = httpx.AsyncClient()
    assert isinstance(build_llm(settings_for_tests(), http), TemplateOnly)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        build_llm(settings_for_tests(llm_provider="gemini", gemini_api_key=None), http)
    with pytest.raises(ValueError, match="OPENAI_COMPAT_URL"):
        build_llm(settings_for_tests(llm_provider="openai_compat"), http)
    built = build_llm(settings_for_tests(llm_provider="gemini", gemini_api_key=KEY), http)
    assert built.name == "gemini"
    assert build_llm(settings_for_tests(llm_provider="ollama"), http).name == "ollama"
    chain = build_llm(settings_for_tests(llm_provider="gemini,ollama", gemini_api_key=KEY), http)
    assert chain.name == "gemini,ollama"
    # No key on this machine: Gemini is skipped and Ollama serves alone.
    skipped = build_llm(settings_for_tests(llm_provider="gemini,ollama", gemini_api_key=""), http)
    assert skipped.name == "ollama"
    with pytest.raises(ValueError, match="LLM_PROVIDER takes"):
        settings_for_tests(llm_provider="gpt")


async def test_the_chain_falls_through_to_the_next_provider() -> None:
    failing = GeminiClient(client(lambda _: httpx.Response(401, json={})), "m", KEY, 5)
    local = OllamaClient(
        client(lambda _: httpx.Response(200, json={"message": {"content": "COERCION"}})),
        "qwen2.5:3b",
        "http://127.0.0.1:11434",
        5,
    )
    assert await ProviderChain([failing, local]).classify("x", "en") is Boundary.COERCION
    with pytest.raises(LlmUnavailable):
        await ProviderChain([failing]).draft(REQUEST, [], "en")


def test_production_refuses_a_hosted_model_without_approval() -> None:
    with pytest.raises(ValueError, match="LLM_EXTERNAL_APPROVED"):
        settings_for_tests(**production(llm_provider="gemini", gemini_api_key=KEY))
    assert settings_for_tests(
        **production(llm_provider="gemini", gemini_api_key=KEY, llm_external_approved=True)
    ).is_production
    assert settings_for_tests(**production(llm_provider="ollama")).is_production


class Opinion:
    name = "opinion"

    def __init__(self, label: Boundary | None) -> None:
        self.label = label
        self.seen: list[str] = []

    async def draft(self, request: LlmRequest, passages: list[str], language: str) -> str:
        raise LlmUnavailable("drafts not used here")

    async def classify(self, question: str, language: str) -> Boundary:
        self.seen.append(question)
        if self.label is None:
            raise LlmUnavailable("no opinion")
        return self.label


async def test_a_second_opinion_can_escalate_a_question() -> None:
    question = "What is a gene panel, I feel so tired of everything"
    found = route(question, "en")
    model = Opinion(Boundary.DISTRESS)
    checked = await second_opinion(question, "en", found, PACK, model)
    assert checked.boundary is Boundary.DISTRESS
    assert "model_check" in checked.reasons


async def test_a_second_opinion_can_never_relax_a_question() -> None:
    question = "I'm 12 weeks pregnant, what should I do?"
    found = route(question, "en")
    checked = await second_opinion(question, "en", found, PACK, Opinion(Boundary.EDUCATION))
    assert checked == found


async def test_without_a_model_the_rules_stand() -> None:
    found = route("What does being a carrier mean?", "en")
    assert (
        await second_opinion("What does being a carrier mean?", "en", found, PACK, Opinion(None))
        == found
    )


async def test_the_model_check_only_sees_the_redacted_question() -> None:
    model = Opinion(Boundary.EDUCATION)
    await second_opinion(
        "Fatima asks what a carrier is, ID 784-1990-1234567-1",
        "en",
        route("what is a carrier", "en"),
        PACK,
        model,
    )
    assert "Fatima" not in model.seen[0]
    assert "784" not in model.seen[0]


async def test_an_escalated_answer_is_the_fixed_text_and_no_draft_is_requested() -> None:
    facts = [_fact(Scenario.CARRIER_SELF, "HBB", Label.CARRIER, None, "c")]
    model = Opinion(Boundary.DISTRESS)
    result = await answer(
        "Tell me about carriers, I can't see a way forward", "en", "simple", facts, PACK, model
    )
    assert result.boundary is Boundary.DISTRESS
    assert "local emergency services" in result.text
    _ = Fraction  # facts above need no figures


async def test_once_a_person_is_reached_the_model_may_only_add_the_crisis_reading() -> None:
    """A small model relabelled a pregnancy question as coercion. The person was reached either way,
    so only DISTRESS, which adds the crisis line and urgency, may change such a route."""
    question = "ana hamil fi al-shahr al-thalith"
    found = route(question, "ar")
    assert found.boundary is Boundary.CLINICAL_ADVICE
    assert await second_opinion(question, "ar", found, PACK, Opinion(Boundary.COERCION)) == found
    upgraded = await second_opinion(question, "ar", found, PACK, Opinion(Boundary.DISTRESS))
    assert upgraded.boundary is Boundary.DISTRESS


async def test_an_unplaced_message_can_be_placed_by_the_model() -> None:
    found = route("Nobody would notice if I was gone", "en")
    assert found.reasons == ("unclear",)
    placed = await second_opinion(
        "Nobody would notice if I was gone", "en", found, PACK, Opinion(Boundary.COERCION)
    )
    assert placed.boundary is Boundary.COERCION


async def test_a_decision_label_from_the_model_changes_nothing() -> None:
    """A decision label brings in nobody, so it would only cost the person their explanation."""
    found = route("What does being a carrier mean?", "en")
    assert (
        await second_opinion(
            "What does being a carrier mean?", "en", found, PACK, Opinion(Boundary.DECISION_SUPPORT)
        )
        == found
    )
