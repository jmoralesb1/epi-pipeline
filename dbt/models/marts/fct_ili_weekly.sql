-- Fact table: weekly ILI (Influenza-Like Illness) metrics
-- Gold layer ready for anomaly detection and API consumption

with base as (
    select * from {{ ref('stg_fluview') }}
    where region_type = 'National'
),

with_lag as (
    select
        report_week_end,
        year,
        week,
        ili_total_cases,
        total_patients,
        pct_ili,
        num_providers,
        lag(pct_ili) over (order by report_week_end)        as pct_ili_prev_week,
        lag(pct_ili, 52) over (order by report_week_end)    as pct_ili_prev_year
    from base
),

final as (
    select
        *,
        round(pct_ili - pct_ili_prev_week, 4)       as wow_change,
        round(pct_ili - pct_ili_prev_year, 4)       as yoy_change
    from with_lag
)

select * from final
order by report_week_end
