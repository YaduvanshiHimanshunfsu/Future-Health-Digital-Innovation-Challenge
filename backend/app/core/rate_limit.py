import logging
import time
from collections.abc import Awaitable, Callable
from http import HTTPStatus

from fastapi import Depends, Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.errors import ApiError
from app.core.security import Principal, get_principal

log = logging.getLogger("samvid.rate_limit")

# INCR and EXPIRE must be one step. If a crash fell between them, the counter would have no expiry
# and the person would stay locked out for good.
_INCREMENT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return count
"""


async def enforce(redis: Redis, key: str, limit: int, window_seconds: int) -> None:
    window = int(time.time() // window_seconds)
    bucket = f"rl:{key}:{window}"
    try:
        count = await redis.eval(_INCREMENT, 1, bucket, str(window_seconds))  # type: ignore[misc]
    except RedisError as exc:
        # These limits guard sensitive flows like invitations and matching, so an outage closes
        # them instead of letting traffic through unmetered.
        log.warning("rate_limit_unavailable", extra={"ctx": {"error": type(exc).__name__}})
        raise ApiError(HTTPStatus.SERVICE_UNAVAILABLE, "rate_limiter_unavailable") from None
    if int(count) > limit:
        retry_after = window_seconds - int(time.time() % window_seconds)
        raise ApiError(
            HTTPStatus.TOO_MANY_REQUESTS, "rate_limited", headers={"Retry-After": str(retry_after)}
        )


def rate_limit(action: str, limit: int, window_seconds: int) -> Callable[..., Awaitable[None]]:
    async def dependency(request: Request, principal: Principal = Depends(get_principal)) -> None:
        redis: Redis = request.app.state.redis
        await enforce(redis, f"{action}:{principal.sub}", limit, window_seconds)

    return dependency
