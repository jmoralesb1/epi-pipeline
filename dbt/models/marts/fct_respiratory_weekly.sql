-- Fact table: Weekly respiratory illness metrics (Gold layer)
-- Includes Flu, COVID-19, RSV with week-over-week and year-over-year changes
-- Ready for anomaly detection and API consumption

with base as (
    select * from {{ ref('stg_nhsn_hrd') }}
),

national as (
    -- Aggregate to national level by week
    select
        week_ending_date,
        resp_season,
        sum(flu_new_admissions)         as flu_new_admissions,
        sum(flu_hospitalized)           as flu_hospitalized,
        sum(flu_icu)                    as flu_icu,
        avg(flu_new_adm_per_100k)       as flu_new_adm_per_100k_avg,
        sum(covid_new_admissions)       as covid_new_admissions,
        sum(covid_hospitalized)         as covid_hospitalized,
        sum(covid_icu)                  as covid_icu,
        avg(covid_new_adm_per_100k)     as covid_new_adm_per_100k_avg,
        sum(rsv_new_admissions)         as rsv_new_admissions,
        sum(inpatient_beds_total)       as beds_total,
        sum(inpatient_beds_occupied)    as beds_occupied,
        avg(pct_beds_occupied)          as pct_beds_occupied_avg
    from base
    group by 1, 2
),

with_trends as (
    select
        *,
        -- Week-over-week change
        lag(flu_new_admissions)  over (order by week_ending_date) as flu_adm_prev_week,
        lag(covid_new_admissions) over (order by week_ending_date) as covid_adm_prev_week,

        -- Year-over-year change (52 weeks back)
        lag(flu_new_admissions, 52)  over (order by week_ending_date) as flu_adm_prev_year,
        lag(covid_new_admissions, 52) over (order by week_ending_date) as covid_adm_prev_year
    from national
),

final as (
    select
        *,
        round(flu_new_admissions - flu_adm_prev_week, 0)    as flu_wow_change,
        round(flu_new_admissions - flu_adm_prev_year, 0)    as flu_yoy_change,
        round(covid_new_admissions - covid_adm_prev_week, 0) as covid_wow_change,
        round(covid_new_admissions - covid_adm_prev_year, 0) as covid_yoy_change
    from with_trends
)

select * from final
order by week_ending_date
