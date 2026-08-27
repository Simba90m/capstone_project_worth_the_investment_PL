-- Combines injury events (Transfermarkt) with playing-time load (FBref) into
-- one per-player workload/risk feature table.
--
-- Injuries join directly on player_id (confirmed 100% ID overlap with the
-- values/players source). FBref still joins on name_normalized since it
-- has no shared ID with Transfermarkt.
--
-- Design note: a player with zero rows in stg_transfermarkt_injuries could
-- mean "genuinely never injured" OR "missing from this source" -- decide
-- how you're handling that (documented assumption, not a silent default)
-- before this feeds the risk score.
--
-- date_of_birth/position/sub_position pulled through from player_key_map
-- to support the "position predicts injury/workload risk" and "younger
-- players show better value-risk tradeoff" stakeholder hypotheses --
-- compute age (current_date - date_of_birth) in the notebook rather than
-- here, so "current age" doesn't get baked into a materialized table.

with key_map as (
    select * from {{ ref('player_key_map') }}
),

injuries as (
    select * from {{ ref('stg_transfermarkt_injuries') }}
),

fbref as (
    select * from {{ ref('stg_fbref_performance') }}
),

injury_summary as (
    select
        player_id,
        count(*) as injury_count,
        sum(days_missed) as total_days_missed,
        max(from_date) as most_recent_injury_date
    from injuries
    group by player_id
),

workload_summary as (
    select
        name_normalized,
        sum(minutes_90s) as total_90s_played,
        sum(matches_played) as total_matches
    from fbref
    group by name_normalized
),

final as (
    select
        key_map.player_id,
        key_map.canonical_name,
        key_map.date_of_birth,
        key_map.position,
        key_map.sub_position,
        coalesce(injury_summary.injury_count, 0) as injury_count,
        coalesce(injury_summary.total_days_missed, 0) as total_days_missed,
        injury_summary.most_recent_injury_date,
        coalesce(workload_summary.total_90s_played, 0) as total_90s_played,
        coalesce(workload_summary.total_matches, 0) as total_matches
    from key_map
    left join injury_summary on key_map.player_id = injury_summary.player_id
    left join workload_summary on key_map.name_normalized = workload_summary.name_normalized
)

select * from final

