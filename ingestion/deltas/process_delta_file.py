from pathlib import Path

import duckdb

from delta_metadata import (
    get_downloaded_unprocessed_deltas,
    mark_delta_as_processed,
)

from load_delta_file import (
    load_delta_file,
)

ESTONIA_TAG = "en:estonia"

DELTA_DIR = Path("data/deltas/files")


def get_schema_mode(
    con,
    delta_file,
):
    """
    Määrab, kuidas DuckDB konkreetset
    deltafaili parsib.

    RELATIONAL: Veerud on eraldi väljad.
    MAP: Kogu dokument on ühes json veerus.
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

        return "MAP"

    return "RELATIONAL"


def print_delta_schema_modes():
    """
    Kuvab kõikide lokaalselt allalaaditud
    deltafailide schema mode'i.
    """

    con = duckdb.connect()

    try:

        print("\n=== DELTA SCHEMA MODES ===\n")

        for delta_file in sorted(DELTA_DIR.glob("*.json.gz")):

            mode = get_schema_mode(
                con,
                delta_file,
            )

            print(f"{mode:<12}" f"{delta_file.name}")

    finally:

        con.close()


def get_estonia_product_count(
    con,
    delta_file,
):
    """
    Loendab Eesti tooted sõltumata sellest,
    kas DuckDB inferib faili relatsioonilise
    skeemina või MAP(JSON) skeemina.
    """

    mode = get_schema_mode(
        con,
        delta_file,
    )

    if mode == "MAP":

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
    Töötleb ühe deltafaili:
    - määrab schema mode'i
    - loendab Eesti tooted
    - laadib need raw kihti
    - uuendab metadata tabelit
    """

    delta_file = DELTA_DIR / delta_filename

    if not delta_file.exists():

        raise FileNotFoundError(f"Delta fail puudub: " f"{delta_file}")

    print(f"\nTöötlen deltafaili:\n" f"{delta_filename}")

    con = duckdb.connect()

    try:

        schema_mode = get_schema_mode(
            con,
            delta_file,
        )

        print(f"Schema mode: " f"{schema_mode}")

        filtered_product_count = get_estonia_product_count(
            con,
            delta_file,
        )

        print(f"Leitud Eesti tooteid: " f"{filtered_product_count}")

        rows_loaded = load_delta_file(delta_filename)

        if rows_loaded is None:

            raise RuntimeError("Delta laadimine ei " "tagastanud ridade arvu.")

        mark_delta_as_processed(
            delta_id=delta_id,
            filtered_product_count=(filtered_product_count),
            loaded_product_count=(rows_loaded),
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

    # print_delta_schema_modes()

    process_all_deltas()
