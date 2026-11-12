import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ContentStatus, ReadingLevel, one_of

EMBEDDING_DIMENSIONS = 1024


class KbChunk(Base):
    __tablename__ = "kb_chunk"
    __table_args__ = (
        one_of("level", ReadingLevel),
        one_of("status", ContentStatus),
        Index("ix_kb_chunk_lookup", "pack_code", "lang", "level", "condition_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Null for content shared by every pack.
    pack_code: Mapped[str | None] = mapped_column(String(32))
    condition_id: Mapped[str] = mapped_column(String(32))
    lang: Mapped[str] = mapped_column(String(8))
    level: Mapped[str] = mapped_column(String(8))
    text: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default=ContentStatus.DRAFT.value)
    reviewed_by: Mapped[str | None] = mapped_column(String(64))
    content_version: Mapped[str] = mapped_column(String(16))
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
