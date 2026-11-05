import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.models.audit import AuditLog
from app.models.consent import Consent
from app.models.enums import OutboxOperation
from app.models.outbox import AuthzOutbox
from app.ops.bootstrap_openfga import bootstrap
from app.privacy import outbox
from app.privacy.authz import Authz, AuthzRejected, AuthzUnavailable, RelationTuple
from tests.api.helpers import Stack, bundle_for
from tests.conftest import OPENFGA_TOKEN

pytestmark = pytest.mark.db


def member(user: uuid.UUID, couple: uuid.UUID) -> RelationTuple:
    return RelationTuple(f"user:{user}", "member", f"couple:{couple}")


async def test_write_check_delete(stack: Stack) -> None:
    authz: Authz = stack.app.state.authz
    tuple_ = member(uuid.uuid4(), uuid.uuid4())
    assert not await authz.check(tuple_.user, tuple_.relation, tuple_.object)
    await authz.write(tuple_)
    assert await authz.check(tuple_.user, tuple_.relation, tuple_.object)
    await authz.delete(tuple_)
    assert not await authz.check(tuple_.user, tuple_.relation, tuple_.object)


async def test_writes_can_be_repeated(stack: Stack) -> None:
    """H7. In the original spec a duplicate tuple was an error, which broke a second grant."""
    authz: Authz = stack.app.state.authz
    tuple_ = member(uuid.uuid4(), uuid.uuid4())
    await authz.write(tuple_)
    await authz.write(tuple_)
    await authz.delete(tuple_)
    await authz.delete(tuple_)


async def test_a_grant_expires_on_its_own(stack: Stack) -> None:
    """OpenFGA decides this from the tuple, so no job has to run for access to end."""
    authz: Authz = stack.app.state.authz
    grant, owner, user = uuid.uuid4(), uuid.uuid4(), f"user:{uuid.uuid4()}"
    expiry = datetime.now(UTC) + timedelta(hours=1)
    await authz.write(RelationTuple(user, "holder", f"grant:{grant}", expiry))
    await authz.write(RelationTuple(f"grant:{grant}#holder", "full_grant", f"report:{owner}"))
    assert await authz.check(user, "can_view_full", f"report:{owner}")
    authz.clock = lambda: expiry + timedelta(seconds=1)
    assert not await authz.check(user, "can_view_full", f"report:{owner}")


async def test_summary_access_is_not_full_access(stack: Stack) -> None:
    authz: Authz = stack.app.state.authz
    grant, owner, user = uuid.uuid4(), uuid.uuid4(), f"user:{uuid.uuid4()}"
    expiry = datetime.now(UTC) + timedelta(hours=1)
    await authz.write(RelationTuple(user, "holder", f"grant:{grant}", expiry))
    await authz.write(RelationTuple(f"grant:{grant}#holder", "summary_grant", f"report:{owner}"))
    assert await authz.check(user, "can_view_summary", f"report:{owner}")
    assert not await authz.check(user, "can_view_full", f"report:{owner}")


async def test_an_outage_means_no_access_and_writes_say_so() -> None:
    """V3.1.1, at the adapter."""
    authz = Authz("http://127.0.0.1:1", "none", timeout_seconds=0.2)
    assert await authz.check("user:a", "member", "couple:b") is False
    with pytest.raises(AuthzUnavailable):
        await authz.delete(RelationTuple("user:a", "member", "couple:b"))
    await authz.aclose()


@pytest.mark.parametrize("status", [500, 503, 401, 403])
async def test_an_error_from_openfga_means_no_access(status: int) -> None:
    authz = Authz(
        "http://fga.test",
        "s",
        transport=httpx.MockTransport(lambda _: httpx.Response(status, json={})),
    )
    assert await authz.check("user:a", "member", "couple:b") is False
    await authz.aclose()


async def test_an_odd_answer_from_openfga_means_no_access() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/stores":
            return httpx.Response(200, json={"stores": [{"id": "1", "name": "s"}]})
        if request.url.path.endswith("/authorization-models"):
            return httpx.Response(200, json={"authorization_models": [{"id": "m"}]})
        return httpx.Response(200, json={"allowed": "yes"})

    authz = Authz("http://fga.test", "s", transport=httpx.MockTransport(handler))
    assert await authz.check("user:a", "member", "couple:b") is False
    await authz.aclose()


async def test_a_bad_tuple_is_rejected_not_hidden(stack: Stack) -> None:
    authz: Authz = stack.app.state.authz
    with pytest.raises(AuthzRejected):
        await authz.write(RelationTuple("user:a", "no_such_relation", "couple:b"))


async def test_bootstrap_can_run_on_every_start(openfga_url: str) -> None:
    name = f"test-{uuid.uuid4().hex}"
    first = await bootstrap(openfga_url, name, token=OPENFGA_TOKEN)
    second = await bootstrap(openfga_url, name, token=OPENFGA_TOKEN)
    assert first == second


async def test_openfga_refuses_a_wrong_key(openfga_url: str) -> None:
    with pytest.raises(httpx.HTTPStatusError):
        await bootstrap(openfga_url, "x", token="wrong-key")


async def test_outbox_applies_and_marks_done(stack: Stack) -> None:
    authz: Authz = stack.app.state.authz
    tuple_ = member(uuid.uuid4(), uuid.uuid4())
    async with stack.factory() as session:
        outbox.enqueue(session, OutboxOperation.WRITE, tuple_)
        await session.commit()
    assert await outbox.drain(stack.factory, authz) == 1
    assert await authz.check(tuple_.user, tuple_.relation, tuple_.object)
    assert await outbox.drain(stack.factory, authz) == 0


async def test_outbox_waits_out_an_outage(stack: Stack) -> None:
    real: Authz = stack.app.state.authz
    tuple_ = member(uuid.uuid4(), uuid.uuid4())
    async with stack.factory() as session:
        outbox.enqueue(session, OutboxOperation.WRITE, tuple_)
        await session.commit()
    down = Authz("http://127.0.0.1:1", "none", timeout_seconds=0.2)
    assert await outbox.drain(stack.factory, down) == 0
    await down.aclose()
    async with stack.factory() as session:
        row = await session.scalar(select(AuthzOutbox))
        assert row is not None
        assert row.applied_at is None
        assert row.attempts == 0, "an outage isn't the tuple's fault"
    assert await outbox.drain(stack.factory, real) == 1


async def test_a_rejected_change_stops_after_a_few_tries(stack: Stack) -> None:
    authz: Authz = stack.app.state.authz
    good = member(uuid.uuid4(), uuid.uuid4())
    async with stack.factory() as session:
        outbox.enqueue(session, OutboxOperation.WRITE, RelationTuple("user:a", "nope", "couple:b"))
        await session.flush()
        outbox.enqueue(session, OutboxOperation.WRITE, good)
        await session.commit()
    await outbox.drain(stack.factory, authz)
    assert await authz.check(good.user, good.relation, good.object), (
        "one bad row can't block others"
    )
    async with stack.factory() as session:
        stuck = await session.scalar(select(AuthzOutbox).where(AuthzOutbox.relation == "nope"))
        assert stuck is not None
        assert stuck.applied_at is None
        assert stuck.attempts == 5


async def test_a_failed_commit_leaves_no_access(stack: Stack) -> None:
    """V3.1.5. The tuple is only ever written after the consent has committed."""
    owner = await stack.sign_in("owner")
    grantee = await stack.sign_in("grantee")
    code = (await stack.http.post("/v1/consents/receive-code", headers=grantee)).json()["code"]
    grantee_id = await stack.person_id(grantee)
    owner_id = await stack.person_id(owner)

    real_commit = stack.factory.class_.commit
    from sqlalchemy.ext.asyncio import AsyncSession

    async def failing_commit(self: AsyncSession) -> None:
        raise SQLAlchemyError("commit failed")

    AsyncSession.commit = failing_commit  # type: ignore[method-assign]
    try:
        response = await stack.http.post(
            "/v1/consents",
            json={
                "grantee_code": code,
                "kind": "share_full",
                "purpose": "family_support",
                "terms_version": "1",
                "duration_days": 1,
            },
            headers=owner,
        )
    finally:
        AsyncSession.commit = real_commit  # type: ignore[method-assign]
    assert response.status_code == 500

    authz: Authz = stack.app.state.authz
    assert await outbox.drain(stack.factory, authz) == 0
    assert not await authz.check(f"user:{grantee_id}", "can_view_full", f"report:{owner_id}")
    async with stack.factory() as session:
        assert await session.scalar(select(func.count()).select_from(Consent)) == 2
        assert await session.scalar(select(func.count()).select_from(AuthzOutbox)) == 0


async def test_reconcile_removes_grants_with_no_live_record(stack: Stack) -> None:
    authz: Authz = stack.app.state.authz
    orphan = RelationTuple(
        f"user:{uuid.uuid4()}",
        "holder",
        f"grant:{uuid.uuid4()}",
        datetime.now(UTC) + timedelta(hours=1),
    )
    await authz.write(orphan)
    owner = await stack.sign_in("owner")
    grantee = await stack.sign_in("grantee")
    await stack.ingest(bundle_for("fatima"))
    live = await stack.share(owner, grantee)
    revoked = await stack.share(owner, grantee)
    # A tuple left behind on purpose: the ledger says revoked, and OpenFGA still has it.
    async with stack.factory() as session:
        row = await session.get(Consent, uuid.UUID(revoked["id"]))
        assert row is not None
        row.revoked_at = datetime.now(UTC)
        await session.commit()

    assert await outbox.reconcile(stack.factory, authz) == 2
    grantee_id = await stack.person_id(grantee)
    assert await authz.check(f"user:{grantee_id}", "holder", f"grant:{live['id']}")
    assert not await authz.check(f"user:{grantee_id}", "holder", f"grant:{revoked['id']}")
    assert await outbox.reconcile(stack.factory, authz) == 0


async def test_reconcile_never_restores_a_missing_tuple(stack: Stack) -> None:
    """Restoring one could undo a revocation whose commit failed."""
    authz: Authz = stack.app.state.authz
    owner = await stack.sign_in("owner")
    grantee = await stack.sign_in("grantee")
    share = await stack.share(owner, grantee)
    grantee_id = await stack.person_id(grantee)
    await authz.delete(RelationTuple(f"user:{grantee_id}", "holder", f"grant:{share['id']}"))
    await outbox.reconcile(stack.factory, authz)
    assert not await authz.check(f"user:{grantee_id}", "holder", f"grant:{share['id']}")


async def test_denied_access_gets_404_and_an_audit_row(stack: Stack) -> None:
    """V3.1.2."""
    stranger = await stack.sign_in("stranger")
    missing = uuid.uuid4()
    response = await stack.http.get(f"/v1/couples/{missing}", headers=stranger)
    assert response.status_code == 404
    async with stack.factory() as session:
        rows = (await session.scalars(select(AuditLog))).all()
    denied = [row for row in rows if row.action == "access.denied"]
    assert [row.resource for row in denied] == [f"couple:{missing}"]
    assert denied[0].outcome == "denied"
