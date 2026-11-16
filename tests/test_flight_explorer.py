import pytest
from fastapi.testclient import TestClient

from main import app


def create_flight(client, **changes):
    payload = {
        "flight_number": "100",
        "origin": "JFK",
        "destination": "LAX",
        "flight_date": "2025-06-01",
        "carrier_code": "AA",
    }
    payload.update(changes)

    response = client.post("/flights", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_all_filters_work_together():
    with TestClient(app) as client:
        expected = create_flight(client)

        create_flight(client, origin="BOS")
        create_flight(client, destination="ORD")
        create_flight(client, flight_date="2025-06-02")
        create_flight(client, carrier_code="DL")

        response = client.get(
            "/flights",
            params={
                "origin": "JFK",
                "destination": "LAX",
                "flight_date": "2025-06-01",
                "carrier_code": "AA",
            },
        )

    assert response.status_code == 200
    page = response.json()
    assert page["total"] == 1
    assert page["items"] == [expected]


@pytest.mark.parametrize(
    "sort_order, expected_dates",
    [
        ("asc", ["2025-06-01", "2025-06-02", "2025-06-03"]),
        ("desc", ["2025-06-03", "2025-06-02", "2025-06-01"]),
    ],
)
def test_sort_by_date(sort_order, expected_dates):
    with TestClient(app) as client:
        for day in ["2025-06-03", "2025-06-01", "2025-06-02"]:
            create_flight(client, flight_date=day)

        response = client.get(
            "/flights",
            params={
                "carrier_code": "AA",
                "sort_by": "flight_date",
                "sort_order": sort_order,
            },
        )

    assert response.status_code == 200
    page = response.json()
    assert page["total"] == 3
    assert [
        flight["flight_date"] for flight in page["items"]
    ] == expected_dates


def test_equal_sort_values_have_stable_pagination():
    with TestClient(app) as client:
        created = [
            create_flight(client, flight_number=number)
            for number in ["300", "100", "200"]
        ]

        received_ids = []

        for offset in range(3):
            response = client.get(
                "/flights",
                params={
                    "carrier_code": "AA",
                    "sort_by": "flight_date",
                    "limit": 1,
                    "offset": offset,
                },
            )

            assert response.status_code == 200
            page = response.json()
            assert page["total"] == 3
            assert len(page["items"]) == 1
            received_ids.append(page["items"][0]["id"])

    # All dates are equal, so the secondary ordering must use ID.
    assert received_ids == sorted(flight["id"] for flight in created)
    assert len(set(received_ids)) == 3


def test_date_sort_places_missing_dates_last():
    with TestClient(app) as client:
        dated = create_flight(client)

        response = client.get(
            "/flights",
            params={"sort_by": "flight_date", "sort_order": "asc"},
        )

    assert response.status_code == 200
    items = response.json()["items"]

    assert len(items) == 2
    assert items[0]["id"] == dated["id"]
    assert items[1]["flight_number"] == "LO123"
    assert "flight_date" not in items[1]


@pytest.mark.parametrize(
    "field, value",
    [
        ("sort_by", "unknown_column"),
        ("sort_by", "id; DROP TABLE flights"),
        ("sort_order", "sideways"),
        ("flight_date", "2025-02-30"),
        ("flight_date", "not-a-date"),
        ("origin", "jfk"),
        ("destination", "LAXX"),
        ("carrier_code", "aa"),
        ("carrier_code", " "),
    ],
)
def test_invalid_search_parameters_return_422(field, value):
    with TestClient(app) as client:
        response = client.get("/flights", params={field: value})

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(
        error["loc"] == ["query", field]
        for error in errors
    )


def test_duplicate_returns_409_and_original_remains_available():
    payload = {
        "flight_number": "100",
        "origin": "JFK",
        "destination": "LAX",
        "flight_date": "2025-06-01",
        "carrier_code": "AA",
    }

    with TestClient(app) as client:
        first = client.post("/flights", json=payload)
        assert first.status_code == 201
        original = first.json()

        duplicate = client.post("/flights", json=payload)
        assert duplicate.status_code == 409
        assert duplicate.json() == {
            "detail": "A flight with these details already exists"
        }

        read_response = client.get(f"/flights/{original['id']}")
        assert read_response.status_code == 200
        assert read_response.json() == original

        listing = client.get(
            "/flights",
            params={
                "flight_date": "2025-06-01",
                "carrier_code": "AA",
            },
        )

        assert listing.status_code == 200
        assert listing.json()["total"] == 1


def test_same_flight_on_different_dates_is_allowed():
    with TestClient(app) as client:
        first = create_flight(client, flight_date="2025-06-01")
        second = create_flight(client, flight_date="2025-06-02")

    assert first["id"] != second["id"]


def test_no_matching_flights_returns_empty_result():
    with TestClient(app) as client:
        response = client.get(
            "/flights",
            params={
                "origin": "JFK",
                "destination": "LAX",
                "flight_date": "2000-01-01",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }
