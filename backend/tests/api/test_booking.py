"""Booking, referrals and the centre finder. Checks V5.2.1 to V5.2.6."""

import asyncio
import json
from datetime import UTC, datetime, timedelta

import pytest
from fhir.resources.servicerequest import ServiceRequest
from fhir.resources.task import Task
from sqlalchemy import select

from app.models.case import CareCase, PathwayStep
from app.pathway.fhir_mapper import SERVICE_REQUEST_FIELDS, TASK_FIELDS
from tests.api.helpers import Stack, bundle_for

pytestmark = pytest.mark.db


async def counsellor(stack: Stack, sub: str = "counsellor-1") -> dict[str, str]:
    headers = stack.staff(sub, "counsellor")
    await stack.http.post("/v1/me", json={}, headers=headers)
    return headers


async def publish(stack: Stack, headers: dict[str, str], hours_ahead: int = 24) -> str:
    starts = (datetime.now(UTC) + timedelta(hours=hours_ahead)).replace(microsecond=0)
    made = await stack.http.post(
        "/v1/booking/slots",
        json={"starts_at": starts.isoformat(), "minutes": 30, "mode": "video", "lang": "en"},
        headers=headers,
    )
    assert made.status_code == 201, made.text
    return str(made.json()["id"])


async def test_a_person_books_a_slot_and_the_case_moves(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    person = await stack.sign_in("f-login", "fatima")
    case = await stack.only_case()
    staff = await counsellor(stack)
    slot = await publish(stack, staff)

    offered = (await stack.http.get(f"/v1/booking/slots?case_id={case.id}", headers=person)).json()
    assert [item["id"] for item in offered] == [slot]
    assert "counsellor_id" not in offered[0]

    booked = await stack.http.post(
        f"/v1/booking/slots/{slot}/book", json={"case_id": str(case.id)}, headers=person
    )
    assert booked.status_code == 200, booked.text
    assert booked.json()["status"] == "booked"
    async with stack.factory() as session:
        row = await session.get(CareCase, case.id)
        assert row is not None
        assert row.state == "COUNSELLING_BOOKED"
        assert row.counsellor_id is not None
    mine = (await stack.http.get("/v1/booking/mine", headers=person)).json()
    assert [item["id"] for item in mine] == [slot]


async def test_two_people_can_never_book_one_slot(stack: Stack) -> None:
    """V5.2.3. Both press at once: exactly one gets it."""
    await stack.ingest(bundle_for("fatima"))
    await stack.ingest(bundle_for("khalid"))
    first = await stack.sign_in("f-login", "fatima")
    second = await stack.sign_in("k-login", "khalid")
    async with stack.factory() as session:
        cases = {c.subject_id: c.id for c in (await session.scalars(select(CareCase))).all()}
    ids = {
        "first": (await stack.http.get("/v1/me", headers=first)).json()["id"],
        "second": (await stack.http.get("/v1/me", headers=second)).json()["id"],
    }
    slot = await publish(stack, await counsellor(stack))

    async def book(headers: dict[str, str], who: str) -> int:
        case_id = next(v for k, v in cases.items() if str(k) == ids[who])
        response = await stack.http.post(
            f"/v1/booking/slots/{slot}/book", json={"case_id": str(case_id)}, headers=headers
        )
        return response.status_code

    codes = await asyncio.gather(book(first, "first"), book(second, "second"))
    assert sorted(codes) == [200, 409]


async def test_nobody_books_for_someone_elses_case(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    case = await stack.only_case()
    stranger = await stack.sign_in("stranger")
    slot = await publish(stack, await counsellor(stack))
    response = await stack.http.post(
        f"/v1/booking/slots/{slot}/book", json={"case_id": str(case.id)}, headers=stranger
    )
    assert response.status_code == 404


async def test_overlapping_slots_and_odd_times_are_refused(stack: Stack) -> None:
    staff = await counsellor(stack)
    await publish(stack, staff, hours_ahead=30)
    clash = await stack.http.post(
        "/v1/booking/slots",
        json={
            "starts_at": (datetime.now(UTC) + timedelta(hours=30, minutes=10)).isoformat(),
            "minutes": 30,
        },
        headers=staff,
    )
    assert clash.status_code == 409
    past = await stack.http.post(
        "/v1/booking/slots",
        json={"starts_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat()},
        headers=staff,
    )
    assert past.status_code == 422


async def test_cancelling_reopens_the_slot_and_completing_moves_the_case(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    person = await stack.sign_in("f-login", "fatima")
    case = await stack.only_case()
    staff = await counsellor(stack)
    slot = await publish(stack, staff)
    await stack.http.post(
        f"/v1/booking/slots/{slot}/book", json={"case_id": str(case.id)}, headers=person
    )
    cancelled = await stack.http.post(f"/v1/booking/appointments/{slot}/cancel", headers=person)
    assert cancelled.status_code == 204
    again = await stack.http.post(
        f"/v1/booking/slots/{slot}/book", json={"case_id": str(case.id)}, headers=person
    )
    assert again.status_code == 200
    done = await stack.http.post(f"/v1/booking/appointments/{slot}/complete", headers=staff)
    assert done.status_code == 204
    async with stack.factory() as session:
        row = await session.get(CareCase, case.id)
        assert row is not None and row.state == "COUNSELLING_DONE"


async def booked_and_done(stack: Stack) -> tuple[CareCase, dict[str, str]]:
    await stack.ingest(bundle_for("fatima"))
    person = await stack.sign_in("f-login", "fatima")
    case = await stack.only_case()
    staff = await counsellor(stack)
    slot = await publish(stack, staff)
    await stack.http.post(
        f"/v1/booking/slots/{slot}/book", json={"case_id": str(case.id)}, headers=person
    )
    await stack.http.post(f"/v1/booking/appointments/{slot}/complete", headers=staff)
    # No manual outbox drain here: booking must apply the counsellor's access itself.
    return case, staff


async def test_a_referral_is_valid_fhir_with_only_the_agreed_fields(stack: Stack) -> None:
    """V5.2.1 and V5.2.2."""
    case, staff = await booked_and_done(stack)
    made = await stack.http.post(
        f"/v1/cases/{case.id}/referrals",
        json={"kind": "confirmatory_lab", "destination": "Regional genetics laboratory"},
        headers=staff,
    )
    assert made.status_code == 201, made.text
    body = made.json()
    ServiceRequest.model_validate(body["service_request"])
    Task.model_validate(body["task"])
    assert set(body["service_request"]) <= SERVICE_REQUEST_FIELDS
    assert set(body["task"]) <= TASK_FIELDS
    text = json.dumps(body)
    for private in ("HBB", "Fatima", "784-", "carrier", "thalass", str(case.subject_id)):
        assert private not in text


async def test_sending_a_referral_moves_the_case_and_traces_the_step(stack: Stack) -> None:
    """V5.2.5: the result-to-referral timeline, with the FHIR reference on the step."""
    case, staff = await booked_and_done(stack)
    made = (
        await stack.http.post(
            f"/v1/cases/{case.id}/referrals",
            json={"kind": "confirmatory_lab", "destination": "Regional genetics laboratory"},
            headers=staff,
        )
    ).json()
    sent = await stack.http.post(f"/v1/referrals/{made['id']}/send", headers=staff)
    assert sent.status_code == 200, sent.text
    assert sent.json()["service_request"]["status"] == "active"
    async with stack.factory() as session:
        row = await session.get(CareCase, case.id)
        assert row is not None and row.state == "CONFIRMATORY_TEST_ORDERED"
        steps = (
            await session.scalars(
                select(PathwayStep).where(PathwayStep.case_id == case.id).order_by(PathwayStep.at)
            )
        ).all()
    assert steps[0].to_state == "RESULT_RELEASED"
    assert steps[-1].fhir_ref == f"ServiceRequest/{made['id']}"
    twice = await stack.http.post(f"/v1/referrals/{made['id']}/send", headers=staff)
    assert twice.status_code == 409


async def test_only_the_assigned_counsellor_handles_referrals(stack: Stack) -> None:
    case, _ = await booked_and_done(stack)
    other = await counsellor(stack, "counsellor-2")
    response = await stack.http.post(
        f"/v1/cases/{case.id}/referrals",
        json={"kind": "confirmatory_lab", "destination": "Somewhere"},
        headers=other,
    )
    assert response.status_code == 404


async def test_the_centre_finder_needs_no_account_and_never_invents_entries(stack: Stack) -> None:
    """V5.2.6. Both packs' lists are empty until filled from a public source, and say so."""
    public = await stack.http.get("/v1/centres")
    assert public.status_code == 200
    body = public.json()
    assert body["centres"] == [] and body["as_of"] is None
    india = (await stack.http.get("/v1/centres?pack=in-india")).json()
    assert india["qualified_human"] == "none"
    assert (await stack.http.get("/v1/centres?pack=xx-nowhere")).status_code == 404
