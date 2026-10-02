"""WSGI entry point: waitress-serve --call app:create_app, or gunicorn wsgi:app."""
from app import create_app

app = create_app()
