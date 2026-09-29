# Worth the Investment?

**Forecasting player value trend & injury risk for Premier League recruitment decisions.**

Capstone project — neue fische Data Analytics & AI Bootcamp. Presented September 29, 2026.

## The question

Once you account for injury risk, can a rising transfer value still be trusted as a recruitment signal? This project combines three real data sources, tests three hypotheses for three different recruitment stakeholders, and reports the results honestly, including where they didn't hold up.

## Data

- **Transfermarkt** — player market values
- **Transfermarkt** — injury records
- **FBref** — match performance, 2017–2024, top 5 leagues

1,959 players in scope; 649 with usable FBref playing-time data (582 after stricter filtering for the age/position analyses). The coverage gap is documented and investigated rather than hidden — see the final presentation for the full breakdown.

Pipeline: raw sources → dbt staging → player-matching → dbt marts → DuckDB warehouse (6 models, `dbt/`).

## Key findings

| Stakeholder | Hypothesis | Result |
|---|---|---|
| Recruitment / Scouting | Injury recency predicts value decline | Mixed — it's *any* injury history that matters, not recency. No injury history: +4.35% median value growth. Any injury history: 0.0%. (n ≈ 29,000 snapshots) |
| Sporting Directors / Front Office | Younger players have a better value-risk tradeoff | Split — injury rate more than doubles with age (2.5 → 6.0 per 1,000 90s), but only the 21–24 band shows real value growth (+7.1%) |
| Medical / Performance | Position predicts injury risk | Not statistically confirmed (p = 0.61), though goalkeepers trend lower (2.3 vs. ~4.2 for outfield players, n = 52) |

The value-forecast model itself is **not reliable on its own**: backtested on 150 players, it calls the direction right only 22.7% of the time, worse than a coin flip, with a systematic bias toward predicting "rising." The injury-history signal is the one that actually holds up and is recommended for use; the forecast is reported honestly as a negative result rather than hidden.

## Repository structure

```
dbt/            dbt models: staging → prep → marts, DuckDB target
notebooks/      exploration, hypothesis tests, forecasting, risk scoring
scripts/        data fetch (Kaggle) and load-to-DuckDB scripts
presentations/  final slide deck, four stakeholder-milestone decks, Tableau workbook
```

## Reproducing the pipeline

```bash
pip install -r requirements.txt
python scripts/01_fetch_data.py
python scripts/02_load_to_duckdb.py
cd dbt && dbt run
```

Then open the notebooks in `notebooks/` in order, or open `presentations/Capstone project. Injury Risk in Premier League Recruitment.twbx` in Tableau to explore the dashboards interactively.

## Author

Mahmoud Abdelaziz — [LinkedIn](https://linkedin.com/in/mahmoud-abdelaziz-mm) · [Tableau Public](https://public.tableau.com/app/profile/mahmoud.abdelaziz2733/vizzes)
