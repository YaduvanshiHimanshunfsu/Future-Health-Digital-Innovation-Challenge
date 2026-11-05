from collections.abc import AsyncIterator, Mapping
from http import HTTPStatus
from typing import Any, NoReturn

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.security import Principal, get_principal
from app.country_packs.loader import PackRegistry
from app.models.person import Person
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz
from app.privacy.crypto import FieldCipher


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """A session per request. Routes commit explicitly, and anything uncommitted is rolled back."""
    async with request.app.state.session_factory() as session:
        yield session


def get_audit(request: Request) -> AuditTrail:
    audit: AuditTrail = request.app.state.audit
    return audit


def get_authz(request: Request) -> Authz:
    authz: Authz = request.app.state.authz
    return authz


def get_cipher(request: Request) -> FieldCipher:
    cipher: FieldCipher = request.app.state.cipher
    return cipher


def get_packs(request: Request) -> PackRegistry:
    packs: PackRegistry = request.app.state.packs
    return packs


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


def require_service_consent(person: Person) -> None:
    if person.service_consent_at is None:
        raise ApiError(HTTPStatus.FORBIDDEN, "service_consent_required")


async def deny(
    audit: AuditTrail, actor: str, resource: str, *, meta: Mapping[str, Any] | None = None
) -> NoReturn:
    """Looks exactly like the thing not existing, and leaves a record that outlives the request."""
    await audit.record_independently(
        actor=actor, action="access.denied", resource=resource, outcome="denied", meta=meta
    )
    raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
