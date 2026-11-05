import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    current_person,
    get_audit,
    get_cipher,
    get_db,
    get_packs,
    require_service_consent,
)
from app.core.errors import ApiError
from app.core.rate_limit import rate_limit
from app.core.security import Principal, get_principal
from app.country_packs.loader import PackRegistry
from app.explain import graph
from app.explain.context import own_facts
from app.models.conversation import Conversation, Message
from app.models.enums import Boundary
from app.models.person import Person
from app.privacy.audit import AuditTrail
from app.privacy.crypto import FieldCipher
from app.schemas.chat import ChatIn, ChatOut, ContactOut
from app.triage.scoring import score
from app.triage.service import open_or_escalate

router = APIRouter(tags=["chat"])


def message_aad(message_id: uuid.UUID) -> str:
    return f"message:{message_id}:content"


@router.post("/chat", response_model=ChatOut, dependencies=[Depends(rate_limit("chat", 20, 60))])
async def chat(
    request: Request,
    body: ChatIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    packs: PackRegistry = Depends(get_packs),
) -> ChatOut:
    require_service_consent(person)
    pack = packs.require(person.pack_code)
    conversation: Conversation | None = None
    if body.conversation_id is not None:
        conversation = await db.scalar(
            select(Conversation).where(
                Conversation.id == body.conversation_id, Conversation.person_id == person.id
            )
        )
        if conversation is None:
            raise ApiError(HTTPStatus.NOT_FOUND, "not_found")

    facts = await own_facts(db, cipher, person, pack)
    language, level = person.preferred_lang, person.literacy_level
    # Nothing holds a transaction open while the answer is worked out (H9).
    await db.commit()

    result = await graph.answer(body.message, language, level, facts, pack, request.app.state.llm)

    if conversation is None:
        conversation = Conversation(id=uuid.uuid4(), person_id=person.id, lang=language)
        db.add(conversation)
        await db.flush()
    for role, text, boundary in (
        ("user", body.message, None),
        ("assistant", result.text, result.boundary),
    ):
        message_id = uuid.uuid4()
        db.add(
            Message(
                id=message_id,
                conversation_id=conversation.id,
                role=role,
                content_enc=await cipher.encrypt_json(text, aad=message_aad(message_id)),
                boundary=boundary.value if boundary else None,
                source=result.source.value if role == "assistant" else None,
                validator_flags=list(result.flags) if role == "assistant" else [],
            )
        )
    await db.flush()

    escalated = False
    if result.escalate and result.route is not None:
        triage = score(
            facts,
            distress=result.boundary is Boundary.DISTRESS,
            coercion=result.boundary is Boundary.COERCION,
            clinical_question=result.boundary is Boundary.CLINICAL_ADVICE,
            pregnant=result.route.pregnant,
        )
        if triage is not None:
            await open_or_escalate(
                db, cipher, audit, person=person, pack=pack, result=triage, actor=principal.sub
            )
            escalated = True
    await audit.append(
        db,
        actor=principal.sub,
        action="chat.answer",
        resource=f"person:{person.id}",
        meta={"boundary": result.boundary.value, "mode": result.source.value},
    )
    await db.commit()
    return ChatOut(
        conversation_id=conversation.id,
        answer=result.text,
        boundary=result.boundary.value,
        source=result.source.value,
        fact_ids=list(result.fact_ids),
        escalated=escalated,
        contacts=[ContactOut(**contact) for contact in result.contacts],
    )
