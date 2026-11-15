from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator


class FlightCreate(BaseModel):
    flight_number: str

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

    @model_validator(mode="after")
    def validate_different_airports(self):
        if self.origin == self.destination:
            raise ValueError(
                "Origin and destination must be different"
            )

        return self


app = FastAPI()

flights = {
    1: {
        "id": 1,
        "flight_number": "LO123",
        "origin": "WAW",
        "destination": "LHR",
    }
}


@app.get("/health")
def health():
    return {"status": "broken"}


@app.get("/flights/{flight_id}")
def get_flight(flight_id: int):
    if flight_id not in flights:
        raise HTTPException(
            status_code=404,
            detail="Flight not found",
        )

    return flights[flight_id]


@app.post("/flights", status_code=201)
def create_flight(flight: FlightCreate):
    new_id = max(flights, default=0) + 1

    new_flight = {
        "id": new_id,
        **flight.model_dump(),
    }

    flights[new_id] = new_flight

    return new_flight
