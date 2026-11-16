"""Booking, referrals and the centre finder. Checks V5.2.1 to V5.2.6."""

import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fhir.resources.servicerequest import ServiceRequest
from fhir.resources.task import Task
from sqlalchemy import select

from app.models.appointment import Appointment
from app.models.case import CareCase, PathwayStep
from app.models.counsellor import CounsellorProfile
from app.models.person import Person
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
    # Who runs a slot is shown since 15 Nov 2026, by the user's decision. Anything about another
    # client is not: see the team tests below.
    staff_id = (await stack.http.get("/v1/me", headers=staff)).json()["id"]
    assert offered[0]["counsellor_id"] == staff_id

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


async def test_the_centre_finder_needs_no_account_and_marks_every_invented_entry(
    stack: Stack,
) -> None:
    """V5.2.6. Public. The demo centres are all fictional, say so, and carry no way to reach one."""
    public = await stack.http.get("/v1/centres")
    assert public.status_code == 200
    body = public.json()
    assert body["total"] == body["fictional_count"] == len(body["centres"]) > 0
    for centre in body["centres"]:
        assert centre["fictional"] is True
        assert (centre["contact"], centre["source_url"], centre["checked_on"]) == (None, None, None)
    # No real centre is shown, so there is no check date to report.
    assert body["as_of"] is None
    assert body["qualified_human"] == "counsellor"
    # The notice on screen reads "{name} settings are a draft", so the name has to come with it.
    assert (body["pack"], body["pack_name"]) == ("ae-abu-dhabi", "Abu Dhabi")
    # A region that is a place's name comes from the pack, never from the screens' own words.
    assert body["region_names"]["al-ain"] == "Al Ain"
    assert (await stack.http.get("/v1/centres?pack=xx-nowhere")).status_code == 404


async def test_centre_filters_narrow_the_list_and_the_order_is_never_a_ranking(
    stack: Stack,
) -> None:
    async def ids(query: str) -> list[str]:
        response = await stack.http.get(f"/v1/centres?{query}")
        assert response.status_code == 200
        return [centre["id"] for centre in response.json()["centres"]]

    everything = (await stack.http.get("/v1/centres")).json()
    # The pack's own region order, then city, then name: the same for everyone, bought by no one.
    order = stack.pack.strata.regions
    regions = [centre["region"] for centre in everything["centres"]]
    assert regions == sorted(regions, key=order.index)
    assert everything["regions"] == [name for name in order if name in set(regions)]
    assert [c["id"] for c in everything["centres"]] == [
        "ae-abu-dhabi-darb",
        "ae-abu-dhabi-lulua",
        "ae-abu-dhabi-nakhla",
        "ae-al-ain-ghaf",
        "ae-al-ain-samar",
        "ae-al-dhafra-sabkha",
    ]

    assert await ids("region=al-dhafra") == ["ae-al-dhafra-sabkha"]
    assert await ids("q=madinat") == ["ae-al-dhafra-sabkha"]
    assert await ids("q=GENETICS centre") == ["ae-abu-dhabi-nakhla"]
    video_only = "ae-abu-dhabi-darb"
    assert video_only in await ids("mode=video")
    assert video_only not in await ids("mode=in_person")
    # "Not checked" is not step-free: only an explicit yes passes.
    step_free = await ids("step_free=true")
    assert video_only not in step_free and "ae-al-dhafra-sabkha" not in step_free
    prenatal = await ids("service=prenatal_diagnosis")
    assert set(prenatal) == {"ae-abu-dhabi-nakhla", "ae-al-ain-samar"}
    assert await ids("region=al-dhafra&service=haemoglobin_clinic") == []
    # The full count stays, so a screen can say "0 of 6" rather than "none exist".
    narrowed = (await stack.http.get("/v1/centres?region=al-dhafra")).json()
    assert narrowed["total"] == everything["total"] == 6

    for bad in ("service=miracle_cure", "mode=teleport", "q=" + "x" * 61):
        assert (await stack.http.get(f"/v1/centres?{bad}")).status_code == 422


async def profile(
    stack: Stack, headers: dict[str, str], name: str, pack: str = "ae-abu-dhabi"
) -> str:
    pid = (await stack.http.get("/v1/me", headers=headers)).json()["id"]
    async with stack.factory() as session:
        person = await session.get(Person, uuid.UUID(pid))
        assert person is not None
        person.pack_code = pack
        session.add(
            CounsellorProfile(
                person_id=person.id,
                display_name=name,
                role="genetic_counsellor",
                languages=["ar", "en"],
                fictional=True,
            )
        )
        await session.commit()
    return str(pid)


async def test_the_team_shows_each_status_and_nothing_about_other_clients(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    person = await stack.sign_in("f-login", "fatima")
    case = await stack.only_case()
    soon = await counsellor(stack, "c-soon")
    busy = await counsellor(stack, "c-busy")
    idle = await counsellor(stack, "c-idle")
    ids = {
        "soon": await profile(stack, soon, "Aaliya Soon"),
        "busy": await profile(stack, busy, "Bilal Busy"),
        "idle": await profile(stack, idle, "Chandra Idle"),
    }
    await publish(stack, soon, hours_ahead=3)
    now = datetime.now(UTC)
    async with stack.factory() as session:
        # Another client's session, happening now. It has no case: it points at nobody.
        session.add(
            Appointment(
                counsellor_id=uuid.UUID(ids["busy"]),
                starts_at=now - timedelta(minutes=10),
                ends_at=now + timedelta(minutes=20),
                mode="in_person",
                lang="en",
                status="booked",
            )
        )
        await session.commit()

    response = await stack.http.get(f"/v1/booking/counsellors?case_id={case.id}", headers=person)
    assert response.status_code == 200, response.text
    team = {item["id"]: item for item in response.json()}
    assert team[ids["soon"]]["status"] == "free_soon"
    assert team[ids["busy"]]["status"] == "in_session"
    assert team[ids["idle"]]["status"] == "no_times"
    assert [item["display_name"] for item in response.json()] == [
        "Aaliya Soon",
        "Bilal Busy",
        "Chandra Idle",
    ]
    for item in response.json():
        assert set(item) == {
            "id",
            "display_name",
            "role",
            "languages",
            "fictional",
            "status",
            "next_open",
            "yours",
        }
    assert not any(item["yours"] for item in response.json())


async def test_the_team_refuses_someone_elses_case_and_needs_consent(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    await stack.ingest(bundle_for("khalid"))
    fatima = await stack.sign_in("f-login", "fatima")
    khalid = await stack.sign_in("k-login", "khalid")
    fatima_id = uuid.UUID((await stack.http.get("/v1/me", headers=fatima)).json()["id"])
    async with stack.factory() as session:
        case = (
            await session.scalars(select(CareCase).where(CareCase.subject_id == fatima_id))
        ).one()
    stolen = await stack.http.get(f"/v1/booking/counsellors?case_id={case.id}", headers=khalid)
    assert stolen.status_code == 404
    # Signed in but never agreed to the service: no team, as with results.
    stranger = stack.headers(sub="no-consent")
    await stack.http.post("/v1/me", json={}, headers=stranger)
    assert (await stack.http.get("/v1/booking/counsellors", headers=stranger)).status_code == 403


async def test_a_counsellor_from_another_country_is_never_offered_or_bookable(
    stack: Stack,
) -> None:
    """A counsellor works under one country's rules, so a slot ID from elsewhere gets nothing."""
    await stack.ingest(bundle_for("fatima"))
    person = await stack.sign_in("f-login", "fatima")
    case = await stack.only_case()
    abroad = await counsellor(stack, "c-abroad")
    await profile(stack, abroad, "Dina Abroad", pack="xx-elsewhere")
    slot = await publish(stack, abroad)

    offered = (await stack.http.get(f"/v1/booking/slots?case_id={case.id}", headers=person)).json()
    assert slot not in [item["id"] for item in offered]
    team = (await stack.http.get("/v1/booking/counsellors", headers=person)).json()
    assert "Dina Abroad" not in [item["display_name"] for item in team]
    booked = await stack.http.post(
        f"/v1/booking/slots/{slot}/book", json={"case_id": str(case.id)}, headers=person
    )
    assert booked.status_code == 404
