/* Kvaliteedikontrollide kokkuvõte */

select
    count(distinct case when product_code_count > 1 then product_code end) as duplicate_product_code_count,
    sum(invalid_carbohydrates_100g) as invalid_carbohydrates_100g_count,
    sum(invalid_sugars_100g) as invalid_sugars_100g_count,
    sum(invalid_fat_100g) as invalid_fat_100g_count,
    sum(invalid_saturated_fat_100g) as invalid_saturated_fat_100g_count,
    sum(invalid_proteins_100g) as invalid_proteins_100g_count,
    sum(invalid_salt_100g) as invalid_salt_100g_count,
    sum(sugars_greater_than_carbohydrates) as sugars_greater_than_carbohydrates_count,
    sum(saturated_fat_greater_than_fat) as saturated_fat_greater_than_fat_count,
    sum(invalid_ingredients_text) as invalid_ingredients_text_count,
    sum(invalid_packaging) as invalid_packaging_count,
    sum(invalid_quantity) as invalid_quantity_count,
    sum(invalid_categories_en) as invalid_categories_en_count
from {{ ref('quality_checks_results') }}