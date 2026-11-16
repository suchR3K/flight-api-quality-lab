# Manual Test Results

These results document checks performed on an earlier version of the project.
They do not constitute a complete verification of the Flight Explorer release.

## MT-001: Create and Retrieve a Valid Flight

Tool: Interactive API documentation (`/docs`).

### Test Data

- `flight_number`: `" LO789 "`
- `origin`: `WAW`
- `destination`: `FRA`

### Expected Result

- POST returns HTTP 201 and trims surrounding whitespace from the flight number.
- GET using the returned ID responds with HTTP 200 and the created flight data.

### Actual Result

- POST returned HTTP 201.
- The flight number was returned as `"LO789"`, without surrounding whitespace.
- GET returned HTTP 200 and data matching the created flight.

**Status: PASS**

## MT-002: Identical Origin and Destination Airports

Tool: Interactive API documentation (`/docs`).

### Test Data

- `flight_number`: `LO999`
- `origin`: `WAW`
- `destination`: `WAW`

### Expected Result

- HTTP 422.
- The response contains: `"Origin and destination must be different"`.

### Actual Result

- POST returned HTTP 422.
- The response contained: `"Origin and destination must be different"`.
- The request was rejected as required.

**Status: PASS**

## MT-003: Data Persistence After Recreating the API Container

### Environment

API and PostgreSQL running through Docker Compose.

### Steps

1. Create a flight using `POST /flights`.
2. Retrieve the flight using `GET /flights/{id}`.
3. Recreate the API container:

   ```bash
   docker compose up -d --force-recreate --no-deps api
