import os
import re
import sys
import psycopg2
from datetime import datetime, UTC
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.bootstrap.bootstrap_metadata import (
    get_latest_bootstrap_snapshot_date,
)

load_dotenv()

DELTA_FILENAME_PATTERN = re.compile(r"openfoodfacts_products_(\d+)_(\d+)\.json\.gz")


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


def parse_delta_filename(delta_filename):
    """
    Parsib delta failinimest välja algus- ja lõpuajad.

    Näide:
    openfoodfacts_products_1780467227_1780552801.json.gz
    """

    match = DELTA_FILENAME_PATTERN.match(delta_filename)

    if not match:

        raise ValueError(f"Vigane delta failinimi: " f"{delta_filename}")

    start_ts = int(match.group(1))
    end_ts = int(match.group(2))

    return {
        "delta_start_ts": start_ts,
        "delta_end_ts": end_ts,
        "delta_start_datetime": datetime.fromtimestamp(
            start_ts,
            UTC,
        ),
        "delta_end_datetime": datetime.fromtimestamp(
            end_ts,
            UTC,
        ),
    }


def delta_file_exists(delta_filename):
    """
    Kontrollib, kas deltafail on juba registris.
    """

    conn = get_postgres_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT 1
                FROM raw.delta_files
                WHERE delta_filename = %s
                """,
                (delta_filename,),
            )

            return cursor.fetchone() is not None

    finally:

        conn.close()


def register_delta_file(
    delta_filename,
    source_url,
):
    """
    Registreerib uue deltafaili metadata tabelis.
    """

    if delta_file_exists(delta_filename):

        return None

    parsed = parse_delta_filename(delta_filename)

    conn = get_postgres_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO raw.delta_files (
                    delta_filename,
                    source_url,
                    delta_start_ts,
                    delta_end_ts,
                    delta_start_datetime,
                    delta_end_datetime
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING delta_id
                """,
                (
                    delta_filename,
                    source_url,
                    parsed["delta_start_ts"],
                    parsed["delta_end_ts"],
                    parsed["delta_start_datetime"],
                    parsed["delta_end_datetime"],
                ),
            )

            delta_id = cursor.fetchone()[0]

        conn.commit()

        print(f"Delta registreeritud " f"(delta_id={delta_id})")

        return delta_id

    finally:

        conn.close()


def get_required_delta_files():
    """
    Tagastab allalaadimata deltafailid,
    mis on uuemad kui viimane bootstrap.
    """

    bootstrap_date = get_latest_bootstrap_snapshot_date()

    if bootstrap_date is None:

        raise RuntimeError("Bootstrap snapshot puudub.")

    conn = get_postgres_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    delta_id,
                    delta_filename,
                    source_url,
                    delta_start_datetime,
                    delta_end_datetime
                FROM raw.delta_files
                WHERE
                    downloaded_at IS NULL
                    AND delta_end_datetime > %s
                ORDER BY delta_start_datetime
                """,
                (bootstrap_date,),
            )

            rows = cursor.fetchall()

            return [
                {
                    "delta_id": row[0],
                    "delta_filename": row[1],
                    "source_url": row[2],
                    "delta_start_datetime": row[3],
                    "delta_end_datetime": row[4],
                }
                for row in rows
            ]

    finally:

        conn.close()


def get_downloaded_unprocessed_deltas():
    """
    Tagastab alla laaditud,
    kuid veel töötlemata deltad.
    """

    conn = get_postgres_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    delta_id,
                    delta_filename,
                    source_url
                FROM raw.delta_files
                WHERE
                    downloaded_at IS NOT NULL
                    AND processed_at IS NULL
                ORDER BY delta_start_datetime
                """)

            rows = cursor.fetchall()

            return [
                {
                    "delta_id": row[0],
                    "delta_filename": row[1],
                    "source_url": row[2],
                }
                for row in rows
            ]

    finally:

        conn.close()


def mark_delta_as_downloaded(
    delta_id,
):
    """
    Märgib deltafaili allalaadituks.
    """

    conn = get_postgres_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                UPDATE raw.delta_files
                SET downloaded_at = NOW()
                WHERE delta_id = %s
                """,
                (delta_id,),
            )

        conn.commit()

    finally:

        conn.close()


def mark_delta_as_processed(
    delta_id,
    filtered_product_count,
    loaded_product_count,
):
    """
    Märgib delta töödelduks.
    """

    conn = get_postgres_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                UPDATE raw.delta_files
                SET
                    filtered_product_count = %s,
                    loaded_product_count = %s,
                    processed_at = NOW()
                WHERE delta_id = %s
                """,
                (
                    filtered_product_count,
                    loaded_product_count,
                    delta_id,
                ),
            )

        conn.commit()

    finally:

        conn.close()
