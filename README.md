# Flight API Quality Lab

An educational API testing project built with Python, FastAPI and PostgreSQL.

The project demonstrates API validation, automated integration tests,
manual testing in Postman and continuous integration with GitHub Actions.

All flight data is fictional. This project is not affiliated with an airline.

## Features

- Check whether the API is responding.
- Retrieve a flight by ID.
- Create and persist a flight in PostgreSQL.
- Reject missing required fields and blank flight numbers.
- Trim whitespace around flight numbers.
- Validate airport codes as exactly three uppercase letters from A to Z.
- Reject identical departure and arrival airports.
- Run automated tests against a separate test database.
- Generate downloadable JUnit XML reports in GitHub Actions.

## Technologies

- Python 3.13
- FastAPI and Pydantic
- PostgreSQL 17 and Psycopg
- pytest and FastAPI TestClient
- Postman
- Docker Compose
- Git and GitHub Actions

## Architecture

```text
Postman / HTTP client
        |
        v
FastAPI application
        |
        v
PostgreSQL: flight_lab

pytest + TestClient
        |
        v
FastAPI with a test database dependency override
        |
        v
PostgreSQL: flight_lab_test
```

The API runs locally in Python. PostgreSQL runs in Docker.
The API itself is not yet containerized.

## Requirements

- Python 3.13 with pip and venv support
- Git
- Docker Engine and Docker Compose
- Postman, optionally, for running the collection

The commands below are intended for Linux.
Run them from the project directory unless stated otherwise.

## First-time setup

### 1. Clone the repository

```bash
git clone https://github.com/suchR3K/flight-api-quality-lab.git
cd flight-api-quality-lab
```

### 2. Create a Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 3. Configure the database connection

```bash
cp .env.example .env
```

Edit `.env` and replace the example password with a local development
password. Keep the following database names and user for these instructions:

```dotenv
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=flight_lab
POSTGRES_USER=flight_app
POSTGRES_PASSWORD=replace_with_your_local_password
```

Do not commit `.env`. It is excluded by `.gitignore`.

### 4. Start PostgreSQL

```bash
docker compose up -d db
docker compose ps
```

Wait until the database reports `healthy`.

The database port is bound to `127.0.0.1` on the Docker host.
Database files are stored in a named Docker volume.

### 5. Create the application table

```bash
docker compose exec -T db psql -U flight_app -d flight_lab -v ON_ERROR_STOP=1 < sql/001_create_flights.sql
```

### 6. Create the test database and table

```bash
docker compose exec db createdb -U flight_app flight_lab_test
docker compose exec -T db psql -U flight_app -d flight_lab_test -v ON_ERROR_STOP=1 < sql/001_create_flights.sql
```

Run the database and table creation commands only once per new database.
Repeated execution will report that the database or table already exists.

The application database starts empty. Create flights through the API.
The test fixture prepares its own example flight in the test database.

## Run the application

```bash
source .venv/bin/activate
docker compose up -d db
python -m uvicorn main:app --reload
```

- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

Use Ctrl+C to stop the API.

The `--reload` option is intended for local development.
Saved flights remain in PostgreSQL after the API restarts.

If the API runs in a virtual machine, `127.0.0.1` refers to that VM.
Run Postman inside the same VM for the local addresses above to work.

## API endpoints

| Method | Path | Success response | Expected error responses |
|---|---|---|---|
| GET | `/health` | 200 | — |
| GET | `/flights/{flight_id}` | 200 | 404 for an unknown ID; 422 for an invalid ID format |
| POST | `/flights` | 201 | 422 for invalid request data |

### Create a flight

Example request body for `POST /flights`:

```json
{
  "flight_number": "  LO456  ",
  "origin": "WAW",
  "destination": "CDG"
}
```

Example response:

```json
{
  "id": 1,
  "flight_number": "LO456",
  "origin": "WAW",
  "destination": "CDG"
}
```

The database generates the ID, so its value may differ.
IDs are not guaranteed to be consecutive.

### Validation rules

- `flight_number`, `origin` and `destination` are required strings.
- Leading and trailing whitespace is removed from `flight_number`.
- A blank flight number is rejected.
- Airport codes must contain exactly three uppercase ASCII letters.
- Airport codes with surrounding spaces are rejected.
- `origin` and `destination` must be different.

Airport codes are checked for format, not against a real airport directory.

## Run automated tests

Start PostgreSQL and activate the Python environment:

```bash
docker compose up -d db
source .venv/bin/activate
```

Run the tests:

```bash
python -m pytest -v
```

The current suite contains 30 test cases, including parameterized cases.

Tests cover:

- Health check response.
- Retrieval of an existing flight.
- Unknown flight IDs.
- Invalid flight ID formats.
- Flight creation and subsequent retrieval.
- Missing required fields.
- Blank flight numbers.
- Flight number normalization.
- Invalid airport codes.
- Identical departure and arrival airports.
- Connection to the designated test database.
- Initial database test data.

### Test isolation

Tests use `flight_lab_test`.

Before each test, a fixture:

1. Checks the actual database name.
2. Clears the flights table and resets its identity generator.
3. Inserts a known example flight.
4. Provides the connection to the test and API dependency override.
5. Rolls back the transaction after the test.

Tests and endpoints must not explicitly commit the shared test connection,
because this would prevent the fixture from rolling back those changes.

The regular application database, `flight_lab`, is separate from test data.
The current fixture is designed for sequential test execution.

### Generate a JUnit XML report

```bash
mkdir -p reports
python -m pytest -v --junitxml=reports/junit.xml
```

Generated reports are excluded from Git.

## GitHub Actions

The workflow runs on pushes and pull requests.

It:

1. Starts a PostgreSQL service with a temporary test database.
2. Checks out the repository.
3. Sets up Python 3.13.
4. Installs dependencies from `requirements.txt`.
5. Creates the test database schema.
6. Runs pytest and generates a JUnit XML report.
7. Attempts to upload the report even if tests fail.

Reports are available as the `pytest-results` artifact and retained
for 14 days.

A failed test makes the workflow fail. Uploading a report does not
change that result.

## Postman collection

Import this file into Postman:

```text
postman/flight-api.postman_collection.json
```

Set the collection variable:

```text
base_url = http://127.0.0.1:8000
```

The API must be running.

### Request order

1. Health check
2. Get existing flight
3. Get nonexistent flight
4. Create flight
5. Get created flight

The collection contains 5 requests and 10 assertions.

`Create flight` stores the returned ID in `created_flight_id`.
`Get created flight` uses that variable to retrieve the newly created flight.

### Required data for the collection

The existing-flight request expects ID 1 to contain:

```json
{
  "id": 1,
  "flight_number": "LO123",
  "origin": "WAW",
  "destination": "LHR"
}
```

On a fresh application database, create this flight first through
`POST /flights`, without supplying an ID:

```json
{
  "flight_number": "LO123",
  "origin": "WAW",
  "destination": "LHR"
}
```

Check the returned ID. If it is not 1, update both the URL and the
expected ID in the `Get existing flight` request.

The nonexistent-flight request assumes ID 999 does not exist.
A 404 response for that request is expected and should pass its tests.

Run `Create flight` before `Get created flight` to populate the ID variable.

Postman requests use the application database and can leave records in it.
Repeated collection runs create additional flights.

The collection is run manually. GitHub Actions currently runs pytest,
not the Postman collection.

## Manual testing documentation

- Test cases: `docs/test-cases.md`
- Manual execution results: `docs/manual-test-results.md`

These documents record the scenarios described in them; they are not
automatically updated by CI.

## Stop the local database

```bash
docker compose stop db
```

Restart it with:

```bash
docker compose up -d db
```

Stopping the container does not remove the named volume.

Changing `POSTGRES_PASSWORD` in `.env` does not change the password
of an already initialized PostgreSQL user.

## Current limitations

- No authentication or authorization.
- No duplicate-flight detection.
- No update, deletion, listing or filtering endpoints.
- `/health` checks the API response, not database availability.
- Database schema setup is manual.
- The development database uses a privileged bootstrap user.
- No connection pooling.
- The API is not yet containerized.
- This is a learning project, not a production service.
