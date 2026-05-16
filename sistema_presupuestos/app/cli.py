"""Flask CLI commands.

Run with: ``flask <command>`` from the ``sistema_presupuestos`` directory
(make sure ``FLASK_APP=app:create_app`` is set).
"""
from __future__ import annotations

import click
from flask import Flask

from app.extensions import db
from app.models.studio import Studio
from app.models.user import User
from app.services.seed import seed_studio_defaults


def register_cli(app: Flask) -> None:
    @app.cli.command("bootstrap-studio")
    @click.option("--slug", required=True, help="Studio slug (e.g. sarachaga)")
    @click.option("--name", required=True, help="Studio display name")
    @click.option("--admin-email", required=True)
    @click.option("--admin-password", required=True)
    def bootstrap_studio(
        slug: str, name: str, admin_email: str, admin_password: str
    ) -> None:
        """Create a new studio + admin user + seeded catalog."""
        existing = db.session.query(Studio).filter_by(slug=slug).first()
        if existing:
            click.echo(f"Studio {slug!r} already exists (id={existing.id})")
            studio = existing
        else:
            studio = Studio(slug=slug, name=name)
            db.session.add(studio)
            db.session.commit()
            click.echo(f"Created studio {slug!r} (id={studio.id})")

        seed_studio_defaults(studio)
        click.echo("Seeded rubros, materials, and labor params.")

        user = (
            db.session.query(User)
            .filter_by(studio_id=studio.id, email=admin_email)
            .first()
        )
        if user:
            click.echo(f"Admin {admin_email!r} already exists.")
            return

        user = User(studio_id=studio.id, email=admin_email, role="admin")
        user.set_password(admin_password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Created admin {admin_email!r} for studio {slug!r}.")
