"""Administrator operations. Permissions and lifecycle rules are enforced here."""

import re
from datetime import date
from uuid import UUID

from flask import Blueprint, jsonify
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app import db
from app.models import DriverProfile, DriverWallet, Promotion, Reservation, User, WalletTransaction, money
from app.security import APIError, decimal_field, json_body, lima_now, roles_required, text_field, validate_user, validate_profile
from app.wallets import lock_wallet, post_entry

admin_bp = Blueprint("admin", __name__)
admin_required = roles_required(User.ROLE_ADMIN)
TRANSITIONS = {"pendiente": {"confirmada", "cancelada"}, "confirmada": {"completada", "cancelada"},
               "cancelada": set(), "completada": set()}


def driver_dict(driver):
    return {**driver.to_dict(include_identity=True), "balance": money(driver.wallet.balance) if driver.wallet else "0.00"}


@admin_bp.get("/reservations")
@admin_required
def list_reservations():
    reservations = db.session.scalars(db.select(Reservation).options(joinedload(Reservation.user), joinedload(Reservation.driver))
                                     .order_by(Reservation.created_at.desc(), Reservation.id.desc())).all()
    return jsonify(reservations=[item.to_dict(include_user=True) for item in reservations])


@admin_bp.patch("/reservations/<int:reservation_id>")
@admin_required
def update_reservation(reservation_id):
    data = json_body()
    reservation = db.session.scalar(db.select(Reservation).where(Reservation.id == reservation_id).with_for_update())
    if reservation is None:
        raise APIError("No se encontró la reserva.", 404)
    status = data.get("status", reservation.status)
    if not isinstance(status, str) or status not in Reservation.STATUSES:
        raise APIError("Selecciona un estado válido.", fields={"status": "Estado inválido."})
    driver_id = data.get("driver_id", reservation.driver_id)
    if driver_id is not None and (type(driver_id) is not int or driver_id < 1):
        raise APIError("Selecciona un conductor válido.", fields={"driver_id": "Conductor inválido."})
    commission = reservation.commission
    if "commission" in data:
        commission = None if data["commission"] is None else decimal_field(data, "commission", zero=True)
    if reservation.status in {Reservation.STATUS_CANCELLED, Reservation.STATUS_COMPLETED}:
        if status == reservation.status and driver_id == reservation.driver_id and commission == reservation.commission:
            return jsonify(reservation=reservation.to_dict(include_user=True))
        raise APIError("Una reserva finalizada no puede modificarse ni reabrirse.", 409)
    if status != reservation.status and status not in TRANSITIONS[reservation.status]:
        raise APIError("Ese cambio de estado no está permitido. Confirma la reserva antes de completarla.", 409)
    if driver_id is not None:
        driver = db.session.get(User, driver_id)
        if driver is None or driver.role != User.ROLE_DRIVER:
            raise APIError("Selecciona una cuenta de conductor válida.", fields={"driver_id": "Conductor inválido."})
    reservation.driver_id = driver_id
    reservation.commission = commission
    if status == Reservation.STATUS_COMPLETED:
        if driver_id is None or commission is None:
            raise APIError("Asigna un conductor e indica la comisión antes de completar el viaje.", 409)
        wallet = lock_wallet(driver_id)
        post_entry(wallet, -commission, "commission", f"Comisión del viaje #{reservation.id}", reservation_id=reservation.id)
        reservation.commission_charged = True
    reservation.status = status
    db.session.commit()
    # Relationship caches can contain the previous driver after a foreign-key change.
    db.session.refresh(reservation)
    return jsonify(reservation=reservation.to_dict(include_user=True))


@admin_bp.get("/drivers")
@admin_required
def list_drivers():
    drivers = db.session.scalars(db.select(User).where(User.role == User.ROLE_DRIVER)
                                .options(joinedload(User.wallet), joinedload(User.driver_profile)).order_by(User.first_name, User.id)).all()
    return jsonify(drivers=[driver_dict(driver) for driver in drivers])


@admin_bp.post("/drivers")
@admin_required
def create_driver():
    payload = json_body()
    data = validate_user(payload)
    profile = validate_profile(payload, driver=True)
    password = data.pop("password")
    driver = User(**data, role=User.ROLE_DRIVER)
    driver.driver_profile = DriverProfile(**profile)
    driver.set_password(password)
    driver.wallet = DriverWallet()
    db.session.add(driver)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise APIError("Ese correo o DNI ya está registrado.", 409) from None
    return jsonify(driver=driver_dict(driver)), 201


@admin_bp.post("/drivers/<int:driver_id>/balance")
@admin_required
def adjust_balance(driver_id):
    data = json_body()
    amount = decimal_field(data, "amount", negative=True)
    reason = text_field(data, "reason", 300)
    key = text_field(data, "idempotency_key", 36)
    try:
        key = str(UUID(key))
    except ValueError:
        raise APIError("La clave de la operación debe ser un UUID válido.") from None
    wallet = lock_wallet(driver_id)
    previous = db.session.scalar(db.select(WalletTransaction).where(WalletTransaction.idempotency_key == key).with_for_update())
    if previous:
        if previous.driver_id != driver_id or previous.amount != amount or previous.reason != reason:
            raise APIError("La clave de esta operación ya se utilizó con otros datos.", 409)
        return jsonify(driver=driver_dict(wallet.driver), balance=money(wallet.balance), transaction=previous.to_dict())
    transaction = post_entry(wallet, amount, "adjustment", reason, idempotency_key=key)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise APIError("La clave de esta operación ya está en uso. Comprueba el historial.", 409) from None
    return jsonify(driver=driver_dict(wallet.driver), balance=money(wallet.balance), transaction=transaction.to_dict()), 201


@admin_bp.get("/promotions")
@admin_required
def list_promotions():
    promotions = db.session.scalars(db.select(Promotion).order_by(Promotion.created_at.desc(), Promotion.id.desc())).all()
    return jsonify(promotions=[promotion.to_dict() for promotion in promotions])


@admin_bp.post("/promotions")
@admin_required
def create_promotion():
    data = json_body()
    title = text_field(data, "title", 120)
    description = text_field(data, "description", 500, required=False)
    amount = decimal_field(data, "amount")
    date_value = text_field(data, "expires_at", 10)
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
            raise ValueError
        expiry = date.fromisoformat(date_value)
        if expiry < lima_now().date():
            raise ValueError
    except ValueError:
        raise APIError("La promoción debe vencer hoy o en una fecha futura (hora de Perú).", fields={"expires_at": "Fecha inválida."}) from None
    active = data.get("active", True)
    if type(active) is not bool:
        raise APIError("El estado activo debe ser verdadero o falso.")
    promotion = Promotion(title=title, description=description, amount=amount, expires_at=expiry,
                          active=active, created_by=current_user.id)
    db.session.add(promotion)
    db.session.commit()
    return jsonify(promotion=promotion.to_dict()), 201


@admin_bp.patch("/promotions/<int:promotion_id>")
@admin_required
def update_promotion(promotion_id):
    data = json_body()
    if type(data.get("active")) is not bool:
        raise APIError("Indica si la promoción debe estar activa.")
    promotion = db.session.scalar(db.select(Promotion).where(Promotion.id == promotion_id).with_for_update())
    if promotion is None:
        raise APIError("No se encontró la promoción.", 404)
    promotion.active = data["active"]
    db.session.commit()
    return jsonify(promotion=promotion.to_dict())
