"""Environment-driven config classes.

Resolved via ``APP_ENV``:
  dev   → local Postgres in docker-compose
  test  → in-memory SQLite + suppressed CSRF for pytest
  prod  → reads everything from env, fails loudly if a required secret is unset
"""
from __future__ import annotations

import os


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name!r} is not set")
    return value


class BaseConfig:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    BABEL_DEFAULT_LOCALE = "es"
    SUPPORTED_LOCALES = ("es", "en")
    WTF_CSRF_ENABLED = True

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "mailhog")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "1025"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "0") == "1"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "Estudio Sarachaga <no-reply@sarachaga.uy>"
    )

    PDF_WKHTML_PATH = os.environ.get("PDF_WKHTML_PATH", "/usr/bin/wkhtmltopdf")

    BCU_FX_URL = os.environ.get(
        "BCU_FX_URL",
        "https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Cotizaciones/cotizaciones.aspx",
    )


class DevConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://budget:budget@db:5432/budget",
    )


class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "sqlite:///:memory:"
    )
    WTF_CSRF_ENABLED = False


class ProdConfig(BaseConfig):
    DEBUG = False

    def __init__(self) -> None:
        super().__init__()
        self.SECRET_KEY = _required("SECRET_KEY")
        self.SQLALCHEMY_DATABASE_URI = _required("DATABASE_URL")


CONFIG_MAP: dict[str, type[BaseConfig]] = {
    "dev": DevConfig,
    "test": TestConfig,
    "prod": ProdConfig,
}
