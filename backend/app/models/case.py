import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CaseState, Priority, one_of


class CareCase(Base):
    __tablename__ = "care_case"
    __table_args__ = (
        one_of("priority", Priority),
        one_of("state", CaseState),
        Index("ix_care_case_queue", "counsellor_id", "state", "priority", "step_due"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"), index=True)
    couple_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("couple.id"), index=True)
    # Null means the case is waiting in the unassigned pool.
    counsellor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("person.id"))
    priority: Mapped[str] = mapped_column(String(2))
    # Why the case has its priority ("pregnant", "shared gene"), so it's encrypted.
    reasons_enc: Mapped[bytes] = mapped_column(LargeBinary)
    state: Mapped[str] = mapped_column(String(32), default=CaseState.RESULT_RELEASED.value)
    # The deadline for the current step. Reset on every transition.
    step_due: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    stalled: Mapped[bool] = mapped_column(Boolean, default=False)
    # When this step's one reminder went out. Cleared on every transition, so each step gets one.
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __mapper_args__ = {"version_id_col": version}  # noqa: RUF012


class PathwayStep(Base):
    __tablename__ = "pathway_step"
    __table_args__ = (one_of("to_state", CaseState),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("care_case.id"), index=True)
    from_state: Mapped[str | None] = mapped_column(String(32))
    to_state: Mapped[str] = mapped_column(String(32))
    actor: Mapped[str] = mapped_column(String(64))
    fhir_ref: Mapped[str | None] = mapped_column(String(128))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
