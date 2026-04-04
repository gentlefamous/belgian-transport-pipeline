-- Fact table: Delays
-- Grain: one row per departure event

with departures as (
    select * from {{ ref('stg_departures') }}
)

select
    departure_key,
    station_id,
    destination_id,
    vehicle_id,
    departure_date,
    departure_hour,
    day_of_week,
    delay_seconds,
    delay_minutes,
    is_delayed,
    is_canceled,
    vehicle_type,
    platform,
    occupancy,
    scheduled_time,
    ingested_at
from departures