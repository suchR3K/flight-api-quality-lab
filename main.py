from fastapi import FastAPI, HTTPException

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
    return {"status": "ok"}


@app.get("/flights/{flight_id}")
def get_flight(flight_id: int):
    if flight_id not in flights:
        raise HTTPException(
            status_code=404,
            detail="Flight not found",
        )

    return flights[flight_id]
