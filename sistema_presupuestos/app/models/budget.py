from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Budget(db.Model):
    """Container that groups all versions for a single project quote."""

    __tablename__ = "budget"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    current_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("budget_version.id", use_alter=True, name="fk_budget_current_ver"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    versions: Mapped[list[BudgetVersion]] = relationship(
        back_populates="budget",
        foreign_keys="BudgetVersion.budget_id",
        cascade="all, delete-orphan",
    )


class BudgetVersion(db.Model):
    """A snapshot of a budget at a point in time.

    ``locked_at`` is set when the budget moves out of ``draft`` — at that
    moment ``fx_rate_uyu_usd`` is captured so re-opening the version later
    still recomputes to the original total.
    """

    __tablename__ = "budget_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    budget_id: Mapped[int] = mapped_column(ForeignKey("budget.id"), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)

    labor_param_id: Mapped[int | None] = mapped_column(ForeignKey("labor_param.id"))
    fx_rate_uyu_usd: Mapped[float] = mapped_column(Float, nullable=False, default=41.5)
    contingency_pct: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    margin_pct: Mapped[float] = mapped_column(Float, default=30.0, nullable=False)

    locked_at: Mapped[datetime | None] = mapped_column(DateTime)
    locked_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    budget: Mapped[Budget] = relationship(
        back_populates="versions", foreign_keys=[budget_id]
    )
    line_items: Mapped[list[LineItem]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )


class LineItem(db.Model):
    """One rubro selection inside a budget version (snapshotted price)."""

    __tablename__ = "line_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    budget_version_id: Mapped[int] = mapped_column(
        ForeignKey("budget_version.id"), nullable=False
    )
    rubro_id: Mapped[int] = mapped_column(ForeignKey("rubro.id"), nullable=False)
    material_id: Mapped[int] = mapped_column(ForeignKey("material.id"), nullable=False)
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price_usd_snapshot: Mapped[float] = mapped_column(Float, nullable=False)

    version: Mapped[BudgetVersion] = relationship(back_populates="line_items")
    rubro: Mapped[Rubro] = relationship()  # type: ignore[name-defined]  # noqa: F821
    material: Mapped[Material] = relationship()  # type: ignore[name-defined]  # noqa: F821

    @property
    def total_usd(self) -> float:
        return self.qty * self.unit_price_usd_snapshot
