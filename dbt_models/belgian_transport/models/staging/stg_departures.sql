-- Staging model: clean and standardize raw departure data
-- Grain: one row per departure event

with source as (
    select * from {{ source('raw_transport', 'departures') }}
),

staged as (
    select
        -- Primary key
        md5(cast(station_id as varchar) || '-' || cast(vehicle_id as varchar) || '-' || cast(scheduled_time as varchar)) as departure_key,

        -- Station info
        station_id,
        station_name,

        -- Destination info
        destination,
        destination_id,

        -- Time fields
        scheduled_time,
        cast(departure_hour as integer) as departure_hour,
        cast(day_of_week as integer) as day_of_week,
        departure_date,

        -- Delay fields
        cast(delay_seconds as integer) as delay_seconds,
        cast(delay_minutes as double) as delay_minutes,
        cast(is_delayed as boolean) as is_delayed,
        cast(canceled as boolean) as is_canceled,

        -- Vehicle info
        vehicle_id,
        vehicle_type,
        platform,
        occupancy,

        -- Metadata
        ingested_at,
        processed_at

    from source
)

select * from staged