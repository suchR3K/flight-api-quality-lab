from fastapi.testclient import TestClient
import pytest
from main import app


def test_list_flights_returns_separate_pages():
    with TestClient(app) as client:
        create_response = client.post(
            "/flights",
            json={
                "flight_number": "LO456",
                "origin": "WAW",
                "destination": "CDG",
            },
        )
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        first_response = client.get(
            "/flights",
            params={"limit": 1, "offset": 0},
        )
        second_response = client.get(
            "/flights",
            params={"limit": 1, "offset": 1},
        )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_page = first_response.json()
    second_page = second_response.json()

    assert first_page["total"] == 2
    assert first_page["limit"] == 1
    assert first_page["offset"] == 0
    assert len(first_page["items"]) == 1
    assert first_page["items"][0]["flight_number"] == "LO123"

    assert second_page["total"] == 2
    assert second_page["limit"] == 1
    assert second_page["offset"] == 1
    assert len(second_page["items"]) == 1
    assert second_page["items"][0]["id"] == created_id

    assert first_page["items"][0]["id"] != created_id


@pytest.mark.parametrize(
    "field, value",
    [
        ("limit", 0),
        ("limit", -1),
        ("limit", 101),
        ("limit", "abc"),
        ("offset", -1),
        ("offset", "abc"),
    ],
)
def test_list_flights_rejects_invalid_pagination(field, value):
    with TestClient(app) as client:
        response = client.get("/flights", params={field: value})

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(
        error["loc"] == ["query", field]
        for error in errors
    )


def test_list_flights_returns_empty_page_beyond_last_record():
    with TestClient(app) as client:
        response = client.get(
            "/flights",
            params={"limit": 20, "offset": 100},
        )

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 1,
        "limit": 20,
        "offset": 100,
    }


@pytest.mark.parametrize("limit", [1, 100])
def test_list_flights_accepts_limit_boundaries(limit):
    with TestClient(app) as client:
        response = client.get(
            "/flights",
            params={"limit": limit, "offset": 0},
        )

    assert response.status_code == 200

    page = response.json()
    assert page["limit"] == limit
    assert page["total"] == 1
    assert len(page["items"]) == 1


def test_list_flights_filters_by_origin_and_destination():
    with TestClient(app) as client:
        for origin, destination in [
            ("JFK", "LAX"),
            ("JFK", "ORD"),
            ("LAX", "JFK"),
        ]:
            response = client.post(
                "/flights",
                json={
                    "flight_number": "100",
                    "origin": origin,
                    "destination": destination,
                },
            )
            assert response.status_code == 201

        response = client.get(
            "/flights",
            params={
                "origin": "JFK",
                "destination": "LAX",
                "limit": 20,
                "offset": 0,
            },
        )

    assert response.status_code == 200

    page = response.json()
    assert page["total"] == 1
    assert len(page["items"]) == 1
    assert page["items"][0]["origin"] == "JFK"
    assert page["items"][0]["destination"] == "LAX"

def test_list_flights_filters_by_date_and_carrier():
    with TestClient(app) as client:
        matching_id = None

        for flight_date, carrier_code in [
            ("2025-06-01", "AA"),
            ("2025-06-02", "AA"),
            ("2025-06-01", "DL"),
        ]:
            response = client.post(
                "/flights",
                json={
                    "flight_number": "100",
                    "origin": "JFK",
                    "destination": "LAX",
                    "flight_date": flight_date,
                    "carrier_code": carrier_code,
                },
            )
            assert response.status_code == 201

            if flight_date == "2025-06-01" and carrier_code == "AA":
                matching_id = response.json()["id"]

        response = client.get(
            "/flights",
            params={
                "flight_date": "2025-06-01",
                "carrier_code": "AA",
            },
        )

    assert response.status_code == 200

    page = response.json()
    assert page["total"] == 1
    assert len(page["items"]) == 1

    flight = page["items"][0]
    assert flight["id"] == matching_id
    assert flight["flight_date"] == "2025-06-01"
    assert flight["carrier_code"] == "AA"
