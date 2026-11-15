import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CounsellorRole, one_of


class CounsellorProfile(Base):
    """What a person sees about a counsellor before booking: a name, a role and their languages.

    Kept apart from `person`, which holds no names for anyone. Only staff have a profile.
    """

    __tablename__ = "counsellor_profile"
    __table_args__ = (one_of("role", CounsellorRole),)

    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(32))
    languages: Mapped[list[str]] = mapped_column(ARRAY(String(8)))
    # An invented demo counsellor. Screens say so beside the name.
    fictional: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
