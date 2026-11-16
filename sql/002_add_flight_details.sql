BEGIN;

ALTER TABLE flights
    ADD COLUMN flight_date DATE,
    ADD COLUMN carrier_code TEXT;

ALTER TABLE flights
    ADD CONSTRAINT carrier_code_not_blank
    CHECK (
        carrier_code IS NULL
        OR length(btrim(carrier_code)) > 0
    );

COMMIT;
