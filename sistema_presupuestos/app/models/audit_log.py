from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.utils import utc_now


class AuditLog(db.Model):
    """Every mutation worth retaining for compliance / debugging."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    studio_id: Mapped[int] = mapped_column(ForeignKey("studio.id"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"))
    entity: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    diff: Mapped[dict | None] = mapped_column(JSON)
    ts: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
