"""Model package — all SQLAlchemy classes live here.

Importing this module pulls every model into the metadata so Alembic
autogenerate sees them.
"""
from __future__ import annotations

from app.models.audit_log import AuditLog
from app.models.budget import Budget, BudgetVersion, LineItem
from app.models.client import Client
from app.models.comment import Comment
from app.models.fx_rate import FXRate
from app.models.labor import LaborParam
from app.models.material import Material, Rubro
from app.models.project import Project
from app.models.share_token import ShareToken
from app.models.studio import Studio
from app.models.user import User

__all__ = [
    "AuditLog",
    "Budget",
    "BudgetVersion",
    "Client",
    "Comment",
    "FXRate",
    "LaborParam",
    "LineItem",
    "Material",
    "Project",
    "Rubro",
    "ShareToken",
    "Studio",
    "User",
]
