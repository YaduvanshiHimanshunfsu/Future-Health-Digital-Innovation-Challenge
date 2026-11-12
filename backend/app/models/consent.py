import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ConsentKind, RevealLevel, one_of


class Consent(Base):
    """Every permission a person has given. Nothing is shared without a live row here."""

    __tablename__ = "consent"
    __table_args__ = (
        one_of("kind", ConsentKind),
        one_of("reveal_level", RevealLevel),
        CheckConstraint(
            "(kind = 'couple_match') = (couple_id IS NOT NULL AND reveal_level IS NOT NULL)",
            name="couple_match_fields",
        ),
        CheckConstraint(
            "kind NOT IN ('share_summary', 'share_full') OR "
            "(grantee_id IS NOT NULL AND expires_at IS NOT NULL)",
            name="share_needs_grantee_and_expiry",
        ),
        Index(
            "uq_consent_live_couple_match",
            "grantor_id",
            "couple_id",
            unique=True,
            postgresql_where=text("kind = 'couple_match' AND revoked_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    grantor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"), index=True)
    grantee_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("person.id"), index=True)
    couple_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("couple.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    reveal_level: Mapped[str | None] = mapped_column(String(8))
    purpose: Mapped[str] = mapped_column(String(32))
    terms_version: Mapped[str] = mapped_column(String(16))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
