from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.utils import utc_now


class Studio(db.Model):
    __tablename__ = "studio"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    default_lang: Mapped[str] = mapped_column(String(2), default="es", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Studio {self.slug!r}>"
