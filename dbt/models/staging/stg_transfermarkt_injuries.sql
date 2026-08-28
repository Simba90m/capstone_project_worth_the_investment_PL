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
-- 'from'/'until' are also TEXT, formatted like 'Jan 5, 2021', with a
-- '-' placeholder for unknown dates mixed in (confirmed by hitting a
-- literal ValueError parsing them naively -- see DEBUGGING_LOG.md entry
-- 8). try_strptime returns NULL instead of erroring on anything that
-- doesn't match the format, so the '-' placeholder becomes a clean NULL
-- here rather than needing every downstream consumer (SQL or notebook)
-- to re-parse this itself. DEBUGGING_LOG.md entry 8 originally patched
-- this on the notebook side only, flagged as an open item; this is that
-- fix applied at the source instead.
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
        try_strptime("from", '%b %d, %Y')::date as from_date,
        try_strptime("until", '%b %d, %Y')::date as until_date,
        try_cast(regexp_extract("Days", '\d+') as integer) as days_missed,
        try_cast("Games missed" as integer) as games_missed
    from injuries
)

select * from final