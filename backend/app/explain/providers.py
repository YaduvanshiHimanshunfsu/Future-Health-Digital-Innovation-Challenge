"""Model providers: Gemini, Ollama on this machine, and any OpenAI-compatible service.

Each is a thin HTTP client with the same two jobs (see `LlmClient`). They share the prompts below, so
the safety instructions are written once. A provider never decides anything alone:
- a draft is validated, and replaced by the reviewed template if any rule fails;
- a classification can only move a question towards a person, never away (`app/explain/graph.py`).

Any network error, refusal, empty answer or unreadable reply raises `LlmUnavailable`, which the
pipeline treats as "use the template". Keys come from settings and never appear in logs or errors.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.explain.llm import LlmClient, LlmUnavailable, TemplateOnly
from app.models.enums import Boundary
from app.privacy.redaction import LlmRequest

log = logging.getLogger(__name__)

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "ar": "Arabic"}

DRAFT_RULES = """You explain genetic carrier screening results for Samvid, a service that gives
general education only. Follow every rule:
- Write in {language}, in plain words, at most 120 words, as plain text with no markup or links.
- Never write a number, percentage or "1 in N" yourself. To state a chance, copy a placeholder
  exactly as given, such as {{fact:couple_shared_ar:HBB:two_copies}}. Use only the placeholders listed.
- Never tell anyone what to do: no "you should", "best", "recommend", "must". Decisions are theirs.
- Never diagnose, never promise health, never say there is no risk.
- Never call people or genes defective, bad or incompatible.
- Words shown as [word] were removed for privacy. Don't guess them.
- Use only the facts and passages given. If they don't answer the question, say a counsellor can help."""

CLASSIFY_RULES = """Classify one message sent to a genetic screening education service. Reply with
exactly one label and nothing else:
DISTRESS - any sign the person may harm themselves, feels hopeless, or is in crisis
COERCION - someone is pressuring, threatening or controlling them about testing, results or marriage
CLINICAL_ADVICE - about their own or a family member's health, symptoms, pregnancy, tests or treatment
DECISION_SUPPORT - asks what they should decide, such as whether to marry or have children
EDUCATION - a general question about genes, inheritance, carriers, screening or privacy
If more than one fits, choose the one listed first. Words shown as [word] were removed for privacy."""


def draft_messages(request: LlmRequest, passages: list[str], language: str) -> tuple[str, str]:
    """The system text and the user text for a draft. Only the request and passages go out."""
    placeholders = [f"{{fact:{fact['id']}}}" for fact in request.facts if fact.get("has_number")]
    payload = {
        "question": request.question,
        "facts": [
            {k: v for k, v in fact.items() if k not in ("percent", "one_in")}
            for fact in request.facts
        ],
        "placeholders_you_may_use": placeholders,
        "passages": passages,
    }
    system = DRAFT_RULES.format(language=LANGUAGE_NAMES.get(language, "English"))
    return system, json.dumps(payload, ensure_ascii=False)


def parse_label(text: str) -> Boundary:
    """The first known label in the reply. Anything else is unreadable, so it can't be used."""
    for word in text.replace(",", " ").replace(".", " ").split():
        try:
            return Boundary(word.strip().upper())
        except ValueError:
            continue
    raise LlmUnavailable("unreadable classification")


def _text_or_fail(text: object) -> str:
    if not isinstance(text, str) or not text.strip():
        raise LlmUnavailable("empty answer")
    return text.strip()


class _HttpProvider:
    name = "http"

    def __init__(self, http: httpx.AsyncClient, model: str, timeout: float) -> None:
        self._http = http
        self._model = model
        self._timeout = timeout

    async def _complete(self, system: str, user: str, max_tokens: int) -> str:
        raise NotImplementedError

    async def _post(self, url: str, body: dict[str, Any], headers: dict[str, str]) -> Any:
        try:
            response = await self._http.post(url, json=body, headers=headers, timeout=self._timeout)
        except httpx.HTTPError as exc:
            # The exception type only: a message can carry the URL, and some services put keys there.
            raise LlmUnavailable(type(exc).__name__) from None
        if response.status_code != 200:
            raise LlmUnavailable(f"status {response.status_code}")
        try:
            return response.json()
        except ValueError:
            raise LlmUnavailable("not json") from None

    async def draft(self, request: LlmRequest, passages: list[str], language: str) -> str:
        system, user = draft_messages(request, passages, language)
        return await self._complete(system, user, max_tokens=400)

    async def classify(self, question: str, language: str) -> Boundary:
        return parse_label(await self._complete(CLASSIFY_RULES, question, max_tokens=8))


class GeminiClient(_HttpProvider):
    """Google's Gemini API (generateContent). The key travels in a header, never in the URL."""

    name = "gemini"
    BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, http: httpx.AsyncClient, model: str, api_key: str, timeout: float) -> None:
        super().__init__(http, model, timeout)
        self._key = api_key

    async def _complete(self, system: str, user: str, max_tokens: int) -> str:
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": max_tokens},
        }
        data = await self._post(
            f"{self.BASE}/models/{self._model}:generateContent", body, {"x-goog-api-key": self._key}
        )
        try:
            candidate = data["candidates"][0]
            if candidate.get("finishReason") not in (None, "STOP", "MAX_TOKENS"):
                # SAFETY, RECITATION and the like: the template is the safer answer.
                raise LlmUnavailable(f"finish {candidate.get('finishReason')}")
            parts = candidate["content"]["parts"]
            return _text_or_fail("".join(part.get("text", "") for part in parts))
        except (KeyError, IndexError, TypeError):
            raise LlmUnavailable("unexpected reply") from None


class OllamaClient(_HttpProvider):
    """A model served by Ollama, by default on this machine, so nothing leaves it."""

    name = "ollama"

    def __init__(self, http: httpx.AsyncClient, model: str, base_url: str, timeout: float) -> None:
        super().__init__(http, model, timeout)
        self._base = base_url.rstrip("/")

    async def _complete(self, system: str, user: str, max_tokens: int) -> str:
        body = {
            "model": self._model,
            "stream": False,
            # Stay loaded between questions: loading the model again costs several seconds.
            "keep_alive": "30m",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": 0.2, "num_predict": max_tokens},
        }
        data = await self._post(f"{self._base}/api/chat", body, {})
        try:
            return _text_or_fail(data["message"]["content"])
        except (KeyError, TypeError):
            raise LlmUnavailable("unexpected reply") from None


class OpenAICompatClient(_HttpProvider):
    """Any service with the OpenAI chat-completions shape, for a provider chosen later."""

    name = "openai_compat"

    def __init__(
        self, http: httpx.AsyncClient, model: str, base_url: str, api_key: str, timeout: float
    ) -> None:
        super().__init__(http, model, timeout)
        self._base = base_url.rstrip("/")
        self._key = api_key

    async def _complete(self, system: str, user: str, max_tokens: int) -> str:
        body = {
            "model": self._model,
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        headers = {"Authorization": f"Bearer {self._key}"} if self._key else {}
        data = await self._post(f"{self._base}/chat/completions", body, headers)
        try:
            return _text_or_fail(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError):
            raise LlmUnavailable("unexpected reply") from None


class ProviderChain:
    """Tries each provider in order, so a hosted model's outage falls through to the next one.

    Only `LlmUnavailable` moves on to the next provider. Whatever the last one says goes, and if all
    of them fail, the caller gets `LlmUnavailable` and uses the template, as with no provider at all.
    """

    def __init__(self, providers: list[LlmClient]) -> None:
        self._providers = providers
        self.name = ",".join(provider.name for provider in providers)

    async def draft(self, request: LlmRequest, passages: list[str], language: str) -> str:
        for provider in self._providers:
            try:
                return await provider.draft(request, passages, language)
            except LlmUnavailable:
                continue
        raise LlmUnavailable("every provider failed")

    async def classify(self, question: str, language: str) -> Boundary:
        for provider in self._providers:
            try:
                return await provider.classify(question, language)
            except LlmUnavailable:
                continue
        raise LlmUnavailable("every provider failed")


def _one(name: str, settings: Settings, http: httpx.AsyncClient) -> LlmClient:
    timeout = settings.llm_timeout_seconds
    if name == "template":
        return TemplateOnly()
    if name == "gemini":
        if settings.gemini_api_key is None:
            raise ValueError("LLM_PROVIDER gemini needs GEMINI_API_KEY")
        return GeminiClient(
            http, settings.gemini_model, settings.gemini_api_key.get_secret_value(), timeout
        )
    if name == "ollama":
        return OllamaClient(http, settings.ollama_model, str(settings.ollama_url), timeout)
    if settings.openai_compat_url is None or not settings.openai_compat_model:
        raise ValueError(
            "LLM_PROVIDER openai_compat needs OPENAI_COMPAT_URL and OPENAI_COMPAT_MODEL"
        )
    key = (
        settings.openai_compat_api_key.get_secret_value() if settings.openai_compat_api_key else ""
    )
    return OpenAICompatClient(
        http, settings.openai_compat_model, str(settings.openai_compat_url), key, timeout
    )


def build_llm(settings: Settings, http: httpx.AsyncClient) -> LlmClient:
    """The configured providers, in order.

    In a list, a provider missing its settings (say, no Gemini key on this machine) is skipped with a
    warning, so the next one serves. If every model provider asked for is missing its settings, that
    is a startup error rather than a silent switch to templates.
    """
    working: list[LlmClient] = []
    problems: list[ValueError] = []
    for name in settings.llm_provider:
        if name == "template":
            continue
        try:
            working.append(_one(name, settings, http))
        except ValueError as missing:
            problems.append(missing)
    if problems and not working:
        raise problems[0]
    for problem in problems:
        log.warning("llm_provider_skipped", extra={"ctx": {"reason": str(problem)}})
    if not working:
        return TemplateOnly()
    return working[0] if len(working) == 1 else ProviderChain(working)
