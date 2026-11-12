import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import OutboxOperation, one_of


class AuthzOutbox(Base):
    """OpenFGA changes, committed with the row that caused them and applied afterwards.

    Without this, a commit failing after the tuple write would leave access with no consent behind
    it (issue H7).
    """

    __tablename__ = "authz_outbox"
    __table_args__ = (
        one_of("operation", OutboxOperation),
        Index(
            "ix_authz_outbox_pending", "created_at", postgresql_where=text("applied_at IS NULL")
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    operation: Mapped[str] = mapped_column(String(8))
    subject: Mapped[str] = mapped_column(String(128))
    relation: Mapped[str] = mapped_column(String(64))
    object: Mapped[str] = mapped_column(String(128))
    # When the access this tuple gives runs out. OpenFGA enforces it, with no job needed.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
