"""Flask extension singletons.

Kept separate from ``create_app`` so models / blueprints / tests can import
them without triggering app initialization.
"""
from __future__ import annotations

from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Single declarative base so Alembic autogenerate sees every model."""


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
