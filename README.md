# Flight API Quality Lab

An educational API testing project built with Python, FastAPI and PostgreSQL.

The project demonstrates input validation, automated integration tests,
manual testing in Postman, containerization and continuous integration.

All flight data is fictional. This project is not affiliated with an airline.

## Features

- Check whether the API is responding.
- Retrieve a flight by ID.
- Create and persist flights in PostgreSQL.
- Validate required fields and airport codes.
- Reject blank flight numbers and identical departure/arrival airports.
- Trim whitespace around flight numbers.
- Run automated tests against a separate test database.
- Generate downloadable JUnit XML reports in GitHub Actions.
- Run the API and database together using Docker Compose.

## Technologies

- Python 3.13
- FastAPI and Pydantic
- PostgreSQL 17 and Psycopg
- pytest and FastAPI TestClient
- Postman
- Docker and Docker Compose
- Git and GitHub Actions

## Architecture

### Application

```text
Postman / HTTP client
        |
        | localhost:8000
        v
FastAPI container
        |
        | db:5432
        v
PostgreSQL container
        |
        v
Named Docker volume
```

The API can also run directly in a local Python environment while
PostgreSQL runs in Docker.

### Automated tests

```text
pytest + TestClient
        |
        v
FastAPI with a database dependency override
        |
        v
PostgreSQL: flight_lab_test
```

- `flight_lab` stores data used by the application and manual tests.
- `flight_lab_test` is reserved for automated tests.

## Requirements

- Git
- Docker Engine and Docker Compose
- Python 3.13 with pip and venv support for local pytest execution
- Postman, optionally, for running the collection

The commands below are intended for Linux.

When using an Ubuntu virtual machine, run these commands inside Ubuntu.
Run Postman inside the same VM when using the localhost addresses below.

If your Docker installation requires administrator privileges, prefix
Docker commands with `sudo`.

## First-time setup

### 1. Clone the repository

```bash
git clone https://github.com/suchR3K/flight-api-quality-lab.git
cd flight-api-quality-lab
```

Run subsequent commands from this directory.

### 2. Configure the database

Create a local configuration file:

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=flight_lab
POSTGRES_USER=flight_app
POSTGRES_PASSWORD=replace_with_your_local_password
```

Replace the example password before initializing the database.

Keep the database name and username shown above to use the commands
in this guide without modification.

Do not commit `.env`. It is excluded by `.gitignore` and `.dockerignore`.

For an existing installation, do not overwrite a working `.env`.
Changing this file does not change the password of an already initialized
PostgreSQL user.

### 3. Start PostgreSQL

```bash
docker compose up -d db
docker compose ps
```

Wait until the database reports `healthy`.

The database is available locally on port 5432.
Its data is stored in the named volume `postgres_data`, managed by Compose.

### 4. Create the application table

```bash
docker compose exec -T db psql -U flight_app -d flight_lab -v ON_ERROR_STOP=1 < sql/001_create_flights.sql
```

### 5. Create the test database and table

```bash
docker compose exec db createdb -U flight_app flight_lab_test
docker compose exec -T db psql -U flight_app -d flight_lab_test -v ON_ERROR_STOP=1 < sql/001_create_flights.sql
```

Database and table creation should be performed only once per new database.
Repeated execution reports that the database or table already exists.

The application database starts empty.
Create application data through the API.

Automated tests prepare their own data in `flight_lab_test`.

## Run with Docker Compose

After completing the database setup:

```bash
docker compose up -d --build
docker compose ps
```

Expected service states:

- `db`: running and healthy
- `api`: running

The API container waits for the database health check before starting.
This check does not create the database tables.

Available addresses:

- Health check: http://127.0.0.1:8000/health
- Interactive documentation: http://127.0.0.1:8000/docs

Check the response:

```bash
curl -i http://127.0.0.1:8000/health
```

Expected status: `200 OK`.

Expected body:

```json
{
  "status": "ok"
}
```

The health endpoint checks the API response, not database availability.
Use flight creation and retrieval to verify database connectivity.

### Container configuration

- The API runs as `appuser`, with UID 10001.
- Database settings are passed through environment variables.
- The local `.env` file is not copied into the API image.
- The API connects to PostgreSQL using hostname `db`.
- API and database ports are bound to localhost on the Docker host.

Check the container user:

```bash
docker compose exec api id
```

### View logs

```bash
docker compose logs --tail=50 api
docker compose logs --tail=50 db
```

### Rebuild after code changes

```bash
docker compose up -d --build api
```

The image contains a copy of the application code.
Editing local Python files does not automatically update a running container.

### Recreate the API container

```bash
docker compose up -d --force-recreate --no-deps api
```

This replaces the API container while leaving the database service alone.
Previously saved flights remain in PostgreSQL.

### Stop and restart

Stop both services:

```bash
docker compose stop
```

Start them again:

```bash
docker compose up -d
```

Stopping services does not delete the database volume.
Do not use `docker compose down -v` unless you intend to delete its data.

## Alternative: run the API directly in Python

This mode uses a local Python process and the database container.

Create and activate the environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Stop the containerized API to free port 8000:

```bash
docker compose stop api
```

Start PostgreSQL and the local API:

```bash
docker compose up -d db
python -m uvicorn main:app --reload
```

Use Ctrl+C to stop the local API.

The local process uses `POSTGRES_HOST=127.0.0.1` from `.env`.
The containerized API overrides that setting with `POSTGRES_HOST=db`.

Do not run both API variants on port 8000 at the same time.

## API endpoints

| Method | Path | Success response | Expected error responses |
|---|---|---|---|
| GET | `/health` | 200 | — |
| GET | `/flights/{flight_id}` | 200 | 404 for an unknown ID; 422 for an invalid ID format |
| POST | `/flights` | 201 | 422 for invalid request data |

### Create a flight

Request body for `POST /flights`:

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

The database generates the ID. Its value may differ.
IDs are not guaranteed to be consecutive.

### Validation rules

- `flight_number`, `origin` and `destination` are required strings.
- Leading and trailing whitespace is removed from flight numbers.
- A blank flight number is rejected.
- Airport codes must contain exactly three uppercase ASCII letters.
- Airport codes with surrounding spaces are rejected.
- Departure and arrival airports must be different.

Airport codes are checked for format, not against a real airport directory.

Database constraints also reject null fields, space-only flight numbers,
invalid airport code formats and identical airports.

## Run automated tests

Tests run locally through Python and connect to the test database.

If the Python environment has not been created yet:

```bash
python3 -m venv .venv
```

Activate it and install dependencies:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Start PostgreSQL and wait until it is healthy:

```bash
docker compose up -d db
docker compose ps
```

Run tests:

```bash
python -m pytest -v
```

Uvicorn does not need to be running.
FastAPI TestClient communicates directly with the application.

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
4. Provides the same connection to the test and API dependency override.
5. Rolls back the transaction after the test.

Tests and endpoints must not explicitly commit the shared test connection,
because that would prevent the fixture from rolling back those changes.

Application data in `flight_lab` is separate from automated test data.
The current fixture is designed for sequential test execution.

### JUnit XML report

```bash
mkdir -p reports
python -m pytest -v --junitxml=reports/junit.xml
```

Generated reports are excluded from Git.

## GitHub Actions

The workflow runs on pushes and pull requests.

It:

1. Starts PostgreSQL with a temporary test database.
2. Checks out the repository.
3. Sets up Python 3.13.
4. Installs dependencies.
5. Creates the test database schema.
6. Runs pytest and generates a JUnit XML report.
7. Attempts to upload the report even if tests fail.

The `pytest-results` artifact is retained for 14 days.

A failed test makes the workflow fail.
Uploading the report does not change that result.

The current workflow tests Python application code against PostgreSQL.
It does not yet build or test the API Docker image.

## Postman collection

Import:

```text
postman/flight-api.postman_collection.json
```

Set the collection variable:

```text
base_url = http://127.0.0.1:8000
```

The API must be running locally or through Docker Compose.

### Execution order

1. Health check
2. Get existing flight
3. Get nonexistent flight
4. Create flight
5. Get created flight

The collection contains 5 requests and 10 assertions.

`Create flight` saves the returned ID in `created_flight_id`.
`Get created flight` uses that variable to retrieve the new flight.

### Required data

The existing-flight request expects ID 1 to contain:

```json
{
  "id": 1,
  "flight_number": "LO123",
  "origin": "WAW",
  "destination": "LHR"
}
```

On a fresh application database, create the example flight through
`POST /flights`, without supplying an ID:

```json
{
  "flight_number": "LO123",
  "origin": "WAW",
  "destination": "LHR"
}
```

Check the returned ID.
If it is not 1, update the URL and expected ID in
the `Get existing flight` request.

The nonexistent-flight request assumes ID 999 does not exist.
Its expected response is 404.

Run `Create flight` before `Get created flight` to populate the ID variable.

Postman uses the application database and leaves created records in it.
Repeated collection runs create additional flights.

GitHub Actions currently runs pytest, not the Postman collection.

## Manual testing documentation

- `docs/test-cases.md`
- `docs/manual-test-results.md`

Documented manual checks include:

- Flight creation and retrieval.
- Rejection of identical airports.
- Persistence after recreating the API container.
- Running the API as a non-root user.

These documents are not automatically updated by CI.

## Troubleshooting

A documented investigation of a local port conflict is available here:

[API container port conflict](docs/troubleshooting/port-8000-conflict.md)

### Port 8000 is already in use

A local Uvicorn process may already be listening on that port.

Check:

```bash
sudo ss -ltnp 'sport = :8000'
```

Stop the local Uvicorn process with Ctrl+C in its terminal before starting
the API container.

### API container does not start or requests return errors

Check service states and logs:

```bash
docker compose ps -a
docker compose logs --tail=50 api
docker compose logs --tail=50 db
```

Verify that:

- PostgreSQL is healthy.
- The application table has been created.
- The configured database credentials match the initialized database.
- The API container uses hostname `db`.

### Tests cannot connect to PostgreSQL

Verify that:

- The database container is running.
- `flight_lab_test` exists and contains the `flights` table.
- Local `.env` uses `POSTGRES_HOST=127.0.0.1`.
- Dependencies are installed in the active Python environment.

## Current limitations

- No authentication or authorization.
- No duplicate-flight detection.
- No update, deletion, listing or filtering endpoints.
- `/health` does not check database readiness.
- Database schema setup is manual.
- The development database uses a privileged bootstrap user.
- No connection pooling.
- Automated tests are designed for sequential execution.
- The Docker image currently installs test dependencies as well as runtime dependencies.
- This is a learning project, not a production service.


## Reproducibility verification

[Fresh-clone verification report](docs/fresh-clone-verification.md)

The project was installed and tested from a separate GitHub clone,
using a new Python environment and a separate PostgreSQL volume.
All 30 automated cases passed, and basic API operations were verified.
