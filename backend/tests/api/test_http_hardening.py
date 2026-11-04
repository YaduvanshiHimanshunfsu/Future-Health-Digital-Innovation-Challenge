import io
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest_asyncio
from fastapi import APIRouter, FastAPI
from pydantic import Field

from app.core.logging import PhiSafeJsonFormatter
from app.schemas.common import StrictIn
from tests.conftest import client_for

router = APIRouter()
SECRET_IN_EXCEPTION = "variant c.1234A>G for 784-1990-1234567-1"


class Note(StrictIn):
    text: str = Field(max_length=10)
    level: int


@router.post("/test/note")
async def note(body: Note) -> dict[str, str]:
    return {"text": body.text}


@router.get("/test/boom")
async def boom() -> None:
    raise RuntimeError(SECRET_IN_EXCEPTION)


REQUIRED_HEADERS = {
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "cache-control",
    "content-security-policy",
    "x-request-id",
    "permissions-policy",
}


def with_test_routes(app: FastAPI) -> FastAPI:
    app.include_router(router)
    return app


@pytest_asyncio.fixture
async def client(app_factory: Any) -> AsyncIterator[httpx.AsyncClient]:
    async with client_for(with_test_routes(app_factory(max_body_bytes=2048))) as http:
        yield http


def assert_hardened(response: httpx.Response) -> None:
    assert set(response.headers) >= REQUIRED_HEADERS, REQUIRED_HEADERS - set(response.headers)
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-frame-options"] == "DENY"
    assert "server" not in response.headers


async def test_headers_on_200(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/health")
    assert response.status_code == 200
    assert_hardened(response)


async def test_headers_on_404(client: httpx.AsyncClient) -> None:
    response = await client.get("/nothing/here")
    assert response.status_code == 404
    assert_hardened(response)


async def test_headers_on_422(client: httpx.AsyncClient) -> None:
    response = await client.post("/test/note", json={"text": "x"})
    assert response.status_code == 422
    assert_hardened(response)


async def test_headers_on_500(client: httpx.AsyncClient) -> None:
    response = await client.get("/test/boom")
    assert response.status_code == 500
    assert_hardened(response)


async def test_headers_on_rejected_host(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/health", headers={"Host": "evil.test"})
    assert response.status_code == 400
    assert_hardened(response)


async def test_headers_on_rejected_body(client: httpx.AsyncClient) -> None:
    response = await client.post("/test/note", content=b"x" * 4096)
    assert response.status_code == 413
    assert_hardened(response)


async def test_500_reveals_nothing_about_the_failure(client: httpx.AsyncClient) -> None:
    response = await client.get("/test/boom")
    assert response.json()["code"] == "internal_error"
    assert "c.1234" not in response.text
    assert "784" not in response.text
    assert "RuntimeError" not in response.text
    assert response.json()["request_id"] == response.headers["x-request-id"]


async def test_500_log_line_holds_the_type_and_not_the_message(
    client: httpx.AsyncClient,
) -> None:
    captured = io.StringIO()
    handler = logging.StreamHandler(captured)
    handler.setFormatter(PhiSafeJsonFormatter())
    logger = logging.getLogger("samvid.http")
    logger.addHandler(handler)
    try:
        await client.get("/test/boom")
    finally:
        logger.removeHandler(handler)
    output = captured.getvalue()
    assert "RuntimeError" in output
    assert "c.1234" not in output
    assert "784-1990" not in output


async def test_validation_error_does_not_echo_input(client: httpx.AsyncClient) -> None:
    sensitive = "my brother HBB"
    response = await client.post("/test/note", json={"text": sensitive, "level": "not a number"})
    assert response.status_code == 422
    assert sensitive not in response.text
    assert "not a number" not in response.text
    assert response.json()["errors"][0]["loc"] == ["body", "text"]
    assert all(set(error) == {"loc", "type"} for error in response.json()["errors"])


async def test_unknown_fields_are_refused(client: httpx.AsyncClient) -> None:
    response = await client.post("/test/note", json={"text": "ok", "level": 1, "role": "admin"})
    assert response.status_code == 422
    assert response.json()["errors"][0]["type"] == "extra_forbidden"


async def test_oversized_body_is_refused_by_declared_length(client: httpx.AsyncClient) -> None:
    response = await client.post("/test/note", content=b"x" * 4096)
    assert response.status_code == 413
    assert response.json()["code"] == "body_too_large"


async def test_oversized_chunked_body_is_refused_while_reading(client: httpx.AsyncClient) -> None:
    async def chunks() -> AsyncIterator[bytes]:
        for _ in range(8):
            yield b"x" * 1024

    response = await client.post(
        "/test/note", content=chunks(), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413
    assert response.json()["code"] == "body_too_large"


async def test_malformed_content_length_is_refused(client: httpx.AsyncClient) -> None:
    response = await client.post("/test/note", content=b"{}", headers={"Content-Length": "abc"})
    assert response.status_code == 400


async def test_docs_are_on_in_development(app_factory: Any) -> None:
    async with client_for(app_factory(env="dev")) as http:
        docs = await http.get("/docs")
        schema = await http.get("/openapi.json")
    assert docs.status_code == 200
    assert schema.status_code == 200
    # Swagger UI can't load under the strict policy, so /docs gets the one relaxed CSP.
    assert "cdn.jsdelivr.net" in docs.headers["content-security-policy"]


async def test_docs_csp_does_not_leak_to_other_routes(app_factory: Any) -> None:
    async with client_for(app_factory(env="dev")) as http:
        response = await http.get("/v1/health")
    assert "cdn.jsdelivr.net" not in response.headers["content-security-policy"]
    assert "default-src 'none'" in response.headers["content-security-policy"]


async def test_docs_are_off_in_production(app_factory: Any) -> None:
    app = app_factory(
        env="prod",
        kms_provider="vault",
        local_kek_b64=None,
        oidc_issuer="https://idp.example/realms/samvid",
        oidc_jwks_url="https://idp.example/realms/samvid/protocol/openid-connect/certs",
    )
    async with client_for(app) as http:
        assert (await http.get("/docs")).status_code == 404
        assert (await http.get("/openapi.json")).status_code == 404


async def test_errors_follow_the_requested_language(client: httpx.AsyncClient) -> None:
    english = await client.get("/nothing")
    hindi = await client.get("/nothing", headers={"Accept-Language": "hi-IN,hi;q=0.9,en;q=0.8"})
    assert english.json()["code"] == hindi.json()["code"]
    assert english.json()["message"] != hindi.json()["message"]


async def test_language_with_no_translation_falls_back_to_english(
    client: httpx.AsyncClient,
) -> None:
    english = await client.get("/nothing")
    arabic = await client.get("/nothing", headers={"Accept-Language": "ar"})
    assert arabic.json()["message"] == english.json()["message"]


async def test_liveness_says_nothing_about_internals(client: httpx.AsyncClient) -> None:
    assert (await client.get("/v1/health")).json() == {"status": "ok"}


async def test_readiness_fails_closed_without_naming_what_broke(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/ready")
    assert response.status_code == 503
    assert response.json()["code"] == "not_ready"
    assert "postgres" not in response.text.lower()
    assert "redis" not in response.text.lower()
