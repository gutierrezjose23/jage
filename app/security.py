"""Shared strict validation and database-backed abuse protection."""

import hashlib
import hmac
import math
import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
from zoneinfo import ZoneInfo

from flask import current_app, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import RateLimitBucket, utc_now

LIMA = ZoneInfo("America/Lima")
MAX_MONEY = Decimal("99999999.99")


class APIError(Exception):
    def __init__(self, message, status=400, fields=None, retry_after=None):
        super().__init__(message)
        self.message, self.status, self.fields = message, status, fields
        self.retry_after = retry_after


def lima_now():
    return datetime.now(LIMA)


def json_body():
    if not request.is_json:
        raise APIError("Envía los datos en formato JSON.", 415)
    data = request.get_json()
    if not isinstance(data, dict):
        raise APIError("El cuerpo de la solicitud debe ser un objeto JSON.")
    return data


def text_field(data, key, maximum, required=True, strip=True):
    value = data.get(key, "")
    if not isinstance(value, str):
        raise APIError("Revisa los campos indicados.", fields={key: "Ingresa un texto válido."})
    value = value.strip() if strip else value
    if (required and not value) or len(value) > maximum or "\x00" in value:
        raise APIError("Revisa los campos indicados.", fields={key: f"Completa este campo con hasta {maximum} caracteres."})
    return value


def validate_profile(data, driver=False):
    dni = text_field(data, "dni", 8)
    if not re.fullmatch(r"[0-9]{8}", dni):
        raise APIError("Revisa el DNI.", fields={"dni": "El DNI debe tener exactamente 8 dígitos."})
    result = {"dni": dni}
    if driver:
        plate = text_field(data, "license_plate", 7).upper()
        if not re.fullmatch(r"[A-Z0-9]{3}-?[A-Z0-9]{3}", plate):
            raise APIError("Revisa la placa.", fields={"license_plate": "Usa 6 letras o números, por ejemplo ABC-123."})
        compact = plate.replace("-", "")
        result["license_plate"] = compact[:3] + "-" + compact[3:]
    return result


def validate_user(data):
    first_name = text_field(data, "first_name", 80)
    last_name = text_field(data, "last_name", 80)
    phone = text_field(data, "phone", 20)
    email = text_field(data, "email", 254).lower()
    password = text_field(data, "password", 128, strip=False)
    errors = {}
    if not re.fullmatch(r"\+?[0-9 ()-]{7,20}", phone) or not 7 <= len(re.sub(r"\D", "", phone)) <= 15:
        errors["phone"] = "Ingresa un celular válido, con código de país si corresponde."
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        errors["email"] = "Ingresa un correo válido."
    if len(password) < 12 or not password.strip():
        errors["password"] = "La contraseña debe tener entre 12 y 128 caracteres."
    if errors:
        raise APIError("Revisa los campos indicados.", fields=errors)
    return {"first_name": first_name, "last_name": last_name, "phone": phone,
            "email": email, "password": password}


def decimal_field(data, key, *, negative=False, zero=False):
    value = data.get(key)
    # A decimal string is required, so JS float rounding never affects wallet entries.
    if not isinstance(value, str) or not re.fullmatch(r"-?\d{1,8}(?:\.\d{1,2})?", value):
        raise APIError("Revisa el importe.", fields={key: "Usa un importe decimal con hasta dos decimales."})
    try:
        amount = Decimal(value).quantize(Decimal("0.01"))
    except InvalidOperation:
        raise APIError("El importe no es válido.") from None
    if abs(amount) > MAX_MONEY or (not negative and amount < 0) or (not zero and amount == 0):
        raise APIError("El importe está fuera del rango permitido.", fields={key: "Revisa el importe."})
    return amount


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                raise APIError("No tienes permiso para acceder a esta sección.", 403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def rate_limit(scope, limit, seconds, subject=None):
    """Fixed-window counters shared across workers; no raw IP/email is persisted."""
    if not current_app.config.get("RATELIMIT_ENABLED", True):
        return
    subject = subject if subject is not None else (request.remote_addr or "unknown")
    digest = hmac.new(current_app.secret_key.encode(), f"{scope}:{subject}".encode(), hashlib.sha256).hexdigest()
    now = utc_now()
    bucket = db.session.scalar(db.select(RateLimitBucket).where(RateLimitBucket.key_hash == digest).with_for_update())
    if bucket is None:
        try:
            with db.session.begin_nested():
                bucket = RateLimitBucket(key_hash=digest, hits=0, window_start=now)
                db.session.add(bucket)
                db.session.flush()
        except IntegrityError:
            bucket = db.session.scalar(db.select(RateLimitBucket).where(RateLimitBucket.key_hash == digest).with_for_update())
    if now >= bucket.window_start + timedelta(seconds=seconds):
        bucket.window_start, bucket.hits = now, 0
    if bucket.hits >= limit:
        retry_after = max(1, math.ceil((bucket.window_start + timedelta(seconds=seconds) - now).total_seconds()))
        db.session.rollback()
        raise APIError("Demasiados intentos. Vuelve a intentar cuando termine el tiempo de espera.", 429, retry_after=retry_after)
    bucket.hits += 1
    # Authentication calls this before changing any business data.
    db.session.commit()
