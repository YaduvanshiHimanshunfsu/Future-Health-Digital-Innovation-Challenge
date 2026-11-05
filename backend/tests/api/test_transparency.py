import uuid
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.break_glass import BreakGlassEvent
from app.models.person import Person
from app.privacy.authz import Authz, RelationTuple
from tests.api.helpers import Stack, bundle_for

pytestmark = pytest.mark.db

REASON = "Unconscious patient, treating team needs the record"


async def a_case(stack: Stack, slug: str = "x_man") -> tuple[str, dict[str, str]]:
    await stack.ingest(bundle_for(slug))
    subject = await stack.sign_in(f"{slug}-login", slug)
    return str((await stack.only_case()).id), subject


async def staff_person(stack: Stack, sub: str, role: str) -> tuple[dict[str, str], str]:
    headers = stack.staff(sub, role)
    created = await stack.http.post("/v1/me", json={}, headers=headers)
    assert created.status_code == 200
    return headers, created.json()["id"]


async def log_of(stack: Stack, headers: dict[str, str]) -> list[dict[str, Any]]:
    response = await stack.http.get("/v1/me/access-log", headers=headers)
    assert response.status_code == 200
    entries: list[dict[str, Any]] = response.json()["entries"]
    return entries


async def test_a_counsellor_viewing_a_case_shows_in_the_subjects_log(stack: Stack) -> None:
    """V3.5.1. Assignment itself arrives in sub-phase 4.5, so the test writes the tuple directly."""
    case_id, subject = await a_case(stack)
    headers, counsellor_id = await staff_person(stack, "counsellor-1", "counsellor")
    authz: Authz = stack.app.state.authz
    await authz.write(RelationTuple(f"user:{counsellor_id}", "assigned", f"care_case:{case_id}"))

    response = await stack.http.get(f"/v1/cases/{case_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["through_break_glass"] is False

    entries = await log_of(stack, subject)
    view = next(entry for entry in entries if entry["action"] == "case.view")
    assert view["who"] == "counsellor"
    assert view["summary"] == "Staff viewed your care case"
    assert view["flagged"] is False


async def test_the_log_shows_kinds_of_actor_and_never_login_ids(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    owner = await stack.sign_in("owner-login", "fatima")
    grantee = await stack.sign_in("grantee-login")
    share = await stack.share(owner, grantee)
    await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)
    await stack.http.get("/v1/me/results", headers=owner)

    response = await stack.http.get("/v1/me/access-log", headers=owner)
    assert "grantee-login" not in response.text
    assert "lab-1" not in response.text
    entries = response.json()["entries"]
    who = {entry["action"]: entry["who"] for entry in entries}
    assert who["shared.view"] == "shared_with"
    assert who["results.view"] == "you"
    assert who["report.ingest"] == "lab"


async def test_the_log_includes_a_partners_actions(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    await stack.ingest(bundle_for("khalid"))
    first = await stack.sign_in("fatima-login", "fatima")
    second = await stack.sign_in("khalid-login", "khalid")
    couple_id = await stack.link_couple(first, second)
    await stack.agree_to_match(couple_id, first)
    await stack.agree_to_match(couple_id, second)
    await stack.http.post(f"/v1/couples/{couple_id}/match", headers=second)
    entries = await log_of(stack, first)
    match_entry = next(entry for entry in entries if entry["action"] == "match.run")
    assert match_entry["who"] == "partner"


async def test_a_refused_attempt_on_a_real_share_shows_in_the_owners_log(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    owner = await stack.sign_in("owner", "fatima")
    grantee = await stack.sign_in("grantee")
    share = await stack.share(owner, grantee)
    await stack.http.delete(f"/v1/consents/{share['id']}", headers=owner)
    await stack.http.get(f"/v1/shared/{share['id']}", headers=grantee)
    entries = await log_of(stack, owner)
    denied = next(entry for entry in entries if entry["action"] == "access.denied")
    assert denied["outcome"] == "denied"
    assert denied["summary"] == "Someone was refused access"


async def test_the_log_holds_nobody_elses_rows(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    await stack.ingest(bundle_for("khalid"))
    first = await stack.sign_in("fatima-login", "fatima")
    second = await stack.sign_in("khalid-login", "khalid")
    await stack.http.get("/v1/me/results", headers=second)
    first_entries = await log_of(stack, first)
    assert [entry for entry in first_entries if entry["action"] == "results.view"] == []
    assert first_entries, "the person's own rows are there"


async def test_the_log_is_in_the_persons_language(stack: Stack) -> None:
    from tests.api.helpers import INDIA

    await stack.ingest(bundle_for("priya", pack=INDIA), pack=INDIA)
    headers = await stack.sign_in("priya-login", "priya", pack=INDIA)
    await stack.http.patch("/v1/me", json={"preferred_lang": "hi"}, headers=headers)
    entries = await log_of(stack, headers)
    assert any("लैब" in entry["summary"] for entry in entries)


async def test_a_person_cannot_call_a_staff_route(stack: Stack) -> None:
    """V3.1.3."""
    case_id, subject = await a_case(stack)
    response = await stack.http.get(f"/v1/cases/{case_id}", headers=subject)
    assert response.status_code == 403
    async with stack.factory() as session:
        rows = (await session.scalars(select(AuditLog))).all()
    assert any(row.action == "access.denied" and row.outcome == "denied" for row in rows)


async def test_staff_with_no_link_to_a_case_get_404(stack: Stack) -> None:
    case_id, _ = await a_case(stack)
    headers, _ = await staff_person(stack, "counsellor-1", "counsellor")
    real = await stack.http.get(f"/v1/cases/{case_id}", headers=headers)
    absent = await stack.http.get(f"/v1/cases/{uuid.uuid4()}", headers=headers)
    assert real.status_code == absent.status_code == 404
    assert "possibly" not in real.text


@pytest.mark.parametrize("reason", ["", "too short", "x" * 501])
async def test_break_glass_without_a_real_reason_is_refused(stack: Stack, reason: str) -> None:
    """V3.5.2."""
    case_id, _ = await a_case(stack)
    headers, _ = await staff_person(stack, "doctor-1", "physician")
    response = await stack.http.post(
        f"/v1/cases/{case_id}/break-glass", json={"reason": reason}, headers=headers
    )
    assert response.status_code == 422
    assert (await stack.http.get(f"/v1/cases/{case_id}", headers=headers)).status_code == 404


async def test_break_glass_gives_time_limited_access_and_is_flagged(stack: Stack) -> None:
    """V3.5.2."""
    case_id, subject = await a_case(stack)
    headers, _ = await staff_person(stack, "doctor-1", "physician")
    assert (await stack.http.get(f"/v1/cases/{case_id}", headers=headers)).status_code == 404

    opened = await stack.http.post(
        f"/v1/cases/{case_id}/break-glass", json={"reason": REASON}, headers=headers
    )
    assert opened.status_code == 201
    assert opened.json()["access_ready"] is True

    view = await stack.http.get(f"/v1/cases/{case_id}", headers=headers)
    assert view.status_code == 200
    assert view.json()["through_break_glass"] is True

    entries = await log_of(stack, subject)
    flagged = {entry["action"] for entry in entries if entry["flagged"]}
    assert flagged == {"break_glass.open", "case.view"}
    assert all(e["who"] == "physician" for e in entries if e["flagged"])

    authz: Authz = stack.app.state.authz
    now = authz.clock()
    authz.clock = lambda: now + timedelta(hours=2)
    assert (await stack.http.get(f"/v1/cases/{case_id}", headers=headers)).status_code == 404


async def test_ordinary_people_cannot_break_glass(stack: Stack) -> None:
    case_id, subject = await a_case(stack)
    response = await stack.http.post(
        f"/v1/cases/{case_id}/break-glass", json={"reason": REASON}, headers=subject
    )
    assert response.status_code == 403


async def test_break_glass_on_nothing_gets_404(stack: Stack) -> None:
    headers, _ = await staff_person(stack, "doctor-1", "physician")
    response = await stack.http.post(
        f"/v1/cases/{uuid.uuid4()}/break-glass", json={"reason": REASON}, headers=headers
    )
    assert response.status_code == 404


async def test_identifiers_are_taken_out_of_the_reason(stack: Stack) -> None:
    case_id, _ = await a_case(stack)
    headers, _ = await staff_person(stack, "doctor-1", "physician")
    await stack.http.post(
        f"/v1/cases/{case_id}/break-glass",
        json={"reason": "Family called from +971 50 123 4567, need the record now"},
        headers=headers,
    )
    async with stack.factory() as session:
        event = await session.scalar(select(BreakGlassEvent))
    assert event is not None
    assert "123 4567" not in event.reason
    assert "need the record" in event.reason


async def test_reviewers_see_and_close_break_glass_events(stack: Stack) -> None:
    case_id, _ = await a_case(stack)
    headers, _ = await staff_person(stack, "doctor-1", "physician")
    await stack.http.post(
        f"/v1/cases/{case_id}/break-glass", json={"reason": REASON}, headers=headers
    )
    auditor, _ = await staff_person(stack, "auditor-1", "auditor")
    pending = (await stack.http.get("/v1/break-glass", headers=auditor)).json()
    assert [event["case_id"] for event in pending] == [case_id]
    assert pending[0]["reason"] == REASON

    assert (
        await stack.http.post(f"/v1/break-glass/{pending[0]['id']}/review", headers=auditor)
    ).status_code == 204
    assert (await stack.http.get("/v1/break-glass", headers=auditor)).json() == []
    async with stack.factory() as session:
        event = await session.scalar(select(BreakGlassEvent))
        reviewer = await session.scalar(select(Person).where(Person.keycloak_sub == "auditor-1"))
    assert event is not None
    assert reviewer is not None
    assert event.reviewed_by == reviewer.id


async def test_nobody_reviews_their_own_access(stack: Stack) -> None:
    case_id, _ = await a_case(stack)
    # One person holding both roles, which real organisations do sometimes allow.
    both = stack.headers(sub="both", realm_access={"roles": ["physician", "auditor"]})
    await stack.http.post("/v1/me", json={}, headers=both)
    await stack.http.post(f"/v1/cases/{case_id}/break-glass", json={"reason": REASON}, headers=both)
    event_id = (await stack.http.get("/v1/break-glass", headers=both)).json()[0]["id"]
    response = await stack.http.post(f"/v1/break-glass/{event_id}/review", headers=both)
    assert response.status_code == 409
    assert response.json()["code"] == "cannot_review_own_access"


async def test_only_auditors_see_the_review_list(stack: Stack) -> None:
    headers, _ = await staff_person(stack, "doctor-1", "physician")
    assert (await stack.http.get("/v1/break-glass", headers=headers)).status_code == 403


async def test_the_log_covers_couple_and_case_records_too(stack: Stack) -> None:
    case_id, subject = await a_case(stack, "x_man")
    other = await stack.sign_in("other")
    couple_id = await stack.link_couple(subject, other)
    entries = await log_of(stack, subject)
    actions = {entry["action"] for entry in entries}
    assert {"case.triage", "couple.create", "couple.join"} <= actions
    assert case_id and couple_id
