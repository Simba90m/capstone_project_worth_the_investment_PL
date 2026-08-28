# Debugging Log

Running log of issues hit while setting up this project and how they were
resolved. Kept for two reasons: (1) faster fixes if the same thing recurs,
and (2) legitimate material for the capstone presentation — real-world data
projects always involve this kind of friction, and being able to speak to
it concretely is a stronger story than pretending everything just worked.

---

### 1. `kaggle: command not found` (Windows)
**Symptom:** `FileNotFoundError: [WinError 2] The system cannot find the
file specified` when running `subprocess.run(["kaggle", ...])`.
**Cause:** `kaggle.exe` wasn't reliably on PATH, even though the `kaggle`
package was installed via pip.
**Fix:** Call it as a Python module instead of a bare command:
`subprocess.run([sys.executable, "-m", "kaggle", ...])`. This guarantees
it uses the same Python environment the script is already running under.

---

### 2. `ImportError: Import lxml failed` (pandas.read_html)
**Symptom:** `pandas.read_html()` failed immediately with a missing-parser
error.
**Cause:** `read_html()` needs an HTML parser backend (`lxml` or
`html5lib`), which isn't a pandas dependency by default.
**Fix:** `pip install lxml`.

---

### 3. FBref returned `HTTP 403 Forbidden`
**Symptom:** Both a plain `urllib`-based request (via
`pandas.read_html(url)` directly) and a `requests` call with a spoofed
browser `User-Agent` header were blocked with 403.
**Cause:** FBref uses Cloudflare bot-protection that goes beyond checking
the User-Agent string — it does deeper request fingerprinting that simple
header spoofing doesn't bypass.
**Attempted fix:** `cloudscraper` (a library designed to solve Cloudflare's
challenge automatically).

---

### 4. `ModuleNotFoundError: No module named 'cloudscraper'`
**Symptom:** Install appeared to succeed, but the notebook still couldn't
import it.
**Cause:** Environment mismatch — this machine has both a Miniconda
install (`miniconda3`) and a separate `pythoncore-3.14-64` install, and a
package installed into one isn't visible to the other. This same root
cause likely explains issue #1 as well.
**Fix / ongoing risk:** Always confirm which interpreter is active first
(`import sys; print(sys.executable)`), then install with that exact
interpreter (`python -m pip install <package>`), or install directly from
inside the notebook cell (`!{sys.executable} -m pip install <package>`) to
remove any ambiguity. **Worth doing a one-time check of which environment
Jupyter/VS Code is actually using by default, to stop hitting this repeatedly.**

---

### 5. Manually saved FBref HTML page disappeared after download
**Symptom:** Saving the FBref page directly from the browser (as a
fallback to scripted scraping) resulted in the file being deleted shortly
after download.
**Likely cause:** Windows Defender / browser download-protection flagging
the saved HTML as suspicious (not confirmed, but consistent with the
symptom — worth checking Windows Defender's protection history / quarantine
if this needs revisiting).
**Resolution:** Abandoned the scraping approach entirely rather than keep
fighting Cloudflare + AV false positives. Switched to a pre-scraped Kaggle
mirror of the same FBref data instead:
`siddhrajthakor/fbref-premier-league-202425-player-stats-dataset`.
This is now the project's actual FBref data source — see README.

---

### 6. Player ID matching across sources — resolved cleanly
Not a bug, but worth logging as a design decision: checked whether
`player_id` in `davidcariboo/player-scores` and `irrazional/transfermarkt-
injuries` referred to the same players, by computing the ID set overlap
directly:

```python
values_ids = set(pd.read_csv('players.csv')['player_id'])
injury_ids = set(pd.read_csv('transfermarkt.csv')['player_id'])
overlap = values_ids & injury_ids
# Result: 18,824 / 18,825 = 100% overlap
```

**Conclusion:** both datasets use real, shared Transfermarkt internal
player IDs. These two sources join directly on `player_id` — no
name-matching needed between them. FBref (now Kaggle-sourced) still needs
name-based matching, since it has no shared ID scheme with Transfermarkt.
This simplified `player_key_map.sql` significantly from the original plan.

---

### 7. FBref source: reverted to the multi-season akshankrithick dataset
**Context:** Entry 5 above recorded switching to the single-season
`siddhrajthakor/fbref-premier-league-202425-player-stats-dataset` mirror as
the fix for FBref access. In practice the project ended up built against
the multi-season `akshankrithick/fbref-2017-2024-for-europes-top-5-leagues`
dataset instead (7 seasons, 2017-18 through 2023-24) — that's what's
actually sitting in `data/raw/fbref/` and what `stg_fbref_performance.sql`
is written against, and it's what `Project_brainstorm.md`'s data-sources
table always documented.
**Fix:** Updated `scripts/01_fetch_data.py` and
`dbt/models/staging/sources.yml`, which had been left pointing at the
single-season mirror, so a clean re-run of the fetch script now pulls the
dataset the pipeline actually expects.

---

### 8. `injuries.from_date` — `"-"` placeholder breaks naive date parsing
**Symptom:** `ValueError: time data "-" doesn't match format "%b %d, %Y"`
from `pd.to_datetime(injuries["from_date"])`, while building the "injury
recency vs. value decline" hypothesis notebook.
**Cause:** the raw Transfermarkt injuries data uses `"-"` as a placeholder
for an unknown/missing injury date, mixed in among real dates like
`"Jan 5, 2021"`. `stg_transfermarkt_injuries.sql` currently passes
`from_date`/`until_date` through as raw text (same as the `"Days"` column
before entry 1's fix), so this hits every consumer, not just this notebook.
**Fix (notebook-side, applied):** parse with
`pd.to_datetime(..., format="mixed", errors="coerce")`, then drop rows
where the result is `NaT`, printing how many were dropped so it's not a
silent data loss.
**Follow-up (applied, not yet tested):** `stg_transfermarkt_injuries.sql`
now parses `from_date`/`until_date` to a real `DATE` type at the source via
`try_strptime("from", '%b %d, %Y')::date`, the same way entry 1 fixed
`"Days"` — the `-` placeholder becomes a clean `NULL` instead of every
consumer needing its own text-parsing workaround. This also fixes a latent
bug in `player_injury_workload.sql`'s `max(from_date)` — with `from_date`
as TEXT, that `max()` was comparing dates *alphabetically* (e.g. "Feb"
sorts before "Jan"), so `most_recent_injury_date` could have been wrong
even for players with clean data. **Needs a `dbt run` to confirm it
compiles and to spot-check `most_recent_injury_date` before/after** — not
yet run, since this fix was made without a live dbt connection.

---

### 4 (follow-up, corrected). Interpreter mismatch — not actually settled
The earlier note here declared this "settled" based on one notebook run's
traceback showing the Miniconda interpreter. That was one data point, not
a fix -- wrong to call it closed. Real evidence: a *different* notebook
(`hypothesis_position_vs_injury_risk.ipynb`) hit `ModuleNotFoundError: No
module named 'scipy'` even though `pip install scipy` in the terminal
confirmed it was already installed under `miniconda3`. Checked
`sys.executable` from inside the notebook directly -- it printed
`pythoncore-3.14-64\python.exe`. So which interpreter a given notebook
actually runs on depends on whatever kernel VS Code happens to have
selected *for that specific notebook*, independent of what's active in the
terminal -- installing a package in the terminal doesn't help a notebook on
a different kernel, and a notebook that worked once doesn't mean the next
one will use the same kernel.

---

### 9. Real fix for the interpreter mismatch (entry 4/4-follow-up)
**Fix:** in VS Code, the kernel selector is per-notebook (top-right corner
of the notebook editor) -- explicitly select the `miniconda3` environment
for *every* notebook in this project, not just the one that happens to be
open. Confirm with `import sys; print(sys.executable)` in a fresh cell
after switching, expect a path containing `miniconda3`, then restart the
kernel before running anything else. Checked and fixed for
`hypothesis_injury_recency_vs_value.ipynb` and
`hypothesis_position_vs_injury_risk.ipynb`; **still needs checking** for
`01_exploration.ipynb` through `04_recruitment_signal.ipynb` and
`00a_fetch_kaggle_data.ipynb` -- don't assume they're fine just because
they ran successfully earlier in the project, per the lesson above.
**Confirmed working, this time for real:** after switching
`hypothesis_position_vs_injury_risk.ipynb` to the `miniconda3` kernel,
`dbt run` (via `python -m dbt.cli.main run`, entry 10) succeeded and the
full notebook ran end to end against the new columns -- see
`Project_brainstorm.md` for the result.

---

### 10. `dbt run` picked up dbt Cloud CLI instead of dbt Core
**Symptom:** `Encountered an error loading configuration: dbt_cloud.yml
credentials file for dbt Cloud not found.`
**Cause:** two different `dbt.exe` files exist under `miniconda3`
(`miniconda3\dbt.exe` and `miniconda3\Scripts\dbt.exe`) -- the first is a
dbt Cloud CLI install (unrelated to this project, which uses dbt Core +
DuckDB per `profiles.yml`), and it's earlier in PATH, so the bare `dbt`
command always resolves to the wrong one.
**Fix:** `python -m dbt.cli.main run` instead of `dbt run` -- bypasses
PATH entirely and uses the dbt Core package installed via
`pip install -r requirements.txt` in the active interpreter. Same
"call it as a module" pattern as entry 1's `kaggle` fix.
**Related, hit right after:** a Jupyter kernel with an open DuckDB
connection (from a notebook cell that errored before reaching
`con.close()`) blocked `dbt run` with `IO Error: Cannot open file ...
being used by another process` -- DuckDB only allows one process to touch
the file at a time. Fixed the underlying cause by switching both
hypothesis notebooks' connection-opening cells to `with duckdb.connect(...)
as con:` so the connection auto-closes even if a later line in the same
cell raises an error.

---

## Open items
- `stg_transfermarkt_injuries.sql`'s `from_date`/`until_date` fix (entry 8
  follow-up) needs a `dbt run` to confirm it actually compiles/works
  against the real data — not yet tested live.
- Per entry 9: confirm every notebook (not just the two hypothesis
  notebooks) is actually running on the `miniconda3` kernel, not
  `pythoncore-3.14-64` — specifically `00a_fetch_kaggle_data.ipynb` through
  `04_recruitment_signal.ipynb`, still unchecked.
- Decide whether the position/age hypothesis boxplots are worth adding as
  Tableau worksheets alongside the existing four.
