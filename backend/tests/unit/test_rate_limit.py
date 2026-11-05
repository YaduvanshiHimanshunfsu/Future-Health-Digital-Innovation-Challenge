import pytest
from redis.asyncio import Redis

from app.core.errors import ApiError
from app.core.rate_limit import enforce


@pytest.mark.db
async def test_requests_over_the_limit_are_refused(redis_url: str) -> None:
    client = Redis.from_url(redis_url, decode_responses=True)
    for _ in range(3):
        await enforce(client, "action:over-limit", limit=3, window_seconds=60)
    with pytest.raises(ApiError) as caught:
        await enforce(client, "action:over-limit", limit=3, window_seconds=60)
    assert caught.value.status == 429
    assert caught.value.headers is not None
    assert 0 < int(caught.value.headers["Retry-After"]) <= 60
    await client.aclose()


@pytest.mark.db
async def test_limits_are_per_key(redis_url: str) -> None:
    client = Redis.from_url(redis_url, decode_responses=True)
    await enforce(client, "action:person-a", limit=1, window_seconds=60)
    await enforce(client, "action:person-b", limit=1, window_seconds=60)
    await client.aclose()


@pytest.mark.db
async def test_every_counter_gets_an_expiry(redis_url: str) -> None:
    """A counter with no expiry would lock someone out for good."""
    client = Redis.from_url(redis_url, decode_responses=True)
    await enforce(client, "action:expiry", limit=5, window_seconds=60)
    keys = await client.keys("rl:action:expiry:*")
    assert len(keys) == 1
    assert 0 < await client.ttl(keys[0]) <= 60
    await client.aclose()


async def test_redis_outage_closes_the_limit() -> None:
    client = Redis.from_url("redis://127.0.0.1:1/0", socket_connect_timeout=0.2)
    with pytest.raises(ApiError) as caught:
        await enforce(client, "action:outage", limit=5, window_seconds=60)
    assert caught.value.status == 503
    await client.aclose()
