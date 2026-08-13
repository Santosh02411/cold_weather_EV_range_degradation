# Project Workflow — Build Log

This is a real log of how Phase 1 was actually built and debugged, not a
retrospective summary written after the fact. Each entry below reflects
something that was actually run and actually failed (or nearly did)
during development. Bugs are logged even when they were caught before
ever reaching a user, because "how was it caught" is often as useful as
"what was wrong."

**Scope note:** Phase 1 touched the `backend/app/ml/` module and the
real-data/documentation layer around it. It did not touch the API
blueprints, weather integration, or frontend, so this log doesn't
contain CORS or timezone-style bugs — those are more likely to surface
in Phase 2 (real-time weather/route integration) and will be logged
here when that work happens, not invented for this entry.

---

## Step 1 — Establish a real calibration source

**Goal:** stop the temperature→degradation relationship from being
arbitrary hand-picked thresholds.

Searched for row-level public EV cold-weather telemetry first (see
`TECHNICAL_ARCHITECTURE.md` §5 for the full list of what was checked —
Vicomtech d-EVD, OpenEV Data, Kaggle sets). None combine temperature +
HVAC + terrain + measured degradation at the row level without either a
non-commercial license, a manual access-request form, or a login-gated
bulk download that isn't automatable from this environment. Fell back to
what *is* real and freely citable: aggregate published field studies
(Geotab, Recurrent Auto, AAA, DOE). Compiled these into
`data/real_world_calibration/temperature_range_benchmarks.csv` with a
source and URL on every row.

## Step 2 — Build the physics baseline curve (`physics.py`)

First implementation: load the CSV, filter out the best/worst-performer
and heat-pump/resistive-heater split rows (since they're not part of a
single "average" curve), then `np.interp()` straight through the
remaining points.

**Bug #1 — non-monotonic curve from duplicate -7°C points.**
Ran a manual spot-check (`physics_baseline_degradation_pct(t)` for
`t` from -25 to 35) and got:
```
-10  25.0
-7   12.0     <- degradation *dropped* going from -10C to -7C
0    22.0
5    11.0     <- dropped again
```
Root cause: the AAA source contributes two rows for the same -7°C point
("with climate control" and "temperature alone, no cabin heating") —
`np.interp` needs strictly increasing x-values, and having two different
y-values at the same x point produced an interpolation order artifact
that made the curve wobble instead of smoothly worsening in the cold.

**Fix (first pass):** excluded the "temperature alone" AAA row (every
other row in the curve implicitly includes normal HVAC use, so keeping
only the "with heater" AAA row is the fair comparison) and added a
de-duplication step that averages any remaining rows sharing the same
temperature before building the curve, so `np.interp` always receives a
strictly increasing sequence.

**Bug #2 — still non-monotonic, different cause.**
Re-ran the same spot-check after the fix above:
```
-10  25.0
-7   40.0     <- WORSE at -7C than at -10C
0    22.0
```
This wasn't a duplicate-point bug anymore — it's that AAA's -7°C lab
test (`40% degradation with heater`) and Recurrent's -10°C real-world
fleet average (`25% degradation`) are two *different, real* studies that
genuinely disagree, because they measured under different conditions
(controlled lab test vs. real-world fleet driving). Straight-line
interpolation has no way to represent "two real sources disagree here"
except by literally reproducing the disagreement as a physically
nonsensical dip.

**Fix (second pass):** replaced raw interpolation with
`sklearn.isotonic.IsotonicRegression(increasing=False)`, fit on the
cold-side anchor points only (temperature ≤ the ~21.5°C sweet spot
Geotab identifies). Isotonic regression finds the best monotonic fit
through the points — it doesn't discard AAA's or Recurrent's data, it
reconciles them into a single curve that's still guaranteed to only get
worse as temperature drops. Re-checked:
```
-25  50.0
-15  46.0
-10  32.5
-7   32.5
0    22.0
5    11.0
10    0.0
```
Monotonic, and every value still traceable to the source data (not
independently invented).

## Step 3 — Wire the physics baseline into training (`train.py`)

Added `physics_baseline_degradation` as an explicit input feature, ran
`python train.py` for the first time end-to-end. It completed without
crashing (CV MAE ~1.7–2.7 across models, R² ~0.97–0.99 on synthetic
held-out data) — but the real signal that mattered was the new
real-world calibration check.

**Bug #3 — calibration check off by ~22 percentage points.**
First run of `run_calibration_check()` reported
`mae_vs_real_world_benchmarks_pct: 22.13`. Inspected the per-point
detail output and found the model was predicting **~17-19% degradation
even at temperatures where the physics baseline itself was 0%**
(10°C, 21.5°C, 30°C — all should be ~0% real-world degradation).

Diagnosis: the calibration check built its "typical trip" comparison row
from `X_train.median()` — but the synthetic training data samples
`terrain_type`, `battery_age_years`, `hvac_usage`, `wind_speed_kmh`, and
`vehicle_weight_kg` from wide uniform/near-uniform distributions, so
their *medians* skewed toward a harsher-than-typical combination
(HVAC on, ~5-year-old battery, above-average wind, above-average
weight) rather than an "ordinary commute." Those effects stacked
additively on top of the physics baseline, so even a 0% baseline showed
up as ~17-19% total — the model was correct given the (wrong) input, but
the *comparison methodology* wasn't isolating what the field studies
actually measured.

**Fix:** replaced the "use training medians" approach with a fixed,
explicit `BASELINE_TRIP_CONDITIONS` dict representing a genuinely
ordinary commute (flat terrain, light wind, ~1-year-old battery, normal
speed, no precipitation, heater on since that matches how the field
studies were actually collected). Re-ran: `mae_vs_real_world_benchmarks_pct`
dropped to `11.98`. The remaining ~12pp is consistent with — and now
attributable to — genuine disagreement between the source studies
themselves (e.g. the AAA vs. Recurrent difference from Step 2), not a
methodology artifact. This distinction (irreducible source disagreement
vs. our own bug) is exactly why the calibration report keeps full
per-point detail in `metadata.json` instead of only the summary number —
so this kind of root-causing stays possible later.

## Step 4 — Wire the physics baseline into prediction (`predict.py`)

Rewrote `get_prediction()` to compute `physics_baseline_degradation` per
request and pass all four models' predictions through a new
`_ensemble_confidence()` function.

**Near-miss #1 — renamed function reference.**
`train.py`'s `get_models_dir()` was renamed to `get_models_root()` as
part of the versioning rework. Before wiring `predict.py`, ran
`grep -rn "get_models_dir"` across the whole `backend/app` tree first
(not just the two files being edited) and found `predict.py` importing
the old name directly, plus `xai.py` re-importing names from
`predict.py`. Kept a `get_models_dir = get_models_root` alias in
`predict.py` rather than silently breaking any other caller (in-repo or
external script) that might still reference the old name. Caught by
proactive grep before ever running the code — logged here because the
"did I check every caller" step is easy to skip and is exactly how this
class of bug ships.

**Bug #4 — sklearn feature-name mismatch warning on every prediction.**
First end-to-end test of `get_prediction()` produced:
```
UserWarning: X does not have valid feature names, but LinearRegression
was fitted with feature names
```
on every model, every call. Root cause: `train.py` fits models on a
`pandas.DataFrame` (which carries column names), but `predict.py` was
building `X` as a raw `numpy.array([[...]])` for inference. Functionally
harmless in the installed scikit-learn version (predictions were still
correct), but it's a warning-per-request that would spam production
logs and is a real risk in a future sklearn version where this becomes
a hard error instead of a warning.

**Fix:** build the prediction row as a `pandas.DataFrame` with the exact
same `FEATURE_COLS` order used in training. Re-ran the same test with
`warnings.simplefilter('error')` (turns every warning into a hard
failure) across three scenarios (extreme cold + high speed +
mountainous, mild/no-HVAC, and a max-stress -30°C case) — all three
passed with zero warnings raised.

## Step 5 — Audit downstream consumers of the `ml/` module

Before considering Phase 1 done, ran a repo-wide grep for every consumer
of `train.py`/`predict.py` internals (`get_models_dir`, `FEATURE_COLS`,
`from ..ml.predict import ...`, `from ..ml.train import ...`) rather
than assuming the two rewritten files were the only ones that mattered.

**Bug #5 (caught by audit, not by running code) — `xai.py` would have
silently zeroed the new feature.**
`xai.py` imports `FEATURE_COLS` and independently rebuilds `X` with
`np.array([[processed.get(col, 0) for col in FEATURE_COLS]])` for its
SHAP explainer. Since `processed` (built locally in `xai.py`) never
computed `physics_baseline_degradation`, that `.get(col, 0)` would have
silently defaulted it to `0` for every SHAP call — meaning SHAP would
explain a model input that doesn't match what the model actually
receives at prediction time via `predict.py`. This wouldn't have thrown
an error; it would have quietly produced misleading feature-importance
explanations, which is a worse failure mode than a crash because
nothing would have flagged it.

**Fix:** exported `_build_feature_row()` from `predict.py` and had
`xai.py` call it directly instead of re-deriving the feature row by
hand, so the two code paths can't drift apart again by construction.

**Also checked:** `backend/app/api/admin.py`'s `/admin/retrain` route
calls `train_all_models()` and does `jsonify(results)` on the return
value. `train_all_models()`'s return shape changed from a flat
`{model_name: metrics}` dict to a richer metadata dict (version, all
metrics, calibration report) — this is backward-*compatible* for that
route (still valid JSON, just more informative), so no code change was
needed there, but it's noted here because a return-shape change is
exactly the kind of thing that's easy to miss if you only test the file
you edited.

## What Wasn't Tested (documented rather than glossed over)

- **The full Flask app was not run end-to-end in this environment** —
  `flask-sqlalchemy` and related packages aren't available in the
  sandbox this was built in (no package-installation network access).
  `physics.py`, `train.py`, and `predict.py` were tested directly
  (bypassing the Flask app factory's package `__init__.py`, which
  imports Flask extensions at import time) via `importlib` module
  loading. **Before merging, run `pip install -r requirements.txt` and
  `python run.py` locally, then exercise the `/predictions` endpoint
  through the actual UI** — that full-stack pass has not happened yet
  and is the single most important remaining verification step.
- **XGBoost-specific behavior** — `xgboost` isn't installed in the
  sandbox either, so the `HAS_XGBOOST` fallback path was exercised
  (training/prediction with 3 models instead of 4), but the actual
  XGBoost code path itself was not run. It's a well-established library
  and the code path is a straightforward `model.fit()`/`model.predict()`
  call identical in shape to the other three models, so risk is judged
  low, but it genuinely wasn't executed here.

---

# Phase 2 — Real-Time & Data-Source Accuracy

## Step 1 — Weather fallback visibility (ARCH-2)

Straightforward: `get_demo_weather()` and `fetch_openweathermap()` now
both set an explicit `data_source` field (`'live'` or `'demo_fallback'`)
instead of only a `note` string that the UI never rendered. Added a
visible badge in `main.js`'s `fetchWeather()`. No bugs surfaced here —
flagged specifically because "no bugs" is worth stating plainly rather
than manufacturing drama for a simple, low-risk change.

## Step 2 — Real elevation/terrain (RT-1) and route prediction (RT-2)

Built `services/geo.py` around three keyless providers (Nominatim, OSRM
demo server, Open-Elevation — see `TECHNICAL_ARCHITECTURE.md` §5 for
why each was chosen and their real usage limits).

**Constraint hit immediately: no outbound network in this sandbox.**
Unlike Phase 1 (where `physics.py`/`train.py`/`predict.py` are pure
computation and could be fully exercised locally), `geo.py`'s entire
job is making HTTP calls to external services — `requests.get()` to
`nominatim.openstreetmap.org`, `router.project-osrm.org`, and
`api.open-elevation.com` all fail here with no network path out of the
container. This is a hard capability boundary, not a bug to fix.

**What was actually verified vs. not**, stated plainly rather than
glossed over:
- `classify_terrain_from_elevations()` and `_sample_coordinates()` are
  pure Python with no network dependency — tested directly with
  synthetic elevation profiles (flat/hilly/mountainous cases, plus
  empty-list and single-point edge cases). All behaved correctly,
  including the two edge cases returning `('flat', 0.0)` instead of
  crashing on a division by zero (`span_points` could be 0 for a
  single-point list — guarded explicitly rather than relying on Python
  not raising, since `0/0` would raise `ZeroDivisionError` for a plain
  `/`, not silently return something wrong).
- `geocode_place()`, `get_route()`, `get_elevation_profile()`, and the
  new `/trip/api/route-predict` endpoint that chains them together are
  syntax-checked (`py_compile`) and code-reviewed against each
  provider's documented request/response shape, but **not** run against
  the live APIs. This is the single most important thing to verify
  before this ships — see the note at the top of `geo.py` and the
  README's Phase 2 section.

**Design decision made because of this constraint:** `route_predict()`
fails loudly (returns an HTTP error) if geocoding or routing fails, but
fails *softly* (falls back to a manual/default terrain value, and says
so in the response via `terrain_source`) if only the elevation lookup
fails. Reasoning: a missing route or unresolvable place name means the
core request can't be fulfilled at all, but a missing elevation profile
just means one input feature reverts to an estimate — better to still
return a prediction with a labeled caveat than to fail the whole
request over a secondary enrichment. This mirrors the "fail loud vs.
fail soft, and always say which one happened" pattern already
established in `predict.py`'s physics fallback from Phase 1.

## Step 3 — Vehicle spec verification (DATA-1)

Attempted a full bulk sync against OpenEV Data's live API first — same
network constraint as Step 2 blocked it. Wrote `scripts/sync_openev_data.py`
against OpenEV Data's documented API shape, ready to run in a normal
network environment, but explicitly labeled as unverified in its own
docstring rather than presented as working.

As a partial, actually-completed alternative: used web search (available
in this environment, unlike arbitrary `requests` calls from the sandboxed
code execution tool) to manually verify two vehicle entries against real
cited sources.

**Real correction found — Tesla Model 3 Long Range:** original seed data
listed 82 kWh / 580 km / 1830 kg. Cross-referenced against
evspecifications.com's 2024 Tesla Model 3 Long Range AWD listing (82.1
kWh, 1851 kg curb weight) and KBB's reporting on Tesla's EPA-rated range
history for this configuration (342 mi ≈ 550 km, following a 358 mi
rating for an earlier configuration). Updated to 82.1 kWh / 550 km /
1851 kg, and recalculated `energy_consumption_wh_km` to stay consistent
with the corrected capacity/range ratio (149 Wh/km) rather than leaving
the old derived value in place next to new inputs.

**Real correction found — Hyundai IONIQ 5 Long Range:** original seed
data listed 507 km range. Consumer Reports' 2024 Ioniq 5 Road Test
Report states the EPA-rated range is 303 miles (≈488 km) for the
single-motor RWD configuration with the 77.4 kWh battery — corroborated
by TopSpeed and a dealer spec page. Updated to 488 km, again
recalculating `energy_consumption_wh_km` (159 Wh/km) to match.

**What wasn't done:** the other 9 vehicles in `VEHICLES` were not
individually re-verified — doing that properly for every entry would
mean a dedicated search per vehicle trim, which wasn't proportionate to
do by hand within this phase. Rather than silently leave the impression
that "the vehicle list was fixed," `seed_data.py` now has an explicit
comment stating which entries were checked and which weren't, and
`scripts/sync_openev_data.py` exists specifically so the remaining
entries can be bulk-verified for real once run somewhere with network
access, instead of hand-checked one at a time indefinitely.

## What Wasn't Tested — Phase 2 addendum

- **All three live HTTP integrations in `geo.py`** (geocoding, routing,
  elevation) — code-reviewed against documented API shapes, not
  executed. **This is the top item to verify before relying on
  `/trip/api/route-predict` in production.**
- **`scripts/sync_openev_data.py`** — written against OpenEV Data's
  documented API, not executed.
- **The full Flask app, including the new `/trip/api/route-predict`
  route** — same underlying limitation carried over from Phase 1 (no
  `flask-sqlalchemy` installed in this sandbox, no network for the
  route's external calls either way). Run `pip install -r
  requirements.txt && python run.py`, then exercise both `/trip`'s
  existing manual simulator and the new route-based predictor through
  the actual UI before considering Phase 2 done.

---

# Phase 3 — AI/GenAI Layer

## Step 1 — Decide what the LLM is and isn't allowed to do

Before writing any code: the original project's core flaw (established
back in Phase 1) was presenting ungrounded output as more solid than it
was. Adding an LLM without a hard constraint would risk reintroducing
exactly that problem in a new form — a fluent paragraph that quietly
gets a number wrong is arguably worse than a fake `confidence: 0.85`,
because it *reads* more convincing. So the very first thing written was
`GROUNDING_RULES` in `ai_features.py` — the LLM only ever phrases
numbers this app already computed, never generates or adjusts one. This
constraint shaped every function that came after it, and is checked
here first because it's the thing most worth getting right before any
code review of the rest.

## Step 2 — `services/llm.py`

Thin wrapper around the Anthropic Messages API. Modeled directly on
`services/geo.py`'s pattern from Phase 2 (return `(result, error)`
tuples, never raise to the caller) for consistency across the two
external-API service modules.

**Constraint hit immediately, same as Phase 2:** no outbound network in
this sandbox, so `call_claude()`'s actual HTTP call to
`api.anthropic.com` could not be executed here. Written against the
documented Messages API request/response shape (`system` + `messages`
fields, `content` array of blocks with `type: 'text'`).

## Step 3 — `services/ai_features.py`

Built `_facts_block()` first (the shared grounding data every prompt
uses), then the three features on top of it.

**Tested what could actually be tested without network access** — the
full fallback (no-API-key) path for all three functions, using the same
`importlib`-based module loading pattern established in Phase 1 to
bypass the Flask app factory's package-level imports:

```
BRIEFING (template):
In today's conditions (-18°C), your Tesla Model 3 Long Range is predicted
to lose about 64.8% of its rated range, giving roughly 112.6 km of usable
range. Range decreased because of Extreme Cold Temperature, Cabin Heater
Active, and Snow Conditions. (Generated from the prediction model
directly — set ANTHROPIC_API_KEY for a more natural-language briefing.)
```

This confirmed the template fallback actually reuses `xai.py`'s real
`summary` field rather than a disconnected hardcoded string, and that
the whole call chain (predict → explain → brief) works end to end
without a network dependency.

**Anomaly threshold — first test case revealed a design gap, not a bug.**
Tested `detect_anomaly()` against an intentionally extreme scenario
(-25°C, 135 km/h, mountainous terrain, 9-year-old battery) expecting it
to trigger. It didn't:
```
ANOMALY: {'is_anomaly': False, 'physics_baseline_pct': 50.0,
          'predicted_pct': 65.0, 'deviation_pct': 15.0, ...}
```
Root cause (not a bug — a real property of the system): both the
physics baseline (`physics.py`) and the ML prediction (`predict.py`)
cap degradation at 65%, and at -25°C the baseline is already 50%. Two
values both near their respective ceilings can't diverge by more than
15 points no matter how extreme the other inputs get — the caps
themselves limit the deviation. Re-tested with a *mild* temperature (5°C,
where the physics baseline is naturally low) but the same extreme
speed/terrain/battery-age stress:
```
ANOMALY: {'is_anomaly': True, 'physics_baseline_pct': 11.0,
          'predicted_pct': 45.2, 'deviation_pct': 34.2,
          'direction': 'worse_than_expected'}
```
This confirmed the detector works as intended — it's just that "extreme
cold" isn't the scenario that produces large deviations, because
extreme cold is exactly where the physics baseline is already high.
Anomalies show up when the *other* factors (speed, terrain, battery
age) do a lot of work relative to what temperature alone would predict
— which is arguably the more useful case to catch anyway (a mild-weather
trip that's unexpectedly bad is more actionable to flag than "it's very
cold and also very bad," which the driver already expects). No code
change was needed here — logged because the first test result looked
like a bug and understanding *why* it wasn't one is worth recording so
it isn't re-litigated later.

## Step 4 — Wiring into `api/predictions.py` and the frontend

Added three new ownership-checked endpoints (briefing/ask/anomaly) plus
an `anomaly` field on the main `/api/predict` response. Added a
`_load_owned_prediction()` helper rather than repeating the ownership
check three times, after noticing the copy-paste risk while writing the
second endpoint (same "check every caller" discipline from Phase 1's
Step 5 audit, applied proactively this time instead of after the fact).

Wired a briefing button, a Q&A input, and an anomaly warning badge into
`main.js`'s `displayPredictionResult()`. Checked with `node --check`
(available in this sandbox, unlike a live browser) to catch syntax
errors — confirmed clean, but this is not the same as testing the DOM
interaction/rendering in an actual browser, which wasn't possible here.

## Step 5 — RT-5, segment-by-segment weather (queued from Phase 2)

Upgraded `/trip/api/route-predict` from single-origin-point weather to
sampling both origin and destination, using whichever is colder for the
actual prediction (a deliberate worst-case choice — see `MEMORY.md`).
Full multi-waypoint sampling for long routes was scoped out as ticket
RT-6 rather than attempted here, because it has a real cost/rate-limit
tradeoff against the free OpenWeatherMap tier this app defaults to that
deserves its own decision, not a default assumption bundled into this
change.

## What Wasn't Tested — Phase 3 addendum

- **The actual Anthropic API call in `llm.py`** — written against the
  documented Messages API, not executed. This is the single most
  important thing to verify (with a real `ANTHROPIC_API_KEY`) before
  relying on the LLM-generated (non-template) versions of any Phase 3
  feature.
- **Frontend rendering in an actual browser** — JS syntax-checked via
  `node --check`, but the briefing button / Q&A box / anomaly badge UI
  was not visually verified in a browser DOM.
- **The full Flask app** — same standing limitation from Phases 1-2.

---

# Post-Delivery Fixes

This section logs real problems reported after a phase was delivered —
the actual "run it for real" verification step flagged as outstanding
in every phase above, happening as it happens, not retroactively
smoothed over.

## Fix 1 — `pip install -r requirements.txt` failed on Python 3.13 / Windows

**Reported:** user ran `pip install -r requirements.txt` on Windows with
Python 3.13 and got a hard failure trying to build `scikit-learn==1.5.1`
from source (`Cython requires python3 dependency for link testing, but
it could not be found`, via a Meson build using an old MinGW gcc 6.3.0
toolchain).

**Root cause:** `requirements.txt` pinned exact versions
(`scikit-learn==1.5.1`, `numpy==1.26.4`, `scipy==1.14.0`,
`pandas==2.2.2`) that all predate their projects publishing prebuilt
Windows wheels for Python 3.13:
- scikit-learn added Python 3.13 wheel support in 1.6.0 (1.5.x only
  supports up to Python 3.12)
- numpy added Python 3.13 wheels in 2.1.1
- pandas added Python 3.13 wheels in 2.2.3
- scipy added Python 3.13 wheels around 1.14.1

With no matching wheel for their Python version, pip fell back to
building scikit-learn from source, which requires a full C/C++/Fortran
toolchain plus Cython and Meson — not something a typical Windows
Python install has configured, hence the failure. This wasn't caught in
Phases 1-3 because none of those phases could install packages in the
sandbox they were built in (no outbound network for `pip install`
either) — this is precisely the gap flagged repeatedly across "What
Wasn't Tested" sections, now materialized as a real report.

**Fix:** relaxed the scientific/ML stack in `requirements.txt` from
exact pins to `>=` minimums that do have Python 3.13 wheels
(`scikit-learn>=1.6.0`, `numpy>=2.1.1`, `pandas>=2.2.3`,
`scipy>=1.14.1`, plus `xgboost`, `shap`, `matplotlib`, `Pillow` bumped
the same way for consistency) — reasoned about via public release notes
research rather than guessed, since getting a wheel-availability claim
wrong here would just produce the same failure again. Pure-Python /
low-risk packages (Flask family, WTForms, etc.) were left as exact
pins, since they're not the ones that fail to build from source.

**What to verify next:** this fix is reasoned from public version-support
information, not confirmed by actually running `pip install` on Windows
Python 3.13 in this sandbox (still no outbound network here). If it
still fails, the most robust fallback is installing Python 3.11 or 3.12
instead (both have full, long-standing wheel coverage for this entire
stack) rather than continuing to chase Python 3.13 compatibility.

**Outcome:** confirmed fixed — user re-ran `pip install -r
requirements.txt` and it installed cleanly, pulling prebuilt wheels
(scikit-learn 1.7.1, numpy 2.1.3, pandas 2.3.1, scipy 1.16.1, etc.) as
intended. One unrelated dependency-conflict warning appeared
(`llama-index-core` wanting a different `tqdm` version) — that's from
an unrelated package already in the user's global environment, not from
this project, and not a blocker.

## Fix 2 — `python run.py` crashed on startup: `ImportError: cannot import name 'get_models_dir'`

**Reported:** immediately after the successful `pip install`, running
`python run.py` failed with
`ImportError: cannot import name 'get_models_dir' from 'app.ml.train'`.

**Root cause — a real gap in Phase 1's own audit process.** Phase 1's
Step 5 (see above) explicitly grepped for every caller of the renamed
`get_models_dir` → `get_models_root` function specifically to avoid
this exact failure mode, and found/fixed `predict.py` and `xai.py`. That
grep was scoped to `backend/app` — but `run.py` lives in `backend/`,
one level above `backend/app`, so it was silently outside the search
scope and never checked. `run.py` imports `get_models_dir` directly
from `app.ml.train` (not through `predict.py`, where a backward-compat
alias *was* added), so it hit the rename directly.

This is worth being direct about: the Phase 1 doc explicitly framed
that audit step as "the discipline of checking every caller, not just
the files you edited" — and then the audit itself had a scope gap that
produced exactly the failure it was meant to prevent. Logged plainly
rather than glossed over, because the lesson here isn't "don't make
mistakes," it's "grep the whole repo, not the directory that feels
relevant."

**Second issue found in the same file while fixing the first:** even
after fixing the import, `run.py`'s first-run training block would have
crashed anyway — it iterated `train_all_models()`'s return value as
`results[name]['r2_score']` / `results[name]['mae']`, which was the
*old* (pre-Phase-1) flat return shape. Phase 1 changed
`train_all_models()` to return a richer metadata dict
(`meta['metrics'][name]['validation_set']['r2_score']`, etc. — see
`TECHNICAL_ARCHITECTURE.md` §2.2). `admin.py`'s `/admin/retrain` route
was checked against this shape change back in Phase 1 (it just does
`jsonify(results)`, which doesn't break on a different shape) — but
`run.py`'s console-print loop, which *does* index into specific keys,
was not checked, for the same reason as the import: it's outside
`backend/app`.

**Fix:** updated `run.py` to import `get_models_root` (no alias
needed — fixed at the source instead of patching around it again) and
to read the new nested metrics structure, including printing the
real-world calibration MAE alongside the per-model validation metrics
so the first-run console output actually shows the number that matters
most (see Phase 1's `PROJECT_REQUIREMENTS.md` success criteria).

**Re-audited the whole repository, not just `backend/app`, this time** —
searched every `.py` file for `get_models_dir`, every caller of
`train_all_models()`, every use of `FEATURE_COLS`, and every place
indexing `['r2_score']`/`['mae']` directly. Confirmed `admin.py` was
already fine (Phase 1), `predict.py`/`xai.py` were already fine (Phase
1), and `run.py` was the only remaining gap — now fixed. No other
scope-gap callers found.

**Verified:** re-ran `run.py`'s exact (now-fixed) first-run training
logic end-to-end in this sandbox (via the same `importlib`-bypass
technique used throughout Phases 1-3, since the Flask app factory still
can't run here) and confirmed it trains and prints correctly:
```
[ROBOT] Training ML models for the first time...
  linear_regression: R2=0.9681, MAE=2.9432
  random_forest: R2=0.9827, MAE=2.051
  gradient_boosting: R2=0.9873, MAE=1.8307
  Real-world calibration MAE (vs 13 published benchmarks): 11.98 pp
[OK] ML models trained and saved!
```
This confirms the training logic itself; it does not confirm the
subsequent `app.run(...)` / Flask server startup, which still hasn't
been exercised for real. That remains the next real risk if something
else was missed the same way.

## Fix 3 — Phase 2/3 backend features existed but weren't reachable from the UI

**Reported:** user got the app running successfully and asked directly
why none of the new features seemed to show up.

**Root cause:** a real gap, not a misunderstanding — `/trip/api/route-predict`
(real geocoding, real route, real elevation-derived terrain, real
weather; built and tested at the API level in Phase 2) was never wired
to `trip/simulate.html`. The form still called the old
`/trip/api/simulate` endpoint with manually-typed distance and
temperature, exactly as it did before Phase 2. This shipped without
being caught because every verification step in Phases 2-3 tested the
*API layer* directly (via `importlib`-bypassed Python, `py_compile`,
`node --check` on the JS in isolation) — nothing in this sandbox could
click through the actual rendered pages, so "is this endpoint called
from anywhere in the UI" was never actually checked as its own
question. Every other Phase 3 addition (weather badge, AI briefing/ask,
anomaly badge) happened to get wired into an *existing* result-rendering
function while building it, so those were reachable; route-predict was
Phase 2's only *new* endpoint needing *new* UI, and that step was
missed.

**Fix:** `trip/simulate.html` now has a "Use real route, terrain &
weather" checkbox (checked by default). When checked, the manual
distance/temperature fields hide and `submitTrip()` calls
`/trip/api/route-predict`; the result panel shows the real distance,
terrain source, and weather source it got back. Unchecked falls back to
the original manual `/trip/api/simulate` flow, preserved rather than
removed, in case someone wants to enter an already-known distance and
skip the geocoding/routing calls.

**Re-audited for the same gap elsewhere:** grepped `frontend/` for
`route-predict`, `briefing`, `/ask`, `anomaly`, and `data_source` to
confirm every other Phase 2/3 endpoint is actually called from
somewhere in the UI. All four were already wired (briefing/ask/anomaly
into `predictions/index.html`'s result rendering, `data_source` into
both the weather page and the now-fixed trip page). `route-predict` was
the only orphaned one.

**What this means going forward:** "the code runs and returns the right
JSON" and "a user can actually reach this feature by clicking through
the app" are different claims, and this sandbox can only verify the
first one. Every future phase should end with an explicit "grep the
frontend for every new endpoint path" check, the same way Phase 1
established "grep every caller of a renamed function" — logged here as
a standing practice, not just a one-off fix.
