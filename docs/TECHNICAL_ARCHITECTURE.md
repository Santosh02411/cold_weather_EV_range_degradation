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

## 5. Phase 2 — Geo Services (`services/geo.py`)

Added to replace two manual-input gaps identified in Phase 1's roadmap:
the terrain dropdown (a guess) and single-point trip input (no real
route). Three free, keyless providers, each chosen and scoped
deliberately:

| Provider | Used for | Real-world constraint |
|---|---|---|
| Nominatim (OpenStreetMap) | Geocoding place names → lat/lon | ~1 req/sec public rate limit; requires a descriptive `User-Agent` header (set in `_HEADERS`) |
| OSRM public demo server | Driving route + geometry | Explicitly "light usage/evaluation" only — not for production traffic (ticket RT-4) |
| Open-Elevation | Elevation profile along the route | Free but can be slow under load; route coordinates are sampled down to ≤25 points before lookup to keep each request small |

**`classify_terrain_from_elevations()`** turns a raw elevation profile
into the same `flat` / `hilly` / `mountainous` category the ML model
already expects (see `train.py`/`predict.py`'s `terrain_type` feature),
using cumulative elevation gain normalized per 100 sampled points.
Thresholds (150m / 500m) are a documented judgment call for mapping a
continuous real measurement onto this project's existing 3-bucket
categorical feature — not derived from a formal grading-classification
standard — see `MEMORY.md` for the reasoning.

**New endpoint:** `POST /trip/api/route-predict` (in `trip.py`) chains
these together: geocode origin + destination → fetch real route →
derive real terrain from the route's actual elevation profile → fetch
real current weather at the origin → run the same `get_prediction()`
used everywhere else. It reuses `weather.py`'s `fetch_openweathermap`/
`get_demo_weather` functions directly rather than duplicating weather
logic, and falls back gracefully (not fatally) if elevation lookup
fails, labeling the terrain source as `'fallback'` in the response
rather than silently pretending it was measured.

**What this endpoint does NOT do yet** (see `FEATURE_TICKET_LIST.md`
RT-5): weather is only fetched at the origin, not sampled along the
route. For a short local trip this is a reasonable approximation; for
a long multi-region trip it isn't, and that limitation is surfaced in
the ticket list rather than left implicit.

**Verification status:** these three HTTP integrations were written
against each provider's documented API but could not be executed
against the live internet in the sandbox this was built in (no
outbound network access there — see `PROJECT_WORKFLOW.md`). The
terrain-classification *logic* itself (pure Python, no network) was
tested directly with synthetic elevation profiles. The network calls
themselves need a real run-through before shipping.

## 6. Phase 3 — AI Services (`services/llm.py`, `services/ai_features.py`)

This is where actual LLM involvement enters the project for the first
time — the original codebase branded itself "AI-powered" with zero
generative-model calls anywhere. Phase 3 adds real ones, scoped
deliberately narrow: **the LLM only ever phrases already-computed
facts; it never computes a number.**

### 6.1 `services/llm.py` — thin Anthropic Messages API wrapper

- Reads `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` from Flask config
  (`config.py`), defaulting to `claude-sonnet-5`.
- `call_claude(app_config, system_prompt, user_message, max_tokens)`
  returns `(text, error)` — never raises. Every caller in
  `ai_features.py` checks `error` and falls back to a template instead
  of surfacing a 500 to the user.
- `is_configured()` lets callers skip the network call entirely when no
  key is set, rather than attempting a call that would just fail.

### 6.2 `services/ai_features.py` — the three Phase 3 features

All three share `_facts_block()`, one function that renders a
prediction's already-computed numbers (temperature, degradation %,
predicted range, energy consumption, charging slowdown, confidence, and
the SHAP/rule-based contributing factors from `xai.py`) into a single
text block. Every prompt embeds this same block, with an explicit,
repeated instruction (`GROUNDING_RULES`): never invent, adjust, or
recompute a number that isn't in the block; if asked about something
the block doesn't cover, say so rather than guess. This is the
"RAG-style, not free generation" grounding requested for this phase —
the "retrieval" step is simply this app's own already-correct ML
pipeline output, not a vector search, since the relevant facts are
already fully known and structured by the time the LLM is called.

**AI-1 (`generate_trip_briefing`):** 3-5 sentence natural-language
summary. Falls back to a template built from `xai.py`'s existing
rule-based `summary` field, not a from-scratch fallback string.

**AI-2 (`answer_question`):** free-form Q&A scoped to one saved
prediction's facts. The system prompt explicitly tells the model to
redirect off-topic questions back to the prediction rather than answer
from general knowledge or follow instructions embedded in the driver's
question that would override the grounding rules (basic prompt-
injection awareness, not a hardened defense — see `SECURITY_AND_ACCESS.md`
§7 for what "hardened" would still require).

**AI-3 (`detect_anomaly` + `narrate_anomaly`):** deliberately split into
two functions on purpose. `detect_anomaly()` is pure arithmetic —
compares the actual prediction against `physics.py`'s real-world-
calibrated baseline for that temperature (from Phase 1) and flags a gap
over 20 percentage points. **The LLM is never involved in deciding
whether something is anomalous** — only `narrate_anomaly()`, called
afterward and only when `detect_anomaly()` already flagged something,
turns that real computation into a sentence. This split matters: an
LLM asked "is this anomalous?" would be making a judgment call with no
real grounding of its own, which is exactly the kind of ungrounded
"looks like AI, isn't really" pattern this whole project has been
correcting since Phase 1.

### 6.3 New endpoints (`api/predictions.py`)

- `GET /predictions/api/<id>/briefing`
- `POST /predictions/api/<id>/ask` (body: `{"question": "..."}`)
- `GET /predictions/api/<id>/anomaly`

All three are ownership-checked (`_load_owned_prediction` — a
prediction only returns data to the user who created it, matching the
existing `/api/history` rule) and operate on a **saved** `Prediction`
row's stored facts, not a fresh recomputation — so a briefing always
describes the exact prediction the user is looking at, not a
potentially-different one from re-running the model.

`POST /predictions/api/predict` (the main prediction endpoint) now also
returns an `anomaly` field on every response, computed automatically —
the frontend surfaces a warning badge with an "Explain why" button when
`anomaly.is_anomaly` is true (see `frontend/static/js/main.js`).

### 6.4 Verification status

Same limitation as Phase 2's `geo.py`: `llm.py`'s actual HTTP call to
`api.anthropic.com` was written against the documented Messages API
shape but could not be executed in this sandbox (no outbound network).
**What was verified:** the full fallback path (`is_configured() ==
False` → template generation) for all three features, end-to-end,
including the real `detect_anomaly()` arithmetic against real feature
inputs (see `PROJECT_WORKFLOW.md` for the exact test cases run — one
that correctly did NOT flag as anomalous, one that correctly did).
**What wasn't verified:** an actual round-trip to Claude with a real API
key. Test this before enabling Phase 3 in any deployment with a real
key configured.

## 7. What Was Checked for Real Row-Level Data (and why it wasn't used)

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
