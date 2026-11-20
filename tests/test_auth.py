from sqlalchemy.exc import IntegrityError

from api.endpoints import auth as auth_endpoints
from core.security import create_access_token


def test_register_integrity_error_returns_400(client, monkeypatch):
    def raise_integrity(*args, **kwargs):
        raise IntegrityError("INSERT", {}, Exception("duplicate key"))

    monkeypatch.setattr(auth_endpoints.crud_user, "create_user", raise_integrity)
    response = client.post(
        "/auth/register",
        json={
            "email": "race@example.com",
            "full_name": "Race User",
            "password": "ValidPassword123!",
        },
    )
    assert response.status_code == 400


def test_register_user_success_and_normalizes_email(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "NewUser@Example.COM",
            "full_name": "New User",
            "password": "ValidPassword123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["is_active"] is True
    assert data["is_superuser"] is False
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_email_case_insensitive_rejected(client, regular_user):
    response = client.post(
        "/auth/register",
        json={
            "email": "USER@EXAMPLE.COM",
            "full_name": "Dup User",
            "password": "ValidPassword123!",
        },
    )
    assert response.status_code == 400


def test_register_validation_errors(client):
    # Invalid email
    r1 = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "ValidPassword123!"},
    )
    assert r1.status_code == 422

    # Short password (< 8 chars)
    r2 = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "abc"},
    )
    assert r2.status_code == 422

    # Too-long password (> 72 bytes)
    r3 = client.post(
        "/auth/register",
        json={"email": "long@example.com", "password": "a" * 73},
    )
    assert r3.status_code == 422


def test_login_success_and_case_insensitive_email(client, regular_user):
    response = client.post(
        "/auth/login",
        data={"username": "  USER@example.com ", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and len(body["access_token"]) > 10


def test_login_invalid_credentials_and_overlong_password(client, regular_user):
    r_wrong = client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "WrongPassword!"},
    )
    assert r_wrong.status_code == 401

    r_unknown = client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "StrongPass123!"},
    )
    assert r_unknown.status_code == 401

    r_overlong = client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "x" * 100},
    )
    assert r_overlong.status_code == 401


def test_inactive_user_rejected_on_login_and_protected_endpoints(client, inactive_user):
    login_resp = client.post(
        "/auth/login",
        data={"username": inactive_user.email, "password": "InactivePass123!"},
    )
    assert login_resp.status_code == 403

    token = create_access_token(data={"sub": str(inactive_user.id)})
    orders_resp = client.get(
        "/orders/my-orders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert orders_resp.status_code == 403


def test_malformed_and_non_integer_jwt_sub_rejected_with_401(client):
    # Invalid signature / malformed token
    r_bad = client.get(
        "/orders/my-orders",
        headers={"Authorization": "Bearer not.a.jwt"},
    )
    assert r_bad.status_code == 401

    # Validly signed token with non-numeric sub
    bad_sub_token = create_access_token(data={"sub": "not-an-int"})
    r_str = client.get(
        "/orders/my-orders",
        headers={"Authorization": f"Bearer {bad_sub_token}"},
    )
    assert r_str.status_code == 401

    # Validly signed token with non-string sub
    int_sub_token = create_access_token(data={"sub": 123})
    r_int = client.get(
        "/orders/my-orders",
        headers={"Authorization": f"Bearer {int_sub_token}"},
    )
    assert r_int.status_code == 401

    # Validly signed token for nonexistent user
    ghost_token = create_access_token(data={"sub": "999999"})
    r_ghost = client.get(
        "/orders/my-orders",
        headers={"Authorization": f"Bearer {ghost_token}"},
    )
    assert r_ghost.status_code == 401
