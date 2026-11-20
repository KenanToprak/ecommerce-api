import os

# Configure isolated test settings before importing application modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-automated-pytest-suite"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from core.security import create_access_token, get_password_hash
from main import app
from models.product import Product
from models.user import User

TEST_SQLALCHEMY_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def regular_user(db_session) -> User:
    user = User(
        email="user@example.com",
        full_name="Regular User",
        hashed_password=get_password_hash("StrongPass123!"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_user(db_session) -> User:
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("AdminPass123!"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def inactive_user(db_session) -> User:
    user = User(
        email="inactive@example.com",
        full_name="Inactive User",
        hashed_password=get_password_hash("InactivePass123!"),
        is_active=False,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def user_headers(regular_user: User) -> dict[str, str]:
    token = create_access_token(data={"sub": str(regular_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(admin_user: User) -> dict[str, str]:
    token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_products(db_session) -> list[Product]:
    products = [
        Product(name="Mechanical Keyboard", description="RGB", price=99.99, stock_quantity=10),
        Product(name="USB-C Mouse", description="Wireless", price=25.50, stock_quantity=3),
    ]
    db_session.add_all(products)
    db_session.commit()
    for p in products:
        db_session.refresh(p)
    return products
