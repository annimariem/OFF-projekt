import os
import re
from datetime import datetime, UTC

import psycopg2
from dotenv import load_dotenv

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


def get_pending_delta_files():
    """
    Tagastab allalaadimata deltafailid.
    """

    conn = get_postgres_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    delta_id,
                    delta_filename,
                    source_url,
                    delta_start_ts,
                    delta_end_ts,
                    delta_start_datetime,
                    delta_end_datetime,
                    discovered_at,
                    downloaded_at
                FROM raw.delta_files
                WHERE downloaded_at IS NULL
                ORDER BY delta_start_datetime
                """)

            rows = cursor.fetchall()

            return [
                {
                    "delta_id": row[0],
                    "delta_filename": row[1],
                    "source_url": row[2],
                    "delta_start_ts": row[3],
                    "delta_end_ts": row[4],
                    "delta_start_datetime": row[5],
                    "delta_end_datetime": row[6],
                    "discovered_at": row[7],
                    "downloaded_at": row[8],
                }
                for row in rows
            ]

    finally:

        conn.close()


def mark_delta_as_downloaded(
    delta_id,
):
    """
    Märgib deltafaili allalaetuks.
    """

    conn = get_postgres_connection()

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                """
                UPDATE raw.delta_files
                SET
                    downloaded_at = NOW()
                WHERE delta_id = %s
                """,
                (delta_id,),
            )

        conn.commit()

    finally:

        conn.close()
