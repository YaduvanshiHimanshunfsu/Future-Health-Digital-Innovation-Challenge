from typing import Any

import pytest
from sqlalchemy import select, text

from app.explain.llm import LlmUnavailable
from app.models.case import CareCase
from app.models.conversation import Message
from app.models.enums import Boundary
from app.privacy.redaction import LlmRequest
from tests.api.helpers import Stack, bundle_for

pytestmark = pytest.mark.db


async def ask(stack: Stack, headers: dict[str, str], message: str, **extra: Any) -> Any:
    response = await stack.http.post(
        "/v1/chat", json={"message": message, **extra}, headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


async def test_chat_works_with_no_model(stack: Stack) -> None:
    """V4.3.7, and the exit gate's "chat works with the LLM switched off"."""
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("fatima-login", "fatima")
    body = await ask(stack, headers, "What does being a carrier mean?")
    assert body["boundary"] == "EDUCATION"
    assert body["source"] == "template"
    assert "HBB" in body["answer"]
    assert body["escalated"] is False


async def test_a_carrier_question_in_arabic_gets_an_education_answer(stack: Stack) -> None:
    """The exit gate. Roman-letter Arabic: "what does it mean that I'm a carrier of the gene?"."""
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("fatima-login", "fatima")
    body = await ask(stack, headers, "madha ya'ni annani hamil lil-jin?")
    assert body["boundary"] == "EDUCATION"
    assert body["escalated"] is False


@pytest.mark.parametrize(
    "question",
    [
        "I'm 12 weeks pregnant, what should I do?",
        "मैं गर्भवती हूँ, क्या करूँ?",  # "I'm pregnant, what should I do?"
        "ana hamil fi al-shahr al-thalith",  # "I'm three months pregnant"
    ],
)
async def test_clinical_questions_are_refused_kindly_and_reach_a_person(
    stack: Stack, question: str
) -> None:
    """The exit gate, in all three languages: a refusal, a booking offer, and a case."""
    headers = await stack.sign_in("someone")
    body = await ask(stack, headers, question)
    assert body["boundary"] == "CLINICAL_ADVICE"
    assert body["escalated"] is True
    case = await stack.only_case()
    assert case.priority == "P3"


async def test_distress_is_urgent_and_shows_no_made_up_number(stack: Stack) -> None:
    """V4.3.4. The pack lists no verified contacts, so none appear."""
    headers = await stack.sign_in("someone")
    body = await ask(stack, headers, "I can't go on")
    assert body["boundary"] == "DISTRESS"
    assert body["contacts"] == []
    assert "emergency services" in body["answer"]
    assert (await stack.only_case()).priority == "P1"


async def test_coercion_reaches_a_person_quickly(stack: Stack) -> None:
    """V4.3.12 and C10."""
    headers = await stack.sign_in("someone")
    body = await ask(stack, headers, "My in-laws are forcing me to show them my result")
    assert body["boundary"] == "COERCION"
    assert (await stack.only_case()).priority == "P2"


async def test_pregnancy_with_a_finding_is_urgent(stack: Stack) -> None:
    """A pregnant person who is a possible X-linked carrier gets P1."""
    await stack.ingest(bundle_for("x_carrier"))
    headers = await stack.sign_in("x-login", "x_carrier")
    await ask(stack, headers, "I am pregnant, is my baby ok?")
    assert (await stack.only_case()).priority == "P1"


async def test_messages_are_stored_encrypted_with_flags_and_no_text(stack: Stack) -> None:
    headers = await stack.sign_in("someone")
    await ask(stack, headers, "My name is Priya, what does carrier mean?")
    async with stack.factory() as session:
        rows = (await session.scalars(select(Message))).all()
    assert len(rows) == 2
    for row in rows:
        assert b"Priya" not in row.content_enc
        assert b"carrier" not in row.content_enc


async def test_a_conversation_belongs_to_one_person(stack: Stack) -> None:
    owner = await stack.sign_in("owner")
    stranger = await stack.sign_in("stranger")
    first = await ask(stack, owner, "What is a carrier?")
    response = await stack.http.post(
        "/v1/chat",
        json={"message": "hello", "conversation_id": first["conversation_id"]},
        headers=stranger,
    )
    assert response.status_code == 404


async def test_fact_ids_are_the_askers_own(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("fatima-login", "fatima")
    body = await ask(stack, headers, "What does my result mean?")
    assert body["fact_ids"] == ["carrier_self:HBB:carrier"]


async def test_no_transaction_is_open_while_the_answer_is_drafted(stack: Stack) -> None:
    """V4.3.11. A slow model must not hold database locks or connections in a transaction."""
    seen: list[int] = []

    class Watching:
        name = "watching"

        async def classify(self, question: str, language: str) -> Boundary:
            raise LlmUnavailable("not asked here")

        async def draft(self, request: LlmRequest, passages: list[str], language: str) -> str:
            async with stack.factory() as session:
                found = await session.scalar(
                    text(
                        "SELECT count(*) FROM pg_stat_activity "
                        "WHERE datname = current_database() AND state = 'idle in transaction'"
                    )
                )
                seen.append(int(found or 0))
            return "A short safe answer about carriers."

    stack.app.state.llm = Watching()
    headers = await stack.sign_in("someone")
    body = await ask(stack, headers, "What is a carrier?")
    assert seen == [0]
    assert body["source"] == "llm"


async def test_chat_needs_service_consent(stack: Stack) -> None:
    headers = await stack.provision("no-consent")
    response = await stack.http.post("/v1/chat", json={"message": "hi"}, headers=headers)
    assert response.status_code == 403


async def test_a_long_message_is_refused(stack: Stack) -> None:
    headers = await stack.sign_in("someone")
    response = await stack.http.post("/v1/chat", json={"message": "x" * 1001}, headers=headers)
    assert response.status_code == 422


async def test_chat_cases_are_new_cases_only_when_needed(stack: Stack) -> None:
    headers = await stack.sign_in("someone")
    await ask(stack, headers, "What is a carrier?")
    async with stack.factory() as session:
        assert (await session.scalars(select(CareCase))).all() == []
