# Technical Architecture

## 1. System Overview

```
┌─────────────┐      ┌──────────────────────────┐      ┌────────────────┐
│  Frontend    │◄────►│   Flask App (backend/app) │◄────►│  SQLite/MySQL   │
│  Jinja2 +    │      │                            │      │  (db.py models) │
│  Chart.js    │      │  ┌──────────────────────┐  │      └────────────────┘
└─────────────┘      │  │  API Blueprints       │  │
                       │  │  auth/vehicles/weather│  │      ┌────────────────┐
                       │  │  predictions/trip/... │  │◄────►│ OpenWeatherMap  │
                       │  └──────────┬───────────┘  │      │ (external API)  │
                       │             │               │      └────────────────┘
                       │  ┌──────────▼───────────┐  │
                       │  │  ml/ module            │  │
                       │  │  physics.py            │  │
                       │  │  train.py              │  │
                       │  │  predict.py            │  │
                       │  │  xai.py                │  │
                       │  └──────────┬───────────┘  │
                       │             │               │
                       │  ┌──────────▼───────────┐  │
                       │  │  saved_models/         │  │
                       │  │  v<N>_<timestamp>/     │  │
                       │  └────────────────────────┘  │
                       └──────────────────────────────┘
```

## 2. The `ml/` Module (core of Phase 1)

### 2.1 `physics.py` — real-world-calibrated baseline

Reads `data/real_world_calibration/temperature_range_benchmarks.csv`
(real, cited published study data points — Geotab, Recurrent Auto, AAA,
DOE) and fits a **monotonic (isotonic) regression** through them to get
a temperature → % degradation curve.

**Why isotonic regression and not simple linear interpolation:**
different studies measured under different methodologies disagree with
each other at nearby temperatures (e.g. AAA's -7°C lab test with active
heating reads *worse* than Recurrent's -10°C real-world fleet average).
Connecting raw points with straight lines produces a curve where
degradation briefly gets *better* as it gets colder — not physically
meaningful. Isotonic regression finds the best-fitting curve that still
only worsens as temperature drops, which is the right shape constraint
for this relationship, and it reconciles disagreeing sources rather than
literally connecting them point to point.

**Why scope is capped at the ~21.5°C "sweet spot":** Geotab's data shows
EVs modestly *exceed* rated range in mild weather and lose range again in
heat, which is a real but separate phenomenon (heat degrades cooling
systems and battery chemistry differently than cold does). This project
is scoped to cold-weather degradation, so degradation is floored at 0%
above the sweet spot rather than modeling the heat side without
comparable citation coverage.

### 2.2 `train.py` — training pipeline

1. Generates a synthetic training dataset where the **temperature
   component** comes from `physics.py`'s real-calibrated curve, and
   **other operating conditions** (HVAC, wind, terrain, battery age,
   speed, precipitation, vehicle weight) are added as engineering
   estimates on top (see §4 for why these aren't also grounded in
   row-level real data).
2. `physics_baseline_degradation` is included as an explicit **input
   feature** to every model — this is what makes it "physics-informed
   ML" rather than "ML with synthetic data": the models are trained to
   *correct* a real-grounded starting point using the other conditions,
   not to learn the temperature relationship from nothing.
3. Splits data 70/15/15 into train/validation/held-out test, and runs
   5-fold cross-validation on the training split. All three sets of
   metrics (CV, validation, held-out test) are reported per model —
   not just a single train/test split like the original version.
4. Runs `run_calibration_check()`: takes the trained ensemble and scores
   it directly against the real benchmark CSV, using a fixed **neutral
   "typical commute" baseline** (`BASELINE_TRIP_CONDITIONS`) for every
   non-temperature feature, so the comparison isolates the temperature
   effect the field studies actually measured. This is the number that
   answers "how close is this model to reality," and it's computed
   against real external data, not the model's own synthetic test split.
5. Saves a **versioned** model bundle to
   `saved_models/v<N>_<timestamp>/`, with `metadata.json` recording the
   version, training timestamp, feature list, all metrics, the
   calibration report, and the physics anchor points used. A flat copy
   of the `.pkl` files is also written to `saved_models/` directly for
   backward compatibility with how `predict.py` loads models, and
   `current_version.json` points at the active version.

### 2.3 `predict.py` — inference

- Encodes categorical inputs, computes `physics_baseline_degradation`
  for the given temperature, and builds a **named** `pandas.DataFrame`
  row (not a raw numpy array — see `PROJECT_WORKFLOW.md` for why that
  matters) matching the training feature order.
- Runs every currently-available model and computes the **spread**
  (standard deviation) of their predictions for this specific input.
  Low spread → high confidence; high spread (e.g. an unusual combination
  like extreme cold + very high speed + mountainous terrain, where
  models trained on different algorithms tend to extrapolate
  differently) → lower confidence. This replaces the old hardcoded
  `confidence: 0.85`.
- Falls back to `_physics_prediction()` (physics baseline + a simple
  HVAC adjustment) if no trained model is available at all, e.g. a
  fresh clone before the first training run completes.

### 2.4 `xai.py` — explainability

- Rule-based, human-readable explanations (unchanged from v1's
  approach — these are legitimate expert-system-style rules, not a
  learned model, and are treated as such rather than mislabeled).
- SHAP-based feature importances when the `shap` package can build a
  `TreeExplainer` for the loaded model; falls back to the model's native
  `feature_importances_` otherwise.
- Now reuses `predict.py`'s shared `_build_feature_row()` helper instead
  of rebuilding the feature vector by hand, so SHAP always explains the
  same feature values the model was actually trained on.

## 3. Model Versioning & Conflict Resolution Strategy

- Each `python train.py` run creates a new `saved_models/v<N>_<UTC
  timestamp>/` directory — never overwrites a previous version's
  directory.
- `saved_models/current_version.json` is the single pointer to "what
  the app should currently be using" (`{"active_version": N,
  "active_dir": "..."}`).
- `predict.py` currently loads models from the flat `saved_models/*.pkl`
  layout (written alongside the versioned directory on every training
  run) rather than reading `current_version.json` directly. This is a
  known simplification — see `FEATURE_TICKET_LIST.md` ticket ML-4 for
  making `predict.py` version-aware (e.g. to support instant rollback
  to an older version without retraining). Until then, "rollback" means
  copying an older version's `.pkl` files back into the flat
  `saved_models/` directory.
- **Conflict resolution:** because training always writes a brand-new
  version directory and only the flat copy + pointer file are mutated,
  two admins triggering `/admin/retrain` around the same time cannot
  corrupt a version directory — the worst case is a race on which
  training run's flat copy "wins" as briefly active, which the next
  retrain (or an explicit rollback) resolves. There is currently no
  distributed lock around this — acceptable for the current
  single-process deployment target, revisit if horizontally scaled
  (see `SECURITY_AND_ACCESS.md` §5 for related known limitations).

## 4. Data Model

Unchanged from v1 for the web-app-facing tables (`User`, `EVVehicle`,
`Prediction`, `TripSimulation`, `Dataset`) — see
`backend/app/models/*.py` for the SQLAlchemy schema. Phase 1 did not
change the persisted schema; `Prediction.prediction_confidence` now
receives a *real* varying value instead of always `0.85`, and
`Prediction.shap_explanation` now reflects the physics-informed feature
set.

## 5. What Was Checked for Real Row-Level Data (and why it wasn't used)

Before building the physics-informed hybrid, the following were
evaluated as potential sources of real, row-level (per-trip) EV
cold-weather telemetry with the full feature set this project needs
(temperature + HVAC + terrain + speed + battery age simultaneously):

- **Vicomtech d-EVD dataset** — real EV trip data with weather, but
  requires a request form / access grant and is CC BY-NC-SA (non-
  commercial), and doesn't isolate cold-weather degradation specifically.
- **OpenEV Data** — real and directly downloadable (CDLA-Permissive-2.0,
  no login), but it's vehicle *specifications* (battery capacity, rated
  range), not trip-level telemetry with weather/degradation outcomes.
  Used as a candidate source for real vehicle specs (see README), not
  for the degradation model itself.
- **Geotab / Recurrent Auto / AAA / DOE** — real, aggregate, and freely
  citable, but published as *summary statistics* (temperature vs. %
  range retained), not row-level telemetry. This is what's actually
  used, via the isotonic calibration curve.
- **Kaggle EV datasets** — several exist but require an account/login to
  bulk-download, and none combine temperature + HVAC + terrain +
  measured range loss at the row level for a broad vehicle set.

**Conclusion:** the honest, buildable-today approach is what's
implemented — ground the one relationship for which real aggregate data
exists (temperature → degradation) directly in citations, and clearly
label the remaining operating-condition effects as engineering
estimates rather than pretend they're all equally "real." If a real
telemetry source becomes available (e.g. a research partnership, a
crowdsourced dataset per `FEATURE_TICKET_LIST.md`'s community-reports
ticket), it should replace the estimated portions first, since the
temperature curve is already grounded.
