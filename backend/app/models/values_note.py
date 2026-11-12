import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ValuesNote(Base):
    """What a person said matters to them. Reflected back to them, and never scored."""

    __tablename__ = "values_note"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"), index=True)
    answers_enc: Mapped[bytes] = mapped_column(LargeBinary)
    # Set only when the person chooses to share these answers with their counsellor.
    shared_with_case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("care_case.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
