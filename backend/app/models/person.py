import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, LargeBinary, String, Uuid, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ReadingLevel, one_of


class Person(Base):
    __tablename__ = "person"
    __table_args__ = (
        one_of("literacy_level", ReadingLevel),
        CheckConstraint("keycloak_sub IS NOT NULL OR national_id_hash IS NOT NULL", name="has_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Null until first sign-in. A lab can report on someone who hasn't signed in yet.
    keycloak_sub: Mapped[str | None] = mapped_column(String(64), unique=True)
    national_id_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    pack_code: Mapped[str] = mapped_column(String(32))
    preferred_lang: Mapped[str] = mapped_column(String(8))
    literacy_level: Mapped[str] = mapped_column(String(8), default=ReadingLevel.SIMPLE.value)
    region: Mapped[str | None] = mapped_column(String(32))
    age_band: Mapped[str | None] = mapped_column(String(8))
    gender: Mapped[str | None] = mapped_column(String(16))
    # Sex and pregnancy status: encrypted JSON, needed by the risk rules and triage only.
    clinical_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    service_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Set when someone has stated they don't want to know their results.
    results_withheld_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # No reminders at all. Declining care also stops them, whatever this says.
    reminders_opt_out: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
