CREATE TABLE flights (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flight_number TEXT NOT NULL,
    origin VARCHAR(3) NOT NULL,
    destination VARCHAR(3) NOT NULL,

    CONSTRAINT flight_number_not_blank
        CHECK (length(btrim(flight_number)) > 0),

    CONSTRAINT origin_format
        CHECK (origin ~ '^[A-Z]{3}$'),

    CONSTRAINT destination_format
        CHECK (destination ~ '^[A-Z]{3}$'),

    CONSTRAINT different_airports
        CHECK (origin <> destination)
);
