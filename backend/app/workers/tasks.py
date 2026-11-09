import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.db.session import build_engine, build_session_factory
from app.privacy import outbox
from app.privacy.authz import Authz
from app.workers.celery_app import celery_app


@celery_app.task(name="samvid.ping")  # type: ignore[untyped-decorator]
def ping() -> str:
    return "pong"


async def _with_authz(
    job: Callable[[async_sessionmaker[AsyncSession], Authz], Awaitable[Any]],
) -> None:
    # Each task gets its own event loop, so connections can't be shared between tasks.
    settings = get_settings()
    engine = build_engine(settings.database_url.get_secret_value())
    authz = Authz.from_settings(settings)
    try:
        await job(build_session_factory(engine), authz)
    finally:
        await authz.aclose()
        await engine.dispose()


@celery_app.task(name="samvid.apply_authz_outbox")  # type: ignore[untyped-decorator]
def apply_authz_outbox() -> None:
    asyncio.run(_with_authz(outbox.drain))


@celery_app.task(name="samvid.reconcile_authz")  # type: ignore[untyped-decorator]
def reconcile_authz() -> None:
    asyncio.run(_with_authz(outbox.reconcile))


async def _scan_pathway() -> None:
    from app.core.config import decode_key
    from app.country_packs.loader import load_registry
    from app.notifications.service import MockNotifier
    from app.pathway.scheduler import scan

    settings = get_settings()
    engine = build_engine(settings.database_url.get_secret_value())
    packs = load_registry(
        settings.packs_dir,
        settings.enabled_packs,
        settings.default_pack,
        production=settings.is_production,
    )
    try:
        await scan(
            build_session_factory(engine),
            packs,
            # The prototype sends no real messages: the mock records what would have gone out.
            MockNotifier(),
            decode_key(settings.analytics_hmac_key, "ANALYTICS_HMAC_KEY"),
        )
    finally:
        await engine.dispose()


@celery_app.task(name="samvid.scan_pathway")  # type: ignore[untyped-decorator]
def scan_pathway() -> None:
    asyncio.run(_scan_pathway())
