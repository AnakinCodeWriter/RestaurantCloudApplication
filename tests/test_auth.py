import pytest
from werkzeug.security import check_password_hash

from app.main import create_app
from app.models import db, User


@pytest.fixture()
def app():
    app = create_app()
    # Use an in-memory DB for tests (fast, isolated)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_register_creates_user(client, app):
    resp = client.post("/register", data={"email": "test@example.com", "password": "pass123"}, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user is not None
        assert user.email == "test@example.com"
        assert check_password_hash(user.password_hash, "pass123")


def test_login_sets_session(client):
    # Register first
    client.post("/register", data={"email": "login@example.com", "password": "pass123"}, follow_redirects=True)

    # Then login
    resp = client.post("/login", data={"email": "login@example.com", "password": "pass123"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Dashboard" in resp.data  # user is redirected to dashboard


def test_dashboard_requires_login(client):
    resp = client.get("/dashboard", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Login" in resp.data