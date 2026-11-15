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


def test_create_flight():
    payload = {
        "flight_number": "LO456",
        "origin": "WAW",
        "destination": "CDG",
    }

    with TestClient(app) as client:
        response = client.post("/flights", json=payload)

        assert response.status_code == 201

        created_flight = response.json()

        assert isinstance(created_flight["id"], int)
        assert created_flight["id"] > 0
        assert created_flight["flight_number"] == payload["flight_number"]
        assert created_flight["origin"] == payload["origin"]
        assert created_flight["destination"] == payload["destination"]

        saved_response = client.get(
            f"/flights/{created_flight['id']}"
        )

        assert saved_response.status_code == 200
        assert saved_response.json() == created_flight

@pytest.mark.parametrize(
    "missing_field",
    ["flight_number", "origin", "destination"],
)
def test_create_flight_without_required_field_returns_422(missing_field):
    payload = {
        "flight_number": "LO456",
        "origin": "WAW",
        "destination": "CDG",
    }
    del payload[missing_field]

    with TestClient(app) as client:
        response = client.post("/flights", json=payload)

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(
        error["loc"] == ["body", missing_field]
        and error["type"] == "missing"
        for error in errors
    )


@pytest.mark.parametrize("invalid_number", ["", "   "])
def test_create_flight_with_blank_number_returns_422(invalid_number):
    payload = {
        "flight_number": invalid_number,
        "origin": "WAW",
        "destination": "CDG",
    }

    with TestClient(app) as client:
        response = client.post("/flights", json=payload)

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(
        error["loc"] == ["body", "flight_number"]
        for error in errors
    )


def test_create_flight_trims_flight_number():
    payload = {
        "flight_number": "  LO456  ",
        "origin": "WAW",
        "destination": "CDG",
    }

    with TestClient(app) as client:
        response = client.post("/flights", json=payload)

        assert response.status_code == 201

        created_flight = response.json()
        assert created_flight["flight_number"] == "LO456"

        saved_response = client.get(
            f"/flights/{created_flight['id']}"
        )

        assert saved_response.status_code == 200
        assert saved_response.json()["flight_number"] == "LO456"


@pytest.mark.parametrize("field", ["origin", "destination"])
@pytest.mark.parametrize(
    "invalid_code",
    ["", "WA", "WAWX", "waw", "W4W", " WAW ", "ŁÓD"],
)
def test_create_flight_with_invalid_airport_returns_422(
    field, invalid_code
):
    payload = {
        "flight_number": "LO456",
        "origin": "WAW",
        "destination": "CDG",
    }
    payload[field] = invalid_code

    with TestClient(app) as client:
        response = client.post("/flights", json=payload)

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(
        error["loc"] == ["body", field]
        for error in errors
    )


def test_create_flight_with_same_airports_returns_422():
    payload = {
        "flight_number": "LO456",
        "origin": "WAW",
        "destination": "WAW",
    }

    with TestClient(app) as client:
        response = client.post("/flights", json=payload)

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(
        error["loc"] == ["body"]
        and error["type"] == "value_error"
        and "Origin and destination must be different" in error["msg"]
        for error in errors
    )
