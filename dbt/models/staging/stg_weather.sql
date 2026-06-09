with source as (
    select * from {{ source('raw', 'weather') }}
),

deduplicated as (
    select *
    from source
    qualify row_number() over (partition by time order by ingested_at desc) = 1
)

select
    cast(time                 as timestamp)  as time,
    cast(temperature_2m       as float64)    as temperature_2m,
    cast(relative_humidity_2m as float64)    as relative_humidity_2m,
    cast(precipitation        as float64)    as precipitation,
    cast(wind_speed_10m       as float64)    as wind_speed_10m,
    cast(wind_direction_10m   as float64)    as wind_direction_10m,
    cast(weather_code         as int64)      as weather_code,
    cast(ingested_at          as timestamp)  as ingested_at
from deduplicated
