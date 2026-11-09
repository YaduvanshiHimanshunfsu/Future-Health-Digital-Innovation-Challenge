"""Programme metrics on the real database. Checks V5.4.2, V5.4.4, V5.4.5, V5.4.7 and V5.4.8."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import inspect

from app.models.analytics import Event
from app.models.case import CareCase, PathwayStep
from app.models.enums import CaseState as S
from app.models.person import Person
from tests.api.helpers import Stack

pytestmark = pytest.mark.db


async def add_cases(
    stack: Stack, count: int, path: list[S], *, priority: str = "P3", region: str = "abu-dhabi"
) -> None:
    start = datetime.now(UTC) - timedelta(days=10)
    async with stack.factory() as session:
        for _ in range(count):
            pid = uuid.uuid4()
            person = Person(
                id=pid,
                keycloak_sub=f"test:{pid}",
                pack_code="ae-abu-dhabi",
                preferred_lang="en",
                literacy_level="simple",
                region=region,
                age_band="25-34",
                gender="woman",
            )
            session.add(person)
            await session.flush()
            case = CareCase(
                subject_id=person.id,
                priority=priority,
                reasons_enc=b"x",
                state=path[-1].value,
                step_due=start,
            )
            session.add(case)
            await session.flush()
            for hours, state in enumerate(path):
                session.add(
                    PathwayStep(
                        case_id=case.id,
                        to_state=state.value,
                        actor="system:test",
                        at=start + timedelta(hours=hours * 24),
                    )
                )
        await session.commit()


async def overview(stack: Stack) -> dict:  # type: ignore[type-arg]
    admin = stack.staff("coordinator", "program_admin")
    response = await stack.http.get("/v1/analytics/overview", headers=admin)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


async def test_only_a_programme_administrator_sees_metrics(stack: Stack) -> None:
    for role in ("counsellor", "physician", "auditor"):
        headers = stack.staff(f"someone-{role}", role)
        assert (await stack.http.get("/v1/analytics/overview", headers=headers)).status_code == 403
    person = await stack.sign_in("someone")
    assert (await stack.http.get("/v1/analytics/overview", headers=person)).status_code == 403


async def test_the_dashboard_says_synthetic_and_names_its_sources(stack: Stack) -> None:
    """V5.4.7 and O5.4.1."""
    body = await overview(stack)
    assert body["synthetic"] is True
    assert {"funnel", "time_to_referral", "comprehension", "equity"} <= set(body["sources"])


async def test_escalated_cases_count_in_time_to_referral(stack: Stack) -> None:
    """V5.4.2. Urgent cases skip straight to counselling, and still count, from RESULT_RELEASED."""
    urgent = [
        S.RESULT_RELEASED,
        S.COUNSELLING_REQUESTED,
        S.COUNSELLING_BOOKED,
        S.COUNSELLING_DONE,
        S.CONFIRMATORY_TEST_ORDERED,
    ]
    await add_cases(stack, 12, urgent, priority="P1")
    body = await overview(stack)
    assert body["time_to_referral"]["cases"] == 12
    # Four steps a day apart: 96 hours from release to the referral step.
    assert body["time_to_referral"]["median_hours"] == 96.0
    p1 = next(item for item in body["time_to_counselling"] if item["key"] == "P1")
    assert p1["median_hours"] == 48.0 and p1["sla_hours"] == 24


async def test_small_numbers_are_withheld_everywhere(stack: Stack) -> None:
    """V5.4.4. Five cases is too few to show anything about them."""
    await add_cases(stack, 5, [S.RESULT_RELEASED, S.EDUCATION_VIEWED], region="al-ain")
    await add_cases(stack, 30, [S.RESULT_RELEASED], region="abu-dhabi")
    body = await overview(stack)
    funnel = {item["key"]: item["value"] for item in body["funnel"]}
    assert funnel["RESULT_RELEASED"] == 35
    assert funnel["EDUCATION_VIEWED"] is None
    cells = {(c["row"], c["column"]): c["value"] for c in body["heatmap"]}
    assert cells[("al-ain", "25-34")] is None
    region = next(
        e
        for e in body["equity"]
        if e["dimension"] == "region" and e["measure"] == "counselling_reached"
    )
    assert {g["group"]: g["n"] for g in region["groups"]}["al-ain"] is None


def test_events_have_no_free_text_column() -> None:
    """V5.4.5."""
    columns = {column.key: column.type for column in inspect(Event).columns}
    text_like = {
        name for name, kind in columns.items() if getattr(kind, "length", 0) and kind.length > 32
    }  # type: ignore[attr-defined]
    assert text_like == set()
    assert "note" not in columns and "text" not in columns


def test_no_metric_treats_a_choice_as_success() -> None:
    """V5.4.8. No field, event or measure is about marriages, or about any one reproductive choice."""
    from app.analytics.events import KINDS
    from app.schemas.analytics import AnalyticsOut

    words = " ".join(
        [*KINDS, *AnalyticsOut.model_fields, *(str(f) for f in AnalyticsOut.model_json_schema())]
    )
    for forbidden in ("marriage", "cancel", "prevent", "avoid", "terminat", "ivf"):
        assert forbidden not in words.lower()
