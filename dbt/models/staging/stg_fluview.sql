-- Staging model for CDC FluView raw data
-- Standardizes column names and types from the raw Parquet files

with source as (
    select * from read_parquet('../data/raw/fluview/*.parquet')
),

renamed as (
    select
        cast(weekend_date as date)          as report_week_end,
        cast(region_type as varchar)        as region_type,
        cast(region as varchar)             as region,
        cast(year as integer)               as year,
        cast(week as integer)               as week,
        cast(ilitotal as integer)           as ili_total_cases,
        cast(num_of_providers as integer)   as num_providers,
        cast(total_patients as integer)     as total_patients,
        cast(percent_of_ili as double)      as pct_ili,
        _ingested_at::timestamp             as ingested_at
    from source
)

select * from renamed
