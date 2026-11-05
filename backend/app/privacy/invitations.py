import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invitation import Invitation
from app.models.person import Person
from app.privacy.audit import AuditTrail
from app.privacy.crypto import FieldCipher

LIFETIME = timedelta(days=30)
RELATIONS = frozenset({"parent", "child", "sibling", "cousin", "aunt_uncle", "other"})
# No claim about cost or eligibility, since neither is confirmed for any country (issue H13).
CONTENT_KEY = "invite.generic_screening_info"
_MIN_TOKEN = 20
_MAX_TOKEN = 64


def token_hash(key: bytes, token: str) -> str:
    return hmac.new(key, token.encode(), hashlib.sha256).hexdigest()


def relation_aad(invitation_id: uuid.UUID) -> str:
    return f"invitation:{invitation_id}:relation"


async def create(
    db: AsyncSession,
    cipher: FieldCipher,
    audit: AuditTrail,
    *,
    actor: str,
    sender: Person,
    relation: str,
    disclose_identity: bool,
    key: bytes,
    now: datetime,
) -> str:
    token = secrets.token_urlsafe(32)
    invitation_id = uuid.uuid4()
    db.add(
        Invitation(
            id=invitation_id,
            sender_id=sender.id,
            token_hash=token_hash(key, token),
            relation_enc=await cipher.encrypt_json(relation, aad=relation_aad(invitation_id)),
            disclose_identity=disclose_identity,
            expires_at=now + LIFETIME,
        )
    )
    await db.flush()
    await audit.append(db, actor=actor, action="invitation.create", resource=f"person:{sender.id}")
    return token


async def find_usable(
    db: AsyncSession, key: bytes, token: str, now: datetime, *, lock: bool = False
) -> Invitation | None:
    """Reused, expired and unknown links all come back as None, so they can't be told apart."""
    if not _MIN_TOKEN <= len(token) <= _MAX_TOKEN:
        return None
    query = select(Invitation).where(Invitation.token_hash == token_hash(key, token))
    invitation: Invitation | None = await db.scalar(query.with_for_update() if lock else query)
    if invitation is None or invitation.redeemed_at is not None or invitation.expires_at <= now:
        return None
    return invitation


async def page_for(cipher: FieldCipher, invitation: Invitation) -> dict[str, str | None]:
    """What the recipient sees. The sender stays out of it unless they chose otherwise."""
    relation: str | None = None
    if invitation.disclose_identity:
        relation = await cipher.decrypt_json(
            invitation.relation_enc, aad=relation_aad(invitation.id)
        )
    return {"content_key": CONTENT_KEY, "from_relation": relation}
