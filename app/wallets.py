"""Transactional wallet operations. Callers lock and commit in one transaction."""

from flask_login import current_user

from app import db
from app.models import DriverWallet, WalletTransaction
from app.security import APIError, MAX_MONEY


def lock_wallet(driver_id):
    wallet = db.session.scalar(db.select(DriverWallet).where(DriverWallet.driver_id == driver_id).with_for_update())
    if wallet is None:
        raise APIError("No se encontró la billetera del conductor.", 404)
    return wallet


def post_entry(wallet, amount, kind, reason, **references):
    """Balance and immutable ledger entry must commit together, under a row lock."""
    new_balance = wallet.balance + amount
    if new_balance < 0:
        raise APIError("El conductor no tiene saldo suficiente para esta operación.", 409)
    if new_balance > MAX_MONEY:
        raise APIError("La operación supera el saldo máximo permitido.", 409)
    wallet.balance = new_balance
    entry = WalletTransaction(driver_id=wallet.driver_id, amount=amount, balance_after=new_balance,
                              kind=kind, reason=reason, actor_id=current_user.id, **references)
    db.session.add(entry)
    return entry
