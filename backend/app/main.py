from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from redis.asyncio import Redis
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import api_v1
from app.core.config import Settings, decode_key, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import (
    BodySizeLimitMiddleware,
    ErrorBoundaryMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.security import JwksCache, TokenVerifier
from app.country_packs.loader import load_registry
from app.db.session import build_engine, build_session_factory
from app.explain.providers import build_llm
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz
from app.privacy.crypto import FieldCipher
from app.privacy.kms import build_kek


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await app.state.redis.aclose()
    await app.state.authz.aclose()
    await app.state.llm_http.aclose()
    await app.state.engine.dispose()


def create_app(
    settings: Settings | None = None,
    *,
    jwks_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    docs_enabled = not settings.is_production
    app = FastAPI(
        title="Samvid API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    # Nothing here connects until first use, so the app can be built without its dependencies up.
    app.state.settings = settings
    app.state.engine = build_engine(settings.database_url.get_secret_value())
    app.state.session_factory = build_session_factory(app.state.engine)
    app.state.redis = Redis.from_url(
        settings.redis_url.get_secret_value(), decode_responses=True, socket_timeout=2.0
    )
    app.state.token_verifier = TokenVerifier(
        settings,
        JwksCache(
            str(settings.oidc_jwks_url),
            ttl_seconds=settings.jwks_ttl_seconds,
            cooldown_seconds=settings.jwks_refresh_cooldown_seconds,
            transport=jwks_transport,
        ),
    )
    app.state.audit = AuditTrail(
        decode_key(settings.audit_hmac_key, "AUDIT_HMAC_KEY"), app.state.session_factory
    )

    app.state.authz = Authz.from_settings(settings)
    # The configured model, or TemplateOnly. See app/explain/providers.py.
    app.state.llm_http = httpx.AsyncClient(follow_redirects=False)
    app.state.llm = build_llm(settings, app.state.llm_http)
    app.state.cipher = FieldCipher(build_kek(settings))
    app.state.packs = load_registry(
        settings.packs_dir,
        settings.enabled_packs,
        settings.default_pack,
        production=settings.is_production,
    )

    # add_middleware wraps what's already there, so the last one added runs first on a request.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        # Tokens travel as bearer headers through the frontend's server, never as cookies here.
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "Accept-Language"],
    )
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    app.add_middleware(ErrorBoundaryMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, docs_enabled=docs_enabled)

    register_error_handlers(app)
    app.include_router(api_v1, prefix="/v1")
    return app
