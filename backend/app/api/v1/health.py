import asyncio
import logging
from http import HTTPStatus

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_redis
from app.core.errors import ApiError

log = logging.getLogger("samvid.health")
router = APIRouter(tags=["health"])

READINESS_TIMEOUT_SECONDS = 2.0


@router.get("/health")
async def health() -> dict[str, str]:
    """Is the process alive. Says nothing about versions, hosts or dependencies."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict[str, str]:
    """Can this instance take traffic. Which dependency failed goes to the logs, not the caller."""
    try:
        async with asyncio.timeout(READINESS_TIMEOUT_SECONDS):
            await db.execute(text("SELECT 1"))
            await redis.ping()
    except (SQLAlchemyError, RedisError, OSError, TimeoutError) as exc:
        log.warning("not_ready", extra={"ctx": {"error": type(exc).__name__}})
        raise ApiError(HTTPStatus.SERVICE_UNAVAILABLE, "not_ready") from None
    return {"status": "ready"}
