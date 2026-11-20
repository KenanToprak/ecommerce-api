from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from core.database import get_db
from main import app


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the E-Commerce API!"}


def test_health_check_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "ok"}


def test_health_check_db_unavailable(client):
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise OperationalError("SELECT 1", {}, Exception("db down"))

    def broken_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy", "database": "unavailable"}


def test_cors_allows_configured_origin(client):
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_global_sqlalchemy_error_handler_hides_internals():
    class FailingSession:
        def query(self, *args, **kwargs):
            raise SQLAlchemyError("sensitive-db-internal-message")

    def failing_db():
        yield FailingSession()

    app.dependency_overrides[get_db] = failing_db
    try:
        with TestClient(app, raise_server_exceptions=False) as err_client:
            response = err_client.get("/products/")
            assert response.status_code == 500
            assert response.json() == {"detail": "Internal database error"}
    finally:
        app.dependency_overrides.clear()
