# Notebooks

Suggested notebook breakdown, matching the roadmap weeks:

- `01_exploration.ipynb` — Week 2–3: value-by-age curves, injury frequency
  patterns, first look at player_value_history and player_injury_workload
  from dbt.
- `02_value_forecast.ipynb` — Week 3: Prophet (or trend model) forecasting
  market value per player, backtested against held-out recent valuations.
- `03_risk_score.ipynb` — Week 3: build the injury/workload risk score from
  player_injury_workload; decide and document your weighting logic.
- `04_recruitment_signal.ipynb` — Week 3–4: combine value forecast + risk
  score into the final recruitment signal table, export for Tableau.

Keep each notebook fully solved with markdown explanations above each cell,
per your usual preference for presenting to the cohort.
