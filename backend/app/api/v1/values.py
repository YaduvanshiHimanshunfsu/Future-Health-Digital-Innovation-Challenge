import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    current_person,
    deny,
    get_audit,
    get_cipher,
    get_db,
    require_service_consent,
)
from app.core.errors import ApiError
from app.core.security import Principal, get_principal
from app.decision.values import QUESTIONS, values_aad
from app.models.case import CareCase
from app.models.person import Person
from app.models.values_note import ValuesNote
from app.privacy.audit import AuditTrail
from app.privacy.crypto import FieldCipher
from app.schemas.options import ShareValuesIn, ValuesIn, ValuesOut

router = APIRouter(prefix="/values", tags=["values"])


async def _out(cipher: FieldCipher, note: ValuesNote) -> ValuesOut:
    answers = await cipher.decrypt_json(note.answers_enc, aad=values_aad(note.id))
    return ValuesOut(
        id=note.id,
        answers={key: str(answers.get(key, "")) for key in QUESTIONS},
        shared_with_case=note.shared_with_case_id is not None,
        created_at=note.created_at,
    )


async def _latest(db: AsyncSession, person: Person) -> ValuesNote | None:
    note: ValuesNote | None = await db.scalar(
        select(ValuesNote)
        .where(ValuesNote.person_id == person.id)
        .order_by(ValuesNote.created_at.desc())
        .limit(1)
    )
    return note


@router.get("", response_model=ValuesOut | None)
async def read_values(
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
) -> ValuesOut | None:
    require_service_consent(person)
    note = await _latest(db, person)
    return await _out(cipher, note) if note else None


@router.post("", response_model=ValuesOut, status_code=HTTPStatus.CREATED)
async def save_values(
    body: ValuesIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
) -> ValuesOut:
    """Each save is a new note. Earlier ones stay private, and are never shared by this."""
    require_service_consent(person)
    note_id = uuid.uuid4()
    note = ValuesNote(
        id=note_id,
        person_id=person.id,
        answers_enc=await cipher.encrypt_json(body.model_dump(), aad=values_aad(note_id)),
    )
    db.add(note)
    await db.flush()
    await audit.append(
        db, actor=principal.sub, action="values.save", resource=f"person:{person.id}"
    )
    await db.commit()
    await db.refresh(note)
    return await _out(cipher, note)


@router.post("/{note_id}/share", response_model=ValuesOut)
async def share_values(
    note_id: uuid.UUID,
    body: ShareValuesIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
) -> ValuesOut:
    """Only with the person's own case, and only when they ask."""
    note = await db.get(ValuesNote, note_id)
    case = await db.get(CareCase, body.case_id)
    if note is None or note.person_id != person.id or case is None or case.subject_id != person.id:
        await deny(audit, principal.sub, f"person:{person.id}")
    note.shared_with_case_id = case.id
    await db.flush()
    await audit.append(db, actor=principal.sub, action="values.share", resource=f"case:{case.id}")
    await db.commit()
    await db.refresh(note)
    return await _out(cipher, note)


@router.delete("/{note_id}/share", status_code=HTTPStatus.NO_CONTENT)
async def unshare_values(
    note_id: uuid.UUID,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    audit: AuditTrail = Depends(get_audit),
) -> None:
    note = await db.get(ValuesNote, note_id)
    if note is None or note.person_id != person.id:
        raise ApiError(HTTPStatus.NOT_FOUND, "not_found")
    if note.shared_with_case_id is None:
        return
    case_id = note.shared_with_case_id
    note.shared_with_case_id = None
    await db.flush()
    await audit.append(db, actor=principal.sub, action="values.unshare", resource=f"case:{case_id}")
    await db.commit()
