from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Project(db.Model):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True)
    studio_id: Mapped[int] = mapped_column(ForeignKey("studio.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    location: Mapped[str | None] = mapped_column(String(160))
    casa_m2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    deck_m2: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    client: Mapped[Client] = relationship()  # type: ignore[name-defined]  # noqa: F821
