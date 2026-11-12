import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Attestation, one_of


class GeneticReport(Base):
    __tablename__ = "genetic_report"
    __table_args__ = (
        UniqueConstraint("source_lab", "source_report_id", "report_version"),
        one_of("attestation", Attestation),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"), index=True)
    source_lab: Mapped[str] = mapped_column(String(64))
    source_report_id: Mapped[str] = mapped_column(String(128))
    # A later version of a report supersedes the earlier one, for example when a variant is
    # reclassified. Findings from superseded versions stay for the record but aren't read.
    report_version: Mapped[int] = mapped_column(Integer, default=1)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    panel_version: Mapped[str] = mapped_column(String(32))
    bundle_sha256: Mapped[str] = mapped_column(String(64))
    attestation: Mapped[str] = mapped_column(String(16), default=Attestation.UNVERIFIED.value)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    findings: Mapped[list["CarrierFinding"]] = relationship(
        back_populates="report", lazy="selectin", cascade="all, delete-orphan"
    )


class CarrierFinding(Base):
    __tablename__ = "carrier_finding"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("genetic_report.id", ondelete="CASCADE"), index=True
    )
    # Gene, variant, classification, zygosity, inheritance and conditions. Even classification alone
    # reveals that someone has a finding, so nothing about the finding sits in the clear.
    payload_enc: Mapped[bytes] = mapped_column(LargeBinary)

    report: Mapped[GeneticReport] = relationship(back_populates="findings")
