from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.i18n import negotiate_language, translate

_MESSAGE_KEY_BY_STATUS = {
    HTTPStatus.BAD_REQUEST: "error.bad_request",
    HTTPStatus.UNAUTHORIZED: "error.unauthenticated",
    HTTPStatus.FORBIDDEN: "error.forbidden",
    HTTPStatus.NOT_FOUND: "error.not_found",
    HTTPStatus.METHOD_NOT_ALLOWED: "error.method_not_allowed",
    HTTPStatus.CONFLICT: "error.conflict",
    HTTPStatus.REQUEST_ENTITY_TOO_LARGE: "error.too_large",
    HTTPStatus.UNPROCESSABLE_ENTITY: "error.validation",
    HTTPStatus.TOO_MANY_REQUESTS: "error.rate_limited",
    HTTPStatus.INTERNAL_SERVER_ERROR: "error.internal",
    HTTPStatus.SERVICE_UNAVAILABLE: "error.unavailable",
}


@dataclass(slots=True)
class ApiError(Exception):
    """An error the client is meant to see: a status plus a stable, machine-readable code."""

    status: int
    code: str
    headers: dict[str, str] | None = None


def error_payload(status: int, code: str, language: str, request_id: str) -> dict[str, Any]:
    key = _MESSAGE_KEY_BY_STATUS.get(HTTPStatus(status), "error.internal")
    return {"code": code, "message": translate(key, language), "request_id": request_id}


def _request_context(request: Request) -> tuple[str, str]:
    settings = request.app.state.settings
    language = negotiate_language(
        request.headers.get("accept-language"),
        settings.supported_languages,
        settings.default_language,
    )
    return language, getattr(request.state, "request_id", "-")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        language, request_id = _request_context(request)
        return JSONResponse(
            status_code=exc.status,
            content=error_payload(exc.status, exc.code, language, request_id),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        language, request_id = _request_context(request)
        status = HTTPStatus.UNPROCESSABLE_ENTITY
        content = error_payload(status, "validation_failed", language, request_id)
        # Location and error type only. Pydantic's `input` and `ctx` can echo what the person sent,
        # and in this API that may be health data.
        content["errors"] = [
            {"loc": [str(part) for part in error["loc"]], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(status_code=status, content=content)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        language, request_id = _request_context(request)
        code = getattr(exc, "code", None) or HTTPStatus(exc.status_code).name.lower()
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.status_code, code, language, request_id),
            headers=exc.headers,
        )
