import hashlib
import os
import re
import uuid
from datetime import date
from pathlib import Path

from psycopg import sql

from database import get_connection


ROOT = Path(__file__).resolve().parent
MIGRATIONS = [
    ROOT / "sql/001_create_flights.sql",
    ROOT / "sql/002_add_flight_details.sql",
    ROOT / "sql/003_add_flight_unique_index.sql",
]


def migration_body(path):
    # These three legacy files may contain transaction wrappers.
    # The bootstrap process manages one transaction for the entire operation.
    text = path.read_text(encoding="utf-8")
    return re.sub(
        r"^\s*(BEGIN|COMMIT);\s*$",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(cursor, schema):
    table = f"{schema}.flights"

    cursor.execute("SELECT to_regclass(%s) AS relation", (table,))
    if cursor.fetchone()["relation"] is None:
        return None

    cursor.execute(
        """
        SELECT
            attname,
            format_type(atttypid, atttypmod) AS data_type,
            attnotnull,
            attidentity,
            pg_get_expr(d.adbin, d.adrelid) AS default_expression
        FROM pg_attribute AS a
        LEFT JOIN pg_attrdef AS d
          ON d.adrelid = a.attrelid AND d.adnum = a.attnum
        WHERE a.attrelid = %s::regclass
          AND a.attnum > 0
          AND NOT a.attisdropped
        ORDER BY a.attnum
        """,
        (table,),
    )
    columns = cursor.fetchall()

    cursor.execute(
        """
        SELECT conname, contype, convalidated,
               pg_get_constraintdef(oid) AS definition
        FROM pg_constraint
        WHERE conrelid = %s::regclass
        ORDER BY conname
        """,
        (table,),
    )
    constraints = cursor.fetchall()

    cursor.execute(
        """
        SELECT c.relname AS name,
               i.indisvalid,
               i.indisready,
               pg_get_indexdef(i.indexrelid) AS definition
        FROM pg_index AS i
        JOIN pg_class AS c ON c.oid = i.indexrelid
        WHERE i.indrelid = %s::regclass
        ORDER BY c.relname
        """,
        (table,),
    )
    indexes = cursor.fetchall()

    for index in indexes:
        index["definition"] = index["definition"].replace(
            f" ON {schema}.flights ", " ON flights "
        )

    return columns, constraints, indexes


def reference_states(cursor):
    # Build empty reference tables in an isolated schema.
    # No application records are copied or modified here.
    schema = "bootstrap_reference_" + uuid.uuid4().hex
    cursor.execute(sql.SQL("CREATE SCHEMA {}").format(
        sql.Identifier(schema)
    ))

    states = [None]

    for path in MIGRATIONS:
        cursor.execute(
            sql.SQL("SET LOCAL search_path TO {}, pg_catalog").format(
                sql.Identifier(schema)
            )
        )
        cursor.execute(migration_body(path))
        cursor.execute("SET LOCAL search_path TO public, pg_catalog")
        states.append(fingerprint(cursor, schema))

    cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(
        sql.Identifier(schema)
    ))
    return states


def record_migration(cursor, path):
    cursor.execute(
        """
        INSERT INTO public.schema_migrations (name, checksum)
        VALUES (%s, %s)
        """,
        (path.name, checksum(path)),
    )


def migrate(cursor):
    cursor.execute("SET LOCAL search_path TO public, pg_catalog")
    states = reference_states(cursor)
    actual = fingerprint(cursor, "public")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS public.schema_migrations (
            name TEXT PRIMARY KEY,
            checksum TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    cursor.execute(
        "SELECT name, checksum FROM public.schema_migrations ORDER BY name"
    )
    recorded = cursor.fetchall()

    expected_names = [path.name for path in MIGRATIONS]

    if recorded:
        names = [row["name"] for row in recorded]
        if names != expected_names[:len(names)]:
            raise RuntimeError("Unexpected migration history; stopping.")

        for row, path in zip(recorded, MIGRATIONS):
            if row["checksum"] != checksum(path):
                raise RuntimeError(
                    f"Applied migration was modified: {path.name}"
                )

        current = len(recorded)
        if actual != states[current]:
            raise RuntimeError(
                "Database schema differs from migration history; stopping."
            )
    else:
        matching = [
            index for index, state in enumerate(states)
            if actual == state
        ]
        if not matching:
            raise RuntimeError(
                "Existing flights schema is not recognized; "
                "no application data was changed."
            )

        current = matching[0]
        for path in MIGRATIONS[:current]:
            record_migration(cursor, path)
            print(f"Recognized existing migration: {path.name}")

    for index in range(current, len(MIGRATIONS)):
        path = MIGRATIONS[index]
        cursor.execute(migration_body(path))

        if fingerprint(cursor, "public") != states[index + 1]:
            raise RuntimeError(f"Schema verification failed: {path.name}")

        record_migration(cursor, path)
        print(f"Applied migration: {path.name}")

    print("Database schema is up to date.")


def seed_demo(cursor):
    if os.environ.get("SEED_DEMO", "false").lower() != "true":
        print("Demo seed disabled.")
        return

    cursor.execute("LOCK TABLE public.flights IN SHARE ROW EXCLUSIVE MODE")
    cursor.execute("SELECT EXISTS(SELECT 1 FROM public.flights) AS populated")

    if cursor.fetchone()["populated"]:
        print("Database already contains flights; demo seed skipped.")
        return

    rows = [
        (
            f"DEMO{index + 1:03}",
            "JFK",
            "LAX",
            date(2025, 6, 1),
            "AA",
        )
        for index in range(25)
    ]

    cursor.executemany(
        """
        INSERT INTO public.flights (
            flight_number, origin, destination, flight_date, carrier_code
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        rows,
    )
    print("Inserted 25 fictional DEMO flights into an empty database.")


def main():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL lock_timeout = '15s'")
            cursor.execute("SET LOCAL statement_timeout = '120s'")

            # Serialize simultaneous bootstrap processes in this database.
            cursor.execute("SELECT pg_advisory_xact_lock(714025001)")

            migrate(cursor)
            seed_demo(cursor)

    print("Bootstrap committed successfully.")


if __name__ == "__main__":
    main()
