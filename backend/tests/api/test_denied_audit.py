import time
from typing import Any

import pytest
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import Principal, require_role
from app.models.audit import AuditLog
from app.models.person import Person
from app.privacy.audit import AuditTrail
from tests.conftest import IdentityProvider, client_for

pytestmark = pytest.mark.db

router = APIRouter()


@router.get("/test/admin-only")
async def admin_only(
    principal: Principal = Depends(require_role("program_admin")),
) -> dict[str, str]:
    return {"sub": principal.sub}


async def test_denied_request_leaves_an_audit_row(
    app_factory: Any,
    app_url: str,
    idp: IdentityProvider,
    session_factory: async_sessionmaker[AsyncSession],
    audit: AuditTrail,
) -> None:
    app = app_factory(database_url=app_url)
    app.include_router(router)
    app.state.audit = audit

    async with client_for(app) as http:
        token = idp.token(sub="curious-person")
        response = await http.get("/test/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

    async with session_factory() as session:
        row = await session.scalar(select(AuditLog))
        assert row is not None
        assert row.actor == "curious-person"
        assert row.action == "access.denied"
        assert row.outcome == "denied"
        assert row.resource == "route:/test/admin-only"
        assert (await audit.verify_chain(session)).intact


async def test_denied_attempt_survives_the_requests_rollback(
    audit: AuditTrail, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    async with session_factory() as session:
        session.add(
            Person(keycloak_sub="rolled-back", pack_code="ae-abu-dhabi", preferred_lang="en")
        )
        await session.flush()
        assert await audit.record_independently(
            actor="a", action="access.denied", resource="person:2", outcome="denied"
        )
        await session.rollback()

    async with session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(Person)) == 0
        rows = (await session.scalars(select(AuditLog))).all()
        assert [row.action for row in rows] == ["access.denied"]
        assert (await audit.verify_chain(session)).intact


async def test_independent_write_gives_up_instead_of_waiting_on_a_held_chain_lock(
    audit: AuditTrail, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    async with session_factory() as holder:
        await audit.append(holder, actor="a", action="in.progress", resource="r")
        started = time.monotonic()
        written = await audit.record_independently(
            actor="a", action="access.denied", resource="r", outcome="denied"
        )
        waited = time.monotonic() - started
        await holder.rollback()
    assert written is False
    assert waited < 4


async def test_a_failed_audit_write_does_not_raise_or_grant_anything(
    idp: IdentityProvider, app_factory: Any
) -> None:
    """With the database down the write fails, and the caller must still be refused."""
    app = app_factory()
    app.include_router(router)
    async with client_for(app) as http:
        response = await http.get(
            "/test/admin-only", headers={"Authorization": f"Bearer {idp.token()}"}
        )
    assert response.status_code == 403


async def test_allowed_request_adds_no_denied_row(
    app_factory: Any,
    app_url: str,
    idp: IdentityProvider,
    session_factory: async_sessionmaker[AsyncSession],
    audit: AuditTrail,
) -> None:
    app = app_factory(database_url=app_url)
    app.include_router(router)
    app.state.audit = audit
    token = idp.token(realm_access={"roles": ["program_admin"]})
    async with client_for(app) as http:
        response = await http.get("/test/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    async with session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(AuditLog)) == 0
