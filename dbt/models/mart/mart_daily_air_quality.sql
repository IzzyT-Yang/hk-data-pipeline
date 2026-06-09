with air_quality as (
    select * from {{ ref('stg_air_quality') }}
)

select
    date(time)              as date,
    avg(pm10)               as avg_pm10,
    max(pm10)               as max_pm10,
    avg(pm2_5)              as avg_pm2_5,
    max(pm2_5)              as max_pm2_5,
    avg(nitrogen_dioxide)   as avg_no2,
    max(nitrogen_dioxide)   as max_no2,
    avg(ozone)              as avg_o3,
    max(ozone)              as max_o3,
    avg(european_aqi)       as avg_aqi,
    max(european_aqi)       as max_aqi
from air_quality
group by 1
order by 1 desc
