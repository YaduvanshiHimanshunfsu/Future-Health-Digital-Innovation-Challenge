import json
import logging
import secrets
import time

from fastapi import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import error_payload
from app.core.i18n import negotiate_language

log = logging.getLogger("samvid.http")

_STRICT_CSP = b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
# Swagger UI loads from a CDN and runs an inline bootstrap. Only ever applied to /docs outside
# production, where those routes exist at all.
_DOCS_CSP = (
    b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'; "
    b"script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    b"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    b"img-src 'self' data: https://fastapi.tiangolo.com; connect-src 'self'"
)
_SECURITY_HEADERS: dict[bytes, bytes] = {
    b"strict-transport-security": b"max-age=63072000; includeSubDomains",
    b"x-content-type-options": b"nosniff",
    b"x-frame-options": b"DENY",
    b"referrer-policy": b"no-referrer",
    b"cache-control": b"no-store",
    b"cross-origin-resource-policy": b"same-origin",
    b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
}
_DOCS_PATHS = frozenset({"/docs", "/docs/oauth2-redirect"})


def _header(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key == name:
            return str(value.decode("latin-1"))
    return None


async def _send_json(scope: Scope, send: Send, status: int, code: str) -> None:
    settings = scope["app"].state.settings
    language = negotiate_language(
        _header(scope, b"accept-language"),
        settings.supported_languages,
        settings.default_language,
    )
    request_id = scope.get("state", {}).get("request_id", "-")
    body = json.dumps(error_payload(status, code, language, request_id)).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


class SecurityHeadersMiddleware:
    """Outermost layer: every response leaves with a request ID and the security headers."""

    def __init__(self, app: ASGIApp, *, docs_enabled: bool) -> None:
        self.app = app
        self.docs_enabled = docs_enabled

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = secrets.token_hex(8)
        scope.setdefault("state", {})["request_id"] = request_id
        csp = _DOCS_CSP if self.docs_enabled and scope.get("path") in _DOCS_PATHS else _STRICT_CSP
        started = time.perf_counter()
        status_code = 500

        async def send_with_headers(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                kept = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() not in _SECURITY_HEADERS
                    and key.lower() not in {b"content-security-policy", b"server"}
                ]
                kept.extend(_SECURITY_HEADERS.items())
                kept.append((b"content-security-policy", csp))
                kept.append((b"x-request-id", request_id.encode()))
                message["headers"] = kept
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        finally:
            route = scope.get("route")
            log.info(
                "request",
                extra={
                    "ctx": {
                        "request_id": request_id,
                        "method": scope.get("method"),
                        # The route template, not the path: paths can carry IDs and tokens.
                        "route": getattr(route, "path", "unmatched"),
                        "status": status_code,
                        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                    }
                },
            )


class ErrorBoundaryMiddleware:
    """Turns an unhandled exception into a generic 500 inside the security-headers layer.

    An @app.exception_handler(Exception) runs in Starlette's ServerErrorMiddleware, which sits
    outside all user middleware, so its responses would miss the security headers.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, tracking_send)
        except Exception as exc:
            log.error(
                "unhandled_error",
                exc_info=exc,
                extra={"ctx": {"request_id": scope.get("state", {}).get("request_id", "-")}},
            )
            if response_started:
                # Too late to change the status. Dropping the connection beats a truncated success.
                raise
            await _send_json(scope, send, 500, "internal_error")


class _BodyTooLarge(HTTPException):
    """Raised while FastAPI reads the body. It turns anything but an HTTPException into a 400."""

    code = "body_too_large"

    def __init__(self) -> None:
        super().__init__(status_code=413)


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = _header(scope, b"content-length")
        if declared is not None:
            if not declared.isascii() or not declared.isdigit():
                await _send_json(scope, send, 400, "invalid_content_length")
                return
            if int(declared) > self.max_bytes:
                await _send_json(scope, send, 413, "body_too_large")
                return

        received = 0
        response_started = False

        # A chunked body has no Content-Length, and a client can also lie about it, so the bytes
        # that actually arrive are counted too.
        async def counting_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _BodyTooLarge
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, counting_receive, tracking_send)
        except _BodyTooLarge:
            if response_started:
                raise
            await _send_json(scope, send, 413, "body_too_large")
