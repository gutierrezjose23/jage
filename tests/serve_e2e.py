"""Isolated E2E server. Never starts against a normal application database."""
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.engine import make_url
from app import create_app, db
from app.models import User, DriverWallet

uri = os.environ.get("TEST_DATABASE_URL", "sqlite://")
if uri != "sqlite://" and not (make_url(uri).database or "").startswith("jage_test"):
    raise RuntimeError("E2E requiere una base aislada jage_test*.")
password = os.environ["JAGE_E2E_PASSWORD"]
application = create_app({
    "TESTING": True, "SECRET_KEY": secrets.token_hex(32),
    "SQLALCHEMY_DATABASE_URI": uri, "SESSION_COOKIE_SECURE": False,
    "RATELIMIT_ENABLED": False,
})
with application.app_context():
    db.drop_all()
    db.create_all()
    for role in ("admin", "driver"):
        user = User(first_name="Prueba", last_name="JAGE", phone="934613286",
                    email=f"{role}@example.test", role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        if role == "driver":
            db.session.add(DriverWallet(driver_id=user.id, balance=0))
    db.session.commit()

# Flask-SQLAlchemy shares one SQLite in-memory connection across requests.
# Serialize this fixture to avoid concurrent transactions on that connection;
# the MySQL test mode retains threaded requests for its independent connections.
application.run(host="127.0.0.1", port=5010, debug=False, use_reloader=False,
                threaded=uri != "sqlite://")
