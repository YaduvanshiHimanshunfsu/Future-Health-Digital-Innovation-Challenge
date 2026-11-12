import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CaseNote(Base):
    """A clinician's own notes. Nothing automated ever writes to this table."""

    __tablename__ = "case_note"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("care_case.id"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"))
    body_enc: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
