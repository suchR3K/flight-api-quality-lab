import logging
from datetime import date
from pathlib import Path
from typing import Literal

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from database import get_connection, get_db


logger = logging.getLogger("uvicorn.error")
BASE_DIR = Path(__file__).resolve().parent

FLIGHT_COLUMNS = """
    id, flight_number, origin, destination,
    flight_date, carrier_code
"""

app = FastAPI(
    title="Flight Explorer API",
    description="Explore historical flight data and demonstration records.",
    version="0.2.0",
)


class FlightCreate(BaseModel):
    flight_number: str
    flight_date: date | None = None
    carrier_code: str | None = None

    origin: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    destination: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    @field_validator("flight_number")
    @classmethod
    def validate_flight_number(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("Flight number must not be blank")

        return cleaned_value

    @field_validator("carrier_code")
    @classmethod
    def validate_carrier_code(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("Carrier code must not be blank")

        return cleaned_value

    @model_validator(mode="after")
    def validate_different_airports(self):
        if self.origin == self.destination:
            raise ValueError(
                "Origin and destination must be different"
            )

        return self


def serialize_flight(flight: dict) -> dict:
    """Preserve the original response format for records without details."""
    return {
        key: value
        for key, value in flight.items()
        if key not in {"flight_date", "carrier_code"} or value is not None
    }


@app.exception_handler(psycopg.Error)
async def database_error_handler(
    request: Request,
    error: psycopg.Error,
):
    logger.error(
        "Database error during %s %s",
        request.method,
        request.url.path,
        exc_info=(type(error), error, error.__traceback__),
    )

    return JSONResponse(
        status_code=503,
        content={"detail": "Database operation failed. Please try again later."},
    )


@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse(
        BASE_DIR / "static" / "index.html",
        media_type="text/html",
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def readiness():
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT " + FLIGHT_COLUMNS + " FROM flights LIMIT 0;"
                )
    except psycopg.Error as error:
        logger.warning("Readiness check failed: %s", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="Database or required flight schema is unavailable",
        ) from error

    return {"status": "ready", "database": "ok"}


@app.get("/flights")
def list_flights(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    origin: str | None = Query(
        default=None,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    ),
    destination: str | None = Query(
        default=None,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    ),
    flight_date: date | None = Query(default=None),
    carrier_code: str | None = Query(
        default=None,
        min_length=1,
        max_length=10,
        pattern=r"^[A-Z0-9]+(?:\([0-9]+\))?$",
    ),
    sort_by: Literal[
        "id",
        "flight_date",
        "carrier_code",
        "flight_number",
        "origin",
        "destination",
    ] = "id",
    sort_order: Literal["asc", "desc"] = "asc",
    connection=Depends(get_db),
):
    conditions = []
    parameters = []

    for column, value in [
        ("origin", origin),
        ("destination", destination),
        ("flight_date", flight_date),
        ("carrier_code", carrier_code),
    ]:
        if value is not None:
            conditions.append(f"{column} = %s")
            parameters.append(value)

    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    # sort_by and sort_order can only contain values allowed by Literal.
    order_clause = f" ORDER BY {sort_by} {sort_order.upper()} NULLS LAST"

    # Unique tie-breaker makes ordering deterministic.
    if sort_by != "id":
        order_clause += ", id ASC"

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM flights" + where_clause,
            parameters,
        )
        total = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT "
            + FLIGHT_COLUMNS
            + " FROM flights"
            + where_clause
            + order_clause
            + " LIMIT %s OFFSET %s;",
            parameters + [limit, offset],
        )
        flights = cursor.fetchall()

    return {
        "items": [serialize_flight(flight) for flight in flights],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/flights/{flight_id}")
def get_flight(flight_id: int, connection=Depends(get_db)):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT "
            + FLIGHT_COLUMNS
            + " FROM flights WHERE id = %s;",
            (flight_id,),
        )
        flight = cursor.fetchone()

    if flight is None:
        raise HTTPException(status_code=404, detail="Flight not found")

    return serialize_flight(flight)


@app.post("/flights", status_code=201)
def create_flight(flight: FlightCreate, connection=Depends(get_db)):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO flights (
                flight_number, origin, destination,
                flight_date, carrier_code
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (
                flight_date,
                carrier_code,
                flight_number,
                origin,
                destination
            )
            WHERE flight_date IS NOT NULL
              AND carrier_code IS NOT NULL
            DO NOTHING
            RETURNING
                id, flight_number, origin, destination,
                flight_date, carrier_code;
            """,
            (
                flight.flight_number,
                flight.origin,
                flight.destination,
                flight.flight_date,
                flight.carrier_code,
            ),
        )
        created_flight = cursor.fetchone()

    if created_flight is None:
        raise HTTPException(
            status_code=409,
            detail="A flight with these details already exists",
        )

    return serialize_flight(created_flight)
