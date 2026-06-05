from pathlib import Path
import os

import duckdb
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

ESTONIA_TAG = "en:estonia"

DELTA_DIR = Path("data/deltas/files")

COLUMN_MAPPING = {
    "code": {
        "rel": "code",
        "map": "$.code",
        "type": "string",
    },
    "creator": {
        "rel": "creator",
        "map": "$.creator",
        "type": "string",
    },
    "created_t": {
        "rel": "created_t",
        "map": "$.created_t",
        "type": "bigint",
    },
    "last_modified_t": {
        "rel": "last_modified_t",
        "map": "$.last_modified_t",
        "type": "bigint",
    },
    "last_updated_t": {
        "rel": "last_updated_t",
        "map": "$.last_updated_t",
        "type": "bigint",
    },
    "product_name": {
        "rel": "product_name",
        "map": "$.product_name",
        "type": "string",
    },
    "countries_tags": {
        "rel": "countries_tags",
        "map": "$.countries_tags[*]",
        "type": "tags",
    },
    "ingredients_text": {
        "rel": "ingredients_text",
        "map": "$.ingredients_text",
        "type": "string",
    },
    "quantity": {
        "rel": "quantity",
        "map": "$.quantity",
        "type": "string",
    },
    "product_quantity": {
        "rel": "product_quantity",
        "map": "$.product_quantity",
        "type": "string",
    },
    "packaging": {
        "rel": "packaging",
        "map": "$.packaging",
        "type": "string",
    },
    "packaging_text": {
        "rel": "packaging_text",
        "map": "$.packaging_text",
        "type": "string",
    },
    "packaging_tags": {
        "rel": "packaging_tags",
        "map": "$.packaging_tags[*]",
        "type": "tags",
    },
    "brands": {
        "rel": "brands",
        "map": "$.brands",
        "type": "string",
    },
    "brands_tags": {
        "rel": "brands_tags",
        "map": "$.brands_tags[*]",
        "type": "tags",
    },
    "categories_tags": {
        "rel": "categories_tags",
        "map": "$.categories_tags[*]",
        "type": "tags",
    },
    "nutriscore_grade": {
        "rel": "nutriscore_grade",
        "map": "$.nutriscore_grade",
        "type": "string",
    },
    "nova_group": {
        "rel": "nova_group",
        "map": "$.nova_group",
        "type": "bigint",
    },
    # nutrition
    "energy-kcal_100g": {
        "rel": 'nutrition.aggregated_set.nutrients."energy-kcal".value',
        "map": "$.nutrition.aggregated_set.nutrients.energy-kcal.value",
        "type": "double",
    },
    "fat_100g": {
        "rel": "nutrition.aggregated_set.nutrients.fat.value",
        "map": "$.nutrition.aggregated_set.nutrients.fat.value",
        "type": "double",
    },
    "saturated-fat_100g": {
        "rel": 'nutrition.aggregated_set.nutrients."saturated-fat".value',
        "map": "$.nutrition.aggregated_set.nutrients.saturated-fat.value",
        "type": "double",
    },
    "carbohydrates_100g": {
        "rel": "nutrition.aggregated_set.nutrients.carbohydrates.value",
        "map": "$.nutrition.aggregated_set.nutrients.carbohydrates.value",
        "type": "double",
    },
    "sugars_100g": {
        "rel": "nutrition.aggregated_set.nutrients.sugars.value",
        "map": "$.nutrition.aggregated_set.nutrients.sugars.value",
        "type": "double",
    },
    "fiber_100g": {
        "rel": "nutrition.aggregated_set.nutrients.fiber.value",
        "map": "$.nutrition.aggregated_set.nutrients.fiber.value",
        "type": "double",
    },
    "proteins_100g": {
        "rel": "nutrition.aggregated_set.nutrients.proteins.value",
        "map": "$.nutrition.aggregated_set.nutrients.proteins.value",
        "type": "double",
    },
    "salt_100g": {
        "rel": "nutrition.aggregated_set.nutrients.salt.value",
        "map": "$.nutrition.aggregated_set.nutrients.salt.value",
        "type": "double",
    },
    "sodium_100g": {
        "rel": "nutrition.aggregated_set.nutrients.sodium.value",
        "map": "$.nutrition.aggregated_set.nutrients.sodium.value",
        "type": "double",
    },
}

RAW_COLUMNS = list(COLUMN_MAPPING.keys())


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


def is_map_mode(
    con,
    delta_file,
):
    """
    Kontrollib, kas fail on MAP(JSON) kujul.
    """

    schema = con.execute(f"""
        DESCRIBE
        SELECT *
        FROM read_json_auto(
            '{delta_file}'
        )
    """).fetchall()

    return len(schema) == 1 and schema[0][0] == "json"


def build_relational_query(delta_file):

    selected_columns = []

    for column, config in COLUMN_MAPPING.items():

        if config["type"] == "tags":

            expr = f"""
                array_to_string(
                    {config["rel"]},
                    ','
                )
            """

        elif config["type"] == "double":

            expr = f"""
                CAST(
                    {config["rel"]}
                    AS DOUBLE
                )
            """

        elif config["type"] == "bigint":

            expr = f"""
                CAST(
                    {config["rel"]}
                    AS BIGINT
                )
            """

        else:

            expr = config["rel"]

        selected_columns.append(f'{expr} AS "{column}"')

    return f"""
        SELECT
            {",".join(selected_columns)}
        FROM read_ndjson('{delta_file}')
        WHERE list_contains(
            countries_tags,
            '{ESTONIA_TAG}'
        )
    """


def build_map_query(delta_file):

    selected_columns = []

    for column, config in COLUMN_MAPPING.items():

        if config["type"] == "tags":

            expr = f"""
                array_to_string(
                    list_transform(
                        json_extract(
                            json,
                            '{config["map"]}'
                        ),
                        lambda x:
                            json_extract_string(
                                x,
                                '$'
                            )
                    ),
                    ','
                )
            """

        elif config["type"] == "double":

            expr = f"""
                CAST(
                    json_extract(
                        json,
                        '{config["map"]}'
                    )
                    AS DOUBLE
                )
            """

        elif config["type"] == "bigint":

            expr = f"""
                CAST(
                    json_extract(
                        json,
                        '{config["map"]}'
                    )
                    AS BIGINT
                )
            """

        else:

            expr = f"""
                json_extract_string(
                    json,
                    '{config["map"]}'
                )
            """

        selected_columns.append(f'{expr} AS "{column}"')

    return f"""
        SELECT
            {",".join(selected_columns)}
        FROM read_json_auto('{delta_file}')
        WHERE
            json_extract_string(
                json,
                '$.countries_tags'
            )
            LIKE '%{ESTONIA_TAG}%'
    """


def load_delta_file(
    delta_filename,
):
    """
    Laeb ühe deltafaili raw.raw_products tabelisse.
    """

    delta_file = DELTA_DIR / delta_filename

    if not delta_file.exists():

        raise FileNotFoundError(f"Delta fail puudub: {delta_file}")

    print(f"\nLaen deltafaili:\n" f"{delta_filename}")

    duck_conn = duckdb.connect()

    postgres_conn = None
    cursor = None

    try:

        postgres_conn = get_postgres_connection()

        cursor = postgres_conn.cursor()

        if is_map_mode(
            duck_conn,
            delta_file,
        ):

            print("Schema mode: MAP")

            query = build_map_query(delta_file)

        else:

            print("Schema mode: RELATIONAL")

            query = build_relational_query(delta_file)

        rows = duck_conn.execute(query).fetchall()

        if not rows:

            print("Eesti tooteid ei leitud.")

            return 0

        insert_sql = sql.SQL("""
            INSERT INTO raw.raw_products (
                {}
            )
            VALUES (
                {}
            )
        """).format(
            sql.SQL(", ").join(sql.Identifier(c) for c in RAW_COLUMNS),
            sql.SQL(", ").join(sql.Placeholder() for _ in RAW_COLUMNS),
        )

        cursor.executemany(
            insert_sql,
            rows,
        )

        postgres_conn.commit()

        print(f"Laetud read: {len(rows)}")

        return len(rows)

    finally:

        if cursor:
            cursor.close()

        if postgres_conn:
            postgres_conn.close()

        duck_conn.close()
