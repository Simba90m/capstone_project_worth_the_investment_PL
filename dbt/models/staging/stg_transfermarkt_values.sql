-- Cleans player_valuations + players down to valuations for players
-- CURRENTLY at a Premier League club (see scope note below).
--
-- HISTORY OF THIS FILTER (worth understanding, not just the end result):
-- v1: filtered on valuations.player_club_domestic_competition_id directly.
--     Wrong -- this field was inconsistent per-row (e.g. Tomas Rosicky's
--     Dortmund-era rows were mislabeled 'GB1').
-- v2: joined valuations.current_club_id -> clubs.domestic_competition_id.
--     Also wrong, in the opposite way -- current_club_id turned out to be
--     CONSTANT per player (always their most-recent club), not accurate
--     per valuation date. This made every historical row display the
--     player's current club name, even for years before they'd joined it.
-- v3 (this version): use players.current_club_domestic_competition_id
--     (player-level, confirmed stable/authoritative) to decide WHICH
--     PLAYERS to include, and valuations.current_club_name (confirmed
--     historically accurate per row in the original data) to LABEL each
--     row's club. Two different fields for two different jobs, matched
--     to what each one is actually reliable for.
--
-- SCOPE THIS PRODUCES: full career valuation history for players who are
-- CURRENTLY at a Premier League club -- not "valuations that occurred
-- while at a PL club." This is a deliberate, documented choice: for a
-- recruitment tool, a scout wants a current target's whole trajectory,
-- not just their PL-era numbers. State this explicitly in the capstone
-- write-up rather than presenting it as strictly PL-only valuations.

with players as (
    select *
    from {{ source('raw', 'players') }}
    where current_club_domestic_competition_id = 'GB1'
),

valuations as (
    select * from {{ source('raw', 'player_valuations') }}
),

final as (
    select
        players.player_id,
        players.name,
        lower(trim(players.name)) as name_normalized,
        players.date_of_birth,
        players.position,
        players.sub_position,
        valuations.current_club_id as club_id,
        valuations.current_club_name as club_name,
        valuations.date as valuation_date,
        valuations.market_value_in_eur
    from players
    inner join valuations on players.player_id = valuations.player_id
)

select * from final