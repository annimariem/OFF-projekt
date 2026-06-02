select

    product_code,
    product_name,
    url,
    creator,

    created_datetime as off_created_at,
    last_modified_datetime,
    last_updated_datetime,

    /*
        Praegu kasutatakse OFF created_datetime väärtust, sest
        incremental delta pipeline ja ajalooline ingestion state
        pole veel implementeeritud.

        Tulevikus peaks see väli kirjeldama:
        "millal meie pipeline nägi toodet esimest korda Eesti datasetis"
    */

    created_datetime as estonia_dataset_first_seen_at,

    categories_tags,

    -- Andmete terviklikkuse flagid

    (
        energy_kcal_100g is not null
        and proteins_100g is not null
        and carbohydrates_100g is not null
        and fat_100g is not null
    ) as has_nutrition_info,

    ingredients_text is not null
        as has_ingredients,

    packaging is not null
        as has_packaging,

    quantity is not null
        as has_quantity,

    -- Üldine terviklikkuse skoor (0-4)

    (
        cast(
            (
                energy_kcal_100g is not null
                and proteins_100g is not null
                and carbohydrates_100g is not null
                and fat_100g is not null
            ) as int
        )
        +
        cast(
            ingredients_text is not null
            as int
        )
        +
        cast(
            packaging is not null
            as int
        )
        +
        cast(
            quantity is not null
            as int
        )
    ) as completeness_score

from {{ ref('stg_products') }}
