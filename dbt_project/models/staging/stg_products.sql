select
    -- IDENTIFIERS
    code as product_code,
    url,

    -- TIMESTAMPS
    created_t,
    created_datetime,
    last_modified_t,
    last_modified_datetime,
    last_updated_t,
    last_updated_datetime,

    -- PRODUCT INFO
    product_name,
    abbreviated_product_name,
    generic_name,

    -- CLASSIFICATION
    brands,
    brands_tags,
    categories,
    categories_tags,
    categories_en,
    main_category,
    main_category_en,

    -- GEOGRAPHY
    countries,
    countries_tags,
    countries_en,

    -- PACKAGING / QUANTITY
    quantity,
    product_quantity,
    packaging,
    packaging_tags,
    packaging_text,

    -- INGREDIENTS / ALLERGENS
    ingredients_text,
    ingredients_tags,
    allergens,
    allergens_en,
    traces,
    traces_tags,
    additives_n,
    additives_tags,

    -- QUALITY / COMPLETENESS
    completeness,
    unique_scans_n,
    states,
    states_tags,
    data_quality_errors_tags,

    -- SCORES
    nutriscore_score,
    nutriscore_grade,
    nova_group,
    environmental_score_score,
    environmental_score_grade,

    -- FOOD GROUPS
    pnns_groups_1,
    pnns_groups_2,
    food_groups,
    food_groups_tags,
    food_groups_en,

    -- IMAGES
    image_url,
    image_small_url,
    image_ingredients_url,
    image_nutrition_url,

    -- CORE NUTRITION
    cast(nullif("energy-kcal_100g", '') as numeric) as energy_kcal_100g,
    cast(nullif(fat_100g, '') as numeric) as fat_100g,
    cast(nullif("saturated-fat_100g", '') as numeric) as saturated_fat_100g,
    cast(nullif(carbohydrates_100g, '') as numeric) as carbohydrates_100g,
    cast(nullif(sugars_100g, '') as numeric) as sugars_100g,
    cast(nullif(fiber_100g, '') as numeric) as fiber_100g,
    cast(nullif(proteins_100g, '') as numeric) as proteins_100g,
    cast(nullif(salt_100g, '') as numeric) as salt_100g,
    cast(nullif(sodium_100g, '') as numeric) as sodium_100g

from {{ source('raw', 'raw_products') }} as s

/* Ilmnes, et Eesti toodete väljavõttes leidub hulk ridu, 
mis pole üldsegi toidud, vaid hoopis näiteks puhastusvahendid jms. 
Siin on need read välja filtreeritud,
et meie analüüsid kajastaksid vaid toitudega seotud andmeid. */
where s.categories_en is null or not(
    s.categories_en ilike '%detergents%' 
    or s.categories_en ilike '%cleaning%' 
    or s.categories_en ilike '%varnishes%'
)

