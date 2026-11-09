"""Counselling appointments: counsellors publish slots, people book them for their own case.

A person sees when and how a slot runs, never who runs it, and books only for their own case
(404 for anyone else's). A counsellor sees and completes only their own appointments.
"""

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.events import pseudonym
from app.api.deps import current_person, get_audit, get_db, get_packs, require_service_consent
from app.booking import service
from app.core.config import decode_key
from app.core.errors import ApiError
from app.core.security import Principal, get_principal, require_role
from app.country_packs.loader import PackRegistry
from app.models.appointment import Appointment
from app.models.case import CareCase
from app.models.enums import AppointmentStatus, CaseState
from app.models.person import Person
from app.notifications.service import MockNotifier
from app.pathway.service import commit_or_conflict
from app.privacy.audit import AuditTrail
from app.privacy.outbox import drain_quietly
from app.schemas.booking import (
    AppointmentOut,
    BookIn,
    SlotIn,
    SlotOut,
    StaffAppointmentOut,
)

router = APIRouter(prefix="/booking", tags=["booking"])
# The prototype sends no real messages. One mock per process records what would have gone out.
NOTIFIER = MockNotifier()


async def _own_open_case(db: AsyncSession, person: Person, case_id: UUID) -> CareCase:
    case = await db.get(CareCase, case_id, with_for_update=True)
    if case is None or case.subject_id != person.id:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    if case.state == CaseState.CLOSED.value:
        raise ApiError(HTTPStatus.CONFLICT, "case_closed")
    return case


async def _tell(request: Request, person: Person) -> None:
    key = decode_key(request.app.state.settings.analytics_hmac_key, "ANALYTICS_HMAC_KEY")
    await NOTIFIER.send(pseudonym(key, person.id), "appointment", person.preferred_lang)


@router.post("/slots", response_model=SlotOut, status_code=HTTPStatus.CREATED)
async def publish_slot(
    body: SlotIn,
    principal: Principal = Depends(require_role("counsellor")),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
) -> SlotOut:
    slot = await service.publish(
        db,
        counsellor_id=person.id,
        starts_at=body.starts_at,
        minutes=body.minutes,
        mode=body.mode.value,
        lang=body.lang,
    )
    await db.commit()
    return SlotOut.model_validate(slot, from_attributes=True)


@router.get("/slots", response_model=list[SlotOut])
async def list_slots(
    case_id: UUID = Query(),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
) -> list[SlotOut]:
    require_service_consent(person)
    case = await db.get(CareCase, case_id)
    if case is None or case.subject_id != person.id:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    return [
        SlotOut.model_validate(slot, from_attributes=True)
        for slot in await service.open_slots(db, case=case)
    ]


@router.post("/slots/{slot_id}/book", response_model=AppointmentOut)
async def book_slot(
    request: Request,
    slot_id: UUID,
    body: BookIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> AppointmentOut:
    require_service_consent(person)
    case = await _own_open_case(db, person, body.case_id)
    booked: list[Appointment] = []

    async def work() -> None:
        booked.append(
            await service.book(
                db,
                audit,
                slot_id=slot_id,
                case=case,
                actor=principal.sub,
                pack=packs.require(person.pack_code),
            )
        )

    await commit_or_conflict(db, work)
    # Booking can hand the case to the slot's counsellor. Apply that access now, as claiming does,
    # rather than leaving it for the worker's next pass.
    await drain_quietly(request.app.state.session_factory, request.app.state.authz)
    await _tell(request, person)
    return AppointmentOut.model_validate(booked[0], from_attributes=True)


@router.get("/mine", response_model=list[AppointmentOut])
async def my_appointments(
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
) -> list[AppointmentOut]:
    require_service_consent(person)
    rows = (
        await db.scalars(
            select(Appointment)
            .join(CareCase, CareCase.id == Appointment.case_id)
            .where(CareCase.subject_id == person.id)
            .order_by(Appointment.starts_at)
        )
    ).all()
    return [AppointmentOut.model_validate(row, from_attributes=True) for row in rows]


@router.post("/appointments/{appointment_id}/cancel", status_code=HTTPStatus.NO_CONTENT)
async def cancel_appointment(
    request: Request,
    appointment_id: UUID,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> Response:
    """The person who booked it can cancel it, and so can the counsellor running it."""
    appointment = await db.get(Appointment, appointment_id, with_for_update=True)
    case = (
        await db.get(CareCase, appointment.case_id) if appointment and appointment.case_id else None
    )
    allowed = (
        case is not None
        and appointment is not None
        and (case.subject_id == person.id or appointment.counsellor_id == person.id)
    )
    if not allowed or appointment is None or case is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    subject = await db.get(Person, case.subject_id)
    pack = (packs.get(subject.pack_code) if subject else None) or packs.default

    async def work() -> None:
        await service.cancel(
            db, audit, appointment=appointment, case=case, actor=principal.sub, pack=pack
        )

    await commit_or_conflict(db, work)
    if subject is not None:
        await _tell(request, subject)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/schedule", response_model=list[StaffAppointmentOut])
async def my_schedule(
    principal: Principal = Depends(require_role("counsellor")),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
) -> list[StaffAppointmentOut]:
    rows = (
        await db.scalars(
            select(Appointment)
            .where(
                Appointment.counsellor_id == person.id,
                Appointment.status != AppointmentStatus.CANCELLED.value,
            )
            .order_by(Appointment.starts_at)
            .limit(200)
        )
    ).all()
    return [StaffAppointmentOut.model_validate(row, from_attributes=True) for row in rows]


@router.post("/appointments/{appointment_id}/complete", status_code=HTTPStatus.NO_CONTENT)
async def complete_appointment(
    appointment_id: UUID,
    principal: Principal = Depends(require_role("counsellor")),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> Response:
    appointment = await db.get(Appointment, appointment_id, with_for_update=True)
    if appointment is None or appointment.counsellor_id != person.id or appointment.case_id is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    case = await db.get(CareCase, appointment.case_id, with_for_update=True)
    if case is None:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    subject = await db.get(Person, case.subject_id)
    pack = (packs.get(subject.pack_code) if subject else None) or packs.default

    async def work() -> None:
        await service.complete(
            db, audit, appointment=appointment, case=case, actor=principal.sub, pack=pack
        )

    await commit_or_conflict(db, work)
    return Response(status_code=HTTPStatus.NO_CONTENT)
