"""Integration tests against the API, with CSRF and role checks enabled.

TEST_DATABASE_URL is destructive ONLY for an isolated schema whose name starts
with jage_test. Never point it at the application's database.
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.engine import make_url

from app import create_app, db
from app.models import DriverWallet, Promotion, Reservation, User, WalletTransaction


PASSWORD = "Jage-pruebas-2026-seguras"
LIMA = ZoneInfo("America/Lima")


@pytest.fixture
def app():
    database_url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    parsed_url = make_url(database_url)
    if parsed_url.drivername.startswith("sqlite"):
        if parsed_url.database not in (None, "", ":memory:"):
            raise RuntimeError("Las pruebas SQLite solo pueden usar memoria.")
    elif not (parsed_url.database or "").startswith("jage_test"):
        raise RuntimeError("TEST_DATABASE_URL requiere una base aislada jage_test*.")
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only-secret-key-never-use-in-production",
            "SQLALCHEMY_DATABASE_URI": database_url,
            "SESSION_COOKIE_SECURE": False,
            "WTF_CSRF_ENABLED": True,
            "RATELIMIT_ENABLED": False,
        }
    )
    with application.app_context():
        db.drop_all()
        db.create_all()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def session(client):
    response = client.get("/api/session")
    assert response.status_code == 200, response.get_data(as_text=True)
    assert response.is_json
    assert response.json["csrf_token"]
    return response.json


def mutate(client, path, payload=None, method="POST", headers=None):
    request_headers = {"X-CSRFToken": session(client)["csrf_token"]}
    request_headers.update(headers or {})
    return client.open(path, method=method, json=payload or {}, headers=request_headers)


def registration(email="ana@example.com", **overrides):
    result = {
        "first_name": "Ana",
        "last_name": "Ramírez",
        "phone": "+51 934 613 286",
        "dni": "01234567",
        "license_plate": "ABC-123",
        "email": email,
        "password": PASSWORD,
    }
    result.update(overrides)
    return result


def register(client, email="ana@example.com", **overrides):
    return mutate(client, "/api/auth/register", registration(email, **overrides))


def seed_user(app, email, role):
    with app.app_context():
        user = User(
            first_name="Cuenta",
            last_name="Pruebas",
            email=email,
            phone="51934613286",
            role=role,
        )
        user.set_password(PASSWORD)
        db.session.add(user)
        if role == "driver":
            user.wallet = DriverWallet(balance=Decimal("0.00"))
        db.session.commit()
        return user.id


def login(client, email="ana@example.com", password=PASSWORD):
    return mutate(client, "/api/auth/login", {"email": email, "password": password})


def authenticated(app, role="passenger", email=None):
    email = email or f"{role}-{uuid4().hex}@example.com"
    user_id = seed_user(app, email, role)
    account = app.test_client()
    response = login(account, email)
    assert response.status_code == 200, response.get_data(as_text=True)
    return account, user_id


def booking(**overrides):
    result = {
        "service": "huaral-lima",
        "origin": "Plaza de Armas, Huaral",
        "destination": "Lima, dirección de llegada",
        "travel_date": (datetime.now(LIMA) + timedelta(days=2)).date().isoformat(),
        "travel_time": "10:30",
        "passengers": 2,
        "notes": "Una maleta.",
    }
    result.update(overrides)
    return result


def assert_error(response, status):
    assert response.status_code == status, response.get_data(as_text=True)
    assert response.is_json
    assert isinstance(response.json.get("error"), str)
    assert response.json["error"]


def create_booking(client, **overrides):
    response = mutate(client, "/api/reservations", booking(**overrides))
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.json["reservation"]


def balance_adjustment(admin, driver_id, amount="30.00", **overrides):
    data = {"amount": amount, "reason": "Recarga registrada para comisiones", "idempotency_key": str(uuid4())}
    data.update(overrides)
    return mutate(admin, f"/api/admin/drivers/{driver_id}/balance", data)


def change_reservation(admin, reservation_id, **values):
    return mutate(admin, f"/api/admin/reservations/{reservation_id}", values, method="PATCH")


def create_promotion(admin, **overrides):
    data = {"title": "Crédito para comisiones", "description": "Promoción de prueba controlada.",
            "amount": "5.50", "expires_at": (datetime.now(LIMA) + timedelta(days=5)).date().isoformat(),
            "active": True}
    data.update(overrides)
    response = mutate(admin, "/api/admin/promotions", data)
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.json["promotion"]


def test_anonymous_session_issues_csrf_and_httponly_cookie(client):
    response = client.get("/api/session")
    assert response.status_code == 200
    assert response.json["user"] is None
    assert response.json["csrf_token"]
    cookie = response.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "no-store" in response.headers.get("Cache-Control", "")


@pytest.mark.parametrize("injected_role", ["admin", "driver", {"role": "admin"}])
def test_registration_forces_passenger_and_hashes_password(client, app, injected_role):
    response = register(client, "ANA@EXAMPLE.COM", role=injected_role, first_name="  Ana  ")
    assert response.status_code == 201, response.get_data(as_text=True)
    assert response.json["user"]["role"] == "passenger"
    assert response.json["user"]["email"] == "ana@example.com"
    assert "password" not in response.json["user"]
    assert "password_hash" not in response.json["user"]
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.email == "ana@example.com"))
        assert user.role == User.ROLE_PASSENGER
        assert user.first_name == "Ana"
        assert user.password_hash.startswith("scrypt:")
        assert user.password_hash != PASSWORD
        assert user.check_password(PASSWORD)


def test_duplicate_email_is_normalized_and_not_inserted_twice(client, app):
    assert register(client).status_code == 201
    other = app.test_client()
    assert_error(register(other, " ANA@EXAMPLE.COM "), 409)
    with app.app_context():
        assert db.session.query(User).count() == 1


@pytest.mark.parametrize("field,value", [
    ("first_name", ""), ("first_name", "a" * 81), ("first_name", 5),
    ("last_name", "  "), ("last_name", []), ("last_name", "a" * 81),
    ("phone", "-------"), ("phone", "abcdefghi"), ("phone", "1" * 21), ("phone", None),
    ("email", "sin-arroba.example.com"), ("email", "a@@example.com"),
    ("email", "a b@example.com"), ("email", "a" * 250 + "@e.com"), ("email", {}),
    ("password", "short"), ("password", "x" * 129), ("password", " " * 12),
    ("password", None), ("first_name", "Ana\x00Ramírez"),
])
def test_registration_rejects_malformed_values(client, app, field, value):
    data = registration()
    data[field] = value
    assert_error(mutate(client, "/api/auth/register", data), 400)
    with app.app_context():
        assert db.session.query(User).count() == 0


def test_mutations_require_json_object(client):
    token = session(client)["csrf_token"]
    assert_error(client.post("/api/auth/register", data={"email": "a@example.com"},
                             headers={"X-CSRFToken": token}), 415)
    assert_error(client.post("/api/auth/register", json=[registration()],
                             headers={"X-CSRFToken": token}), 400)
    assert_error(client.post("/api/auth/register", data="{broken-json", content_type="application/json",
                             headers={"X-CSRFToken": token}), 400)


def test_csrf_missing_invalid_and_other_browser_are_rejected(client, app):
    assert_error(client.post("/api/auth/register", json=registration()), 400)
    assert_error(client.post("/api/auth/register", json=registration(),
                             headers={"X-CSRFToken": "not-valid"}), 400)
    unrelated_token = session(app.test_client())["csrf_token"]
    session(client)
    assert_error(client.post("/api/auth/register", json=registration(),
                             headers={"X-CSRFToken": unrelated_token}), 400)


def test_login_logout_rotate_csrf_and_end_authenticated_access(client, app):
    before = session(client)["csrf_token"]
    registered = register(client)
    assert registered.status_code == 201
    assert registered.json["csrf_token"] != before
    assert_error(client.post("/api/auth/logout", json={}, headers={"X-CSRFToken": before}), 400)
    assert session(client)["user"]["email"] == "ana@example.com"
    logout = mutate(client, "/api/auth/logout")
    assert logout.status_code == 200
    assert logout.json["user"] is None
    assert logout.json["csrf_token"] != registered.json["csrf_token"]
    assert_error(client.get("/api/reservations"), 401)
    assert login(client, "ANA@EXAMPLE.COM").status_code == 200
    assert session(client)["user"]["email"] == "ana@example.com"
    assert_error(mutate(client, "/api/auth/register", registration("other@example.com")), 409)


def test_failed_login_has_generic_error_and_sql_input_cannot_bypass_auth(client, app):
    seed_user(app, "ana@example.com", "passenger")
    wrong_password = login(client, password="incorrect-password")
    unknown_user = login(client, "missing@example.com")
    injected = login(client, "' OR 1=1 --")
    for response in (wrong_password, unknown_user, injected):
        assert_error(response, 401)
    assert wrong_password.json["error"] == unknown_user.json["error"]
    assert session(client)["user"] is None


def test_security_headers_and_secure_cookie_configuration(client, app):
    response = client.get("/api/session")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Content-Security-Policy" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    app.config["SESSION_COOKIE_SECURE"] = True
    secure_response = app.test_client().get("/api/session")
    assert "Secure" in secure_response.headers["Set-Cookie"]


def test_anonymous_reservation_requests_require_authentication(client):
    assert_error(client.get("/api/reservations"), 401)
    assert_error(client.get("/api/reservations/1"), 401)
    assert_error(mutate(client, "/api/reservations", booking()), 401)


def test_reservation_is_pending_owned_by_session_and_ignores_privileged_fields(app):
    passenger, passenger_id = authenticated(app)
    other, other_id = authenticated(app)
    reservation = create_booking(passenger, user_id=other_id, status="completada",
                                 driver_id=other_id, commission="999.99", commission_charged=True)
    assert reservation["status"] == "pendiente"
    assert reservation["user_id"] == passenger_id
    assert reservation["driver_id"] is None
    assert reservation["commission"] is None
    assert reservation["commission_charged"] is False
    with app.app_context():
        stored = db.session.get(Reservation, reservation["id"])
        assert stored.user_id == passenger_id
        assert stored.status == "pendiente"


def test_passenger_only_sees_own_reservations_and_detail(app):
    passenger, _ = authenticated(app)
    other, _ = authenticated(app)
    own = create_booking(passenger, origin="Origen privado Ana 9821")
    second = create_booking(other, origin="Origen privado Bea 9172")
    response = passenger.get("/api/reservations")
    assert response.status_code == 200
    assert [item["id"] for item in response.json["reservations"]] == [own["id"]]
    assert "Bea 9172" not in response.get_data(as_text=True)
    assert_error(passenger.get(f"/api/reservations/{second['id']}"), 404)
    assert_error(passenger.get("/api/reservations/99999999"), 404)
    assert passenger.get(f"/api/reservations/{own['id']}").status_code == 200


@pytest.mark.parametrize("field,value", [
    ("service", "inventado"), ("service", []), ("origin", ""), ("origin", "x" * 181),
    ("destination", " "), ("destination", "x" * 181), ("destination", {}),
    ("travel_date", "2026-02-30"), ("travel_date", "01/10/2030"),
    ("travel_time", "24:10"), ("travel_time", "9:30"), ("travel_time", "10:00:30"),
    ("passengers", 0), ("passengers", 9), ("passengers", True), ("passengers", False),
    ("passengers", 1.5), ("passengers", "2"), ("passengers", None),
    ("notes", "x" * 1001), ("notes", []),
])
def test_reservation_backend_validates_fields(app, field, value):
    passenger, _ = authenticated(app)
    assert_error(mutate(passenger, "/api/reservations", booking(**{field: value})), 400)
    with app.app_context():
        assert db.session.query(Reservation).count() == 0


def test_reservation_rejects_past_hour_in_lima_but_accepts_future_hour(app, monkeypatch):
    frozen_now = datetime(2030, 1, 15, 12, 0, tzinfo=LIMA)
    monkeypatch.setattr("app.reservations.lima_now", lambda: frozen_now)
    passenger, _ = authenticated(app)
    for date_value, time_value in [("2030-01-14", "23:59"), ("2030-01-15", "11:59"), ("2030-01-15", "12:00")]:
        assert_error(mutate(passenger, "/api/reservations", booking(travel_date=date_value, travel_time=time_value)), 400)
    assert create_booking(passenger, travel_date="2030-01-15", travel_time="12:01")["status"] == "pendiente"


@pytest.mark.parametrize("role", ["passenger", "driver"])
def test_non_admin_cannot_read_or_mutate_administration(app, role):
    actor, _ = authenticated(app, role)
    for endpoint in ("/api/admin/reservations", "/api/admin/drivers", "/api/admin/promotions"):
        assert_error(actor.get(endpoint), 403)
    for endpoint, method, payload in [
        ("/api/admin/drivers", "POST", registration("new-driver@example.com")),
        ("/api/admin/reservations/1", "PATCH", {"status": "confirmada"}),
        ("/api/admin/drivers/1/balance", "POST", {"amount": "50.00"}),
        ("/api/admin/promotions", "POST", {"title": "Sin permiso"}),
        ("/api/admin/promotions/1", "PATCH", {"active": False}),
    ]:
        assert_error(mutate(actor, endpoint, payload, method), 403)


@pytest.mark.parametrize("role", ["admin", "driver"])
def test_only_passengers_can_create_requests(app, role):
    actor, _ = authenticated(app, role)
    assert_error(mutate(actor, "/api/reservations", booking()), 403)


@pytest.mark.parametrize("role", ["passenger", "admin"])
def test_driver_dashboard_and_redemptions_require_driver_role(app, role):
    actor, _ = authenticated(app, role)
    assert_error(actor.get("/api/driver/dashboard"), 403)
    assert_error(mutate(actor, "/api/driver/promotions/1/redeem"), 403)


def test_admin_creates_driver_with_zero_balance_and_cannot_inject_admin_role(app):
    admin, admin_id = authenticated(app, "admin")
    response = mutate(admin, "/api/admin/drivers", registration("driver@example.com", role="admin"))
    assert response.status_code == 201, response.get_data(as_text=True)
    driver = response.json["driver"]
    assert driver["role"] == "driver"
    assert driver["balance"] == "0.00"
    assert "password_hash" not in driver
    assert session(admin)["user"]["id"] == admin_id
    with app.app_context():
        stored = db.session.get(User, driver["id"])
        assert stored.check_password(PASSWORD)
        assert stored.wallet.balance == Decimal("0.00")
    assert_error(mutate(admin, "/api/admin/drivers", registration("DRIVER@EXAMPLE.COM")), 409)
    driver_client = app.test_client()
    assert login(driver_client, "driver@example.com").status_code == 200
    assert driver_client.get("/api/driver/dashboard").json["balance"] == "0.00"


def test_admin_reads_all_reservations_and_drivers_without_passwords(app):
    admin, _ = authenticated(app, "admin")
    passenger, _ = authenticated(app)
    another, _ = authenticated(app)
    _, driver_id = authenticated(app, "driver")
    first = create_booking(passenger)
    second = create_booking(another)
    result = admin.get("/api/admin/reservations")
    assert result.status_code == 200
    assert {r["id"] for r in result.json["reservations"]} == {first["id"], second["id"]}
    assert "email" in result.json["reservations"][0]["user"]
    assert "password" not in result.get_data(as_text=True)
    listed = admin.get("/api/admin/drivers")
    assert [driver["id"] for driver in listed.json["drivers"]] == [driver_id]


def test_driver_sees_only_assigned_trips_own_ledger_and_minimal_passenger_details(app):
    admin, _ = authenticated(app, "admin")
    passenger, _ = authenticated(app)
    driver, driver_id = authenticated(app, "driver")
    other_driver, other_id = authenticated(app, "driver")
    mine = create_booking(passenger, origin="Origen asignado único 125")
    other = create_booking(passenger, origin="Origen privado otro conductor 995")
    unassigned = create_booking(passenger)
    assert change_reservation(admin, mine["id"], driver_id=driver_id, commission="1.00").status_code == 200
    assert change_reservation(admin, other["id"], driver_id=other_id, commission="2.00").status_code == 200
    assert balance_adjustment(admin, driver_id, "10.00", reason="Recarga propia 452").status_code == 201
    assert balance_adjustment(admin, other_id, "22.00", reason="Recarga privada otro 996").status_code == 201
    response = driver.get("/api/driver/dashboard?driver_id=" + str(other_id))
    assert response.status_code == 200
    assert response.json["balance"] == "10.00"
    assert [item["id"] for item in response.json["reservations"]] == [mine["id"]]
    assert {item["driver_id"] for item in response.json["transactions"]} == {driver_id}
    assert "email" not in response.json["reservations"][0]["user"]
    assert set(response.json["reservations"][0]["user"]) == {"first_name", "last_name", "phone"}
    assert "otro conductor 995" not in response.get_data(as_text=True)
    assert "privada otro 996" not in response.get_data(as_text=True)
    assert_error(driver.get(f"/api/reservations/{other['id']}"), 404)
    assert_error(driver.get(f"/api/reservations/{unassigned['id']}"), 404)
    assert other_driver.get("/api/driver/dashboard").json["balance"] == "22.00"


def test_manual_assignment_confirmation_and_single_commission_at_completion(app):
    admin, admin_id = authenticated(app, "admin")
    passenger, _ = authenticated(app)
    driver, driver_id = authenticated(app, "driver")
    reservation = create_booking(passenger)
    assert balance_adjustment(admin, driver_id, "30.00").status_code == 201
    confirmed = change_reservation(admin, reservation["id"], status="confirmada", driver_id=driver_id, commission="7.25")
    assert confirmed.status_code == 200
    assert confirmed.json["reservation"]["driver"]["id"] == driver_id
    assert driver.get("/api/driver/dashboard").json["balance"] == "30.00"
    completed = change_reservation(admin, reservation["id"], status="completada")
    assert completed.status_code == 200, completed.get_data(as_text=True)
    assert completed.json["reservation"]["commission_charged"] is True
    assert completed.json["reservation"]["status"] == "completada"
    assert change_reservation(admin, reservation["id"], status="completada").status_code == 200
    dashboard = driver.get("/api/driver/dashboard").json
    assert dashboard["balance"] == "22.75"
    commissions = [entry for entry in dashboard["transactions"] if entry["kind"] == "commission"]
    assert len(commissions) == 1
    assert commissions[0]["amount"] == "-7.25"
    assert commissions[0]["reservation_id"] == reservation["id"]
    assert commissions[0]["actor_id"] == admin_id
    with app.app_context():
        assert db.session.query(WalletTransaction).filter_by(reservation_id=reservation["id"]).count() == 1


def test_insufficient_balance_rolls_back_completion_commission_and_ledger(app):
    admin, _ = authenticated(app, "admin")
    passenger, _ = authenticated(app)
    driver, driver_id = authenticated(app, "driver")
    reservation = create_booking(passenger)
    assert balance_adjustment(admin, driver_id, "5.00").status_code == 201
    assert change_reservation(admin, reservation["id"], status="confirmada", driver_id=driver_id, commission="10.00").status_code == 200
    assert_error(change_reservation(admin, reservation["id"], status="completada", commission="12.00"), 409)
    with app.app_context():
        stored = db.session.get(Reservation, reservation["id"])
        assert stored.status == "confirmada"
        assert stored.commission == Decimal("10.00")
        assert stored.commission_charged is False
        assert db.session.get(DriverWallet, driver_id).balance == Decimal("5.00")
        assert db.session.query(WalletTransaction).filter_by(kind="commission").count() == 0
    assert balance_adjustment(admin, driver_id, "5.00").status_code == 201
    assert change_reservation(admin, reservation["id"], status="completada").status_code == 200
    assert driver.get("/api/driver/dashboard").json["balance"] == "0.00"


def test_completion_requires_prior_confirmation_driver_and_commission(app):
    admin, _ = authenticated(app, "admin")
    passenger, _ = authenticated(app)
    _, driver_id = authenticated(app, "driver")
    reservation = create_booking(passenger)
    assert_error(change_reservation(admin, reservation["id"], status="completada"), 409)
    assert change_reservation(admin, reservation["id"], status="confirmada").status_code == 200
    assert_error(change_reservation(admin, reservation["id"], status="completada"), 409)
    assert change_reservation(admin, reservation["id"], driver_id=driver_id).status_code == 200
    assert_error(change_reservation(admin, reservation["id"], status="completada"), 409)
    # A waived commission is an explicit 0.00, not an omitted commission.
    assert change_reservation(admin, reservation["id"], status="completada", commission="0.00").status_code == 200
    with app.app_context():
        assert db.session.get(DriverWallet, driver_id).balance == Decimal("0.00")
        assert db.session.get(Reservation, reservation["id"]).commission_charged is True


@pytest.mark.parametrize("final_status", ["cancelada", "completada"])
def test_final_reservations_cannot_be_reopened_or_reassigned(app, final_status):
    admin, _ = authenticated(app, "admin")
    passenger, _ = authenticated(app)
    _, driver_id = authenticated(app, "driver")
    _, other_driver_id = authenticated(app, "driver")
    reservation = create_booking(passenger)
    assert change_reservation(admin, reservation["id"], status="confirmada", driver_id=driver_id, commission="0.00").status_code == 200
    assert change_reservation(admin, reservation["id"], status=final_status).status_code == 200
    for change in ({"status": "confirmada"}, {"status": "pendiente"}, {"driver_id": other_driver_id}, {"commission": "1.00"}):
        assert_error(change_reservation(admin, reservation["id"], **change), 409)
    if final_status == "cancelada":
        with app.app_context():
            assert db.session.query(WalletTransaction).filter_by(kind="commission").count() == 0


@pytest.mark.parametrize("values", [
    {"status": "inventado"}, {"status": []}, {"driver_id": True}, {"driver_id": "1"},
    {"driver_id": -1}, {"driver_id": 999999}, {"commission": "-0.01"},
    {"commission": 10.5}, {"commission": "10.001"}, {"commission": "NaN"},
])
def test_admin_rejects_invalid_assignment_and_commission_values(app, values):
    admin, _ = authenticated(app, "admin")
    passenger, _ = authenticated(app)
    reservation = create_booking(passenger)
    assert_error(change_reservation(admin, reservation["id"], **values), 400)


def test_admin_cannot_assign_passenger_or_admin_as_driver(app):
    admin, admin_id = authenticated(app, "admin")
    passenger, passenger_id = authenticated(app)
    reservation = create_booking(passenger)
    assert_error(change_reservation(admin, reservation["id"], driver_id=passenger_id), 400)
    assert_error(change_reservation(admin, reservation["id"], driver_id=admin_id), 400)
    assert_error(change_reservation(admin, 99999999, status="confirmada"), 404)


def test_wallet_adjustments_are_exact_audited_and_idempotent(app):
    admin, admin_id = authenticated(app, "admin")
    driver, driver_id = authenticated(app, "driver")
    key = str(uuid4())
    first = balance_adjustment(admin, driver_id, "10.10", idempotency_key=key)
    assert first.status_code == 201
    repeated = balance_adjustment(admin, driver_id, "10.10", idempotency_key=key)
    assert repeated.status_code == 200
    assert first.json["transaction"]["id"] == repeated.json["transaction"]["id"]
    assert repeated.json["balance"] == "10.10"
    adjustment = balance_adjustment(admin, driver_id, "-0.10", reason="Corrección documentada")
    assert adjustment.status_code == 201
    assert adjustment.json["balance"] == "10.00"
    assert adjustment.json["transaction"]["actor_id"] == admin_id
    assert adjustment.json["transaction"]["reason"] == "Corrección documentada"
    dashboard = driver.get("/api/driver/dashboard").json
    assert dashboard["balance"] == "10.00"
    assert len(dashboard["transactions"]) == 2


def test_wallet_rejects_reused_key_with_changed_data_or_different_driver(app):
    admin, _ = authenticated(app, "admin")
    _, first_driver = authenticated(app, "driver")
    _, second_driver = authenticated(app, "driver")
    key = str(uuid4())
    assert balance_adjustment(admin, first_driver, "5.00", idempotency_key=key).status_code == 201
    assert_error(balance_adjustment(admin, first_driver, "6.00", idempotency_key=key), 409)
    assert_error(balance_adjustment(admin, first_driver, "5.00", reason="Motivo distinto", idempotency_key=key), 409)
    assert_error(balance_adjustment(admin, second_driver, "5.00", idempotency_key=key), 409)
    with app.app_context():
        assert db.session.get(DriverWallet, first_driver).balance == Decimal("5.00")
        assert db.session.get(DriverWallet, second_driver).balance == Decimal("0.00")


def test_wallet_balance_cannot_become_negative_or_exceed_limit(app):
    admin, _ = authenticated(app, "admin")
    driver, driver_id = authenticated(app, "driver")
    assert_error(balance_adjustment(admin, driver_id, "-0.01"), 409)
    assert balance_adjustment(admin, driver_id, "99999999.99").status_code == 201
    assert_error(balance_adjustment(admin, driver_id, "0.01"), 409)
    dashboard = driver.get("/api/driver/dashboard").json
    assert dashboard["balance"] == "99999999.99"
    assert len(dashboard["transactions"]) == 1


@pytest.mark.parametrize("field,value", [
    ("amount", 5), ("amount", True), ("amount", "0.00"), ("amount", "NaN"),
    ("amount", "Infinity"), ("amount", "1e2"), ("amount", "1.001"),
    ("amount", "100000000.00"), ("reason", ""), ("reason", "x" * 301),
    ("idempotency_key", "not-a-uuid"), ("idempotency_key", ""),
])
def test_wallet_adjustment_validates_amount_reason_and_uuid(app, field, value):
    admin, _ = authenticated(app, "admin")
    _, driver_id = authenticated(app, "driver")
    assert_error(balance_adjustment(admin, driver_id, **{field: value}), 400)
    with app.app_context():
        assert db.session.get(DriverWallet, driver_id).balance == Decimal("0.00")
        assert db.session.query(WalletTransaction).count() == 0


def test_wallet_adjustment_cannot_target_a_passenger(app):
    admin, _ = authenticated(app, "admin")
    _, passenger_id = authenticated(app)
    assert_error(balance_adjustment(admin, passenger_id), 404)


def test_promotion_credit_is_once_per_driver_and_records_actor(app):
    admin, _ = authenticated(app, "admin")
    first, first_id = authenticated(app, "driver")
    second, second_id = authenticated(app, "driver")
    promotion = create_promotion(admin)
    redeemed = mutate(first, f"/api/driver/promotions/{promotion['id']}/redeem", {"driver_id": second_id})
    assert redeemed.status_code == 201
    assert redeemed.json["balance"] == "5.50"
    assert redeemed.json["transaction"]["driver_id"] == first_id
    assert redeemed.json["transaction"]["actor_id"] == first_id
    assert redeemed.json["promotion"]["redeemed"] is True
    assert_error(mutate(first, f"/api/driver/promotions/{promotion['id']}/redeem"), 409)
    assert second.get("/api/driver/dashboard").json["balance"] == "0.00"
    assert mutate(second, f"/api/driver/promotions/{promotion['id']}/redeem").status_code == 201
    assert first.get("/api/driver/dashboard").json["promotions"][0]["redeemed"] is True
    with app.app_context():
        assert db.session.query(WalletTransaction).filter_by(promotion_id=promotion["id"]).count() == 2


def test_expired_and_deactivated_promotions_cannot_be_redeemed(app, monkeypatch):
    admin, _ = authenticated(app, "admin")
    driver, _ = authenticated(app, "driver")
    active = create_promotion(admin)
    inactive = create_promotion(admin, active=False)
    deactivated = mutate(admin, f"/api/admin/promotions/{active['id']}", {"active": False}, method="PATCH")
    assert deactivated.status_code == 200
    assert driver.get("/api/driver/dashboard").json["promotions"] == []
    for promotion in (active, inactive):
        assert_error(mutate(driver, f"/api/driver/promotions/{promotion['id']}/redeem"), 409)
    assert mutate(admin, f"/api/admin/promotions/{active['id']}", {"active": True}, method="PATCH").status_code == 200
    future = datetime.now(LIMA) + timedelta(days=10)
    monkeypatch.setattr("app.drivers.lima_now", lambda: future)
    assert driver.get("/api/driver/dashboard").json["promotions"] == []
    assert_error(mutate(driver, f"/api/driver/promotions/{active['id']}/redeem"), 409)
    assert_error(mutate(driver, "/api/driver/promotions/99999999/redeem"), 404)
    with app.app_context():
        assert db.session.query(WalletTransaction).count() == 0


@pytest.mark.parametrize("values", [
    {"amount": "-1.00"}, {"amount": "0.00"}, {"amount": 5}, {"amount": "1.001"},
    {"title": ""}, {"title": "x" * 121}, {"description": "x" * 501},
    {"active": "false"}, {"expires_at": "2020-01-01"}, {"expires_at": "2030-02-30"},
])
def test_promotion_creation_validates_fields(app, values):
    admin, _ = authenticated(app, "admin")
    data = {"title": "Prueba", "description": "", "amount": "5.00", "active": True,
            "expires_at": (datetime.now(LIMA) + timedelta(days=5)).date().isoformat()}
    data.update(values)
    assert_error(mutate(admin, "/api/admin/promotions", data), 400)
    with app.app_context():
        assert db.session.query(Promotion).count() == 0


def test_promotion_toggle_requires_boolean_and_existing_resource(app):
    admin, _ = authenticated(app, "admin")
    promotion = create_promotion(admin)
    assert_error(mutate(admin, f"/api/admin/promotions/{promotion['id']}", {"active": "false"}, method="PATCH"), 400)
    assert_error(mutate(admin, "/api/admin/promotions/99999999", {"active": False}, method="PATCH"), 404)
