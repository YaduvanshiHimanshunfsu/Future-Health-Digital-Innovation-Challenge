import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import DEFAULT_PACKS_DIR, decode_key
from app.country_packs.loader import load_pack
from app.ops.bootstrap_openfga import bootstrap
from app.privacy.audit import AuditTrail
from synthetic.generate import load_personas
from tests.api.helpers import AD, Stack
from tests.conftest import OPENFGA_TOKEN, IdentityProvider, client_for


@pytest_asyncio.fixture
async def make_stack(
    app_factory: Any,
    app_url: str,
    redis_url: str,
    openfga_url: str,
    idp: IdentityProvider,
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[Callable[..., Awaitable[Stack]]]:
    clients = []
    apps = []

    async def build(**overrides: Any) -> Stack:
        # A store per app, which keeps one test's access from reaching another.
        store = f"test-{uuid.uuid4().hex}"
        await bootstrap(openfga_url, store, token=OPENFGA_TOKEN)
        app = app_factory(
            database_url=app_url,
            redis_url=redis_url,
            openfga_api_url=openfga_url,
            openfga_store_name=store,
            openfga_token=OPENFGA_TOKEN,
            **overrides,
        )
        apps.append(app)
        await app.state.redis.flushdb()
        http = client_for(app)
        clients.append(http)
        panel, people, _ = load_personas(AD)
        audit = AuditTrail(
            decode_key(app.state.settings.audit_hmac_key, "AUDIT_HMAC_KEY"), session_factory
        )
        app.state.audit = audit
        return Stack(
            app=app,
            http=http,
            idp=idp,
            factory=session_factory,
            audit=audit,
            cipher=app.state.cipher,
            pack=load_pack(DEFAULT_PACKS_DIR / AD),
            panel=panel,
            people=people,
        )

    yield build
    for http in clients:
        await http.aclose()
    for app in apps:
        await app.state.authz.aclose()
        await app.state.redis.aclose()


@pytest_asyncio.fixture
async def stack(make_stack: Callable[..., Awaitable[Stack]]) -> Stack:
    return await make_stack()
