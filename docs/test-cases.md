# API test cases

## Scope

The automated suite checks API behavior and PostgreSQL integration.

Framework: pytest with FastAPI TestClient.
Database: flight_lab_test.

Each test starts with one example flight:

- id: 1
- flight_number: LO123
- origin: WAW
- destination: LHR

Database changes are rolled back after each test.

## Test cases

| ID | Scenario | Input / action | Expected result | Automated cases |
|---|---|---|---|---|
| TC-001 | API health | GET /health | HTTP 200; body equals {"status": "ok"} | 1 |
| TC-002 | Existing flight | GET /flights/1 | HTTP 200; exact example flight data | 1 |
| TC-003 | Unknown flight | GET /flights/999 | HTTP 404; detail equals "Flight not found" | 1 |
| TC-004 | Invalid ID format | GET with abc, 1.5 and null as path values | HTTP 422; error points to path parameter flight_id | 3 |
| TC-005 | Create and retrieve flight | POST valid data, then GET returned ID | HTTP 201; positive integer ID; correct data; GET returns HTTP 200 and the same flight | 1 |
| TC-006 | Missing required field | Omit flight_number, origin or destination separately | HTTP 422; missing-field error identifies the omitted field | 3 |
| TC-007 | Blank flight number | Empty string or three spaces | HTTP 422; error points to flight_number | 2 |
| TC-008 | Normalize flight number | POST flight_number with surrounding spaces | HTTP 201; POST and subsequent GET return the trimmed value | 1 |
| TC-009 | Invalid airport format | Test seven invalid values separately in origin and destination | HTTP 422; error identifies the invalid field | 14 |
| TC-010 | Identical airports | POST origin=WAW and destination=WAW | HTTP 422; model validation error explains that airports must differ | 1 |
| TC-011 | Test database selection | Query current_database() | Database name equals flight_lab_test | 1 |
| TC-012 | Initial database data | Query all flights | Exactly one record matching the example flight | 1 |

Total: 30 automated cases.

## Invalid airport values

TC-009 uses each value for both origin and destination:

| Value | Reason |
|---|---|
| Empty string | No airport code |
| WA | Too short |
| WAWX | Too long |
| waw | Lowercase letters |
| W4W | Contains a digit |
| " WAW " | Contains surrounding spaces |
| ŁÓD | Contains characters outside ASCII A–Z |

Only one field is made invalid in each case.
All other request fields remain valid.

## Test design techniques

- Positive and negative scenarios.
- Equivalence partitioning.
- Boundary values around the required airport code length.
- Parameterization of repeated checks.
- Verification of response status and body.
- Creation followed by retrieval.
- Isolation of database state between tests.

## Execution

Run from the project root with dependencies installed and PostgreSQL ready:

python -m pytest -v

Generate a JUnit XML report:

python -m pytest -v --junitxml=reports/junit.xml

Actual execution results are recorded in the terminal, CI logs
and generated JUnit reports. This document defines expected behavior;
it is not an execution report.

## Current coverage gaps

The suite does not currently verify:

- API behavior when PostgreSQL is unavailable.
- Concurrent requests.
- Authentication or authorization.
- Duplicate-flight handling.
- Load or performance requirements.
- HTTP behavior of the built Docker image in CI.

The application does not currently implement authentication
or duplicate-flight detection.
