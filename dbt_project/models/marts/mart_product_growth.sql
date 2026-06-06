with first_seen as (
    select
        product_code,
        cast(estonia_dataset_first_seen_at as date) as first_seen_date
    from {{ ref('int_product_metrics') }}
    where estonia_dataset_first_seen_at is not null
),
daily_counts as (
    select
        first_seen_date as day,
        count(*) as new_products
    from first_seen
    group by 1
)

select
    day,
    new_products,
    sum(new_products) over (order by day) as cumulative_products,
    round(avg(new_products) over (order by day rows between 6 preceding and current row)::numeric, 2) as new_products_7d_avg
from daily_counts
order by day
