from collections.abc import AsyncIterator
from http import HTTPStatus

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.security import Principal, get_principal
from app.models.person import Person
from app.privacy.audit import AuditTrail


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """A session per request. Routes commit explicitly, and anything uncommitted is rolled back."""
    async with request.app.state.session_factory() as session:
        yield session


def get_audit(request: Request) -> AuditTrail:
    audit: AuditTrail = request.app.state.audit
    return audit


def get_redis(request: Request) -> Redis:
    redis: Redis = request.app.state.redis
    return redis


async def current_person(
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> Person:
    person = await db.scalar(select(Person).where(Person.keycloak_sub == principal.sub))
    if person is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "profile_not_found")
    return person
