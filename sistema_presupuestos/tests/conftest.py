"""Pytest fixtures for the budget app.

The unit tests in ``tests/unit`` exercise pure functions and don't need
a Flask app or a database — they import ``app.services.*`` directly.
Integration tests that need a request context can use the ``app`` and
``client`` fixtures here.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("APP_ENV", "test")


@pytest.fixture()
def app():
    from app import create_app
    from app.extensions import db

    flask_app = create_app("test")
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
