"""WSGI entry point — used by gunicorn / Flask CLI."""
from app import create_app

app = create_app()
