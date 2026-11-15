import pytest

from database import get_connection, get_db
from main import app


@pytest.fixture
def db_connection():
    with get_connection("flight_lab_test") as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT current_database() AS database_name;"
            )
            result = cursor.fetchone()

        if result["database_name"] != "flight_lab_test":
            raise RuntimeError("Tests must use flight_lab_test")

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "TRUNCATE TABLE flights RESTART IDENTITY;"
                )

                cursor.execute(
                    """
                    INSERT INTO flights (
                        flight_number, origin, destination
                    )
                    VALUES (%s, %s, %s);
                    """,
                    ("LO123", "WAW", "LHR"),
                )

            yield connection
        finally:
            connection.rollback()


@pytest.fixture(autouse=True)
def override_database(db_connection):
    def use_test_connection():
        yield db_connection

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = use_test_connection

    try:
        yield
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
