import os

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite://"

import app.db.session as session_mod

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
session_mod.engine = test_engine
session_mod.SessionLocal = sessionmaker(bind=test_engine, autoflush=False)

TestingSession = sessionmaker(bind=test_engine, autoflush=False)

from app.auth import get_current_user, require_social_subscription
from app.db.session import get_db
from app.main import app
from app.models import Base


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def _subscribed_user(user_id: str = "user-1") -> dict:
    return {
        "id": user_id,
        "email": f"{user_id}@test.com",
        "name": "Test User",
        "token": "fake-token",
    }


@pytest.fixture
def client(db):
    test_client = _make_client(db, "user-1")
    yield test_client
    test_client.close()
    app.dependency_overrides.clear()


def _make_client(db, user_id: str):
    def override_db():
        yield db

    async def override_user():
        return _subscribed_user(user_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[require_social_subscription] = override_user
    return TestClient(app)


@pytest.fixture
def user_client(db):
    clients: list[TestClient] = []

    def _factory(user_id: str):
        test_client = _make_client(db, user_id)
        clients.append(test_client)
        return test_client

    yield _factory
    for test_client in clients:
        test_client.close()
    app.dependency_overrides.clear()


@pytest.fixture
def no_subscription_client(db):
    def override_db():
        yield db

    async def override_user():
        return _subscribed_user()

    async def deny_subscription():
        raise HTTPException(status_code=403, detail="Social subscription required")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[require_social_subscription] = deny_subscription
    test_client = TestClient(app)
    yield test_client
    test_client.close()
    app.dependency_overrides.clear()
