-- Player identity resolution across sources.
--
-- CONFIRMED: player_valuations/players and the injuries dataset share the
-- same real Transfermarkt player_id (100% overlap checked directly) --
-- no name-matching needed between those two. This model's canonical
-- player_id IS that shared Transfermarkt ID.
--
-- Uses ROW_NUMBER (not DISTINCT) to guarantee exactly one row per
-- player_id. DISTINCT alone wasn't enough: some players have more than
-- one 'name' spelling across their valuation history (e.g. diacritic or
-- spelling corrections applied at different points on Transfermarkt),
-- which meant DISTINCT still produced duplicate rows per player. Taking
-- the most recent name (by valuation_date) as canonical resolves this
-- deterministically.
--
-- club_name is deliberately NOT included -- it's time-varying (players
-- transfer clubs); each valuation row already carries its own club_name.
--
-- REMAINING WORK: FBref has no shared ID with Transfermarkt, so matching
-- FBref rows to this key still requires name_normalized matching.
--
-- date_of_birth, position and sub_position are added here (not just
-- canonical_name) because they're player-level attributes from the
-- `players` source, not time-varying like club_name -- same reasoning as
-- canonical_name, so they belong in this identity/dimension table rather
-- than being re-derived downstream. Added to support the age- and
-- position-based stakeholder hypotheses (see Project_brainstorm.md).

with values_players as (
    select
        player_id,
        name,
        name_normalized,
        date_of_birth,
        position,
        sub_position,
        row_number() over (
            partition by player_id
            order by valuation_date desc
        ) as rn
    from {{ ref('stg_transfermarkt_values') }}
),

final as (
    select
        player_id,
        name as canonical_name,
        name_normalized,
        date_of_birth,
        position,
        sub_position
    from values_players
    where rn = 1
)

select * from final