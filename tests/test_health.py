from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_endpoint() -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_is_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/dataset/projects" in response.json()["paths"]

