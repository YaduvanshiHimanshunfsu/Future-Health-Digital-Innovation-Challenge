import base64
import json
import os
import secrets
import subprocess
import sys
import time
from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path
from typing import Any

import httpx
import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from jwt.algorithms import RSAAlgorithm
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.redis import RedisContainer
from testcontainers.core.container import DockerContainer

from app.core.config import Settings
from app.core.logging import clear_scrub_patterns
from app.db.base import Base
from app.main import create_app
from app.privacy.audit import AuditTrail

BACKEND_DIR = Path(__file__).resolve().parent.parent
INIT_SQL = BACKEND_DIR.parent / "infra" / "postgres" / "init.sql"

ISSUER = "http://idp.test/realms/samvid"
AUDIENCE = "samvid-api"
JWKS_URL = "http://idp.test/realms/samvid/protocol/openid-connect/certs"
SIGNING_KID = "test-key-1"
OWNER_PASSWORD = secrets.token_urlsafe(16)
APP_PASSWORD = secrets.token_urlsafe(16)


def random_key() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()


def settings_for_tests(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "env": "test",
        # Port 1 refuses instantly, so a test that doesn't declare a database can't reach one.
        "database_url": "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/none",
        "redis_url": "redis://127.0.0.1:1/0",
        "allowed_hosts": ["testserver", "localhost"],
        "oidc_issuer": ISSUER,
        "oidc_audience": AUDIENCE,
        "oidc_jwks_url": JWKS_URL,
        "kms_provider": "local",
        "local_kek_b64": random_key(),
        "audit_hmac_key": random_key(),
        "invite_hmac_key": random_key(),
        "national_id_hmac_key": random_key(),
        "analytics_hmac_key": random_key(),
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


class IdentityProvider:
    """A stand-in for Keycloak: real RSA keys, a real JWKS response, and a request count."""

    def __init__(self) -> None:
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.kid = SIGNING_KID
        self.jwks_requests = 0
        self.available = True

    def rotate(self, kid: str) -> None:
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.kid = kid

    def _handler(self, request: httpx.Request) -> httpx.Response:
        self.jwks_requests += 1
        if not self.available:
            return httpx.Response(503)
        jwk = json.loads(RSAAlgorithm.to_jwk(self.private_key.public_key()))
        jwk.update({"kid": self.kid, "use": "sig", "alg": "RS256"})
        return httpx.Response(200, json={"keys": [jwk]})

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handler)

    def claims(self, **overrides: Any) -> dict[str, Any]:
        now = int(time.time())
        base: dict[str, Any] = {
            "sub": "person-1",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + 300,
            "typ": "Bearer",
            "jti": secrets.token_hex(8),
            "realm_access": {"roles": ["individual"]},
        }
        base.update(overrides)
        return {key: value for key, value in base.items() if value is not ...}

    def token(self, *, headers: dict[str, Any] | None = None, **overrides: Any) -> str:
        return jwt.encode(
            self.claims(**overrides),
            self.private_key,
            algorithm="RS256",
            headers={"kid": self.kid, **(headers or {})},
        )


@pytest.fixture
def idp() -> IdentityProvider:
    return IdentityProvider()


@pytest.fixture(autouse=True)
def _reset_scrub_patterns() -> Iterator[None]:
    yield
    clear_scrub_patterns()


@pytest.fixture
def app_factory(idp: IdentityProvider) -> Callable[..., FastAPI]:
    def build(**overrides: Any) -> FastAPI:
        return create_app(settings_for_tests(**overrides), jwks_transport=idp.transport)

    return build


def client_for(app: FastAPI, *, raise_app_exceptions: bool = False) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=raise_app_exceptions),
        base_url="http://testserver",
    )


def _alembic(database_url: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env={**os.environ, "MIGRATION_DATABASE_URL": database_url},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


OPENFGA_TOKEN = "test-openfga-key"


@pytest.fixture(scope="session")
def openfga_url() -> Iterator[str]:
    """A real OpenFGA, because conditions and tuple rules are the part a mock would get wrong."""
    container = (
        DockerContainer("openfga/openfga:v1.8.4")
        .with_command("run")
        .with_exposed_ports(8080)
        .with_env("OPENFGA_AUTHN_METHOD", "preshared")
        .with_env("OPENFGA_AUTHN_PRESHARED_KEYS", OPENFGA_TOKEN)
    )
    with container:
        url = f"http://{container.get_container_host_ip()}:{container.get_exposed_port(8080)}"
        deadline = time.monotonic() + 60
        while True:
            try:
                if httpx.get(f"{url}/healthz", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if time.monotonic() > deadline:
                raise RuntimeError("OpenFGA didn't start")
            time.sleep(0.25)
        yield url


@pytest.fixture(scope="session")
def redis_url() -> Iterator[str]:
    with RedisContainer("redis:7-alpine") as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(6379)
        yield f"redis://{host}:{port}/0"


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    container = PostgresContainer(
        "pgvector/pgvector:pg16",
        username="postgres",
        password=secrets.token_urlsafe(16),
        dbname="postgres",
    ).with_volume_mapping(str(INIT_SQL), "/seed/init.sql", "ro")
    with container as running:
        # The same bootstrap script the real stack uses, so tests exercise the real roles.
        result = running.get_wrapped_container().exec_run(
            [
                "psql",
                "-U",
                "postgres",
                "-v",
                f"owner_password={OWNER_PASSWORD}",
                "-v",
                f"app_password={APP_PASSWORD}",
                "-v",
                "openfga_password=unused",
                "-f",
                "/seed/init.sql",
            ]
        )
        assert result.exit_code == 0, result.output.decode()
        yield running


def _url(container: PostgresContainer, role: str, password: str) -> str:
    host = container.get_container_host_ip()
    port = container.get_exposed_port(5432)
    return f"postgresql+asyncpg://{role}:{password}@{host}:{port}/samvid"


@pytest.fixture(scope="session")
def owner_url(postgres: PostgresContainer) -> str:
    return _url(postgres, "samvid_owner", OWNER_PASSWORD)


@pytest.fixture(scope="session")
def app_url(postgres: PostgresContainer) -> str:
    return _url(postgres, "samvid_app", APP_PASSWORD)


@pytest.fixture(scope="session")
def migrated(owner_url: str) -> str:
    result = _alembic(owner_url, "upgrade", "head")
    assert result.returncode == 0, result.stdout + result.stderr
    return owner_url


@pytest.fixture(scope="session")
def alembic_runner(owner_url: str) -> Callable[..., subprocess.CompletedProcess[str]]:
    return lambda *args: _alembic(owner_url, *args)


@pytest_asyncio.fixture(scope="session")
async def owner_engine(migrated: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(migrated)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def app_engine(app_url: str, migrated: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(app_url, pool_size=25)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def clean_db(owner_engine: AsyncEngine) -> AsyncIterator[None]:
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    async with owner_engine.begin() as connection:
        await connection.execute(text("ALTER TABLE audit_log DISABLE TRIGGER USER"))
        await connection.execute(text(f"TRUNCATE {tables}"))
        await connection.execute(text("ALTER TABLE audit_log ENABLE TRIGGER USER"))
    yield


@pytest.fixture
def session_factory(app_engine: AsyncEngine, clean_db: None) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(app_engine, expire_on_commit=False, autoflush=False)


@pytest.fixture
def audit_key() -> bytes:
    return secrets.token_bytes(32)


@pytest.fixture
def audit(audit_key: bytes, session_factory: async_sessionmaker[AsyncSession]) -> AuditTrail:
    return AuditTrail(audit_key, session_factory)
