with weather as (
    select * from {{ ref('stg_weather') }}
)

select
    date(time)                      as date,
    avg(temperature_2m)             as avg_temp_c,
    max(temperature_2m)             as max_temp_c,
    min(temperature_2m)             as min_temp_c,
    avg(relative_humidity_2m)       as avg_humidity_pct,
    sum(precipitation)              as total_precipitation_mm,
    avg(wind_speed_10m)             as avg_wind_speed_kmh,
    max(wind_speed_10m)             as max_wind_speed_kmh
from weather
group by 1
order by 1 desc
