"""Verify the studio bootstrap path lays down a usable catalog."""
from __future__ import annotations

from app.extensions import db
from app.models.labor import LaborParam
from app.models.material import Material, Rubro
from app.models.studio import Studio
from app.services.calc import DEFAULT_RUBROS
from app.services.seed import seed_studio_defaults


def test_seed_creates_full_catalog(app):
    with app.app_context():
        studio = Studio(slug="sarachaga", name="Estudio Sarachaga")
        db.session.add(studio)
        db.session.commit()

        seed_studio_defaults(studio)

        rubros = db.session.query(Rubro).filter_by(studio_id=studio.id).all()
        assert len(rubros) == len(DEFAULT_RUBROS)
        for rubro in rubros:
            materials = db.session.query(Material).filter_by(rubro_id=rubro.id).all()
            assert materials, f"Rubro {rubro.code} has no materials"

        labor = db.session.query(LaborParam).filter_by(studio_id=studio.id).one()
        assert labor.jornal_uyu == 2953.0
        assert labor.auc_pct == 75.8


def test_seed_is_idempotent(app):
    with app.app_context():
        studio = Studio(slug="repeat", name="Repeat")
        db.session.add(studio)
        db.session.commit()

        seed_studio_defaults(studio)
        first_rubro_count = db.session.query(Rubro).count()
        first_material_count = db.session.query(Material).count()

        seed_studio_defaults(studio)
        assert db.session.query(Rubro).count() == first_rubro_count
        assert db.session.query(Material).count() == first_material_count
