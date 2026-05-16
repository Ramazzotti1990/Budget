from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class FXRate(db.Model):
    """Daily UYU/USD snapshot, BCU by default."""

    __tablename__ = "fx_rate"
    __table_args__ = (
        UniqueConstraint("date", "source", name="uq_fx_rate_date_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    uyu_per_usd: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="bcu", nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
