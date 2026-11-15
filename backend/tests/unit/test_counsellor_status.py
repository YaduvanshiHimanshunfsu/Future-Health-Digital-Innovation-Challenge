"""A counsellor's status comes from their own calendar, and says nothing about anyone else."""

import uuid
from datetime import UTC, datetime, timedelta

from app.booking.service import availability
from app.models.appointment import Appointment

NOW = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)


def slot(minutes_from_now: int, status: str = "open", length: int = 30) -> Appointment:
    start = NOW + timedelta(minutes=minutes_from_now)
    return Appointment(
        counsellor_id=uuid.uuid4(),
        starts_at=start,
        ends_at=start + timedelta(minutes=length),
        mode="video",
        lang="en",
        status=status,
    )


def test_a_booking_covering_now_means_in_a_session_and_still_gives_the_next_free_time() -> None:
    found = availability([slot(-10, "booked"), slot(120)], NOW)
    assert found.status == "in_session"
    assert found.next_open == NOW + timedelta(minutes=120)


def test_a_free_time_within_a_day_is_soon_and_after_that_later() -> None:
    assert availability([slot(23 * 60)], NOW).status == "free_soon"
    assert availability([slot(25 * 60)], NOW).status == "free_later"


def test_nothing_open_is_said_plainly() -> None:
    assert availability([], NOW).status == "no_times"
    # A booking that has finished, and a time that has started, offer nothing.
    assert availability([slot(-90, "booked"), slot(-5)], NOW).status == "no_times"


def test_cancelled_and_completed_times_count_for_nothing() -> None:
    assert availability([slot(-10, "cancelled"), slot(-10, "completed")], NOW).status == "no_times"


def test_the_next_free_time_is_the_earliest_one() -> None:
    assert availability([slot(300), slot(60), slot(180)], NOW).next_open == NOW + timedelta(
        minutes=60
    )
