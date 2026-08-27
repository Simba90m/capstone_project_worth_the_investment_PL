-- One row per player per valuation date -- the time series that feeds the
-- value-trend forecasting step in Week 3.

with values as (
    select * from {{ ref('stg_transfermarkt_values') }}
),

key_map as (
    select * from {{ ref('player_key_map') }}
),

final as (
    select
        key_map.player_id,
        key_map.canonical_name,
        values.valuation_date,
        values.market_value_in_eur,
        values.club_name
    from values
    inner join key_map on values.player_id = key_map.player_id
    order by key_map.player_id, values.valuation_date
)

select * from final
