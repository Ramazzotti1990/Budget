from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Rubro(db.Model):
    """One of the ~17 cost categories (Estructura, Cubierta, …)."""

    __tablename__ = "rubro"
    __table_args__ = (
        UniqueConstraint("studio_id", "code", name="uq_rubro_studio_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    studio_id: Mapped[int] = mapped_column(ForeignKey("studio.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    materials: Mapped[list[Material]] = relationship(
        back_populates="rubro", cascade="all, delete-orphan"
    )


class Material(db.Model):
    """A priced option that can be assigned to a rubro line item."""

    __tablename__ = "material"

    id: Mapped[int] = mapped_column(primary_key=True)
    rubro_id: Mapped[int] = mapped_column(ForeignKey("rubro.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    supplier: Mapped[str | None] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rubro: Mapped[Rubro] = relationship(back_populates="materials")
