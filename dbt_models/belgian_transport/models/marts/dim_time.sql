-- Dimension: Time
-- Grain: one row per unique hour of day

with hours as (
    select unnest(generate_series(0, 23)) as hour_of_day
)

select
    hour_of_day,
    case
        when hour_of_day between 7 and 9 then true
        when hour_of_day between 16 and 18 then true
        else false
    end as is_peak_hour,
    case
        when hour_of_day between 6 and 11 then 'Morning'
        when hour_of_day between 12 and 16 then 'Afternoon'
        when hour_of_day between 17 and 20 then 'Evening'
        else 'Night'
    end as time_period
from hours