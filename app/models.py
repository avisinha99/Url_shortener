from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_links_original_url", "original_url"),)
