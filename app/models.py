"""Persistence models. Amounts are exact decimal PEN, never floating point."""

from datetime import datetime, timezone
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def timestamp(value):
    return value.isoformat(timespec="seconds") + "Z" if value else None


def money(value):
    return format(value, ".2f") if value is not None else None


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.CheckConstraint("role IN ('passenger', 'admin', 'driver')", name="chk_users_role"),
    )

    ROLE_PASSENGER = "passenger"
    ROLE_ADMIN = "admin"
    ROLE_DRIVER = "driver"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_PASSENGER)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    reservations = db.relationship("Reservation", foreign_keys="Reservation.user_id", back_populates="user")
    wallet = db.relationship("DriverWallet", back_populates="driver", uselist=False)
    customer_profile = db.relationship("CustomerProfile", back_populates="user", uselist=False,
                                       cascade="all, delete-orphan")
    driver_profile = db.relationship("DriverProfile", back_populates="user", uselist=False,
                                     cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_identity=False):
        result = {"id": self.id, "first_name": self.first_name, "last_name": self.last_name,
                  "phone": self.phone, "email": self.email, "role": self.role}
        profile = None
        if self.role == self.ROLE_DRIVER:
            profile = self.driver_profile
        elif include_identity and self.role == self.ROLE_PASSENGER:
            profile = self.customer_profile
        if include_identity:
            result["dni"] = profile.dni if profile else None
        if self.role == self.ROLE_DRIVER:
            result["license_plate"] = profile.license_plate if profile else None
        return result


class CustomerProfile(db.Model):
    """Customer identity, linked to the existing account/contact information."""
    __tablename__ = "clientes"
    __table_args__ = (db.CheckConstraint("dni IS NULL OR length(dni) = 8", name="chk_clientes_dni"),)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    # Legacy accounts have no known DNI. New registrations require it in the API.
    dni = db.Column(db.String(8), unique=True, nullable=True)
    user = db.relationship("User", back_populates="customer_profile")


class DriverProfile(db.Model):
    __tablename__ = "conductores"
    __table_args__ = (
        db.CheckConstraint("dni IS NULL OR length(dni) = 8", name="chk_conductores_dni"),
        db.CheckConstraint("placa IS NULL OR length(placa) = 7", name="chk_conductores_placa"),
    )

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    dni = db.Column(db.String(8), unique=True, nullable=True)
    license_plate = db.Column("placa", db.String(7), nullable=True, index=True)
    user = db.relationship("User", back_populates="driver_profile")


class Reservation(db.Model):
    __tablename__ = "reservations"
    __table_args__ = (
        db.CheckConstraint("service IN ('privado', 'huaral-lima', 'aeropuerto')", name="chk_reservations_service"),
        db.CheckConstraint("status IN ('pendiente', 'confirmada', 'cancelada', 'completada')", name="chk_reservations_status"),
        db.CheckConstraint("passengers BETWEEN 1 AND 8", name="chk_reservations_passengers"),
        db.CheckConstraint("commission IS NULL OR commission >= 0", name="chk_reservations_commission"),
    )

    STATUS_PENDING = "pendiente"
    STATUS_CONFIRMED = "confirmada"
    STATUS_CANCELLED = "cancelada"
    STATUS_COMPLETED = "completada"
    STATUSES = (STATUS_PENDING, STATUS_CONFIRMED, STATUS_CANCELLED, STATUS_COMPLETED)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    service = db.Column(db.String(40), nullable=False)
    origin = db.Column(db.String(180), nullable=False)
    destination = db.Column(db.String(180), nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    travel_time = db.Column(db.Time, nullable=False)
    passengers = db.Column(db.SmallInteger, nullable=False)
    notes = db.Column(db.String(1000), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING)
    commission = db.Column(db.Numeric(12, 2), nullable=True)
    commission_charged = db.Column(db.Boolean, nullable=False, default=False, server_default="0")
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    user = db.relationship("User", foreign_keys=[user_id], back_populates="reservations")
    driver = db.relationship("User", foreign_keys=[driver_id])

    def to_dict(self, include_user=False, driver_view=False):
        result = {"id": self.id, "user_id": self.user_id, "service": self.service,
                  "origin": self.origin, "destination": self.destination,
                  "travel_date": self.travel_date.isoformat(),
                  "travel_time": self.travel_time.strftime("%H:%M"), "passengers": self.passengers,
                  "notes": self.notes or "", "status": self.status,
                  "driver_id": self.driver_id, "commission": money(self.commission),
                  "commission_charged": self.commission_charged,
                  "created_at": timestamp(self.created_at), "updated_at": timestamp(self.updated_at)}
        if include_user:
            result["user"] = self.user.to_dict()
            result["driver"] = self.driver.to_dict() if self.driver else None
        elif driver_view:
            result["user"] = {"first_name": self.user.first_name, "last_name": self.user.last_name,
                              "phone": self.user.phone}
        return result


class DriverWallet(db.Model):
    __tablename__ = "driver_wallets"
    __table_args__ = (db.CheckConstraint("balance >= 0", name="chk_wallet_balance"),)

    driver_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default="0.00")
    driver = db.relationship("User", back_populates="wallet")


class Promotion(db.Model):
    __tablename__ = "promotions"
    __table_args__ = (db.CheckConstraint("amount > 0", name="chk_promotion_amount"),)

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False, default="")
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    expires_at = db.Column(db.Date, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True, server_default="1")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    def to_dict(self, redeemed=False):
        return {"id": self.id, "title": self.title, "description": self.description,
                "amount": money(self.amount), "expires_at": self.expires_at.isoformat(),
                "active": self.active, "redeemed": redeemed, "created_at": timestamp(self.created_at)}


class WalletTransaction(db.Model):
    """Append-only through the API: there is no update or delete operation."""
    __tablename__ = "wallet_transactions"
    __table_args__ = (
        db.UniqueConstraint("driver_id", "promotion_id", name="uq_driver_promotion"),
        db.CheckConstraint("balance_after >= 0", name="chk_transaction_balance"),
        db.CheckConstraint("kind IN ('adjustment', 'commission', 'promotion')", name="chk_transaction_kind"),
    )

    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("driver_wallets.driver_id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(300), nullable=False)
    reservation_id = db.Column(db.Integer, db.ForeignKey("reservations.id", ondelete="RESTRICT"), unique=True, nullable=True)
    promotion_id = db.Column(db.Integer, db.ForeignKey("promotions.id", ondelete="RESTRICT"), nullable=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    idempotency_key = db.Column(db.String(36), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    def to_dict(self):
        return {"id": self.id, "driver_id": self.driver_id, "amount": money(self.amount),
                "balance_after": money(self.balance_after), "kind": self.kind, "reason": self.reason,
                "reservation_id": self.reservation_id, "promotion_id": self.promotion_id,
                "actor_id": self.actor_id, "created_at": timestamp(self.created_at)}


class RateLimitBucket(db.Model):
    __tablename__ = "rate_limit_buckets"

    key_hash = db.Column(db.String(64), primary_key=True)
    hits = db.Column(db.Integer, nullable=False, default=0)
    window_start = db.Column(db.DateTime, nullable=False)
