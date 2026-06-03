select

    product_code,
    product_name,
    url,

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
    /* Lisaks lihtsustatud tootekategooria. */
    categories_en,
    split_part(categories_en, ',', 1) as categories1,
    case
        when categories_en is null then null
        when split_part(categories_en, ',', 1) = 'Condiments' then 'Condiments'
        when split_part(categories_en, ',', 1) = 'Desserts' then 'Desserts'
        when split_part(categories_en, ',', 1) = 'Snacks' then 'Snacks'
        when split_part(categories_en, ',', 1) = 'Meals' then 'Meals'
        when split_part(categories_en, ',', 1) in ('Beverages and beverages preparations', 'Beverages')
             then 'Beverages and beverages preparations'
        when split_part(categories_en, ',', 1) in ('Plant-based foods and beverages', 'Plant-based foods')
             then 'Plant-based foods and beverages'
        when split_part(categories_en, ',', 1) in ('Meats and their products', 'Meats')
             then 'Meats and their products'
        when split_part(categories_en, ',', 1) = 'Dairies' then 'Dairies'
        when split_part(categories_en, ',', 1) = 'Seafood' then 'Seafood'
        when split_part(categories_en, ',', 1) = 'Dietary supplements' then 'Dietary supplements'
        else 'Other'
    end as categories_simplified,

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
