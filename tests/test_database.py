def test_connection_uses_test_database(db_connection):
    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_database() AS database_name;"
        )
        result = cursor.fetchone()

    assert result["database_name"] == "flight_lab_test"


def test_database_starts_with_example_flight(db_connection):
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, flight_number, origin, destination
            FROM flights
            ORDER BY id;
            """
        )
        flights = cursor.fetchall()

    assert flights == [
        {
            "id": 1,
            "flight_number": "LO123",
            "origin": "WAW",
            "destination": "LHR",
        }
    ]
