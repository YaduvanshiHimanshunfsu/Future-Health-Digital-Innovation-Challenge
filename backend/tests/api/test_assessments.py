"""Understanding checks. Checks V5.3.1, V5.3.3 and V5.3.5."""

import pytest
from sqlalchemy import select

from app.assessments.instruments import OFFERED, SURE, TEACH_BACK, WRITTEN_IN
from app.assessments.scoring import BadAnswers, paired_change, score
from app.models.analytics import Event
from app.models.case import CareCase
from app.models.enums import Instrument
from tests.api.helpers import Stack, bundle_for

RIGHT = [item.correct for item in TEACH_BACK.items]
WRONG = [(answer + 1) % 3 for answer in RIGHT]  # type: ignore[operator]


def test_scoring_is_right_on_known_answers() -> None:
    """V5.3.1."""
    assert score(TEACH_BACK, RIGHT, "en").score == 1.0  # type: ignore[arg-type]
    assert score(TEACH_BACK, WRONG, "en").score == 0.0
    four = [*RIGHT[:4], WRONG[4]]
    assert score(TEACH_BACK, four, "en").passed  # type: ignore[arg-type]
    three = [*RIGHT[:3], *WRONG[3:]]
    assert not score(TEACH_BACK, three, "en").passed  # type: ignore[arg-type]
    assert score(SURE, [0, 0, 0, 0], "en").passed
    assert score(SURE, [0, 1, 0, 0], "en").score == 3.0
    with pytest.raises(BadAnswers):
        score(TEACH_BACK, [0, 0], "en")
    with pytest.raises(BadAnswers):
        score(TEACH_BACK, [9, 0, 0, 0, 0], "en")


def test_a_change_needs_both_scores() -> None:
    assert paired_change(0.4, 0.8) == pytest.approx(0.4)
    assert paired_change(None, 0.8) is None


def test_the_right_answer_isnt_always_in_the_same_place() -> None:
    assert len(set(RIGHT)) > 1


def test_every_item_is_written_in_every_language_the_questions_claim() -> None:
    """English only today. Each question has to exist in every language `WRITTEN_IN` names."""
    for instrument in OFFERED.values():
        for item in instrument.items:
            assert set(item.text) == set(WRITTEN_IN)
            assert all(item.options[language] for language in WRITTEN_IN)


@pytest.mark.db
async def test_questions_come_without_answers_and_say_what_they_are(stack: Stack) -> None:
    """V5.3.5. The adapted instrument says so wherever it's shown."""
    person = await stack.sign_in("someone")
    body = (await stack.http.get("/v1/assessments/sure?lang=ar", headers=person)).json()
    assert body["status"] == "adapted, not validated in Arabic"
    assert "correct" not in str(body)
    # Asked for in Arabic, answered in English, and the screen says so from this field.
    assert body["language_used"] == "en"
    arabic = (await stack.http.get("/v1/assessments/teach_back?lang=ar", headers=person)).json()
    assert arabic["language_used"] == "en"
    missing = await stack.http.get("/v1/assessments/mmic_adapted", headers=person)
    assert missing.status_code == 404


@pytest.mark.db
async def test_passing_after_reading_moves_the_journey_and_records_a_score(stack: Stack) -> None:
    await stack.ingest(bundle_for("fatima"))
    person = await stack.sign_in("f-login", "fatima")
    case = await stack.only_case()
    await stack.http.post(
        f"/v1/journey/{case.id}/steps", json={"to_state": "EDUCATION_VIEWED"}, headers=person
    )
    pre = await stack.http.post(
        "/v1/assessments/teach_back", json={"phase": "pre", "answers": WRONG}, headers=person
    )
    post = await stack.http.post(
        "/v1/assessments/teach_back", json={"phase": "post", "answers": RIGHT}, headers=person
    )
    assert pre.status_code == 201 and post.json()["passed"]
    async with stack.factory() as session:
        row = await session.get(CareCase, case.id)
        assert row is not None and row.state == "COMPREHENSION_CHECKED"
        kinds = (await session.scalars(select(Event.kind))).all()
    assert {"comprehension_pre", "comprehension_post"} <= set(kinds)
    mine = (await stack.http.get("/v1/assessments/mine", headers=person)).json()
    teach = next(item for item in mine if item["instrument"] == Instrument.TEACH_BACK.value)
    assert teach["change"] == pytest.approx(1.0)


@pytest.mark.db
async def test_two_missed_checks_bring_in_a_counsellor(stack: Stack) -> None:
    """V5.3.3."""
    person = await stack.sign_in("someone")
    first = await stack.http.post(
        "/v1/assessments/teach_back", json={"phase": "post", "answers": WRONG}, headers=person
    )
    assert first.json()["support_offered"] is False
    second = await stack.http.post(
        "/v1/assessments/teach_back", json={"phase": "post", "answers": WRONG}, headers=person
    )
    assert second.json()["support_offered"] is True
    case = await stack.only_case()
    assert case.priority == "P3"


@pytest.mark.db
async def test_invalid_answers_are_refused(stack: Stack) -> None:
    person = await stack.sign_in("someone")
    response = await stack.http.post(
        "/v1/assessments/teach_back", json={"phase": "post", "answers": [0]}, headers=person
    )
    assert response.status_code == 422
