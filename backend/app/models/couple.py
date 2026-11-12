import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, LargeBinary, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Couple(Base):
    __tablename__ = "couple"
    __table_args__ = (CheckConstraint("person_a <> person_b", name="distinct_partners"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    person_a: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"), index=True)
    person_b: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("person.id"), index=True)
    invite_code_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    invite_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Self-reported relationship between the partners. Match consent lives in the consent ledger.
    details_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
