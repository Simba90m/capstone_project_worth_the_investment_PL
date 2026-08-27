# Worth the Investment?
### Forecasting Player Value Trend and Injury Risk for Premier League Recruitment Decisions

## Project summary
Combines player market-value history, injury records, and match performance data
to answer: **does the market correctly price rising-value players who also carry
high injury/workload risk?**

## Hypothesis
Market value trend alone overstates a player's recruitment worth — players with
rising value *and* high injury/workload risk are systematically over-valued
relative to their realistic future output.

## Questions
1. Can we forecast a player's market value trend over the next 1–2 transfer
   windows from age, performance trend, and appearance data?
2. Does injury history/frequency predict future injury risk well enough to flag
   "high risk" players?
3. Combined, do value-forecast + injury-risk together produce a better
   recruitment signal than value alone?

## Scope
Premier League only, most recent 2–3 seasons (pull enough seasons that each
player has multiple value snapshots to forecast from).

## Data sources
| Source | What it gives us | Link |
|---|---|---|
| Football Data from Transfermarkt (Kaggle) | market values, appearances, games | kaggle.com/datasets/davidcariboo/player-scores |
| Transfermarkt Injuries (Kaggle) | injury type, dates, duration | kaggle.com/datasets/irrazional/transfermarkt-injuries |
| FBref 2017-2024 for Europe's Top 5 Leagues (Kaggle) | match-level minutes/performance stats, 8 seasons | kaggle.com/datasets/akshankrithick/fbref-2017-2024-for-europes-top-5-leagues |

**Note on FBref:** live scraping fbref.com is blocked by their Cloudflare bot
protection (confirmed via both plain `requests` and `cloudscraper`). We use
the pre-scraped multi-season Kaggle dataset above instead -- 8 seasons (2017-
2024) across the top 5 European leagues, filtered down to Premier League
seasons in the staging model.

## Changing seasons
The Transfermarkt datasets (player-scores, injuries) cover full historical
ranges already, so no change needed there beyond filtering dates in the SQL
models if you want to narrow the window. For FBref, swap the Kaggle dataset
slug in `00a_fetch_kaggle_data.ipynb` to whichever season's dataset you want,
or add the multi-season `hubertsidorowicz` dataset alongside/instead of it.
After changing sources, rerun the column-check cell and update
`stg_fbref_performance.sql`'s column names to match.

## Repo structure
```
pl_recruitment_capstone/
├── data/
│   ├── raw/            # untouched downloads land here
│   └── processed/      # cleaned CSVs, matched player keys, etc.
├── dbt/
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/    # one model per raw source, 1:1 with the source
│       ├── prep/        # player_key_map: the cross-source matching logic
│       └── marts/      # joined, analysis-ready tables (value history, injury/workload)
├── scripts/
│   └── 01_fetch_data.py  # download instructions + Kaggle API template
├── notebooks/            # 01_exploration, 02_value_forecast, 03_risk_score,
│                          # 04_recruitment_signal -- real .ipynb files, ready to
│                          # run once you point them at your dbt output
└── README.md

Matches the staging -> prep -> marts pattern from your shop_smart dbt module:
staging cleans, prep resolves identity/business logic (the player matching),
marts is the final analysis-ready output.
```

## Running the pipeline
1. Fetch raw data: run `notebooks/00a_fetch_kaggle_data.ipynb` (needs a
   Kaggle API token, see kaggle.com/docs/api)
2. Combine the 7 FBref season CSVs into one file (see the pandas.concat
   snippet noted in `stg_fbref_performance.sql`'s comments)
3. Load everything into DuckDB: `python scripts/02_load_to_duckdb.py`
4. Run dbt: from inside the `dbt/` folder, `dbt run` (uses `profiles.yml`,
   already configured for the local DuckDB file at `data/warehouse.duckdb`)
5. Query the results: from Python,
   `duckdb.connect('data/warehouse.duckdb').sql("SELECT * FROM main.player_value_history LIMIT 10")`
   or point the notebooks in `notebooks/` at the same DB file

No Postgres server needed -- DuckDB is a local file-based database, so this
runs entirely on your machine with nothing extra to install beyond
`pip install duckdb dbt-core dbt-duckdb` (already in requirements.txt).

## Roadmap
Confirmed at kickoff (Aug 26, 2026). Kickoff **Wed Aug 26** — Capstone
Event / Graduation **Tue Sep 29, 2026**. SH# = stakeholder check-in, per
the kickoff deck's check-in timeline.

- **Week 1 (Aug 26 – Sep 1)** — Project planning: lock hypothesis/questions,
  inventory data sources, start data retrieval.
  **SH#1 check-in:** present subject & question, objective, high-level
  deliverables, project plan, detailed deliverables/milestones.
- **Week 2 (Sep 2 – Sep 8)** — Lay foundations / build the ETL: player-ID
  matching across the 3 sources, dbt staging → marts, get everything into
  DuckDB.
  **SH#2 check-in:** share the key research question and your MVP.
- **Week 3 (Sep 9 – Sep 15)** — Build the tool: raw analysis (value-by-age
  curves, injury frequency patterns), then fine-tune (Prophet value
  forecast, injury-risk score, combined recruitment signal).
  **SH#3 check-in:** present the as-is state — treat it as a dry run of the
  real capstone presentation.
- **Week 4 (Sep 16 – Sep 28)** — Conclusion prepping and polishing: Tableau
  dashboard + story concept, code freeze, presentation design & format,
  speech practice (minimum 10x), rehearsal in class + dress rehearsal, tech
  check.
- **Sep 29 — Capstone Event.** Final presentation to external guests
  (10–15 min).

## Deliverables checklist
Per neue fische's official capstone requirements — track status here as
the project progresses:

- [x] Clearly stated business question with background & impact — hypothesis
  + 3 questions above.
- [ ] Technical analysis in Python + SQL (+ Tableau) — pipeline built
  (dbt/DuckDB), notebooks scaffolded; analysis not yet run end-to-end.
- [x] Work stored in a GitHub repository —
  https://github.com/Simba90m/capstone_project_worth_the_investment_PL
  (pushed, `main` branch tracking `origin/main`). Note: this is its own
  standalone repo, separate from the general `Data_Analytics_Bootcamp`
  folder/repo it lives inside on disk — that's intentional, the capstone
  needed its own dedicated repo, not to be bundled with other coursework.
- [x] Data stored in a SQL database — DuckDB (`data/warehouse.duckdb`), a
  local file-based SQL database.
- [ ] Final presentation (10–15 min), with slides committed to the GitHub
  repo — not started, due Week 4.
- [x] Uses multiple, genuinely-your-own data sources — 3 combined
  (Transfermarkt values, Transfermarkt injuries, FBref performance); not a
  copy of a prior project.

## Stakeholders & their specific hypotheses
Pulled from the master `final_projects.xlsx` Topics sheet — each stakeholder
has their own question *and* a specific, testable hypothesis beyond the 3
general questions above. Status = whether the data needed to test it is in
the marts yet (as of this update) and whether the analysis has actually
been run.

- **Recruitment/Scouting departments** — *Which rising-value targets carry
  hidden injury risk?* Hypothesis: **injury recency predicts near-term
  value decline.**
  **Analyzed** in `notebooks/hypothesis_injury_recency_vs_value.ipynb`.
  Result is mixed/nuanced, not a clean yes: a one-sided Mann-Whitney test
  (recent-injury snapshots vs. all others) came out significant
  (p≈0.0000), but both groups' *median* value change rounds to 0.00% — at
  this sample size (~30k snapshots) that kind of test can be significant
  on a small distributional shift even when the typical case barely
  differs, so don't oversell the p-value alone. The bigger, more robust
  pattern: median value change is ~0% for all three injured buckets
  (recent/moderate/distant) but positive for players with **no** injury
  history at all (+11.11% raw, +4.35% after excluding likely breakout-debut
  snapshots — see below). So the data supports "any injury history
  correlates with flatter value growth" more clearly than it supports
  "recency specifically" as worded.
  **Data quality check done:** the raw "no prior injury" gap was partly a
  mechanical artifact — young/reserve players get a low placeholder
  valuation (e.g. €50k-100k) before their first real one, which is a huge
  % jump unrelated to injuries, and lands almost entirely in the
  "no prior injury" bucket (1,100 of 1,261 excluded snapshots came from
  that bucket alone). After excluding snapshots starting below €100k, the
  gap shrinks (mean 76.57%→45.88%, median 11.11%→4.35%) but survives —
  still clearly above the ~0% injured buckets. Also found and fixed along
  the way: `stg_transfermarkt_injuries.sql`'s raw `from_date` includes a
  `"-"` placeholder for unknown dates that breaks naive date parsing — see
  `DEBUGGING_LOG.md` entry 8.
- **Sporting Directors/Front Office** — *How does injury risk change the
  investment case for a transfer?* Hypothesis: **younger players show a
  better value-risk tradeoff than veterans.**
  Data status: needed `date_of_birth` wasn't flowing past staging — added
  it to `player_key_map` → `player_injury_workload` in this update. Needs
  `dbt run` to materialize, then bucket players by age and compare
  risk-score vs. value-forecast return per bucket. Not yet analyzed.
- **Medical/Performance staff** — *Which workload patterns are worth
  flagging before signing a player?* Hypothesis: **position predicts
  injury/workload risk.**
  Data status: same fix — `position`/`sub_position` now flow through to
  `player_injury_workload`. Needs `dbt run`, then group injury_count /
  total_90s_played by position. Not yet analyzed.

**Next steps to actually answer these three:** (1) `dbt run` to rebuild the
marts with the new columns, (2) add analysis cells to `03_risk_score.ipynb`
or `04_recruitment_signal.ipynb` for each (age-bucket, position, and
injury-recency-vs-value-decline), (3) if the results are worth showing,
add matching Tableau worksheets alongside the existing four.
