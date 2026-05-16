"""Seed defaults into a freshly-created studio.

Used both by the install bootstrap and by tests that need a populated
catalog. Idempotent: re-running upserts on ``(studio_id, code)``.
"""
from __future__ import annotations

from datetime import date

from app.extensions import db
from app.models.labor import LaborParam
from app.models.material import Material, Rubro
from app.models.studio import Studio
from app.services.calc import DEFAULT_LABOR, DEFAULT_RUBROS


def seed_studio_defaults(studio: Studio) -> None:
    """Populate rubros, materials, and an initial LaborParam row.

    Skips rubros that already exist for this studio, so the function is
    safe to call repeatedly.
    """
    _seed_rubros(studio.id)
    _seed_labor_param(studio.id)
    db.session.commit()


def _seed_rubros(studio_id: int) -> None:
    existing_codes = {
        r.code for r in db.session.query(Rubro).filter_by(studio_id=studio_id).all()
    }

    for order, payload in enumerate(DEFAULT_RUBROS):
        if payload["code"] in existing_codes:
            continue

        rubro = Rubro(
            studio_id=studio_id,
            code=payload["code"],
            name=payload["name"],
            category=payload["category"],
            unit=payload["unit"],
            sort_order=order,
        )
        db.session.add(rubro)
        db.session.flush()

        for opt_id, label, desc, price in payload["options"]:
            db.session.add(
                Material(
                    rubro_id=rubro.id,
                    code=opt_id,
                    name=label,
                    description=desc,
                    price_usd=float(price),
                )
            )


def _seed_labor_param(studio_id: int) -> None:
    has_any = db.session.query(LaborParam).filter_by(studio_id=studio_id).first()
    if has_any:
        return

    db.session.add(
        LaborParam(
            studio_id=studio_id,
            effective_from=date.today(),
            **DEFAULT_LABOR,
        )
    )
