"""Identity profiles persist with their accounts and do not leak to other roles."""
import pytest

from app import db
from app.models import CustomerProfile, DriverProfile, DriverWallet, User
from test_app import app, client, authenticated, login, mutate, register, registration, session


def test_customer_profile_preserves_leading_zero_and_existing_contacts(client, app):
    response = register(client, dni="00123456", license_plate="IGNORED", role="driver")
    assert response.status_code == 201
    assert response.json["user"]["dni"] == "00123456"
    assert "license_plate" not in response.json["user"]
    with app.app_context():
        customer = db.session.get(CustomerProfile, response.json["user"]["id"])
        assert customer.dni == "00123456"
        assert customer.user.first_name == "Ana"
        assert customer.user.last_name == "Ramírez"
        assert customer.user.phone == "+51 934 613 286"
        assert customer.user.email == "ana@example.com"
        assert db.session.query(DriverProfile).count() == 0


@pytest.mark.parametrize("dni", ["", "1234567", "123456789", "1234abcd", "１２３４５６７８", 12345678, None, []])
def test_invalid_dni_does_not_create_account_or_profile(client, app, dni):
    response = register(client, dni=dni)
    assert response.status_code == 400
    assert "dni" in response.json["fields"]
    with app.app_context():
        assert db.session.query(User).count() == 0
        assert db.session.query(CustomerProfile).count() == 0


def test_registration_requires_dni(client):
    payload = registration()
    del payload["dni"]
    response = mutate(client, "/api/auth/register", payload)
    assert response.status_code == 400
    assert "dni" in response.json["fields"]


def test_duplicate_customer_dni_rolls_back_account(app, client):
    assert register(client).status_code == 201
    response = register(app.test_client(), "different@example.com")
    assert response.status_code == 409
    with app.app_context():
        assert db.session.query(User).count() == 1
        assert db.session.query(CustomerProfile).count() == 1


def test_driver_profile_plate_normalization_and_duplicate_are_atomic(app):
    admin, _ = authenticated(app, "admin")
    response = mutate(admin, "/api/admin/drivers", registration("driver@example.com", dni="00234567", license_plate=" abc123 "))
    assert response.status_code == 201
    assert response.json["driver"]["dni"] == "00234567"
    assert response.json["driver"]["license_plate"] == "ABC-123"
    driver_id = response.json["driver"]["id"]
    with app.app_context():
        profile = db.session.get(DriverProfile, driver_id)
        assert profile.license_plate == "ABC-123"
        assert profile.dni == "00234567"
        assert profile.user.wallet.balance == 0
    duplicate = mutate(admin, "/api/admin/drivers", registration("different@example.com", dni="00234567"))
    assert duplicate.status_code == 409
    with app.app_context():
        assert db.session.query(User).count() == 2  # admin and the first driver
        assert db.session.query(DriverProfile).count() == 1
        assert db.session.query(DriverWallet).count() == 1
    driver = app.test_client()
    assert login(driver, "driver@example.com").status_code == 200
    assert session(driver)["user"]["license_plate"] == "ABC-123"
    assert session(driver)["user"]["dni"] == "00234567"


@pytest.mark.parametrize("plate", ["", "ABC", "AB-1234", "AB CD12", "ABC_123", "12345678", None, 123456])
def test_driver_rejects_invalid_plate_without_partial_account(app, plate):
    admin, _ = authenticated(app, "admin")
    response = mutate(admin, "/api/admin/drivers", registration("driver@example.com", license_plate=plate))
    assert response.status_code == 400
    assert "license_plate" in response.json["fields"]
    with app.app_context():
        assert db.session.query(User).count() == 1
        assert db.session.query(DriverProfile).count() == 0
        assert db.session.query(DriverWallet).count() == 0


def test_legacy_accounts_without_identity_can_still_login(app):
    driver, _ = authenticated(app, "driver")
    assert session(driver)["user"]["dni"] is None
    assert session(driver)["user"]["license_plate"] is None


def test_public_serialization_omits_dni(app, client):
    response = register(client)
    with app.app_context():
        user = db.session.get(User, response.json["user"]["id"])
        assert "dni" not in user.to_dict()
        assert user.to_dict(include_identity=True)["dni"] == "01234567"


def test_db_check_reports_missing_profile_table(app):
    with app.app_context():
        db.session.remove()
        CustomerProfile.__table__.drop(db.engine)
    result = app.test_cli_runner().invoke(args=["db-check"])
    assert result.exit_code != 0
    assert "clientes" in result.output
