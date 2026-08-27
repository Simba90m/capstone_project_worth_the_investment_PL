"""
02_load_to_duckdb.py

Loads all raw CSVs into a local DuckDB database (data/warehouse.duckdb),
into a 'raw' schema, with table names matching dbt/models/staging/sources.yml.

Run this AFTER 00a_fetch_kaggle_data.ipynb has downloaded everything and
you've combined the FBref season files into one CSV.

Usage:
    python scripts/02_load_to_duckdb.py
"""

from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

# Maps: table name (must match sources.yml) -> CSV file path
TABLE_FILES = {
    "players": RAW_DIR / "player_scores" / "players.csv",
    "player_valuations": RAW_DIR / "player_scores" / "player_valuations.csv",
    "appearances": RAW_DIR / "player_scores" / "appearances.csv",
    "clubs": RAW_DIR / "player_scores" / "clubs.csv",
    "competitions": RAW_DIR / "player_scores" / "competitions.csv",
    "injuries": RAW_DIR / "injuries" / "transfermarkt.csv",
    "fbref_player_stats": RAW_DIR / "fbref" / "combined_all_seasons.csv",
}


def main():
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    for table_name, csv_path in TABLE_FILES.items():
        if not csv_path.exists():
            print(f"SKIPPING {table_name} -- file not found: {csv_path}")
            continue

        df = pd.read_csv(csv_path)
        con.execute(f"CREATE OR REPLACE TABLE raw.{table_name} AS SELECT * FROM df")
        print(f"Loaded raw.{table_name}: {len(df):,} rows from {csv_path.name}")

    con.close()
    print(f"\nDone. Database at {DB_PATH}")


if __name__ == "__main__":
    main()
