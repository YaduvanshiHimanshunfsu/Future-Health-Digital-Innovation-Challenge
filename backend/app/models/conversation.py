import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AnswerSource, Boundary, one_of


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"), index=True)
    lang: Mapped[str] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "message"
    __table_args__ = (one_of("boundary", Boundary), one_of("source", AnswerSource))

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversation.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content_enc: Mapped[bytes] = mapped_column(LargeBinary)
    boundary: Mapped[str | None] = mapped_column(String(32))
    source: Mapped[str | None] = mapped_column(String(16))
    # Kept for the AI safety dashboard. Flags name the rule that fired, never the text.
    validator_flags: Mapped[list[str]] = mapped_column(ARRAY(String(48)), default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
