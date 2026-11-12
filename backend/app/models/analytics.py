import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Event(Base):
    """De-identified measurement events. There's deliberately no free-text column."""

    __tablename__ = "event"
    __table_args__ = (Index("ix_event_kind_at", "kind", "at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Keyed hash of the person's ID, so one person's events pair up without naming them.
    subject: Mapped[str | None] = mapped_column(String(32), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    pack_code: Mapped[str | None] = mapped_column(String(32))
    lang: Mapped[str | None] = mapped_column(String(8))
    literacy: Mapped[str | None] = mapped_column(String(8))
    region: Mapped[str | None] = mapped_column(String(32))
    age_band: Mapped[str | None] = mapped_column(String(8))
    gender: Mapped[str | None] = mapped_column(String(16))
    value: Mapped[float | None] = mapped_column(Float)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
