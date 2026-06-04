from pathlib import Path

import duckdb
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

from bootstrap_metadata import (
    get_latest_bootstrap_snapshot,
    create_bootstrap_load_run,
    finish_bootstrap_load_run_success,
    finish_bootstrap_load_run_failed,
)

load_dotenv()

BOOTSTRAP_DATASET_PATH = Path("data/bootstrap/ee_products_bootstrap.parquet")


def get_postgres_connection():
    """
    PostgreSQL ühendus warehouse'i.
    """

    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def recreate_raw_table(cursor, columns):
    """
    Drop + recreate strategy.

    MVP/full refresh lähenemine.
    """

    create_columns_sql = ", ".join([f'"{column}" TEXT' for column in columns])

    cursor.execute(f"""
        DROP TABLE IF EXISTS raw.raw_products CASCADE;

        CREATE TABLE raw.raw_products (
            {create_columns_sql}
        );
        """)


def load_bootstrap_snapshot():
    """
    Laeb bootstrap parquet dataseti PostgreSQL raw layerisse.
    """

    bootstrap_metadata = get_latest_bootstrap_snapshot()

    if bootstrap_metadata is None:

        raise RuntimeError(
            "Bootstrap metadata puudub tabelis " "raw.bootstrap_snapshots."
        )

    run_id = create_bootstrap_load_run(snapshot_id=bootstrap_metadata["snapshot_id"])

    con = None
    postgres_conn = None
    cursor = None

    try:

        if not BOOTSTRAP_DATASET_PATH.exists():

            raise FileNotFoundError(
                f"Bootstrap dataset puudub: " f"{BOOTSTRAP_DATASET_PATH}"
            )

        print(f"Laen bootstrap datasetti: " f"{BOOTSTRAP_DATASET_PATH}")

        con = duckdb.connect()

        postgres_conn = get_postgres_connection()
        postgres_conn.autocommit = True

        cursor = postgres_conn.cursor()

        print("Loen parquet faili DuckDB kaudu...")

        duckdb_relation = con.execute(f"""
            SELECT *
            FROM read_parquet(
                '{BOOTSTRAP_DATASET_PATH}'
            )
            """)

        columns = [description[0] for description in duckdb_relation.description]

        rows = duckdb_relation.fetchall()

        print(f"Laetud read parquet failist: " f"{len(rows):,}")

        print("Loon raw.raw_products tabeli...")

        recreate_raw_table(
            cursor,
            columns,
        )

        print("Kirjutan PostgreSQL raw layerisse...")

        insert_query = sql.SQL("""
            INSERT INTO raw.raw_products ({fields})
            VALUES ({values})
            """).format(
            fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
            values=sql.SQL(", ").join(sql.Placeholder() * len(columns)),
        )

        cursor.executemany(
            insert_query,
            rows,
        )

        print(f"PostgreSQL kirjutatud read: " f"{len(rows):,}")

        finish_bootstrap_load_run_success(
            run_id=run_id,
            rows_loaded=len(rows),
        )

        print("Bootstrap ingest lõpetatud")

    except Exception as e:

        finish_bootstrap_load_run_failed(
            run_id=run_id,
            error_message=str(e),
        )

        raise

    finally:

        if cursor is not None:
            cursor.close()

        if postgres_conn is not None:
            postgres_conn.close()

        if con is not None:
            con.close()


if __name__ == "__main__":
    load_bootstrap_snapshot()
