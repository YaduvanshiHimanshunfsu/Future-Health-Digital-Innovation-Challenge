from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """Append-only and hash-chained. See app.privacy.audit for how rows are written and verified."""

    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_resource_seq", "resource", "seq"),)

    # Assigned by the chain writer, not a sequence, so a rolled-back write can't leave a gap that
    # would look the same as a deleted row.
    seq: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    resource: Mapped[str] = mapped_column(String(128))
    outcome: Mapped[str] = mapped_column(String(16))
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB)
    prev_hash: Mapped[str] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64), unique=True)
