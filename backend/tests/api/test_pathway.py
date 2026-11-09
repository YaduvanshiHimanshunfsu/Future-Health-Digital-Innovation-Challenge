"""The care pathway end to end: a person's journey, their own steps, a counsellor's moves, and the
overdue scan with its one reminder. Checks V5.1.1 to V5.1.9."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.core.config import decode_key
from app.models.analytics import Event
from app.models.case import CareCase, PathwayStep
from app.models.enums import CaseState as S
from app.notifications.service import TEMPLATES, MockNotifier
from app.pathway.scheduler import scan
from tests.api.helpers import Stack, bundle_for

pytestmark = pytest.mark.db


async def counsellor_for(stack: Stack, case_id: str) -> dict[str, str]:
    headers = stack.staff("counsellor-1", "counsellor")
    await stack.http.post("/v1/me", json={}, headers=headers)
    claimed = await stack.http.post(f"/v1/cases/{case_id}/claim", headers=headers)
    assert claimed.status_code == 200
    return headers


async def step_count(stack: Stack, case_id: object) -> int:
    async with stack.factory() as session:
        return int(
            await session.scalar(select(func.count()).where(PathwayStep.case_id == case_id)) or 0
        )


async def scan_now(stack: Stack, when: datetime) -> tuple[MockNotifier, object]:
    notifier = MockNotifier()
    key = decode_key(stack.app.state.settings.analytics_hmac_key, "ANALYTICS_HMAC_KEY")
    result = await scan(stack.factory, stack.app.state.packs, notifier, key, now=when)
    return notifier, result


async def test_a_person_reads_their_own_journey_and_nobody_elses(stack: Stack) -> None:
    """V5.1.9."""
    await stack.ingest(bundle_for("uncertain"))
    person = await stack.sign_in("u-login", "uncertain")
    stranger = await stack.sign_in("stranger")
    mine = (await stack.http.get("/v1/me/journey", headers=person)).json()
    assert len(mine) == 1
    assert [step["state"] for step in mine[0]["steps"]][0] == "RESULT_RELEASED"
    assert all(step["by"] in ("you", "care_team", "system") for step in mine[0]["steps"])
    assert "DECLINED_BY_USER" in mine[0]["next_steps"]
    assert (await stack.http.get("/v1/me/journey", headers=stranger)).json() == []
    other = await stack.http.post(
        f"/v1/journey/{mine[0]['case_id']}/steps",
        json={"to_state": "DECLINED_BY_USER"},
        headers=stranger,
    )
    assert other.status_code == 404


async def test_every_change_leaves_a_step_and_a_counsellor_can_reach_referral(stack: Stack) -> None:
    """V5.1.1. Step count equals change count, all the way to an accepted referral."""
    await stack.ingest(bundle_for("x_carrier"))
    case = await stack.only_case()
    before = await step_count(stack, case.id)
    counsellor = await counsellor_for(stack, str(case.id))
    route = [
        "COUNSELLING_DONE",
        "CONFIRMATORY_TEST_ORDERED",
        "CONFIRMED",
        "REPRO_GENOMICS_REFERRED",
        "REFERRAL_ACCEPTED",
    ]
    # The x_carrier case starts at COUNSELLING_REQUESTED; booking is its own route, so a
    # counsellor's moves start after it.
    async with stack.factory() as session:
        row = await session.get(CareCase, case.id)
        assert row is not None
        row.state = S.COUNSELLING_BOOKED.value
        await session.commit()
    for state in route:
        moved = await stack.http.post(
            f"/v1/cases/{case.id}/advance", json={"to_state": state}, headers=counsellor
        )
        assert moved.status_code == 204, (state, moved.text)
    assert await step_count(stack, case.id) == before + len(route)


async def test_an_invalid_move_is_409_and_changes_nothing(stack: Stack) -> None:
    """V5.1.2."""
    await stack.ingest(bundle_for("x_carrier"))
    case = await stack.only_case()
    counsellor = await counsellor_for(stack, str(case.id))
    before = await step_count(stack, case.id)
    jumped = await stack.http.post(
        f"/v1/cases/{case.id}/advance", json={"to_state": "REFERRAL_ACCEPTED"}, headers=counsellor
    )
    assert jumped.status_code == 409
    assert await step_count(stack, case.id) == before


async def test_people_take_only_their_own_steps_and_staff_only_theirs(stack: Stack) -> None:
    await stack.ingest(bundle_for("uncertain"))
    person = await stack.sign_in("u-login", "uncertain")
    case = await stack.only_case()
    staff_step = await stack.http.post(
        f"/v1/journey/{case.id}/steps", json={"to_state": "REFERRAL_ACCEPTED"}, headers=person
    )
    assert staff_step.status_code == 403
    other = stack.staff("counsellor-2", "counsellor")
    await stack.http.post("/v1/me", json={}, headers=other)
    unassigned = await stack.http.post(
        f"/v1/cases/{case.id}/advance", json={"to_state": "COUNSELLING_DONE"}, headers=other
    )
    assert unassigned.status_code == 404


async def test_declining_stops_reminders_and_can_be_undone(stack: Stack) -> None:
    """V5.1.3 and V5.1.4."""
    await stack.ingest(bundle_for("uncertain"))
    person = await stack.sign_in("u-login", "uncertain")
    case = await stack.only_case()
    declined = await stack.http.post(
        f"/v1/journey/{case.id}/steps", json={"to_state": "DECLINED_BY_USER"}, headers=person
    )
    assert declined.status_code == 204
    notifier, _ = await scan_now(stack, datetime.now(UTC) + timedelta(days=60))
    assert notifier.sent == []
    back = await stack.http.post(
        f"/v1/journey/{case.id}/steps",
        json={"to_state": "COUNSELLING_REQUESTED"},
        headers=person,
    )
    assert back.status_code == 204


async def test_an_overdue_step_is_flagged_and_reminded_once_with_no_details(stack: Stack) -> None:
    """V5.1.6 for the scan itself, and V5.2.4 for the reminder's text."""
    await stack.ingest(bundle_for("fatima"))
    await stack.sign_in("f-login", "fatima")
    case = await stack.only_case()
    late = case.step_due + timedelta(hours=1)
    notifier, first = await scan_now(stack, late)
    again, _ = await scan_now(stack, late + timedelta(hours=1))
    assert len(notifier.sent) == 1
    assert again.sent == []
    _, purpose, text = notifier.sent[0]
    assert purpose == "reminder"
    for secret in ("HBB", "carrier", "Fatima", "thalass", "result"):
        assert secret.lower() not in text.lower()
    async with stack.factory() as session:
        row = await session.get(CareCase, case.id)
        assert row is not None and row.stalled
        kinds = set((await session.scalars(select(Event.kind))).all())
    assert {"case_stalled", "reminder_sent"} <= kinds


async def test_reminders_can_be_switched_off(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    person = await stack.sign_in("f-login", "fatima")
    off = await stack.http.patch("/v1/me/reminders", json={"opt_out": True}, headers=person)
    assert off.status_code == 204
    case = await stack.only_case()
    notifier, _ = await scan_now(stack, case.step_due + timedelta(hours=1))
    assert notifier.sent == []


async def test_advancing_resets_the_deadline_so_it_does_not_stall_again(stack: Stack) -> None:
    """V5.1.5."""
    await stack.ingest(bundle_for("fatima"))
    person = await stack.sign_in("f-login", "fatima")
    case = await stack.only_case()
    await scan_now(stack, case.step_due + timedelta(hours=1))
    moved = await stack.http.post(
        f"/v1/journey/{case.id}/steps",
        json={"to_state": "COUNSELLING_REQUESTED"},
        headers=person,
    )
    assert moved.status_code == 204
    async with stack.factory() as session:
        row = await session.get(CareCase, case.id)
        assert row is not None
        assert not row.stalled and row.reminded_at is None
        assert row.step_due > datetime.now(UTC) + timedelta(hours=1)


async def test_a_case_left_unanswered_becomes_lost_to_follow_up(stack: Stack) -> None:
    """V5.1.8. Recorded as an outcome, so it counts, and the person can still come back."""
    await stack.ingest(bundle_for("fatima"))
    person = await stack.sign_in("f-login", "fatima")
    case = await stack.only_case()
    _, result = await scan_now(stack, case.step_due + timedelta(days=60))
    assert result.lost == [str(case.id)]  # type: ignore[attr-defined]
    journey = (await stack.http.get("/v1/me/journey", headers=person)).json()
    assert journey[0]["state"] == "LOST_TO_FOLLOW_UP"
    assert "COUNSELLING_REQUESTED" in journey[0]["next_steps"]


async def test_two_changes_at_once_give_one_success_and_one_conflict(stack: Stack) -> None:
    """V5.1.7."""
    await stack.ingest(bundle_for("fatima"))
    person = await stack.sign_in("f-login", "fatima")
    case = await stack.only_case()

    async def step(to_state: str) -> int:
        response = await stack.http.post(
            f"/v1/journey/{case.id}/steps", json={"to_state": to_state}, headers=person
        )
        return response.status_code

    codes = await asyncio.gather(step("DECLINED_BY_USER"), step("EDUCATION_VIEWED"))
    assert sorted(codes) == [204, 409]


def test_no_reminder_text_can_carry_details() -> None:
    """V5.2.4. Fixed texts with nothing to fill in."""
    for texts in TEMPLATES.values():
        for text in texts.values():
            assert "{" not in text
