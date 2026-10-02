"""Flask application factory and same-origin API security configuration."""

import os
import ssl
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError, CSRFProtect
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, static_folder=None)
    production = os.environ.get("APP_ENV", "development").lower() == "production"
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_NAME="jage_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production or os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=production,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=int(os.environ.get("SESSION_TTL_HOURS", "12"))),
        SESSION_REFRESH_EACH_REQUEST=False,
        WTF_CSRF_TIME_LIMIT=3600,
        MAX_CONTENT_LENGTH=32 * 1024,
        RATELIMIT_ENABLED=True,
        DIST_DIR=str(Path(__file__).resolve().parent.parent / "dist"),
        PRODUCTION=production,
    )
    if test_config:
        app.config.update(test_config)
    secret = app.config.get("SECRET_KEY")
    if not secret or (not app.testing and (len(secret) < 32 or "replace" in secret.lower())):
        raise RuntimeError("Define SECRET_KEY con un valor aleatorio de al menos 32 caracteres.")
    database_url = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not database_url:
        raise RuntimeError("Define DATABASE_URL con la conexión a MySQL en .env.")
    url = make_url(database_url)
    if not app.testing and url.drivername != "mysql+pymysql":
        raise RuntimeError("La aplicación utiliza MySQL mediante mysql+pymysql. SQLite solo se permite en pruebas.")
    if url.drivername.startswith("mysql"):
        connect_args = {"connect_timeout": 10, "read_timeout": 20, "write_timeout": 20,
                        "init_command": "SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'"}
        ssl_ca = os.environ.get("MYSQL_SSL_CA", "").strip()
        use_tls = bool(ssl_ca) or os.environ.get("MYSQL_SSL", "false").lower() == "true"
        if production and url.host not in {"localhost", "127.0.0.1", "::1"} and not use_tls:
            raise RuntimeError("Configura MYSQL_SSL=true o MYSQL_SSL_CA para verificar TLS con MySQL remoto.")
        if use_tls:
            connect_args["ssl"] = ssl.create_default_context(cafile=ssl_ca or None)
        engine_options = {"pool_pre_ping": True, "connect_args": connect_args}
        if os.environ.get("DB_POOL_MODE", "null") == "pooled":
            engine_options.update(pool_size=3, max_overflow=2, pool_recycle=240)
        else:
            engine_options["poolclass"] = NullPool
        app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", engine_options)
    if os.environ.get("TRUST_PROXY", "false").lower() == "true":
        # Enable only behind exactly one trusted reverse proxy which strips forged headers.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=0, x_port=0)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    from app.admin import admin_bp
    from app.auth import auth_bp
    from app.drivers import drivers_bp
    from app.main import main_bp
    from app.migrations import register_cli
    from app.reservations import reservations_bp
    from app.security import APIError

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(reservations_bp, url_prefix="/api/reservations")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(drivers_bp, url_prefix="/api/driver")
    register_cli(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify(error="Inicia sesión para continuar."), 401

    @app.errorhandler(APIError)
    def api_error(error):
        db.session.rollback()
        payload = {"error": error.message}
        if error.fields:
            payload["fields"] = error.fields
        response = jsonify(payload)
        if error.status == 429:
            response.headers["Retry-After"] = str(error.retry_after or 900)
        return response, error.status

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        return jsonify(error="Tu sesión de seguridad venció. Actualiza la página e intenta de nuevo.", code="csrf_expired"), 400

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {400: "La solicitud no es válida.", 403: "Acceso no permitido.",
                    404: "No se encontró el recurso.", 405: "Método no permitido.",
                    413: "La solicitud es demasiado grande.", 415: "Formato no admitido."}
        response = error.get_response()
        response.data = app.json.dumps({"error": messages.get(error.code, "No se pudo atender la solicitud.")})
        response.content_type = "application/json"
        return response

    @app.errorhandler(SQLAlchemyError)
    def database_error(_error):
        db.session.rollback()
        # Keep database credentials, bound values and personal information out of logs/responses.
        app.logger.error("No se pudo completar una operación de base de datos (%s).", type(_error).__name__)
        return jsonify(error="No se pudo completar la operación. Intenta nuevamente en unos momentos."), 503

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return jsonify(error="Ocurrió un error inesperado. Intenta nuevamente en unos momentos."), 500

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        if request.path == "/api" or request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Vary"] = "Cookie"
        if app.config["PRODUCTION"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
