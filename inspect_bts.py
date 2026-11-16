import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

path = Path("data/raw/bts_flights_2025_06.csv")

required_columns = {
    "FL_DATE",
    "OP_UNIQUE_CARRIER",
    "OP_CARRIER_FL_NUM",
    "ORIGIN",
    "DEST",
    "CRS_DEP_TIME",
}

keys = Counter()
dates = Counter()
invalid_dates = 0
total = 0

with path.open(encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)

    missing = required_columns - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    for row in reader:
        total += 1

        try:
            flight_date = datetime.strptime(
                row["FL_DATE"].strip(),
                "%m/%d/%Y %I:%M:%S %p",
            ).date()
        except ValueError:
            invalid_dates += 1
            continue

        dates[flight_date.isoformat()] += 1

        key = (
            flight_date,
            row["OP_UNIQUE_CARRIER"].strip(),
            row["OP_CARRIER_FL_NUM"].strip(),
            row["ORIGIN"].strip(),
            row["DEST"].strip(),
        )
        keys[key] += 1

        if total <= 3:
            print("Example:", key, "Departure:", row["CRS_DEP_TIME"])

print("Total rows:", total)
print("Invalid dates:", invalid_dates)
print("First date:", min(dates, default="none"))
print("Last date:", max(dates, default="none"))
print("Repeated five-field keys:", sum(n > 1 for n in keys.values()))
print("Extra rows with repeated keys:", sum(n - 1 for n in keys.values()))
