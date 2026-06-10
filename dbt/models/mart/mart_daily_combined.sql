with weather as (
    select * from {{ ref('mart_daily_weather') }}
),

air_quality as (
    select * from {{ ref('mart_daily_air_quality') }}
)

select
    w.date,

    -- weather
    w.avg_temp_c,
    w.max_temp_c,
    w.min_temp_c,
    w.avg_humidity_pct,
    w.total_precipitation_mm,
    w.avg_wind_speed_kmh,
    w.max_wind_speed_kmh,

    -- air quality
    a.avg_aqi,
    a.max_aqi,
    a.avg_pm2_5,
    a.max_pm2_5,
    a.avg_pm10,
    a.max_pm10,
    a.avg_no2,
    a.avg_o3

from weather w
inner join air_quality a on w.date = a.date
order by w.date desc
