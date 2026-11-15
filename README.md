# Flight API Quality Lab

An educational API testing project built with Python, FastAPI and pytest.
All flight data is fictional.

## Features

- Health check endpoint.
- Retrieve a flight by ID.
- Create a flight.
- Validate required fields and airport code format.
- Reject blank flight numbers and identical departure/arrival airports.
- Trim whitespace around flight numbers.

## Technologies

- Python
- FastAPI and Pydantic
- pytest and HTTPX
- Git

## Local setup

Run these commands from the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the application

```bash
python -m uvicorn main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive documentation: http://127.0.0.1:8000/docs

## Run the tests

```bash
python -m pytest -v
```

Tests cover successful requests, missing flights, invalid identifiers,
required fields, blank flight numbers, airport code validation,
flight number normalization and identical airports.

A pytest fixture resets in-memory data before and after each test.

## Endpoints

| Method | Path | Success status |
|---|---|---|
| GET | `/health` | 200 |
| GET | `/flights/{flight_id}` | 200 |
| POST | `/flights` | 201 |

## Current limitations

- Data is stored in memory and resets when the application restarts.
- Airport codes are checked for format, not real-world existence.
- Authentication and persistent database storage are not implemented.
- This is a learning project, not a production service.

## Postman collection

The collection is available at:

`postman/flight-api.postman_collection.json`

### Run manually

1. Start the API:

   ```bash
   python -m uvicorn main:app --reload
   ```

2. Import the collection JSON file into Postman.
3. Set the collection variable `base_url` to
   `http://127.0.0.1:8000` when Postman and the API run on the same machine.
4. Run the requests in this order:
   - Health check
   - Get existing flight
   - Get nonexistent flight
   - Create flight
   - Get created flight

The collection contains 5 requests and 10 assertions.

`Create flight` saves the returned ID in `created_flight_id`.
`Get created flight` uses this variable to retrieve that flight.

A 404 response for the nonexistent flight is expected.
The API must be running, and flight ID 999 must not exist.
After restarting the API, run `Create flight` again before
`Get created flight`, because application data is stored in memory.
