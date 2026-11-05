from typing import Any

import pytest
from sqlalchemy import select

from app.core.config import DEFAULT_PACKS_DIR
from app.country_packs.loader import load_pack
from app.decision.options import options_for
from app.models.case import CareCase
from tests.api.helpers import Stack, bundle_for

pytestmark = pytest.mark.db


async def staff(stack: Stack, sub: str, role: str) -> tuple[dict[str, str], str]:
    headers = stack.staff(sub, role)
    created = await stack.http.post("/v1/me", json={}, headers=headers)
    return headers, created.json()["id"]


async def test_a_p2_case_reaches_the_pool_and_can_be_claimed(stack: Stack) -> None:
    """V4.5.2, and the exit gate. In the original spec the queue was always empty (C9)."""
    await stack.ingest(bundle_for("x_carrier"))
    case = await stack.only_case()
    counsellor, _ = await staff(stack, "counsellor-1", "counsellor")

    pool = (await stack.http.get("/v1/cases?view=pool", headers=counsellor)).json()
    assert [item["id"] for item in pool] == [str(case.id)]
    assert pool[0]["priority"] == "P2"
    assert pool[0]["reasons"] == ["x_linked_carrier"]

    claimed = await stack.http.post(f"/v1/cases/{case.id}/claim", headers=counsellor)
    assert claimed.status_code == 200
    assert (await stack.http.get("/v1/cases?view=pool", headers=counsellor)).json() == []
    mine = (await stack.http.get("/v1/cases?view=mine", headers=counsellor)).json()
    assert [item["id"] for item in mine] == [str(case.id)]

    view = await stack.http.get(f"/v1/cases/{case.id}", headers=counsellor)
    assert view.status_code == 200
    assert view.json()["through_break_glass"] is False


async def test_other_counsellors_get_404_on_a_claimed_case(stack: Stack) -> None:
    """V4.5.3."""
    await stack.ingest(bundle_for("x_carrier"))
    case = await stack.only_case()
    first, _ = await staff(stack, "counsellor-1", "counsellor")
    second, _ = await staff(stack, "counsellor-2", "counsellor")
    await stack.http.post(f"/v1/cases/{case.id}/claim", headers=first)
    assert (await stack.http.get(f"/v1/cases/{case.id}", headers=second)).status_code == 404
    again = await stack.http.post(f"/v1/cases/{case.id}/claim", headers=second)
    assert again.status_code == 409


async def test_the_most_urgent_case_comes_first(stack: Stack) -> None:
    for persona in ("uncertain", "x_man", "x_carrier"):
        await stack.ingest(bundle_for(persona))
    counsellor, _ = await staff(stack, "counsellor-1", "counsellor")
    pool = (await stack.http.get("/v1/cases?view=pool", headers=counsellor)).json()
    assert [item["priority"] for item in pool] == ["P1", "P2", "P3"]


async def test_a_coordinator_can_move_a_case_and_access_follows(stack: Stack) -> None:
    await stack.ingest(bundle_for("x_carrier"))
    case = await stack.only_case()
    first, _ = await staff(stack, "counsellor-1", "counsellor")
    second, second_id = await staff(stack, "counsellor-2", "counsellor")
    coordinator, _ = await staff(stack, "coordinator", "program_admin")
    await stack.http.post(f"/v1/cases/{case.id}/claim", headers=first)

    moved = await stack.http.post(
        f"/v1/cases/{case.id}/assign", json={"counsellor_id": second_id}, headers=coordinator
    )
    assert moved.status_code == 204
    assert (await stack.http.get(f"/v1/cases/{case.id}", headers=second)).status_code == 200
    assert (await stack.http.get(f"/v1/cases/{case.id}", headers=first)).status_code == 404


async def test_people_and_physicians_cannot_use_the_queue(stack: Stack) -> None:
    person = await stack.sign_in("someone")
    doctor, _ = await staff(stack, "doctor", "physician")
    for headers in (person, doctor):
        assert (await stack.http.get("/v1/cases", headers=headers)).status_code == 403


async def test_the_summary_is_built_from_facts_and_says_verify(stack: Stack) -> None:
    """V4.5.7."""
    await stack.ingest(bundle_for("x_carrier"))
    case = await stack.only_case()
    counsellor, _ = await staff(stack, "counsellor-1", "counsellor")
    await stack.http.post(f"/v1/cases/{case.id}/claim", headers=counsellor)
    summary = (await stack.http.get(f"/v1/cases/{case.id}", headers=counsellor)).json()["summary"]
    assert summary["verify_before_use"] is True
    assert {fact["gene"] for fact in summary["facts"]} == {"DMD"}
    assert summary["values"] is None


async def test_values_reach_a_counsellor_only_when_shared(stack: Stack) -> None:
    """V4.4.4."""
    await stack.ingest(bundle_for("x_carrier"))
    person = await stack.sign_in("x-login", "x_carrier")
    case = await stack.only_case()
    counsellor, _ = await staff(stack, "counsellor-1", "counsellor")
    await stack.http.post(f"/v1/cases/{case.id}/claim", headers=counsellor)

    saved = await stack.http.post(
        "/v1/values",
        json={"what_matters": "Time with family", "worries": "My sisters"},
        headers=person,
    )
    assert saved.status_code == 201
    note_id = saved.json()["id"]
    summary = (await stack.http.get(f"/v1/cases/{case.id}", headers=counsellor)).json()["summary"]
    assert summary["values"] is None

    shared = await stack.http.post(
        f"/v1/values/{note_id}/share", json={"case_id": str(case.id)}, headers=person
    )
    assert shared.status_code == 200
    summary = (await stack.http.get(f"/v1/cases/{case.id}", headers=counsellor)).json()["summary"]
    assert summary["values"]["what_matters"] == "Time with family"

    await stack.http.delete(f"/v1/values/{note_id}/share", headers=person)
    summary = (await stack.http.get(f"/v1/cases/{case.id}", headers=counsellor)).json()["summary"]
    assert summary["values"] is None


async def test_values_cannot_be_shared_with_someone_elses_case(stack: Stack) -> None:
    await stack.ingest(bundle_for("x_carrier"))
    case = await stack.only_case()
    stranger = await stack.sign_in("stranger")
    saved = (
        await stack.http.post("/v1/values", json={"what_matters": "x"}, headers=stranger)
    ).json()
    response = await stack.http.post(
        f"/v1/values/{saved['id']}/share", json={"case_id": str(case.id)}, headers=stranger
    )
    assert response.status_code == 404


async def test_values_are_stored_encrypted(stack: Stack) -> None:
    from app.models.values_note import ValuesNote

    person = await stack.sign_in("someone")
    await stack.http.post(
        "/v1/values", json={"what_matters": "Faith matters to us"}, headers=person
    )
    async with stack.factory() as session:
        note = await session.scalar(select(ValuesNote))
    assert note is not None
    assert b"Faith" not in note.answers_enc


async def test_options_come_from_the_pack_with_equal_fields_and_no_ranking(stack: Stack) -> None:
    """V4.4.1 and V4.4.2."""
    person = await stack.sign_in("someone")
    body = (await stack.http.get("/v1/options", headers=person)).json()
    keys = [option["key"] for option in body["options"]]
    pack = load_pack(DEFAULT_PACKS_DIR / "ae-abu-dhabi")
    assert keys == [option.key for option in pack.options.options]
    assert {frozenset(option) for option in body["options"]} == {
        frozenset({"key", "title", "source", "note", "reviewed"})
    }
    assert body["order_is_not_a_ranking"] is True
    text = str(body).lower()
    assert "recommend" not in text and "best" not in text


async def test_options_differ_by_pack(stack: Stack) -> None:
    """V4.4.5."""
    from tests.api.helpers import INDIA

    abu_dhabi = await stack.sign_in("ad")
    india = await stack.sign_in("in", pack=INDIA)
    first = {
        o["key"] for o in (await stack.http.get("/v1/options", headers=abu_dhabi)).json()["options"]
    }
    second = {
        o["key"] for o in (await stack.http.get("/v1/options", headers=india)).json()["options"]
    }
    assert first != second


def test_values_can_never_change_the_options() -> None:
    """V4.4.3. Options take only the pack, so there is no path for values to reach them."""
    import inspect

    assert list(inspect.signature(options_for).parameters) == ["pack"]


async def test_triage_runs_from_results_match_and_chat(stack: Stack) -> None:
    """V4.5.6: results (ingest), the couple check and chat each open or raise a case."""
    await stack.ingest(bundle_for("uncertain"))
    assert (await stack.only_case()).priority == "P3"
    person = await stack.sign_in("u-login", "uncertain")
    await stack.http.post("/v1/chat", json={"message": "I can't go on"}, headers=person)
    assert (await stack.only_case()).priority == "P1"
    async with stack.factory() as session:
        assert len((await session.scalars(select(CareCase))).all()) == 1


async def test_queue_items_carry_no_identity(stack: Stack) -> None:
    await stack.ingest(bundle_for("x_carrier"))
    counsellor, _ = await staff(stack, "counsellor-1", "counsellor")
    pool: list[dict[str, Any]] = (
        await stack.http.get("/v1/cases?view=pool", headers=counsellor)
    ).json()
    assert set(pool[0]) == {"id", "priority", "state", "step_due", "reasons", "assigned_to_me"}
    assert "DMD" not in str(pool)
