import argparse
import csv
from datetime import datetime
from pathlib import Path

from database import get_connection
from main import FlightCreate


INSERT_SQL = """
    INSERT INTO flights (
        flight_date,
        carrier_code,
        flight_number,
        origin,
        destination
    )
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (
        flight_date,
        carrier_code,
        flight_number,
        origin,
        destination
    )
    WHERE flight_date IS NOT NULL
      AND carrier_code IS NOT NULL
    DO NOTHING;
"""

REQUIRED_COLUMNS = {
    "FL_DATE",
    "OP_UNIQUE_CARRIER",
    "OP_CARRIER_FL_NUM",
    "ORIGIN",
    "DEST",
}


def parse_row(row):
    flight_date = datetime.strptime(
        row["FL_DATE"].strip(),
        "%m/%d/%Y %I:%M:%S %p",
    ).date()

    flight = FlightCreate(
        flight_date=flight_date,
        carrier_code=row["OP_UNIQUE_CARRIER"],
        flight_number=row["OP_CARRIER_FL_NUM"],
        origin=row["ORIGIN"],
        destination=row["DEST"],
    )

    return (
        flight.flight_date,
        flight.carrier_code,
        flight.flight_number,
        flight.origin,
        flight.destination,
    )


def import_file(path, limit):
    processed = 0
    rejected = 0
    inserted = 0
    batch = []

    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT current_database() AS name;"
                )
                print("Target database:", cursor.fetchone()["name"])

                for row_number, row in enumerate(reader, start=2):
                    if limit and processed >= limit:
                        break

                    processed += 1

                    if any(row.get(column) is None
                           for column in REQUIRED_COLUMNS):
                        rejected += 1
                        if rejected <= 5:
                            print(f"Rejected row {row_number}: missing value")
                        continue

                    try:
                        values = parse_row(row)
                    except ValueError as error:
                        rejected += 1
                        if rejected <= 5:
                            print(f"Rejected row {row_number}: {error}")
                        continue

                    batch.append(values)

                    if len(batch) == 1000:
                        cursor.executemany(INSERT_SQL, batch)
                        inserted += cursor.rowcount
                        batch.clear()

                    if processed % 10000 == 0:
                        print(f"Processed: {processed}")

                if batch:
                    cursor.executemany(INSERT_SQL, batch)
                    inserted += cursor.rowcount

        # The connection context has committed successfully here.
        skipped = processed - rejected - inserted

        print("Import committed.")
        print("Processed:", processed)
        print("Inserted:", inserted)
        print("Skipped existing:", skipped)
        print("Rejected:", rejected)


def main():
    parser = argparse.ArgumentParser(
        description="Import historical BTS flights into PostgreSQL."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum rows to read; 0 imports the entire file.",
    )
    args = parser.parse_args()

    if args.limit < 0:
        parser.error("--limit must be zero or positive")

    import_file(args.csv_path, args.limit)


if __name__ == "__main__":
    main()
