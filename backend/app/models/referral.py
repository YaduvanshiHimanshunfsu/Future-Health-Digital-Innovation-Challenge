import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ReferralKind, ReferralStatus, one_of


class Referral(Base):
    __tablename__ = "referral"
    __table_args__ = (one_of("kind", ReferralKind), one_of("status", ReferralStatus))

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("care_case.id"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"))
    kind: Mapped[str] = mapped_column(String(32))
    destination: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default=ReferralStatus.DRAFT.value)
    fhir_ref: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
