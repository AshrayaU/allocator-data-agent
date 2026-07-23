from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Investor(Base):
    """Local read-only cache of Allocator Admin API investors (GET /investors).

    Populated only by the manual sync task — never written to from the chat/
    LLM path. `raw` keeps the full original record since the vendored OpenAPI
    spec under-documents the item shape; pull out more typed columns here
    once the real response shape is confirmed against the live API.
    """

    __tablename__ = "investors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    remote_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    raw: Mapped[dict] = mapped_column(JSONB, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
