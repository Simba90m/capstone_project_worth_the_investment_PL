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
**Not yet fixed (bigger, riskier change):** the cleaner fix is parsing
`from_date`/`until_date` to a real `DATE` type inside
`stg_transfermarkt_injuries.sql` itself (e.g. `try_strptime`), the same way
entry 1 fixed `"Days"` — that way every consumer gets clean dates, not just
this one notebook. Left as an open item below since it needs testing
against the real data via `dbt run`, which wasn't possible while drafting
this fix.

---

### 4 (follow-up). Interpreter mismatch — settled
While hitting entry 8's `scipy` install, confirmed via the traceback that
notebooks are actually running on the Miniconda interpreter
(`c:\Users\mahmo\miniconda3\...`), not `pythoncore-3.14-64`. `pip install -r
requirements.txt` should target that one going forward — this closes the
"worth doing a one-time check" note in entry 4.

---

## Open items
- `stg_transfermarkt_injuries.sql` still passes `from_date`/`until_date`
  through as raw text — see entry 8. Worth converting to real `DATE`
  columns via `try_strptime` once `dbt run` can be tested, so every
  consumer (not just one notebook) gets clean dates.
- `requirements.txt` lists `dbt-duckdb` + `duckdb` now (fixed from
  `dbt-postgres`) and `scipy` (added for the stakeholder-hypothesis
  notebooks) — confirm `pip install -r requirements.txt` under the
  Miniconda interpreter picks both up before the next `dbt run`.
