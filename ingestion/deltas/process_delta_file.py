from pathlib import Path

import duckdb

from delta_metadata import (
    get_downloaded_unprocessed_deltas,
    mark_delta_as_processed,
)

ESTONIA_TAG = "en:estonia"

DELTA_DIR = Path("data/deltas/files")


def get_estonia_product_count(
    con,
    delta_file,
):
    """
    Loendab Eesti tooted sõltumata sellest,
    kas DuckDB inferib faili relatsioonilise
    skeemina või MAP(JSON) skeemina.
    """

    schema = con.execute(f"""
        DESCRIBE
        SELECT *
        FROM read_json_auto(
            '{delta_file}'
        )
    """).fetchall()

    is_map_mode = len(schema) == 1 and schema[0][0] == "json"

    if is_map_mode:

        result = con.execute(f"""
            SELECT COUNT(*)
            FROM read_json_auto(
                '{delta_file}'
            )
            WHERE
                CAST(
                    json['countries_tags']
                    AS VARCHAR
                )
                LIKE '%{ESTONIA_TAG}%'
        """).fetchone()

    else:

        result = con.execute(f"""
            SELECT COUNT(*)
            FROM read_json_auto(
                '{delta_file}'
            )
            WHERE list_contains(
                countries_tags,
                '{ESTONIA_TAG}'
            )
        """).fetchone()

    return result[0]


def process_delta_file(
    delta_id,
    delta_filename,
):
    """
    Töötleb ühe deltafaili.

    MVP:
    - filtreerib Eesti tooted
    - loendab need
    - uuendab metadata tabelit

    Raw kihti veel ei kirjuta.
    """

    delta_file = DELTA_DIR / delta_filename

    if not delta_file.exists():

        raise FileNotFoundError(f"Delta fail puudub: " f"{delta_file}")

    print(f"\nTöötlen deltafaili:\n" f"{delta_filename}")

    con = duckdb.connect()

    try:

        filtered_product_count = get_estonia_product_count(
            con,
            delta_file,
        )

        print(f"Leitud Eesti tooteid: " f"{filtered_product_count}")

        #
        # TODO järgmises commitis:
        # kirjuta Eesti tooted
        # PostgreSQL raw.raw_products tabelisse
        #

        loaded_product_count = filtered_product_count

        mark_delta_as_processed(
            delta_id=delta_id,
            filtered_product_count=(filtered_product_count),
            loaded_product_count=(loaded_product_count),
        )

        print("Delta metadata uuendatud.")

    finally:

        con.close()


def process_all_deltas():
    """
    Töötleb kõik alla laaditud,
    kuid veel töötlemata deltad.
    """

    deltas = get_downloaded_unprocessed_deltas()

    if not deltas:

        print("Töötlemata deltafaile " "ei leitud.")

        return

    print(f"Leitud " f"{len(deltas)} " f"töötlemata deltafaili.")

    for delta in deltas:

        process_delta_file(
            delta_id=delta["delta_id"],
            delta_filename=(delta["delta_filename"]),
        )

    print("\nKõik deltafailid " "on töödeldud.")


if __name__ == "__main__":
    process_all_deltas()
