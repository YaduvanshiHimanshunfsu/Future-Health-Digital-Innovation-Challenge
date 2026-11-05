from http import HTTPStatus

from fastapi import APIRouter, Depends, Path, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    current_person,
    get_audit,
    get_authz,
    get_cipher,
    get_db,
    get_redis,
    require_service_consent,
)
from app.core.config import decode_key
from app.core.errors import ApiError
from app.core.rate_limit import enforce, rate_limit
from app.core.security import Principal, get_principal
from app.models.person import Person
from app.privacy import invitations
from app.privacy.audit import AuditTrail
from app.privacy.authz import Authz
from app.privacy.crypto import FieldCipher
from app.schemas.invitations import InviteIn, InviteOut, InvitePageOut

router = APIRouter(prefix="/invitations", tags=["invitations"])

# Long enough for any genuine link, and short enough to refuse junk before touching the database.
Token = Path(min_length=1, max_length=128)
_UNAVAILABLE = ApiError(HTTPStatus.NOT_FOUND, "invitation_unavailable")


def _key(request: Request) -> bytes:
    return decode_key(request.app.state.settings.invite_hmac_key, "INVITE_HMAC_KEY")


async def _limit_public(request: Request, redis: Redis) -> None:
    client = request.client.host if request.client else "unknown"
    await enforce(redis, f"invite_public:{client}", 60, 60)


@router.post(
    "",
    status_code=HTTPStatus.CREATED,
    response_model=InviteOut,
    dependencies=[Depends(rate_limit("invite", 5, 86400))],
)
async def create(
    request: Request,
    body: InviteIn,
    principal: Principal = Depends(get_principal),
    person: Person = Depends(current_person),
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
) -> InviteOut:
    require_service_consent(person)
    token = await invitations.create(
        db,
        cipher,
        audit,
        actor=principal.sub,
        sender=person,
        relation=body.relation,
        disclose_identity=body.disclose_identity,
        key=_key(request),
        now=authz.clock(),
    )
    await db.commit()
    return InviteOut(token=token)


@router.get("/{token}", response_model=InvitePageOut)
async def view(
    request: Request,
    token: str = Token,
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    authz: Authz = Depends(get_authz),
    redis: Redis = Depends(get_redis),
) -> InvitePageOut:
    """Only shows the page. Messaging apps open links to build previews, so a GET can't use one up."""
    await _limit_public(request, redis)
    invitation = await invitations.find_usable(db, _key(request), token, authz.clock())
    if invitation is None:
        raise _UNAVAILABLE
    return InvitePageOut(**await invitations.page_for(cipher, invitation))


@router.post("/{token}/redeem", response_model=InvitePageOut)
async def redeem(
    request: Request,
    token: str = Token,
    db: AsyncSession = Depends(get_db),
    cipher: FieldCipher = Depends(get_cipher),
    audit: AuditTrail = Depends(get_audit),
    authz: Authz = Depends(get_authz),
    redis: Redis = Depends(get_redis),
) -> InvitePageOut:
    await _limit_public(request, redis)
    now = authz.clock()
    invitation = await invitations.find_usable(db, _key(request), token, now, lock=True)
    if invitation is None:
        raise _UNAVAILABLE
    invitation.redeemed_at = now
    page = await invitations.page_for(cipher, invitation)
    await db.flush()
    # Not filed under the sender, so their log can't show whether a relative followed the link.
    await audit.append(
        db, actor="public", action="invitation.redeem", resource=f"invitation:{invitation.id}"
    )
    await db.commit()
    return InvitePageOut(**page)
