from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class LaborParam(db.Model):
    """Effective-dated history of labor parameters per studio.

    Budgets snapshot the ``id`` at finalization so re-opening a 2024 budget
    still recomputes with 2024 rates even if the studio later raises its
    jornal.
    """

    __tablename__ = "labor_param"

    id: Mapped[int] = mapped_column(primary_key=True)
    studio_id: Mapped[int] = mapped_column(ForeignKey("studio.id"), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    jornal_uyu: Mapped[float] = mapped_column(Float, nullable=False)
    viatico_uyu: Mapped[float] = mapped_column(Float, nullable=False)
    auc_pct: Mapped[float] = mapped_column(Float, nullable=False)
    j_per_m2_casa: Mapped[float] = mapped_column(Float, nullable=False)
    j_per_m2_deck: Mapped[float] = mapped_column(Float, nullable=False)
