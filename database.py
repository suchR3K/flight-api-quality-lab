import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


load_dotenv(Path(__file__).resolve().parent / ".env")


def get_connection(database_name: str | None = None):
    selected_database = (
        database_name
        if database_name is not None
        else os.environ["POSTGRES_DB"]
    )

    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=selected_database,
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=5,
        row_factory=dict_row,
    )


def get_db():
    with get_connection() as connection:
        yield connection
