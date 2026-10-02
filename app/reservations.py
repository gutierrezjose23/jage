"""Passenger reservation requests; a pending request is never a confirmed trip."""

import re
from datetime import date, datetime

from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app import db
from app.models import Reservation, User
from app.security import APIError, LIMA, json_body, lima_now, roles_required, text_field

reservations_bp = Blueprint("reservations", __name__)
SERVICES = {"privado": "Viaje privado", "huaral-lima": "Huaral–Lima", "aeropuerto": "Traslado al aeropuerto"}


@reservations_bp.get("")
@login_required
def list_mine():
    reservations = db.session.scalars(db.select(Reservation).where(Reservation.user_id == current_user.id)
                                     .order_by(Reservation.created_at.desc(), Reservation.id.desc())).all()
    return jsonify(reservations=[item.to_dict() for item in reservations])


@reservations_bp.post("")
@roles_required(User.ROLE_PASSENGER)
def create():
    data = json_body()
    service = text_field(data, "service", 40)
    origin = text_field(data, "origin", 180)
    destination = text_field(data, "destination", 180)
    notes = text_field(data, "notes", 1000, required=False)
    date_value = text_field(data, "travel_date", 10)
    time_value = text_field(data, "travel_time", 5)
    errors = {}
    if service not in SERVICES:
        errors["service"] = "Selecciona un servicio disponible."
    passengers = data.get("passengers")
    if type(passengers) is not int or not 1 <= passengers <= 8:
        errors["passengers"] = "La cantidad debe ser un número entero de 1 a 8 pasajeros."
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value) or not re.fullmatch(r"\d{2}:\d{2}", time_value):
            raise ValueError
        travel_date = date.fromisoformat(date_value)
        travel_time = datetime.strptime(time_value, "%H:%M").time()
        if datetime.combine(travel_date, travel_time, tzinfo=LIMA) <= lima_now():
            errors["travel_date"] = "La fecha y hora deben ser futuras (hora de Perú)."
    except ValueError:
        errors["travel_date"] = "Ingresa una fecha y hora válidas."
    if errors:
        raise APIError("Revisa los datos de tu reserva.", fields=errors)
    reservation = Reservation(user_id=current_user.id, service=service, origin=origin,
                              destination=destination, travel_date=travel_date, travel_time=travel_time,
                              passengers=passengers, notes=notes or None, status=Reservation.STATUS_PENDING)
    db.session.add(reservation)
    db.session.commit()
    return jsonify(reservation=reservation.to_dict()), 201


@reservations_bp.get("/<int:reservation_id>")
@login_required
def detail(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if reservation is None or (reservation.user_id != current_user.id and current_user.role != User.ROLE_ADMIN):
        raise APIError("No se encontró la reserva.", 404)
    return jsonify(reservation=reservation.to_dict(include_user=current_user.role == User.ROLE_ADMIN))
