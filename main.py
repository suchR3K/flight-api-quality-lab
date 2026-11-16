from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from database import get_db


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


app = FastAPI()


def serialize_flight(flight: dict) -> dict:
    # Preserve the previous response format when optional data is absent.
    return {
        key: value
        for key, value in flight.items()
        if key not in {"flight_date", "carrier_code"} or value is not None
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/flights/{flight_id}")
def get_flight(flight_id: int, connection=Depends(get_db)):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id, flight_number, origin, destination,
                flight_date, carrier_code
            FROM flights
            WHERE id = %s;
            """,
            (flight_id,),
        )
        flight = cursor.fetchone()

    if flight is None:
        raise HTTPException(
            status_code=404,
            detail="Flight not found",
        )

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

    return serialize_flight(created_flight)
