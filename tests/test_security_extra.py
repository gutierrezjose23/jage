"""Security boundaries and real-MySQL concurrency regression checks.

Use an isolated TEST_DATABASE_URL named jage_test* as documented in test_app.py.
The concurrency scenarios require MySQL row locks and are skipped on SQLite.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest

from app import create_app, db
from app.models import DriverWallet, RateLimitBucket, Reservation, User, WalletTransaction, utc_now
from test_app import (
    PASSWORD, app, authenticated, balance_adjustment, change_reservation,
    create_booking, create_promotion, login, mutate, registration, seed_user, session,
)


def test_login_limits_persist_across_clients_and_use_hashed_subjects(app):
    seed_user(app, "protected@example.com", "passenger")
    app.config["RATELIMIT_ENABLED"] = True
    first = app.test_client()
    for _ in range(10):
        assert login(first, "protected@example.com", "incorrect-password").status_code == 401
    other_browser = app.test_client()
    response = login(other_browser, "protected@example.com", PASSWORD)
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
    with app.app_context():
        buckets = db.session.scalars(db.select(RateLimitBucket)).all()
        assert len(buckets) == 2
        assert all(len(bucket.key_hash) == 64 for bucket in buckets)
        assert all("@" not in bucket.key_hash and "127.0.0.1" not in bucket.key_hash for bucket in buckets)


def test_expired_login_limit_window_allows_new_attempt(app):
    seed_user(app, "protected@example.com", "passenger")
    app.config["RATELIMIT_ENABLED"] = True
    client = app.test_client()
    for _ in range(10):
        assert login(client, "protected@example.com", "incorrect-password").status_code == 401
    assert login(client, "protected@example.com").status_code == 429
    with app.app_context():
        db.session.execute(db.update(RateLimitBucket).values(window_start=utc_now() - timedelta(minutes=16)))
        db.session.commit()
    assert login(client, "protected@example.com").status_code == 200


def test_registration_limit_counts_invalid_attempts_without_persisting_users(app):
    app.config["RATELIMIT_ENABLED"] = True
    client = app.test_client()
    for i in range(6):
        payload = registration(f"invalid-{i}@example.com", password="short")
        assert mutate(client, "/api/auth/register", payload).status_code == 400
    assert mutate(app.test_client(), "/api/auth/register", registration()).status_code == 429
    with app.app_context():
        assert db.session.query(User).count() == 0


def test_initial_admin_cli_validates_inputs_and_refuses_second_admin(app):
    runner = app.test_cli_runner()
    bad = runner.invoke(args=["init-admin"], input="invalid\nAdmin\nJage\n51934613286\n" + PASSWORD + "\n" + PASSWORD + "\n")
    assert bad.exit_code != 0
    with app.app_context():
        assert db.session.query(User).count() == 0
    valid = runner.invoke(args=["init-admin"], input="admin@example.com\nAdmin\nJage\n51934613286\n" + PASSWORD + "\n" + PASSWORD + "\n")
    assert valid.exit_code == 0, valid.output
    with app.app_context():
        administrator = db.session.scalar(db.select(User))
        assert administrator.role == User.ROLE_ADMIN
        assert administrator.check_password(PASSWORD)
    repeated = runner.invoke(args=["init-admin"])
    assert repeated.exit_code != 0
    assert "Ya existe" in repeated.output


def test_unknown_api_and_missing_assets_are_json_404(app):
    client = app.test_client()
    for path in ("/api", "/api/unknown-route", "/img/no-such-image.png", "/assets/missing.js", "/.env"):
        response = client.get(path)
        assert response.status_code == 404
        assert response.is_json


def test_production_requires_verified_remote_mysql_tls(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "production-configuration-check-1234567890")
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://app:unused@db.example.com/jage")
    monkeypatch.setenv("MYSQL_SSL", "false")
    monkeypatch.setenv("MYSQL_SSL_CA", "")
    with pytest.raises(RuntimeError, match="TLS"):
        create_app()
    monkeypatch.setenv("MYSQL_SSL", "true")
    production = create_app()
    assert production.config["SESSION_COOKIE_SECURE"] is True
    assert production.config["SESSION_COOKIE_HTTPONLY"] is True
    context = production.config["SQLALCHEMY_ENGINE_OPTIONS"]["connect_args"]["ssl"]
    assert context.check_hostname is True


def _mysql_only(app):
    with app.app_context():
        if db.engine.dialect.name != "mysql":
            pytest.skip("Real MySQL required to verify row locking and concurrent writes.")


def _simultaneous(calls):
    barrier = Barrier(len(calls))
    prepared = [(client, method, path, payload, session(client)["csrf_token"])
                for client, method, path, payload in calls]

    def execute(values):
        client, method, path, payload, token = values
        barrier.wait(timeout=15)
        response = client.open(path, method=method, json=payload, headers={"X-CSRFToken": token})
        return response.status_code, response.json

    with ThreadPoolExecutor(max_workers=len(calls)) as executor:
        return list(executor.map(execute, prepared))


def test_mysql_simultaneous_completion_debits_exactly_once(app):
    _mysql_only(app)
    first_admin, _ = authenticated(app, "admin")
    second_admin, _ = authenticated(app, "admin")
    passenger, _ = authenticated(app)
    _, driver_id = authenticated(app, "driver")
    reservation = create_booking(passenger)
    assert balance_adjustment(first_admin, driver_id, "30.00").status_code == 201
    assert change_reservation(first_admin, reservation["id"], status="confirmada", driver_id=driver_id, commission="7.25").status_code == 200
    path = f"/api/admin/reservations/{reservation['id']}"
    results = _simultaneous([(client, "PATCH", path, {"status": "completada"}) for client in (first_admin, second_admin)])
    assert [status for status, _ in results] == [200, 200], results
    with app.app_context():
        assert db.session.get(DriverWallet, driver_id).balance == Decimal("22.75")
        assert db.session.query(WalletTransaction).filter_by(reservation_id=reservation["id"]).count() == 1


def test_mysql_competing_trip_commissions_cannot_overdraw_wallet(app):
    _mysql_only(app)
    first_admin, _ = authenticated(app, "admin")
    second_admin, _ = authenticated(app, "admin")
    passenger, _ = authenticated(app)
    _, driver_id = authenticated(app, "driver")
    reservations = [create_booking(passenger), create_booking(passenger)]
    assert balance_adjustment(first_admin, driver_id, "10.00").status_code == 201
    for reservation in reservations:
        assert change_reservation(first_admin, reservation["id"], status="confirmada", driver_id=driver_id, commission="7.00").status_code == 200
    calls = [(client, "PATCH", f"/api/admin/reservations/{reservation['id']}", {"status": "completada"})
             for client, reservation in zip((first_admin, second_admin), reservations)]
    results = _simultaneous(calls)
    assert sorted(status for status, _ in results) == [200, 409], results
    with app.app_context():
        assert db.session.get(DriverWallet, driver_id).balance == Decimal("3.00")
        assert db.session.query(WalletTransaction).filter_by(kind="commission").count() == 1
        assert db.session.query(Reservation).filter_by(status="completada").count() == 1


def test_mysql_same_idempotency_key_credits_once_during_race(app):
    _mysql_only(app)
    first_admin, _ = authenticated(app, "admin")
    second_admin, _ = authenticated(app, "admin")
    _, driver_id = authenticated(app, "driver")
    payload = {"amount": "10.10", "reason": "Ajuste concurrente", "idempotency_key": str(uuid4())}
    path = f"/api/admin/drivers/{driver_id}/balance"
    results = _simultaneous([(client, "POST", path, payload) for client in (first_admin, second_admin)])
    assert sorted(status for status, _ in results) == [200, 201], results
    assert results[0][1]["transaction"]["id"] == results[1][1]["transaction"]["id"]
    with app.app_context():
        assert db.session.get(DriverWallet, driver_id).balance == Decimal("10.10")
        assert db.session.query(WalletTransaction).count() == 1


def test_mysql_distinct_adjustments_preserve_both_credits(app):
    _mysql_only(app)
    first_admin, _ = authenticated(app, "admin")
    second_admin, _ = authenticated(app, "admin")
    _, driver_id = authenticated(app, "driver")
    path = f"/api/admin/drivers/{driver_id}/balance"
    results = _simultaneous([(client, "POST", path, {"amount": "10.00", "reason": "Ajuste simultáneo", "idempotency_key": str(uuid4())})
                            for client in (first_admin, second_admin)])
    assert [status for status, _ in results] == [201, 201], results
    with app.app_context():
        assert db.session.get(DriverWallet, driver_id).balance == Decimal("20.00")
        assert db.session.query(WalletTransaction).count() == 2


def test_mysql_same_promotion_redeems_once_during_race(app):
    _mysql_only(app)
    admin, _ = authenticated(app, "admin")
    first_driver, driver_id = authenticated(app, "driver", "concurrent-driver@example.com")
    second_driver = app.test_client()
    assert login(second_driver, "concurrent-driver@example.com").status_code == 200
    promotion = create_promotion(admin)
    path = f"/api/driver/promotions/{promotion['id']}/redeem"
    results = _simultaneous([(client, "POST", path, {}) for client in (first_driver, second_driver)])
    assert sorted(status for status, _ in results) == [201, 409], results
    with app.app_context():
        assert db.session.get(DriverWallet, driver_id).balance == Decimal("5.50")
        assert db.session.query(WalletTransaction).filter_by(promotion_id=promotion["id"]).count() == 1
