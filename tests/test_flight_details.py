from fastapi.testclient import TestClient
import pytest
from main import app


def test_create_and_read_flight_with_date_and_carrier():
    payload = {
        "flight_number": "123",
        "origin": "WAW",
        "destination": "LHR",
        "flight_date": "2025-06-15",
        "carrier_code": "LO",
    }

    with TestClient(app) as client:
        create_response = client.post("/flights", json=payload)

        assert create_response.status_code == 201

        created_flight = create_response.json()

        for field, expected_value in payload.items():
            assert field in created_flight, f"Missing field: {field}"
            assert created_flight[field] == expected_value

        flight_id = created_flight["id"]
        get_response = client.get(f"/flights/{flight_id}")

        assert get_response.status_code == 200
        assert get_response.json() == created_flight


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("flight_date", "2025-02-30"),
        ("flight_date", "not-a-date"),
        ("carrier_code", ""),
        ("carrier_code", "   "),
    ],
)
def test_create_flight_with_invalid_details_returns_422(
    field, invalid_value
):
    payload = {
        "flight_number": "123",
        "origin": "WAW",
        "destination": "LHR",
        "flight_date": "2025-06-15",
        "carrier_code": "LO",
    }
    payload[field] = invalid_value

    with TestClient(app) as client:
        response = client.post("/flights", json=payload)

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(
        error["loc"] == ["body", field]
        for error in errors
    )
