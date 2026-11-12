import uuid
from datetime import date

from sqlalchemy import Date, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Centre(Base):
    __tablename__ = "centre"
    __table_args__ = (Index("ix_centre_pack_region", "pack_code", "region"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    pack_code: Mapped[str] = mapped_column(String(32))
    region: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(160))
    services: Mapped[str] = mapped_column(String(160))
    contact: Mapped[str | None] = mapped_column(String(160))
    source_url: Mapped[str] = mapped_column(String(512))
    checked_on: Mapped[date] = mapped_column(Date)
