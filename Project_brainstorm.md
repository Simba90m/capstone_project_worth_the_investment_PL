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
- [x] Technical analysis in Python + SQL (+ Tableau) — pipeline runs
  end-to-end (dbt/DuckDB); all 3 stakeholder-specific hypotheses analyzed
  with statistical tests (Mann-Whitney, Kruskal-Wallis) in dedicated
  notebooks. Tableau already covers the 3 general questions (see below);
  still open whether the stakeholder-hypothesis results get their own
  Tableau worksheets too.
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
  **Analyzed** in `notebooks/hypothesis_age_vs_value_risk_tradeoff.ipynb`.
  Result is split — supported on the risk side, not cleanly on the value
  side. Both Kruskal-Wallis tests came out significant (value growth:
  H=95.27, p≈0.0000; risk: H=34.57, p≈0.0000), and here the significance
  carries more weight than hypothesis #1's did, because this test runs one
  row per player (n=582), not one row per valuation snapshot — no risk of
  a huge N manufacturing significance out of a trivial effect.
  **Risk side — supported:** median injury rate rises with age across the
  buckets with usable sample size — 21-24 "emerging" 2.49, 25-28 "prime"
  3.97, 29-32 "established" 3.22, 33+ "veteran" 5.95 per 1,000 90s. Not
  perfectly monotonic (a small dip at 29-32), but the overall direction —
  younger carries less risk than veterans — holds and is statistically real.
  **Value side — not a clean "younger = better" story:** median value
  change is 0.00% in every bucket except 21-24 "emerging" (+7.14%). Under-21
  also shows 0.00%, but that bucket has only n=4 players — far too small to
  trust, and the wide box in the plot (spanning up to ~200%) is one or two
  outlier valuations dominating a tiny sample, not a real pattern. Honest
  read: "21-24 emerging players uniquely combine above-average value growth
  with below-average risk," not "value growth falls steadily with age."
  **Caveats:** (1) same 1,310/1,959 (67%) zero-`total_90s_played` exclusion
  as the position hypothesis — **now confirmed** (see
  `notebooks/diagnostic_fbref_match_rate.ipynb`) to be a genuine coverage
  gap, not a name-matching bug; (2) the 21-24 bucket's +7.14%
  could be partly inflated by the same low-starting-valuation "breakout
  debut" effect flagged in hypothesis #1 — worth cross-checking against
  that notebook's `PREV_VALUE_FLOOR`-filtered version before presenting as
  clean; (3) Under-21 (n=4) is too small to draw any conclusion from either
  way and shouldn't be cited as evidence.
- **Medical/Performance staff** — *Which workload patterns are worth
  flagging before signing a player?* Hypothesis: **position predicts
  injury/workload risk.**
  **Analyzed** in `notebooks/hypothesis_position_vs_injury_risk.ipynb`,
  after `dbt run` materialized the new columns. **Not statistically
  supported:** Kruskal-Wallis across the 4 positions (workload-adjusted
  injury rate, injuries per 1,000 90s played) gave p=0.61 — nowhere near
  significant. Worth reporting as an honest null result, not hiding it.
  There's a suggestive-but-unconfirmed pattern underneath: goalkeepers show
  a much lower group-level rate (1.85 per 1,000 90s vs. 4.27-4.98 for
  outfield positions), which matches real football knowledge (far less
  running/sprinting exposure), but only 52 goalkeepers had enough playing
  time to include, and their individual rates are highly spread out (see
  the boxplot) — too little data, too much within-group noise, to call it
  significant. Frame as "direction consistent with known injury patterns,
  dataset underpowered to confirm" rather than either overclaiming or
  discarding it.
  **Caveat to flag either way:** 1,310 of 1,959 players (67%) had zero
  recorded `total_90s_played` and were excluded before the position
  breakdown even started. **Confirmed** via
  `notebooks/diagnostic_fbref_match_rate.ipynb`: this is a genuine
  coverage gap, not a name-matching bug. 0 of the 1,310 have *any* exact
  FBref name match at all (rules out "matched but summed to 0"); 257
  never had a valuation during the 2017-2024 FBref window at all (clean
  "too new / not yet a PL target" cases); of the remaining 1,053, a
  last-name substring check flagged 269 as possible near-matches, but
  manually reviewing the sample showed every one is a different real
  player sharing a common surname (e.g. "Alfie Lewis" vs. "Lewis Hall"),
  not the same player under a different spelling — and several of the
  true no-matches are independently verifiable as players who genuinely
  weren't in the Premier League 2017-2024 (Donnarumma at PSG/Milan,
  Zubimendi at Real Sociedad, both transferring to PL clubs in 2025;
  Brobbey at Ajax). Worth a line on the Tableau "Flagged: Known Data
  Limits" sheet regardless — the cause is now understood, but the 67%
  exclusion itself still stands.

**Status: all three stakeholder hypotheses are now analyzed** — see the
three notebooks above. None came back as a clean, unqualified "yes"; all
three are honest nuanced/mixed results (which is fine, and worth saying
plainly in the presentation rather than papering over). Remaining
next steps:
1. Confirm the `miniconda3` kernel is actually selected for the original
   `00a_fetch_kaggle_data.ipynb` through `04_recruitment_signal.ipynb`
   notebooks too, not just the two hypothesis notebooks already checked —
   see `DEBUGGING_LOG.md` entry 9's still-open item.
2. Decide whether any of the three hypothesis results are worth a matching
   Tableau worksheet alongside the existing four (the position and age
   notebooks' boxplots are the most presentation-ready).
3. Optional: the deeper SQL-level date fix for
   `stg_transfermarkt_injuries.sql` (`DEBUGGING_LOG.md` entry 8, open
   items) — now actually testable since `dbt run` works end-to-end.
4. Commit and push all of this (dbt models, notebooks, this doc, the
   debugging log) to GitHub — the last confirmed push predates this
   round of changes.
