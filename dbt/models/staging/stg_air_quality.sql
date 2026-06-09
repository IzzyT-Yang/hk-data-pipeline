with source as (
    select * from {{ source('raw', 'air_quality') }}
),

deduplicated as (
    select *
    from source
    qualify row_number() over (partition by time order by ingested_at desc) = 1
)

select
    cast(time             as timestamp)  as time,
    cast(pm10             as float64)    as pm10,
    cast(pm2_5            as float64)    as pm2_5,
    cast(carbon_monoxide  as float64)    as carbon_monoxide,
    cast(nitrogen_dioxide as float64)    as nitrogen_dioxide,
    cast(sulphur_dioxide  as float64)    as sulphur_dioxide,
    cast(ozone            as float64)    as ozone,
    cast(european_aqi     as int64)      as european_aqi,
    cast(ingested_at      as timestamp)  as ingested_at
from deduplicated
