from typing import Literal

from app.schemas.common import Out, StrictIn


class InviteIn(StrictIn):
    relation: Literal["parent", "child", "sibling", "cousin", "aunt_uncle", "other"]
    # Off by default: the recipient learns nothing about who sent this unless the sender says so.
    disclose_identity: bool = False


class InviteOut(Out):
    # Shown once. Only its hash is stored.
    token: str


class InvitePageOut(Out):
    content_key: str
    from_relation: str | None
