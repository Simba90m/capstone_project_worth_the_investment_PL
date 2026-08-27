-- Cleans the injuries source: normalizes name, standardizes column names.
--
-- NOTE: raw headers are 'Season', 'Injury', 'from', 'until', 'Days',
-- 'Games missed', 'player_name', 'player_id' -- quoted below since some
-- contain spaces/capitals or clash with SQL reserved words ('from').
--
-- 'Days' is stored as TEXT with a suffix (e.g. '90 days', '22 days'), not
-- a plain number -- confirmed by inspecting raw values directly after
-- total_days_missed showed 0 for 100% of injured players (1,176/1,176),
-- which was too uniform to be sparse/missing data and turned out to be
-- try_cast silently failing on every single row due to the ' days' text.
-- Fix: strip the suffix with regexp_extract before casting.
-- 'Games missed' loaded correctly as a plain integer already.
--
-- IMPORTANT: this file has its own player_id column, confirmed via direct
-- overlap check to be the same real Transfermarkt ID used in
-- stg_transfermarkt_values -- joins on player_id directly, no
-- name-matching needed for this pair of sources.

with injuries as (
    select * from {{ source('raw', 'injuries') }}
),

final as (
    select
        player_id,
        player_name,
        lower(trim(player_name)) as name_normalized,
        "Season" as season,
        "Injury" as injury_type,
        "from" as from_date,
        "until" as until_date,
        try_cast(regexp_extract("Days", '\d+') as integer) as days_missed,
        try_cast("Games missed" as integer) as games_missed
    from injuries
)

select * from final