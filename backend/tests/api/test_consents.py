import shutil
import time
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select

from app.core.config import DEFAULT_PACKS_DIR
from app.models.audit import AuditLog
from app.models.consent import Consent
from app.privacy.authz import Authz, RelationTuple
from tests.api.helpers import AD, Stack, bundle_for

pytestmark = pytest.mark.db


async def shared_people(stack: Stack, kind: str = "share_full") -> tuple[Any, Any, dict[str, Any]]:
    await stack.ingest(bundle_for("fatima"))
    owner = await stack.sign_in("owner", "fatima")
    grantee = await stack.sign_in("grantee")
    return owner, grantee, await stack.share(owner, grantee, kind)


async def test_a_full_share_can_be_read(stack: Stack) -> None:
    _, grantee, share = await shared_people(stack)
    assert share["access_ready"] is True
    response = await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)
    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "full"
    assert [fact["gene"] for fact in body["facts"]] == ["HBB"]
    assert "c.20A" not in response.text


async def test_after_revoke_the_grantee_gets_404(stack: Stack) -> None:
    """V3.2.1."""
    owner, grantee, share = await shared_people(stack)
    assert (await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)).status_code == 200
    revoked = await stack.http.delete(f"/v1/consents/{share['id']}", headers=owner)
    assert revoked.status_code == 204
    after = await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)
    assert after.status_code == 404
    assert "HBB" not in after.text


async def test_revoking_takes_under_a_second_and_records_how_long(stack: Stack) -> None:
    """V3.2.2. The figure goes in the audit row, ready for the metrics in sub-phase 5.3."""
    owner, _, share = await shared_people(stack)
    started = time.perf_counter()
    await stack.http.delete(f"/v1/consents/{share['id']}", headers=owner)
    assert time.perf_counter() - started < 1.0
    async with stack.factory() as session:
        rows = (await session.scalars(select(AuditLog))).all()
    revoke = next(row for row in rows if row.action == "consent.revoke")
    assert isinstance(revoke.meta["latency_ms"], int)
    assert revoke.meta["latency_ms"] < 1000


async def test_revoking_during_an_outage_says_so_and_changes_nothing(stack: Stack) -> None:
    """V3.2.3. Claiming success here would be the worst thing it could do."""
    owner, grantee, share = await shared_people(stack)
    real = stack.cut_off_authorisation()
    response = await stack.http.delete(f"/v1/consents/{share['id']}", headers=owner)
    assert response.status_code == 503
    assert response.json()["code"] == "revoke_unavailable"
    listing = (await stack.http.get("/v1/consents", headers=owner)).json()
    entry = next(item for item in listing["given"] if item["id"] == share["id"])
    assert entry["active"] is True
    assert entry["revoked_at"] is None

    await stack.app.state.authz.aclose()
    stack.app.state.authz = real
    assert (
        await stack.http.delete(f"/v1/consents/{share['id']}", headers=owner)
    ).status_code == 204
    assert (await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)).status_code == 404


async def test_protected_routes_deny_during_an_outage(stack: Stack) -> None:
    """V3.1.1."""
    _, grantee, share = await shared_people(stack)
    stack.cut_off_authorisation()
    response = await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)
    assert response.status_code == 404
    assert "HBB" not in response.text
    await stack.app.state.authz.aclose()


async def test_an_expired_share_stops_with_no_job_running(stack: Stack) -> None:
    """V3.2.4. The row is untouched, so nothing but the clock changed."""
    _, grantee, share = await shared_people(stack)
    authz: Authz = stack.app.state.authz
    now = authz.clock()
    authz.clock = lambda: now + timedelta(days=31)
    response = await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)
    assert response.status_code == 404
    async with stack.factory() as session:
        row = await session.get(Consent, uuid.UUID(share["id"]))
        assert row is not None
        assert row.revoked_at is None


async def test_expiry_holds_in_openfga_even_if_the_ledger_is_ignored(stack: Stack) -> None:
    owner, grantee, _ = await shared_people(stack)
    authz: Authz = stack.app.state.authz
    user, report = (
        f"user:{await stack.person_id(grantee)}",
        f"report:{await stack.person_id(owner)}",
    )
    assert await authz.check(user, "can_view_full", report)
    now = authz.clock()
    authz.clock = lambda: now + timedelta(days=31)
    assert not await authz.check(user, "can_view_full", report)


async def test_a_summary_grantee_cannot_see_full_detail(stack: Stack) -> None:
    """V3.2.5."""
    _, grantee, share = await shared_people(stack, "share_summary")
    response = await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)
    body = response.json()
    assert body["scope"] == "summary"
    assert set(body) == {"scope", "has_report", "facts", "pack"}
    assert set(body["facts"][0]) == {"gene", "label"}


async def test_two_grants_to_one_person_are_independent(stack: Stack) -> None:
    """V3.2.6. Revoking one leaves the other working. Each has its own tuple, so they can't clash."""
    await stack.ingest(bundle_for("fatima"))
    owner = await stack.sign_in("owner", "fatima")
    grantee = await stack.sign_in("grantee")
    first = await stack.share(owner, grantee, "share_full")
    second = await stack.share(owner, grantee, "share_summary")
    assert first["access_ready"] and second["access_ready"]

    await stack.http.delete(f"/v1/consents/{first['id']}", headers=owner)
    assert (await stack.http.get(f"/v1/shared/{first['id']}", headers=grantee)).status_code == 404
    still = await stack.http.get(f"/v1/shared/{second['id']}", headers=grantee)
    assert still.status_code == 200
    assert still.json()["scope"] == "summary"

    await stack.http.delete(f"/v1/consents/{second['id']}", headers=owner)
    assert (await stack.http.get(f"/v1/shared/{second['id']}", headers=grantee)).status_code == 404


async def test_someone_else_cannot_use_a_share(stack: Stack) -> None:
    _, _, share = await shared_people(stack)
    stranger = await stack.sign_in("stranger")
    response = await stack.http.get(f"/v1/shared/{share['id']}", headers=stranger)
    assert response.status_code == 404
    assert "HBB" not in response.text


async def test_someone_else_cannot_revoke_a_share(stack: Stack) -> None:
    _, grantee, share = await shared_people(stack)
    assert (
        await stack.http.delete(f"/v1/consents/{share['id']}", headers=grantee)
    ).status_code == 404
    stranger = await stack.sign_in("stranger")
    assert (
        await stack.http.delete(f"/v1/consents/{share['id']}", headers=stranger)
    ).status_code == 404
    assert (await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)).status_code == 200


async def test_a_grant_pending_in_the_outbox_cannot_outlive_its_revocation(stack: Stack) -> None:
    """The grant is saved while OpenFGA is down, and revoked once it's back but before any drain."""
    await stack.ingest(bundle_for("fatima"))
    owner = await stack.sign_in("owner", "fatima")
    grantee = await stack.sign_in("grantee")
    real = stack.cut_off_authorisation()
    share = await stack.share(owner, grantee)
    assert share["access_ready"] is False
    await stack.app.state.authz.aclose()
    stack.app.state.authz = real

    assert (
        await stack.http.delete(f"/v1/consents/{share['id']}", headers=owner)
    ).status_code == 204
    from app.privacy import outbox

    await outbox.drain(stack.factory, real)
    grantee_id = await stack.person_id(grantee)
    assert not await real.check(
        f"user:{grantee_id}", "can_view_full", f"report:{await stack.person_id(owner)}"
    )


@pytest.mark.parametrize(
    "path", ["/v1/shared/{id}", "/v1/couples/{id}/match"], ids=["shared", "match"]
)
async def test_no_genetic_data_before_service_consent(stack: Stack, path: str) -> None:
    """V3.2.7."""
    headers = await stack.provision("no-consent")
    url = path.format(id=uuid.uuid4())
    method = stack.http.post if "match" in path else stack.http.get
    response = await method(url, headers=headers)
    assert response.status_code == 403
    assert response.json()["code"] == "service_consent_required"


async def test_service_consent_can_be_withdrawn(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("fatima-login", "fatima")
    listing = (await stack.http.get("/v1/consents", headers=headers)).json()
    service = next(item for item in listing["given"] if item["kind"] == "service")
    assert (
        await stack.http.delete(f"/v1/consents/{service['id']}", headers=headers)
    ).status_code == 204
    assert (await stack.http.get("/v1/me/results", headers=headers)).status_code == 403


async def test_a_receive_code_works_once_and_identifies_nobody(stack: Stack) -> None:
    owner = await stack.sign_in("owner")
    grantee = await stack.sign_in("grantee")
    code = (await stack.http.post("/v1/consents/receive-code", headers=grantee)).json()["code"]
    grant = {
        "kind": "share_full",
        "purpose": "family_support",
        "terms_version": "1",
        "duration_days": 1,
    }
    first = await stack.http.post(
        "/v1/consents", json={**grant, "grantee_code": code}, headers=owner
    )
    assert first.status_code == 201
    again = await stack.http.post(
        "/v1/consents", json={**grant, "grantee_code": code}, headers=owner
    )
    unknown = await stack.http.post(
        "/v1/consents", json={**grant, "grantee_code": "x" * 22}, headers=owner
    )
    assert again.status_code == unknown.status_code == 404
    assert again.json()["code"] == unknown.json()["code"]


async def test_nobody_can_share_with_themselves(stack: Stack) -> None:
    owner = await stack.sign_in("owner")
    code = (await stack.http.post("/v1/consents/receive-code", headers=owner)).json()["code"]
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
    assert response.status_code == 404


@pytest.mark.parametrize(
    "change",
    [
        {"purpose": "marketing"},
        {"duration_days": 0},
        {"duration_days": 366},
        {"kind": "research"},
        {"role": "program_admin"},
        {"grantee_id": str(uuid.uuid4())},
    ],
)
async def test_invalid_grants_are_refused(stack: Stack, change: dict[str, Any]) -> None:
    """Includes V3.1.4: a `role` in the body is refused, not ignored."""
    owner = await stack.sign_in("owner")
    grantee = await stack.sign_in("grantee")
    code = (await stack.http.post("/v1/consents/receive-code", headers=grantee)).json()["code"]
    body = {
        "grantee_code": code,
        "kind": "share_full",
        "purpose": "family_support",
        "terms_version": "1",
        "duration_days": 1,
        **change,
    }
    response = await stack.http.post("/v1/consents", json=body, headers=owner)
    assert response.status_code == 422


async def test_a_grantee_is_not_shown_a_record_of_being_cut_off(stack: Stack) -> None:
    owner, grantee, share = await shared_people(stack)
    assert [
        i["id"] for i in (await stack.http.get("/v1/consents", headers=grantee)).json()["received"]
    ] == [share["id"]]
    await stack.http.delete(f"/v1/consents/{share['id']}", headers=owner)
    assert (await stack.http.get("/v1/consents", headers=grantee)).json()["received"] == []


async def test_right_not_to_know_withholds_results(stack: Stack) -> None:
    """V3.2.8."""
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("fatima-login", "fatima")
    chosen = await stack.http.post(
        "/v1/me/results-preference", json={"withhold": True, "terms_version": "1"}, headers=headers
    )
    assert chosen.json()["results_withheld"] is True
    for path in ("/v1/me/results", "/v1/me/risk"):
        response = await stack.http.get(path, headers=headers)
        body = response.json()
        assert body["withheld"] is True
        assert body["facts"] == []
        assert body["human_contact_required"] is False
        assert "HBB" not in response.text


async def test_they_can_change_their_mind(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    headers = await stack.sign_in("fatima-login", "fatima")
    for withhold in (True, False):
        await stack.http.post(
            "/v1/me/results-preference",
            json={"withhold": withhold, "terms_version": "1"},
            headers=headers,
        )
    body = (await stack.http.get("/v1/me/results", headers=headers)).json()
    assert body["withheld"] is False
    assert [fact["gene"] for fact in body["facts"]] == ["HBB"]


async def test_a_serious_finding_still_reaches_a_person(stack: Stack) -> None:
    """Art. 9(3) in the reference pack. The screen says someone will call, and never why."""
    await stack.ingest(bundle_for("x_man"))
    headers = await stack.sign_in("x-login", "x_man")
    await stack.http.post(
        "/v1/me/results-preference", json={"withhold": True, "terms_version": "1"}, headers=headers
    )
    response = await stack.http.get("/v1/me/results", headers=headers)
    body = response.json()
    assert body["human_contact_required"] is True
    assert body["facts"] == []
    assert "DMD" not in response.text
    assert (await stack.only_case()).priority == "P1"


def pack_with(tmp_path: Path, **legal: str) -> Path:
    target = tmp_path / AD
    shutil.copytree(DEFAULT_PACKS_DIR / AD, target)
    path = target / "legal.yaml"
    text = path.read_text("utf-8")
    for key, value in legal.items():
        assert f"{key}: true" in text
        text = text.replace(f"{key}: true", f"{key}: {value}")
    path.write_text(text, "utf-8")
    return tmp_path


async def test_a_pack_with_no_duty_to_inform_raises_no_contact_flag(
    make_stack: Any, tmp_path: Path
) -> None:
    stack = await make_stack(
        packs_dir=pack_with(tmp_path, must_inform_if_life_threatening="false"),
        enabled_packs=[AD],
    )
    await stack.ingest(bundle_for("x_man"))
    headers = await stack.sign_in("x-login", "x_man")
    await stack.http.post(
        "/v1/me/results-preference", json={"withhold": True, "terms_version": "1"}, headers=headers
    )
    body = (await stack.http.get("/v1/me/results", headers=headers)).json()
    assert body["human_contact_required"] is False


async def test_a_pack_can_rule_the_option_out(make_stack: Any, tmp_path: Path) -> None:
    stack = await make_stack(
        packs_dir=pack_with(tmp_path, right_not_to_know="false"), enabled_packs=[AD]
    )
    headers = await stack.sign_in("login")
    response = await stack.http.post(
        "/v1/me/results-preference", json={"withhold": True, "terms_version": "1"}, headers=headers
    )
    assert response.status_code == 422
    assert response.json()["code"] == "right_not_to_know_unavailable"


async def test_choosing_not_to_know_blocks_new_shares_and_stops_old_ones(stack: Stack) -> None:
    owner, grantee, share = await shared_people(stack)
    await stack.http.post(
        "/v1/me/results-preference", json={"withhold": True, "terms_version": "1"}, headers=owner
    )
    assert (await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)).status_code == 404
    code = (await stack.http.post("/v1/consents/receive-code", headers=grantee)).json()["code"]
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
    assert response.status_code == 409
    assert response.json()["code"] == "results_withheld"


async def test_a_revoked_ledger_entry_denies_even_if_openfga_still_allows(stack: Stack) -> None:
    """Either layer alone is enough to say no, so a stuck tuple can't keep access alive."""
    owner, grantee, share = await shared_people(stack)
    async with stack.factory() as session:
        row = await session.get(Consent, uuid.UUID(share["id"]))
        assert row is not None
        row.revoked_at = stack.app.state.authz.clock()
        await session.commit()
    authz: Authz = stack.app.state.authz
    assert await authz.check(
        f"user:{await stack.person_id(grantee)}",
        "can_view_full",
        f"report:{await stack.person_id(owner)}",
    ), "the test needs OpenFGA still saying yes"
    response = await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)
    assert response.status_code == 404


async def test_an_expired_ledger_entry_denies_even_if_openfga_still_allows(stack: Stack) -> None:
    _, grantee, share = await shared_people(stack)
    async with stack.factory() as session:
        row = await session.get(Consent, uuid.UUID(share["id"]))
        assert row is not None
        row.expires_at = stack.app.state.authz.clock() - timedelta(minutes=1)
        await session.commit()
    response = await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)
    assert response.status_code == 404
    received = (await stack.http.get("/v1/consents", headers=grantee)).json()["received"]
    assert received == []


async def test_a_missing_tuple_denies_even_if_the_ledger_says_yes(stack: Stack) -> None:
    owner, grantee, share = await shared_people(stack)
    authz: Authz = stack.app.state.authz
    await authz.delete(
        RelationTuple(f"user:{await stack.person_id(grantee)}", "holder", f"grant:{share['id']}")
    )
    response = await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)
    assert response.status_code == 404
    listing = (await stack.http.get("/v1/consents", headers=owner)).json()["given"]
    assert next(item for item in listing if item["id"] == share["id"])["active"] is True


async def test_someone_with_their_own_share_cannot_use_another_persons(stack: Stack) -> None:
    """OpenFGA would say yes here, since both may read this report. Each share is still its own."""
    owner, grantee, share = await shared_people(stack)
    other = await stack.sign_in("other-grantee")
    other_share = await stack.share(owner, other)
    assert (
        await stack.http.get(f"/v1/shared/{other_share['id']}", headers=other)
    ).status_code == 200
    response = await stack.http.get(f"/v1/shared/{share['id']}", headers=other)
    assert response.status_code == 404
    assert grantee


async def test_people_cannot_fake_a_grant_of_another_kind(stack: Stack) -> None:
    """A consent that isn't a share can't be read through the sharing route, whatever it says."""
    headers = await stack.sign_in("someone")
    given = (await stack.http.get("/v1/consents", headers=headers)).json()["given"]
    service = next(item for item in given if item["kind"] == "service")
    assert (await stack.http.get(f"/v1/shared/{service['id']}", headers=headers)).status_code == 404
