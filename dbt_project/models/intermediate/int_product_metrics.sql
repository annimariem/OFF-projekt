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

        Jääb praegu tegemata...
    */

    created_datetime as estonia_dataset_first_seen_at,

    categories_tags,

    /* Lisaks lihtsustatud tootekategooria. */
    case
        when nullif(trim(categories_tags), '') is null
            then null

        when categories_tags ilike '%en:condiments%'
            then 'Condiments'

        when categories_tags ilike '%en:desserts%'
            then 'Desserts'

        when categories_tags ilike '%en:snacks%'
            then 'Snacks'

        when categories_tags ilike '%en:meals%'
            then 'Meals'

        when categories_tags ilike '%en:beverages-and-beverages-preparations%'
          or categories_tags ilike '%en:beverages%'
            then 'Beverages and beverages preparations'

        when categories_tags ilike '%en:plant-based-foods-and-beverages%'
            then 'Plant-based foods and beverages'

        when categories_tags ilike '%en:meats-and-their-products%'
          or categories_tags ilike '%en:meats%'
            then 'Meats and their products'

        when categories_tags ilike '%en:dairies%'
            then 'Dairies'

        when categories_tags ilike '%en:seafood%'
            then 'Seafood'

        when categories_tags ilike '%en:dietary-supplements%'
            then 'Dietary supplements'

        else 'Other'
    end as categories_simplified,

    -- Andmete terviklikkuse flagid

    (
        energy_kcal_100g is not null
        and proteins_100g is not null
        and carbohydrates_100g is not null
        and fat_100g is not null
    ) as has_nutrition_info,
    
    /* Lisaks tunnus, mis katab kõik EL-i 
    kohustuslikud toitainete pakendiandmed. */
    (
        energy_kcal_100g is not null
        and proteins_100g is not null
        and carbohydrates_100g is not null
        and sugars_100g is not null
        and fat_100g is not null
        and saturated_fat_100g is not null
        and salt_100g is not null
    ) as has_eu_nutrition_info,

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
