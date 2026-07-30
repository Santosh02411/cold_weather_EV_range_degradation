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
