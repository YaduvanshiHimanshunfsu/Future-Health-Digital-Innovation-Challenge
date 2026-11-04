"""Operator check: can this container reach everything it depends on?

Run inside the api container. Unlike /v1/ready, this names each dependency, so it's a command and
never an endpoint. With LAB_CLIENT_ID and LAB_CLIENT_SECRET set, it also fetches a real token and
verifies it the way the API would, which proves the issuer and audience settings agree end to end.
"""

import asyncio
import json
import os
import sys
from collections.abc import Awaitable, Callable

import httpx
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.core.security import JwksCache, TokenVerifier
from app.db.session import build_engine


async def _postgres(settings: Settings) -> str:
    engine = build_engine(settings.database_url.get_secret_value())
    try:
        async with engine.connect() as connection:
            version = await connection.scalar(text("SHOW server_version"))
            tables = await connection.scalar(
                text("SELECT count(*) FROM pg_tables WHERE schemaname = 'public'")
            )
    finally:
        await engine.dispose()
    return f"postgres {version}, {tables} tables"


async def _redis(settings: Settings) -> str:
    client = Redis.from_url(settings.redis_url.get_secret_value(), socket_timeout=2.0)
    try:
        await client.ping()
    finally:
        await client.aclose()
    return "pong"


async def _keycloak(settings: Settings) -> str:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(str(settings.oidc_jwks_url))
        response.raise_for_status()
    return f"{len(response.json()['keys'])} signing keys"


async def _openfga(settings: Settings) -> str:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{settings.openfga_api_url.rstrip('/')}/healthz")
        response.raise_for_status()
    return str(response.json().get("status", "ok"))


async def _token_round_trip(settings: Settings) -> str:
    client_id = os.environ["LAB_CLIENT_ID"]
    token_url = str(settings.oidc_jwks_url).replace("/certs", "/token")
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": os.environ["LAB_CLIENT_SECRET"],
            },
        )
        response.raise_for_status()
    verifier = TokenVerifier(
        settings,
        JwksCache(
            str(settings.oidc_jwks_url),
            ttl_seconds=settings.jwks_ttl_seconds,
            cooldown_seconds=settings.jwks_refresh_cooldown_seconds,
        ),
    )
    principal = await verifier.verify(response.json()["access_token"])
    return f"verified, roles={sorted(principal.roles)}"


async def main() -> int:
    settings = get_settings()
    checks: dict[str, Callable[[Settings], Awaitable[str]]] = {
        "postgres": _postgres,
        "redis": _redis,
        "keycloak": _keycloak,
        "openfga": _openfga,
    }
    if os.environ.get("LAB_CLIENT_SECRET"):
        checks["token_round_trip"] = _token_round_trip

    results: dict[str, str] = {}
    failed = False
    for name, check in checks.items():
        try:
            results[name] = await check(settings)
        except Exception as exc:  # noqa: BLE001 - every failure is reported, and the type is enough
            results[name] = f"FAILED: {type(exc).__name__}"
            failed = True
    print(json.dumps(results, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
