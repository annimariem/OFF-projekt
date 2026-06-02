select
    count(*) as total_products,
    count(distinct creator) as unique_creators,
    avg(completeness_score) as avg_completeness_score,
    sum(has_nutrition_info::int) as products_with_nutrition,
    sum(has_ingredients::int) as products_with_ingredients,
    sum(has_packaging::int) as products_with_packaging,
    sum(has_quantity::int) as products_with_quantity
from {{ ref('int_product_metrics') }}
