"""Counselling appointments on an internal calendar (the prototype has no outside calendar).

A counsellor publishes open slots. A person books one for their own case, which moves the case to
COUNSELLING_BOOKED and, if nobody has taken the case yet, gives it to that slot's counsellor.

Double booking is impossible, not just unlikely (V5.2.3): a slot is taken by one conditional UPDATE
("only if it's still open"), so of two people pressing at once exactly one gets it, and the
database's unique index on a counsellor's start time backs that up.
"""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Literal

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.country_packs.loader import CountryPack
from app.models.appointment import Appointment
from app.models.case import CareCase
from app.models.counsellor import CounsellorProfile
from app.models.enums import AppointmentStatus, CaseState
from app.models.person import Person
from app.pathway.service import advance, can_move
from app.privacy.audit import AuditTrail
from app.triage import assignment

LENGTHS_MINUTES = (30, 45, 60)
FURTHEST_AHEAD = timedelta(days=90)
# How far ahead "free soon" looks: later today, or tomorrow morning.
SOON = timedelta(hours=24)

Status = Literal["in_session", "free_soon", "free_later", "no_times"]


@dataclass(frozen=True)
class Availability:
    status: Status
    next_open: datetime | None


def availability(calendar: Iterable[Appointment], now: datetime) -> Availability:
    """A counsellor's status, from their own calendar and nothing else.

    "In a session" means a booking covers this moment. It never says with whom: the person seeing
    it learns that the counsellor is busy, not anything about the other client. There's no
    "online" status, because nothing here tracks who is at a screen, and none is invented.
    """
    rows = list(calendar)
    busy = any(
        row.status == AppointmentStatus.BOOKED.value and row.starts_at <= now < row.ends_at
        for row in rows
    )
    upcoming = sorted(
        row.starts_at
        for row in rows
        if row.status == AppointmentStatus.OPEN.value and row.starts_at > now
    )
    next_open = upcoming[0] if upcoming else None
    if busy:
        return Availability("in_session", next_open)
    if next_open is not None:
        return Availability("free_soon" if next_open - now <= SOON else "free_later", next_open)
    return Availability("no_times", None)


async def team(
    db: AsyncSession, *, pack_code: str, now: datetime | None = None
) -> list[tuple[CounsellorProfile, Availability]]:
    """The counsellors who work in this country, each with their status, in a fixed order."""
    moment = now or datetime.now(UTC)
    profiles = (
        await db.scalars(
            select(CounsellorProfile)
            .join(Person, Person.id == CounsellorProfile.person_id)
            .where(Person.pack_code == pack_code)
            .order_by(CounsellorProfile.display_name)
        )
    ).all()
    if not profiles:
        return []
    rows = (
        await db.scalars(
            select(Appointment).where(
                Appointment.counsellor_id.in_([p.person_id for p in profiles]),
                Appointment.status.in_(
                    [AppointmentStatus.OPEN.value, AppointmentStatus.BOOKED.value]
                ),
                Appointment.ends_at > moment,
                Appointment.starts_at < moment + FURTHEST_AHEAD,
            )
        )
    ).all()
    return [
        (profile, availability((r for r in rows if r.counsellor_id == profile.person_id), moment))
        for profile in profiles
    ]


async def publish(
    db: AsyncSession,
    *,
    counsellor_id: uuid.UUID,
    starts_at: datetime,
    minutes: int,
    mode: str,
    lang: str,
    now: datetime | None = None,
) -> Appointment:
    moment = now or datetime.now(UTC)
    if minutes not in LENGTHS_MINUTES:
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "unsupported_length")
    if starts_at.tzinfo is None:
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "time_zone_required")
    if not moment < starts_at < moment + FURTHEST_AHEAD:
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, "outside_booking_window")
    ends_at = starts_at + timedelta(minutes=minutes)
    clash = await db.scalar(
        select(Appointment.id).where(
            Appointment.counsellor_id == counsellor_id,
            Appointment.status != AppointmentStatus.CANCELLED.value,
            and_(Appointment.starts_at < ends_at, Appointment.ends_at > starts_at),
        )
    )
    if clash is not None:
        raise ApiError(HTTPStatus.CONFLICT, "overlapping_slot")
    slot = Appointment(
        counsellor_id=counsellor_id,
        starts_at=starts_at,
        ends_at=ends_at,
        mode=mode,
        lang=lang,
        status=AppointmentStatus.OPEN.value,
    )
    db.add(slot)
    await db.flush()
    return slot


async def open_slots(
    db: AsyncSession,
    *,
    case: CareCase | None,
    pack_code: str,
    now: datetime | None = None,
) -> list[Appointment]:
    """Open future slots with counsellors in the person's own country.

    Once a case has a counsellor, only that counsellor's slots are offered.
    """
    moment = now or datetime.now(UTC)
    query = (
        select(Appointment)
        .join(Person, Person.id == Appointment.counsellor_id)
        .where(
            Appointment.status == AppointmentStatus.OPEN.value,
            Appointment.starts_at > moment,
            # A counsellor works under one country's rules, so nobody is offered one from another.
            Person.pack_code == pack_code,
        )
    )
    if case is not None and case.counsellor_id is not None:
        query = query.where(Appointment.counsellor_id == case.counsellor_id)
    return list((await db.scalars(query.order_by(Appointment.starts_at).limit(50))).all())


async def book(
    db: AsyncSession,
    audit: AuditTrail,
    *,
    slot_id: uuid.UUID,
    case: CareCase,
    actor: str,
    pack: CountryPack,
    now: datetime | None = None,
) -> Appointment:
    moment = now or datetime.now(UTC)
    existing = await db.scalar(
        select(Appointment.id).where(
            Appointment.case_id == case.id, Appointment.status == AppointmentStatus.BOOKED.value
        )
    )
    if existing is not None:
        raise ApiError(HTTPStatus.CONFLICT, "already_booked")
    slot = await db.get(Appointment, slot_id)
    if slot is None or slot.starts_at <= moment:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    counsellor = await db.get(Person, slot.counsellor_id)
    if counsellor is None or counsellor.pack_code != pack.code:
        # The same answer as a slot that doesn't exist: a guessed ID from another country gets nothing.
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    if case.counsellor_id is not None and slot.counsellor_id != case.counsellor_id:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")

    # Getting to "booked" may need "requested" first, for someone booking straight from a result.
    if not can_move(case, CaseState.COUNSELLING_BOOKED):
        if not can_move(case, CaseState.COUNSELLING_REQUESTED):
            raise ApiError(HTTPStatus.CONFLICT, "invalid_transition")
        await advance(db, case, CaseState.COUNSELLING_REQUESTED, actor=actor, pack=pack, now=moment)

    taken = await db.execute(
        update(Appointment)
        .where(Appointment.id == slot_id, Appointment.status == AppointmentStatus.OPEN.value)
        .values(status=AppointmentStatus.BOOKED.value, case_id=case.id)
        .execution_options(synchronize_session=False)
    )
    if taken.rowcount != 1:  # type: ignore[attr-defined]
        raise ApiError(HTTPStatus.CONFLICT, "slot_taken")
    await db.refresh(slot)

    if case.counsellor_id is None:
        await assignment.claim(db, audit, actor=actor, case=case, counsellor_id=slot.counsellor_id)
    await advance(db, case, CaseState.COUNSELLING_BOOKED, actor=actor, pack=pack, now=moment)
    await audit.append(
        db, actor=actor, action="booking.book", resource=f"case:{case.id}", meta={"mode": slot.mode}
    )
    return slot


async def cancel(
    db: AsyncSession,
    audit: AuditTrail,
    *,
    appointment: Appointment,
    case: CareCase,
    actor: str,
    pack: CountryPack,
) -> None:
    """The slot opens again for someone else, and the case goes back to waiting for a booking."""
    if appointment.status != AppointmentStatus.BOOKED.value:
        raise ApiError(HTTPStatus.CONFLICT, "not_booked")
    appointment.status = AppointmentStatus.OPEN.value
    appointment.case_id = None
    if can_move(case, CaseState.COUNSELLING_REQUESTED):
        await advance(db, case, CaseState.COUNSELLING_REQUESTED, actor=actor, pack=pack)
    await audit.append(db, actor=actor, action="booking.cancel", resource=f"case:{case.id}")


async def complete(
    db: AsyncSession,
    audit: AuditTrail,
    *,
    appointment: Appointment,
    case: CareCase,
    actor: str,
    pack: CountryPack,
) -> None:
    if appointment.status != AppointmentStatus.BOOKED.value:
        raise ApiError(HTTPStatus.CONFLICT, "not_booked")
    appointment.status = AppointmentStatus.COMPLETED.value
    await advance(db, case, CaseState.COUNSELLING_DONE, actor=actor, pack=pack)
    await audit.append(
        db,
        actor=actor,
        action="booking.complete",
        resource=f"case:{case.id}",
        meta={"actor_kind": "counsellor"},
    )
