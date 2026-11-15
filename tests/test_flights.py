from fastapi.testclient import TestClient
import pytest
from main import app


def test_get_existing_flight():
    with TestClient(app) as client:
        response = client.get("/flights/1")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "flight_number": "LO123",
        "origin": "WAW",
        "destination": "LHR",
    }


def test_get_nonexistent_flight_returns_404():
    with TestClient(app) as client:
        response = client.get("/flights/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Flight not found"}


@pytest.mark.parametrize("invalid_id", ["abc", "1.5", "null"])
def test_get_flight_with_invalid_id_returns_422(invalid_id):
    with TestClient(app) as client:
        response = client.get(f"/flights/{invalid_id}")

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(
        error["loc"] == ["path", "flight_id"]
        for error in errors
    )
