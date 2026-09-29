"""
Export the dbt marts (plus a couple of derived tables that mirror the
notebook analysis) to parquet snapshots bundled into the Streamlit app,
so the app runs from a fresh clone without needing the DuckDB warehouse
file or a dbt run. Mirrors the approach used in the Tech Interview
Outcomes and Workforce/HR Streamlit apps.
"""
import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "warehouse.duckdb"
OUT_DIR = Path(__file__).parent.parent / "app" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PREV_VALUE_FLOOR = 100_000  # Transfermarkt's placeholder-valuation floor; see notebooks/hypothesis_injury_recency_vs_value.ipynb


def main():
    con = duckdb.connect(str(DB_PATH), read_only=True)

    players = con.execute("""
        select player_id, canonical_name, position, sub_position,
               injury_count, total_days_missed, most_recent_injury_date,
               total_90s_played, total_matches
        from player_injury_workload
    """).df()

    value_history = con.execute("""
        select player_id, canonical_name, valuation_date, market_value_in_eur, club_name
        from player_value_history
        order by player_id, valuation_date
    """).df()

    injuries = con.execute("select * from stg_transfermarkt_injuries").df()
    con.close()

    # --- Consecutive-snapshot value change, the same construction used in
    # notebooks/hypothesis_injury_recency_vs_value.ipynb ---
    value_history["valuation_date"] = pd.to_datetime(value_history["valuation_date"])
    value_history = value_history.sort_values(["player_id", "valuation_date"]).reset_index(drop=True)
    value_history["prev_value"] = value_history.groupby("player_id")["market_value_in_eur"].shift(1)
    value_history["value_change_pct"] = (
        (value_history["market_value_in_eur"] - value_history["prev_value"]) / value_history["prev_value"]
    )
    changes = value_history.dropna(subset=["value_change_pct"]).copy()

    injuries["from_date"] = pd.to_datetime(injuries["from_date"], errors="coerce")
    injs_sorted = injuries.sort_values("from_date").dropna(subset=["from_date"])
    changes_sorted = changes.sort_values("valuation_date")

    merged = pd.merge_asof(
        changes_sorted, injs_sorted,
        left_on="valuation_date", right_on="from_date",
        by="player_id", direction="backward",
    )
    merged["days_since_injury"] = (merged["valuation_date"] - merged["from_date"]).dt.days
    merged["has_prior_injury"] = merged["days_since_injury"].notna()

    def recency_bucket(days):
        if pd.isna(days):
            return "no prior injury"
        elif days <= 90:
            return "recent (<=90 days)"
        elif days <= 365:
            return "moderate (91-365 days)"
        return "distant (>365 days)"

    merged["recency_bucket"] = merged["days_since_injury"].apply(recency_bucket)
    merged_filtered = merged[merged["prev_value"] > PREV_VALUE_FLOOR].copy()

    value_changes_out = merged_filtered[[
        "player_id", "canonical_name", "valuation_date", "prev_value",
        "market_value_in_eur", "value_change_pct", "has_prior_injury", "recency_bucket",
    ]]

    players.to_parquet(OUT_DIR / "players.parquet", index=False)
    value_history.drop(columns=["prev_value", "value_change_pct"]).to_parquet(
        OUT_DIR / "value_history.parquet", index=False
    )
    value_changes_out.to_parquet(OUT_DIR / "value_changes.parquet", index=False)

    for f in OUT_DIR.glob("*.parquet"):
        print(f"{f.name}: {f.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
