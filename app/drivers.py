"""Driver dashboard: only assigned journeys and the driver's own wallet."""

from flask import Blueprint, jsonify
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app import db
from app.models import DriverWallet, Promotion, Reservation, User, WalletTransaction, money
from app.security import APIError, lima_now, roles_required
from app.wallets import lock_wallet, post_entry

drivers_bp = Blueprint("drivers", __name__)
driver_required = roles_required(User.ROLE_DRIVER)


@drivers_bp.get("/dashboard")
@driver_required
def dashboard():
    wallet = db.session.get(DriverWallet, current_user.id)
    if wallet is None:
        raise APIError("No se encontró tu billetera. Contacta al administrador.", 409)
    transactions = db.session.scalars(db.select(WalletTransaction).where(WalletTransaction.driver_id == current_user.id)
                                     .order_by(WalletTransaction.created_at.desc(), WalletTransaction.id.desc())).all()
    reservations = db.session.scalars(db.select(Reservation).where(Reservation.driver_id == current_user.id)
                                     .options(joinedload(Reservation.user))
                                     .order_by(Reservation.travel_date.desc(), Reservation.travel_time.desc())).all()
    redeemed = {transaction.promotion_id for transaction in transactions if transaction.promotion_id is not None}
    promotions = db.session.scalars(db.select(Promotion).where(Promotion.active.is_(True), Promotion.expires_at >= lima_now().date())
                                   .order_by(Promotion.expires_at, Promotion.id)).all()
    return jsonify(balance=money(wallet.balance), transactions=[item.to_dict() for item in transactions],
                   reservations=[item.to_dict(driver_view=True) for item in reservations],
                   promotions=[item.to_dict(redeemed=item.id in redeemed) for item in promotions])


@drivers_bp.post("/promotions/<int:promotion_id>/redeem")
@driver_required
def redeem_promotion(promotion_id):
    promotion = db.session.scalar(db.select(Promotion).where(Promotion.id == promotion_id).with_for_update())
    if promotion is None:
        raise APIError("No se encontró la promoción.", 404)
    if not promotion.active or promotion.expires_at < lima_now().date():
        raise APIError("Esta promoción ya no está disponible.", 409)
    wallet = lock_wallet(current_user.id)
    existing = db.session.scalar(db.select(WalletTransaction).where(WalletTransaction.driver_id == current_user.id,
                                                                    WalletTransaction.promotion_id == promotion.id).with_for_update())
    if existing is not None:
        raise APIError("Ya canjeaste esta promoción.", 409)
    transaction = post_entry(wallet, promotion.amount, "promotion", f"Promoción: {promotion.title}", promotion_id=promotion.id)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise APIError("Ya canjeaste esta promoción.", 409) from None
    return jsonify(balance=money(wallet.balance), transaction=transaction.to_dict(), promotion=promotion.to_dict(redeemed=True)), 201
