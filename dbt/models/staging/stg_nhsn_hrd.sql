-- Staging model: CDC NHSN Weekly Hospital Respiratory Data
-- Source: data.cdc.gov/resource/ua7e-t2fy
-- Covers: Influenza, COVID-19, RSV by jurisdiction and week

with source as (
    select * from read_parquet('../data/raw/nhsn_hrd/*.parquet')
),

renamed as (
    select
        cast(weekendingdate as date)                    as week_ending_date,
        cast(jurisdiction as varchar)                   as jurisdiction,
        cast(respseason as varchar)                     as resp_season,

        -- Influenza
        cast(totalconfflunewadm as integer)             as flu_new_admissions,
        cast(totalconffluhosppats as integer)           as flu_hospitalized,
        cast(totalconffluicupats as integer)            as flu_icu,
        cast(totalconfflunewadmper100k as double)       as flu_new_adm_per_100k,
        cast(totalconfflunewadmcumulativeseasonalsum as integer) as flu_cumulative_season,

        -- COVID-19
        cast(totalconfc19newadm as integer)             as covid_new_admissions,
        cast(totalconfc19hosppats as integer)           as covid_hospitalized,
        cast(totalconfc19icupats as integer)            as covid_icu,
        cast(totalconfc19newadmper100k as double)       as covid_new_adm_per_100k,
        cast(totalconfc19newadmcumulativeseasonalsum as integer) as covid_cumulative_season,

        -- RSV
        cast(totalconfrsvnewadm as integer)             as rsv_new_admissions,
        cast(totalconfrsvnewadmcumulativeseasonalsum as integer) as rsv_cumulative_season,

        -- Hospital capacity
        cast(numinptbeds as double)                     as inpatient_beds_total,
        cast(numinptbedsocc as double)                  as inpatient_beds_occupied,
        cast(pctinptbedsocc as double)                  as pct_beds_occupied,

        cast(_ingested_at as timestamp)                 as ingested_at
    from source
)

select * from renamed
