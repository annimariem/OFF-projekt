import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


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


def register_bootstrap_snapshot(
    source_snapshot_date,
    bootstrap_file,
    product_count,
    status="SUCCESS",
    notes=None,
):
    """
    Salvestab loodud bootstrap dataseti metadata andmebaasi.
    """

    conn = get_postgres_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO raw.bootstrap_snapshots (
                    source_snapshot_date,
                    bootstrap_file,
                    product_count,
                    status,
                    notes
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING snapshot_id
                """,
                (
                    source_snapshot_date,
                    bootstrap_file,
                    product_count,
                    status,
                    notes,
                ),
            )

            snapshot_id = cursor.fetchone()[0]

        conn.commit()

        print(f"Bootstrap metadata salvestatud " f"(snapshot_id={snapshot_id})")

        return snapshot_id

    finally:
        conn.close()


def get_latest_bootstrap_snapshot():
    """
    Tagastab viimase eduka bootstrapi metadata.
    """

    conn = get_postgres_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    snapshot_id,
                    source_snapshot_date,
                    bootstrap_created_at,
                    bootstrap_file,
                    product_count,
                    status,
                    notes
                FROM raw.bootstrap_snapshots
                WHERE status = 'SUCCESS'
                ORDER BY snapshot_id DESC
                LIMIT 1
                """)

            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "snapshot_id": row[0],
                "source_snapshot_date": row[1],
                "bootstrap_created_at": row[2],
                "bootstrap_file": row[3],
                "product_count": row[4],
                "status": row[5],
                "notes": row[6],
            }

    finally:
        conn.close()


def create_bootstrap_load_run(snapshot_id):
    """
    Registreerib bootstrap laadimise alguse.
    """

    conn = get_postgres_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO raw.bootstrap_load_runs (
                    snapshot_id,
                    status
                )
                VALUES (
                    %s,
                    'RUNNING'
                )
                RETURNING run_id
                """,
                (snapshot_id,),
            )

            run_id = cursor.fetchone()[0]

        conn.commit()

        print(f"Bootstrap laadimine registreeritud " f"(run_id={run_id})")

        return run_id

    finally:
        conn.close()


def finish_bootstrap_load_run_success(
    run_id,
    rows_loaded,
):
    """
    Märgib bootstrap laadimise edukalt lõpetatuks.
    """

    conn = get_postgres_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                UPDATE raw.bootstrap_load_runs
                SET
                    finished_at = NOW(),
                    status = 'SUCCESS',
                    rows_loaded = %s
                WHERE run_id = %s
                """,
                (
                    rows_loaded,
                    run_id,
                ),
            )

        conn.commit()

    finally:
        conn.close()


def finish_bootstrap_load_run_failed(
    run_id,
    error_message,
):
    """
    Märgib bootstrap laadimise ebaõnnestunuks.
    """

    conn = get_postgres_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                UPDATE raw.bootstrap_load_runs
                SET
                    finished_at = NOW(),
                    status = 'FAILED',
                    error_message = %s
                WHERE run_id = %s
                """,
                (
                    error_message,
                    run_id,
                ),
            )

        conn.commit()

    finally:
        conn.close()
