# Fresh-clone verification

## Goal

Verify that the project can be installed, tested and started from
a fresh GitHub clone without relying on the original working directory.

## Environment

- Ubuntu VM
- Separate clone: flight-api-clean-check
- Newly created Python virtual environment
- Dependencies installed from requirements.txt
- Separate Compose project: flight-api-clean-check
- Separate PostgreSQL data volume

The original Compose services were stopped to free ports 8000 and 5432.

## Verification results

| Check | Observed result | Status |
|---|---|---|
| Install dependencies | Installation completed successfully | PASS |
| Run automated tests | 30 passed | PASS |
| Build and start the API | API running; PostgreSQL healthy | PASS |
| GET /health | HTTP 200 and status "ok" | PASS |
| POST /flights | HTTP 201; both Postman assertions passed | PASS |
| GET created flight | HTTP 200; both Postman assertions passed | PASS |

## Scope and limitations

The complete Postman collection was not executed during this verification.

The `Get existing flight` request requires a specific example flight.
A fresh application database does not contain that fixture automatically.

Database and table creation were performed manually following the setup
instructions. Starting Docker Compose alone does not initialize the schema.

## Conclusion

The tested setup steps were sufficient to reproduce automated testing
and basic API operation from a fresh clone.

The verification environment was stopped afterward without deleting
its database volume.
