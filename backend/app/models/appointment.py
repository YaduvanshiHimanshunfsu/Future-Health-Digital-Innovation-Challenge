import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AppointmentMode, AppointmentStatus, one_of


class Appointment(Base):
    __tablename__ = "appointment"
    __table_args__ = (
        one_of("status", AppointmentStatus),
        one_of("mode", AppointmentMode),
        # The database, not application code, is what stops two people booking one slot.
        Index(
            "uq_appointment_counsellor_slot",
            "counsellor_id",
            "starts_at",
            unique=True,
            postgresql_where=text("status <> 'cancelled'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    counsellor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"))
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("care_case.id"), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mode: Mapped[str] = mapped_column(String(16))
    lang: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(16), default=AppointmentStatus.OPEN.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
