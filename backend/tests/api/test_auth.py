import asyncio
import base64
import hashlib
import hmac
import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx
import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from fastapi import APIRouter, Depends

from app.core.security import (
    JwksCache,
    JwksUnavailable,
    Principal,
    get_principal,
    require_role,
)
from tests.conftest import IdentityProvider, client_for

router = APIRouter()


@router.get("/test/whoami")
async def whoami(principal: Principal = Depends(get_principal)) -> dict[str, Any]:
    return {"sub": principal.sub, "roles": sorted(principal.roles)}


@router.get("/test/counsellors-only")
async def counsellors_only(
    principal: Principal = Depends(require_role("counsellor")),
) -> dict[str, str]:
    return {"sub": principal.sub}


@pytest_asyncio.fixture
async def client(app_factory: Any) -> AsyncIterator[httpx.AsyncClient]:
    app = app_factory()
    app.include_router(router)
    async with client_for(app) as http:
        yield http


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def unsigned_token(claims: dict[str, Any], kid: str) -> str:
    def encode(part: dict[str, Any]) -> str:
        return base64.urlsafe_b64encode(json.dumps(part).encode()).rstrip(b"=").decode()

    return f"{encode({'alg': 'none', 'kid': kid})}.{encode(claims)}."


async def test_valid_token_is_accepted(client: httpx.AsyncClient, idp: IdentityProvider) -> None:
    response = await client.get("/test/whoami", headers=bearer(idp.token()))
    assert response.status_code == 200
    assert response.json() == {"sub": "person-1", "roles": ["individual"]}


async def test_missing_token_gets_401(client: httpx.AsyncClient) -> None:
    response = await client.get("/test/whoami")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_other_auth_scheme_gets_401(client: httpx.AsyncClient, idp: IdentityProvider) -> None:
    response = await client.get("/test/whoami", headers={"Authorization": f"Basic {idp.token()}"})
    assert response.status_code == 401


async def test_expired_token_gets_401(client: httpx.AsyncClient, idp: IdentityProvider) -> None:
    token = idp.token(exp=int(time.time()) - 3600, iat=int(time.time()) - 7200)
    assert (await client.get("/test/whoami", headers=bearer(token))).status_code == 401


async def test_tampered_payload_gets_401(client: httpx.AsyncClient, idp: IdentityProvider) -> None:
    header, payload, signature = idp.token().split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["realm_access"]["roles"] = ["program_admin"]
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    token = f"{header}.{forged}.{signature}"
    assert (await client.get("/test/whoami", headers=bearer(token))).status_code == 401


async def test_alg_none_gets_401(client: httpx.AsyncClient, idp: IdentityProvider) -> None:
    await client.get("/test/whoami", headers=bearer(idp.token()))  # key is now cached
    token = unsigned_token(idp.claims(), idp.kid)
    assert (await client.get("/test/whoami", headers=bearer(token))).status_code == 401


async def test_public_key_used_as_hmac_secret_gets_401(
    client: httpx.AsyncClient, idp: IdentityProvider
) -> None:
    """The classic RS256-to-HS256 confusion: signing with the public key, which anyone can get."""
    public_pem = idp.private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "kid": idp.kid, "typ": "JWT"}).encode()
    ).rstrip(b"=")
    payload = base64.urlsafe_b64encode(json.dumps(idp.claims()).encode()).rstrip(b"=")
    signature = base64.urlsafe_b64encode(
        hmac.new(public_pem, header + b"." + payload, hashlib.sha256).digest()
    ).rstrip(b"=")
    token = (header + b"." + payload + b"." + signature).decode()
    assert (await client.get("/test/whoami", headers=bearer(token))).status_code == 401


async def test_wrong_audience_gets_401(client: httpx.AsyncClient, idp: IdentityProvider) -> None:
    token = idp.token(aud="some-other-service")
    assert (await client.get("/test/whoami", headers=bearer(token))).status_code == 401


async def test_wrong_issuer_gets_401(client: httpx.AsyncClient, idp: IdentityProvider) -> None:
    token = idp.token(iss="http://evil.test/realms/samvid")
    assert (await client.get("/test/whoami", headers=bearer(token))).status_code == 401


@pytest.mark.parametrize("claim", ["exp", "iat", "sub", "iss", "aud"])
async def test_missing_required_claim_gets_401(
    client: httpx.AsyncClient, idp: IdentityProvider, claim: str
) -> None:
    token = idp.token(**{claim: ...})
    assert (await client.get("/test/whoami", headers=bearer(token))).status_code == 401


async def test_id_token_is_not_an_access_token(
    client: httpx.AsyncClient, idp: IdentityProvider
) -> None:
    token = idp.token(typ="ID")
    assert (await client.get("/test/whoami", headers=bearer(token))).status_code == 401


async def test_token_without_kid_gets_401(client: httpx.AsyncClient, idp: IdentityProvider) -> None:
    token = jwt.encode(idp.claims(), idp.private_key, algorithm="RS256")
    assert (await client.get("/test/whoami", headers=bearer(token))).status_code == 401


async def test_garbage_and_oversized_tokens_get_401(client: httpx.AsyncClient) -> None:
    assert (await client.get("/test/whoami", headers=bearer("not.a.jwt"))).status_code == 401
    assert (await client.get("/test/whoami", headers=bearer("a" * 9000))).status_code == 401


async def test_failure_reason_is_not_revealed(
    client: httpx.AsyncClient, idp: IdentityProvider
) -> None:
    expired = idp.token(exp=int(time.time()) - 3600, iat=int(time.time()) - 7200)
    wrong_audience = idp.token(aud="other")
    first = await client.get("/test/whoami", headers=bearer(expired))
    second = await client.get("/test/whoami", headers=bearer(wrong_audience))
    assert first.json()["code"] == second.json()["code"] == "unauthenticated"
    assert first.json()["message"] == second.json()["message"]


async def test_identity_provider_outage_denies_with_503(
    client: httpx.AsyncClient, idp: IdentityProvider
) -> None:
    idp.available = False
    response = await client.get("/test/whoami", headers=bearer(idp.token()))
    assert response.status_code == 503
    assert response.json()["code"] == "auth_unavailable"


async def test_cached_keys_survive_an_outage(
    client: httpx.AsyncClient, idp: IdentityProvider
) -> None:
    assert (await client.get("/test/whoami", headers=bearer(idp.token()))).status_code == 200
    idp.available = False
    assert (await client.get("/test/whoami", headers=bearer(idp.token()))).status_code == 200


async def test_random_kids_cannot_hammer_the_identity_provider(
    client: httpx.AsyncClient, idp: IdentityProvider
) -> None:
    await client.get("/test/whoami", headers=bearer(idp.token()))
    before = idp.jwks_requests
    for number in range(20):
        token = idp.token(headers={"kid": f"made-up-{number}"})
        assert (await client.get("/test/whoami", headers=bearer(token))).status_code == 401
    assert idp.jwks_requests == before


async def test_key_rotation_is_picked_up(app_factory: Any, idp: IdentityProvider) -> None:
    app = app_factory(jwks_refresh_cooldown_seconds=1)
    app.include_router(router)
    async with client_for(app) as http:
        assert (await http.get("/test/whoami", headers=bearer(idp.token()))).status_code == 200
        idp.rotate("test-key-2")
        await asyncio.sleep(1.1)
        assert (await http.get("/test/whoami", headers=bearer(idp.token()))).status_code == 200


async def test_unknown_roles_in_a_token_are_dropped(
    client: httpx.AsyncClient, idp: IdentityProvider
) -> None:
    token = idp.token(realm_access={"roles": ["individual", "default-roles-samvid", "superuser"]})
    response = await client.get("/test/whoami", headers=bearer(token))
    assert response.json()["roles"] == ["individual"]


async def test_malformed_roles_claim_gives_no_roles(
    client: httpx.AsyncClient, idp: IdentityProvider
) -> None:
    token = idp.token(realm_access="counsellor")
    response = await client.get("/test/whoami", headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["roles"] == []


async def test_wrong_role_gets_403(client: httpx.AsyncClient, idp: IdentityProvider) -> None:
    response = await client.get("/test/counsellors-only", headers=bearer(idp.token()))
    assert response.status_code == 403


async def test_right_role_gets_through(client: httpx.AsyncClient, idp: IdentityProvider) -> None:
    token = idp.token(realm_access={"roles": ["counsellor"]})
    response = await client.get("/test/counsellors-only", headers=bearer(token))
    assert response.status_code == 200


def test_guarding_a_route_with_a_misspelt_role_fails_at_startup() -> None:
    with pytest.raises(ValueError, match="unknown roles"):
        require_role("counselor")


async def test_keys_stop_being_trusted_after_too_long_without_a_refresh(
    idp: IdentityProvider,
) -> None:
    keys = JwksCache(
        "http://idp.test/certs",
        ttl_seconds=0,
        cooldown_seconds=0,
        max_stale_seconds=0,
        transport=idp.transport,
    )
    assert await keys.get(idp.kid) is not None
    idp.available = False
    await asyncio.sleep(0.01)
    with pytest.raises(JwksUnavailable):
        await keys.get(idp.kid)
