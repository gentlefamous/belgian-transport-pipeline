-- Dimension: Stations
-- Grain: one row per unique station

with stations as (
    select distinct
        station_id,
        station_name
    from {{ ref('stg_departures') }}
    where station_id is not null
)

select
    station_id,
    station_name,
    -- Extract city from station name (before the '/' if bilingual)
    split_part(station_name, '/', 1) as station_name_primary
from stations