from copy import deepcopy

import pytest

from main import flights


INITIAL_FLIGHTS = {
    1: {
        "id": 1,
        "flight_number": "LO123",
        "origin": "WAW",
        "destination": "LHR",
    }
}


@pytest.fixture(autouse=True)
def reset_flights():
    flights.clear()
    flights.update(deepcopy(INITIAL_FLIGHTS))

    yield

    flights.clear()
    flights.update(deepcopy(INITIAL_FLIGHTS))
