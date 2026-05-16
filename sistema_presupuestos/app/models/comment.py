from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.utils import utc_now


class Comment(db.Model):
    """A note left on a budget version, by either a staff user or a client."""

    __tablename__ = "comment"

    id: Mapped[int] = mapped_column(primary_key=True)
    studio_id: Mapped[int] = mapped_column(ForeignKey("studio.id"), nullable=False)
    budget_version_id: Mapped[int] = mapped_column(
        ForeignKey("budget_version.id"), nullable=False
    )
    line_item_id: Mapped[int | None] = mapped_column(ForeignKey("line_item.id"))
    author_kind: Mapped[str] = mapped_column(String(10), nullable=False)
    author_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )
