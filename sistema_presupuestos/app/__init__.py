"""Flask application factory.

Usage:
    from app import create_app
    app = create_app()

Configuration is selected by the ``APP_ENV`` env var (``dev`` | ``test`` | ``prod``).
"""
from __future__ import annotations

import os

from flask import Flask

from app.config import CONFIG_MAP
from app.extensions import db, login_manager, mail, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    config_name = config_name or os.environ.get("APP_ENV", "dev")
    app.config.from_object(CONFIG_MAP[config_name])

    _init_extensions(app)
    _register_blueprints(app)
    _register_cli(app)

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view = "auth.login"

    from app.models.user import User

    @login_manager.user_loader
    def _load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    from app.blueprints.health import health_bp

    app.register_blueprint(health_bp)


def _register_cli(app: Flask) -> None:
    from app.cli import register_cli

    register_cli(app)
