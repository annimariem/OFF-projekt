from pathlib import Path
import json

import duckdb

SNAPSHOT_METADATA_PATH = Path("data/snapshots/snapshot_metadata.json")

BOOTSTRAP_OUTPUT_PATH = Path("data/bootstrap/ee_products_bootstrap.parquet")


def load_snapshot_metadata():
    """
    Loeb snapshot metadata faili.
    """

    with open(SNAPSHOT_METADATA_PATH, "r") as f:
        return json.load(f)


def get_snapshot_path():
    """
    Leiab õige snapshot faili metadata põhjal.
    """

    metadata = load_snapshot_metadata()

    snapshot_filename = metadata["snapshot_filename"]

    return Path("data/snapshots") / snapshot_filename


def filter_estonia_products():
    snapshot_path = get_snapshot_path()

    print(f"Kasutatav snapshot: " f"{snapshot_path}")

    BOOTSTRAP_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    con = duckdb.connect()
    print("Alustan Eesti toodete filtreerimist...")

    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=4")
    con.execute("""
        SET enable_progress_bar=true
    """)

    query = f"""
    COPY (
        SELECT *
        FROM read_csv_auto(
            '{snapshot_path}',
            delim='\\t',
            header=true,
            ignore_errors=true,
            all_varchar=true
        )
        WHERE countries_tags LIKE '%en:estonia%'
    )
    TO '{BOOTSTRAP_OUTPUT_PATH}'
    (
        FORMAT PARQUET
    );
    """

    con.execute(query)

    print(f"Bootstrap dataset salvestatud: " f"{BOOTSTRAP_OUTPUT_PATH}")

    result = con.execute(f"""
        SELECT COUNT(*)
        FROM read_parquet(
            '{BOOTSTRAP_OUTPUT_PATH}'
        )
        """).fetchone()

    print(f"Kokku Eesti tooteid: " f"{result[0]:,}")

    con.close()

    return result[0]


if __name__ == "__main__":
    filter_estonia_products()
