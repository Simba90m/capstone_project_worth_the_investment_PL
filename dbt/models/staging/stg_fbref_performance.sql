-- Cleans FBref stats: normalizes name for matching, filters to Premier
-- League, computes an approximate total-minutes workload figure.
--
-- Source: akshankrithick/fbref-2017-2024-for-europes-top-5-leagues (Kaggle)
-- -- 7 CSVs (one per season, 2017-18 through 2023-24), identical columns,
-- each already carries its own 'season' column. Combined into one file/
-- table before loading (18,243 rows total across all seasons).
--
-- No direct total-minutes column exists, so it's approximated from
-- Matches Played * Avg Mins per Match -- good enough for a workload
-- feature, not exact to the minute.

with fbref as (
    select *
    from {{ source('raw', 'fbref_player_stats') }}
    where "comp" = 'Premier League'
),

final as (
    select
        "player" as player_name,
        lower(trim("player")) as name_normalized,
        "squad" as club_name,
        "season",
        "Matches Played" as matches_played,
        "Avg Mins per Match" as avg_minutes_per_match,
        ("Matches Played" * "Avg Mins per Match") / 90.0 as minutes_90s,
        "Goals" as goals,
        "Assists" as assists
    from fbref
)

select * from final