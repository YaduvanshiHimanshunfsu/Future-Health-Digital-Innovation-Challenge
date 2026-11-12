import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AssessmentPhase, Instrument, one_of


class Assessment(Base):
    __tablename__ = "assessment"
    __table_args__ = (one_of("instrument", Instrument), one_of("phase", AssessmentPhase))

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"), index=True)
    instrument: Mapped[str] = mapped_column(String(16))
    phase: Mapped[str] = mapped_column(String(8))
    lang: Mapped[str] = mapped_column(String(8))
    score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
