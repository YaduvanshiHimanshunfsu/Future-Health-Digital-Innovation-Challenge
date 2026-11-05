import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any

import httpx
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.algorithms import RSAAlgorithm

from app.core.config import Settings
from app.core.errors import ApiError

log = logging.getLogger("samvid.auth")

ALGORITHM = "RS256"
MAX_TOKEN_CHARS = 8192
KNOWN_ROLES = frozenset(
    {"individual", "counsellor", "physician", "program_admin", "auditor", "lab_service"}
)
_REQUIRED_CLAIMS = ["exp", "iat", "sub", "iss", "aud"]

_bearer = HTTPBearer(auto_error=False)


def _unauthenticated() -> ApiError:
    return ApiError(
        HTTPStatus.UNAUTHORIZED, "unauthenticated", headers={"WWW-Authenticate": "Bearer"}
    )


@dataclass(frozen=True, slots=True)
class Principal:
    sub: str
    roles: frozenset[str]
    token_id: str | None = None
    # Only ever read from a verified token. Left out of repr so it can't reach a log by accident.
    national_id: str | None = field(default=None, repr=False)


class JwksUnavailable(Exception):
    """The signing keys can't be fetched, so tokens can't be judged either way."""


class JwksCache:
    """Signing keys from the identity provider, cached and refreshed under a cooldown.

    A token carrying an unknown `kid` triggers a refresh, which is how key rotation is picked up.
    The cooldown stops anyone turning that into a way of hammering the identity provider by
    sending tokens with random `kid` values.
    """

    def __init__(
        self,
        url: str,
        *,
        ttl_seconds: int,
        cooldown_seconds: int,
        max_stale_seconds: int = 3600,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._url = url
        self._ttl = ttl_seconds
        self._max_stale = max_stale_seconds
        self._cooldown = cooldown_seconds
        self._transport = transport
        self._keys: dict[str, Any] = {}
        self._fetched_at = float("-inf")
        self._attempted_at = float("-inf")
        self._lock = asyncio.Lock()

    async def get(self, kid: str) -> Any | None:
        age = time.monotonic() - self._fetched_at
        if self._keys and age > self._max_stale:
            # A key revoked during a long outage must not stay trusted just because nothing could
            # tell us it was revoked. Past this point, refuse rather than keep guessing.
            self._keys = {}
        if kid not in self._keys or age > self._ttl:
            await self._refresh()
        return self._keys.get(kid)

    async def _refresh(self) -> None:
        async with self._lock:
            now = time.monotonic()
            if now - self._attempted_at < self._cooldown:
                if not self._keys:
                    raise JwksUnavailable
                return
            self._attempted_at = now
            try:
                async with httpx.AsyncClient(timeout=5.0, transport=self._transport) as client:
                    response = await client.get(self._url)
                    response.raise_for_status()
                self._keys = self._parse(response.json())
                self._fetched_at = now
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                log.warning("jwks_refresh_failed", extra={"ctx": {"error": type(exc).__name__}})
                # Keys already held keep working through a short identity provider outage.
                if not self._keys:
                    raise JwksUnavailable from exc

    @staticmethod
    def _parse(document: dict[str, Any]) -> dict[str, Any]:
        keys: dict[str, Any] = {}
        for entry in document["keys"]:
            if entry.get("kty") == "RSA" and entry.get("use", "sig") == "sig" and "kid" in entry:
                keys[entry["kid"]] = RSAAlgorithm.from_jwk(json.dumps(entry))
        if not keys:
            raise ValueError("no usable signing keys")
        return keys


class TokenVerifier:
    def __init__(self, settings: Settings, keys: JwksCache) -> None:
        self._issuer = settings.issuer
        self._audience = settings.oidc_audience
        self._leeway = settings.jwt_leeway_seconds
        self._keys = keys

    async def verify(self, token: str) -> Principal:
        if len(token) > MAX_TOKEN_CHARS:
            raise _unauthenticated()
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError:
            raise _unauthenticated() from None

        # Checked before any key lookup, so a forged header can't reach the key cache.
        kid = header.get("kid")
        if header.get("alg") != ALGORITHM or not isinstance(kid, str) or len(kid) > 128:
            raise _unauthenticated()

        try:
            key = await self._keys.get(kid)
        except JwksUnavailable:
            raise ApiError(HTTPStatus.SERVICE_UNAVAILABLE, "auth_unavailable") from None
        if key is None:
            raise _unauthenticated()

        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=[ALGORITHM],
                audience=self._audience,
                issuer=self._issuer,
                leeway=self._leeway,
                options={"require": _REQUIRED_CLAIMS},
            )
        except jwt.PyJWTError:
            # The reason stays out of the response so it can't guide someone forging tokens.
            raise _unauthenticated() from None

        # Keycloak signs ID and refresh tokens with the same key. Only access tokens are accepted.
        if claims.get("typ", "Bearer") != "Bearer":
            raise _unauthenticated()
        subject = claims["sub"]
        if not isinstance(subject, str) or not subject:
            raise _unauthenticated()

        realm_access = claims.get("realm_access")
        raw_roles = realm_access.get("roles", []) if isinstance(realm_access, dict) else []
        roles = frozenset(role for role in raw_roles if role in KNOWN_ROLES)
        national_id = claims.get("national_id")
        return Principal(
            sub=subject,
            roles=roles,
            token_id=claims.get("jti"),
            national_id=national_id if isinstance(national_id, str) and national_id else None,
        )


async def get_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthenticated()
    verifier: TokenVerifier = request.app.state.token_verifier
    principal = await verifier.verify(credentials.credentials)
    request.state.principal = principal
    return principal


def require_role(*allowed: str) -> Callable[..., Awaitable[Principal]]:
    unknown = set(allowed) - KNOWN_ROLES
    if unknown:
        raise ValueError(f"unknown roles: {sorted(unknown)}")
    allowed_roles = frozenset(allowed)

    async def dependency(
        request: Request, principal: Principal = Depends(get_principal)
    ) -> Principal:
        if not principal.roles & allowed_roles:
            route = getattr(request.scope.get("route"), "path", "unmatched")
            await request.app.state.audit.record_independently(
                actor=principal.sub,
                action="access.denied",
                resource=f"route:{route}"[:128],
                outcome="denied",
            )
            raise ApiError(HTTPStatus.FORBIDDEN, "forbidden")
        return principal

    return dependency
