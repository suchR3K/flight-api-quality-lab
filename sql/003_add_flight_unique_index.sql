BEGIN;

CREATE UNIQUE INDEX flights_dated_identity_uidx
ON flights (
    flight_date,
    carrier_code,
    flight_number,
    origin,
    destination
)
WHERE flight_date IS NOT NULL
  AND carrier_code IS NOT NULL;

COMMIT;
