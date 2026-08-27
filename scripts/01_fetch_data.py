"""
01_fetch_data.py

Downloads all three raw data sources into data/raw/. FBref data comes from
a pre-scraped Kaggle mirror rather than live scraping, since fbref.com
blocks scrapers via Cloudflare (confirmed with both requests and
cloudscraper). The FBref mirror used is the multi-season
akshankrithick/fbref-2017-2024-for-europes-top-5-leagues dataset (7 season
CSVs, 2017-18 through 2023-24) -- this is what stg_fbref_performance.sql
is actually built against, see DEBUGGING_LOG.md entry 7.

NOTE: Run this on your own machine (VS Code / Git Bash), not in a sandboxed
environment without internet access to kaggle.com. You'll need a free Kaggle
account and API token (kaggle.json) set up first:
https://www.kaggle.com/docs/api

Install once:
    pip install kaggle pandas

Usage:
    python scripts/01_fetch_data.py
"""

import subprocess
import sys
import zipfile
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "player_scores": "davidcariboo/player-scores",
    "injuries": "irrazional/transfermarkt-injuries",
    "fbref": "akshankrithick/fbref-2017-2024-for-europes-top-5-leagues",
    # multi-season (2017-18 to 2023-24), 7 per-season CSVs -- combine with
    # pandas.concat and filter to Premier League before loading to DuckDB,
    # see stg_fbref_performance.sql for the expected column names.
}


def download_kaggle_dataset(slug: str, dest_subdir: str):
    """Downloads and unzips a Kaggle dataset into data/raw/<dest_subdir>/"""
    dest = RAW_DIR / dest_subdir
    dest.mkdir(exist_ok=True)
    print(f"Downloading {slug} -> {dest}")
    subprocess.run(
        [sys.executable, "-m", "kaggle", "datasets", "download", "-d", slug, "-p", str(dest)],
        check=True,
    )
    # unzip anything that landed there
    for zf in dest.glob("*.zip"):
        with zipfile.ZipFile(zf) as z:
            z.extractall(dest)
        zf.unlink()


if __name__ == "__main__":
    for name, slug in DATASETS.items():
        download_kaggle_dataset(slug, name)

    print("\nAll datasets downloaded. Run the column-check script next to "
          "confirm real column names before wiring up the dbt staging models.\n")
