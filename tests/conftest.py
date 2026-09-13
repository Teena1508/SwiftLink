import pytest
from app import create_app
from app.models import db, User
from config import TestingConfig
from app.utils.rate_limiter import rate_limiter

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    rate_limiter.reset()
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    rate_limiter.reset()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            api_key="test_api_key_12345"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        # Return a dictionary or simple data object to prevent SQLAlchemy DetachedInstanceError
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "api_key": user.api_key
        }
