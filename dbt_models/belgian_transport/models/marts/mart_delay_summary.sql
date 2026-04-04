-- Mart: Delay Summary
-- Pre-computed aggregations for the dashboard
-- Grain: one row per station + departure_hour combination

with delays as (
    select * from {{ ref('fct_delays') }}
),

stations as (
    select * from {{ ref('dim_stations') }}
)

select
    d.station_id,
    s.station_name,
    s.station_name_primary,
    d.departure_hour,
    t.is_peak_hour,
    t.time_period,
    count(*) as total_departures,
    sum(case when d.is_delayed then 1 else 0 end) as delayed_departures,
    sum(case when d.is_canceled then 1 else 0 end) as canceled_departures,
    round(avg(d.delay_seconds), 1) as avg_delay_seconds,
    round(avg(d.delay_minutes), 1) as avg_delay_minutes,
    max(d.delay_seconds) as max_delay_seconds,
    round(
        sum(case when d.is_delayed then 1 else 0 end) * 100.0 / count(*), 1
    ) as delay_rate_pct
from delays d
left join stations s on d.station_id = s.station_id
left join {{ ref('dim_time') }} t on d.departure_hour = t.hour_of_day
group by
    d.station_id,
    s.station_name,
    s.station_name_primary,
    d.departure_hour,
    t.is_peak_hour,
    t.time_period