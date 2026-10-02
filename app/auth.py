"""Cookie session authentication: public registration can only create passengers."""

from flask import Blueprint, jsonify, session
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models import CustomerProfile, User
from app.security import APIError, json_body, rate_limit, text_field, validate_user, validate_profile

auth_bp = Blueprint("auth", __name__)
_DUMMY_HASH = generate_password_hash("not-a-login-password", method="scrypt")


def session_response(status=200):
    return jsonify(user=current_user.to_dict(include_identity=True) if current_user.is_authenticated else None,
                   csrf_token=generate_csrf()), status


@auth_bp.get("/session")
def get_session():
    return session_response()


@auth_bp.post("/auth/register")
def register():
    if current_user.is_authenticated:
        raise APIError("Cierra tu sesión antes de crear otra cuenta.", 409)
    rate_limit("register", limit=6, seconds=3600)
    payload = json_body()
    data = validate_user(payload)
    profile = validate_profile(payload)
    password = data.pop("password")
    user = User(**data, role=User.ROLE_PASSENGER)
    user.customer_profile = CustomerProfile(**profile)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise APIError("El correo o DNI ya está registrado. Prueba iniciar sesión.", 409) from None
    session.clear()
    login_user(user, remember=False, fresh=True)
    session.permanent = True
    return session_response(201)


@auth_bp.post("/auth/login")
def login():
    data = json_body()
    email = text_field(data, "email", 254).lower()
    password = text_field(data, "password", 128, strip=False)
    rate_limit("login-ip", limit=30, seconds=900)
    rate_limit("login-email", limit=10, seconds=900, subject=email)
    user = db.session.scalar(db.select(User).where(User.email == email))
    valid = user.check_password(password) if user else check_password_hash(_DUMMY_HASH, password)
    if user is None or not valid:
        raise APIError("Correo o contraseña incorrectos.", 401)
    session.clear()
    login_user(user, remember=False, fresh=True)
    session.permanent = True
    return session_response()


@auth_bp.post("/auth/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return session_response()
