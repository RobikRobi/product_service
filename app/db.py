import os

import psycopg
from psycopg.rows import dict_row


DATABASE_URL = os.getenv("PRODUCT_DATABASE_URL")


def get_connection() -> psycopg.Connection:
    if not DATABASE_URL:
        raise RuntimeError("PRODUCT_DATABASE_URL environment variable is not set")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db() -> None:
    with get_connection() as connection:
        connection.execute("SELECT pg_advisory_lock(424242)")
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    price DOUBLE PRECISION NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 0,
                    owner_user_id INTEGER NOT NULL
                )
                """
            )
            columns = {
                row["column_name"]
                for row in connection.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'products'
                    """
                ).fetchall()
            }
            if "owner_user_id" not in columns:
                connection.execute(
                    """
                    ALTER TABLE products
                    ADD COLUMN owner_user_id INTEGER NOT NULL DEFAULT 0
                    """
                )
        finally:
            connection.execute("SELECT pg_advisory_unlock(424242)")
