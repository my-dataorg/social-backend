import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    venue_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    author_id: Mapped[str] = mapped_column(String(64))
    body: Mapped[str] = mapped_column(String(2000))
    post_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    checkin_id: Mapped[str | None] = mapped_column(String(36), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
