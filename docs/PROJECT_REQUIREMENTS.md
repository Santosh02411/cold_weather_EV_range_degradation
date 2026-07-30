# Project Requirements

## 1. Purpose

Predict how much range an electric vehicle loses in cold weather, given
ambient conditions and vehicle/trip parameters, and explain *why* — in a
way that is traceable to real published research rather than arbitrary
guesses. This document defines what "done" means for the project,
independent of how any particular phase implements it.

## 2. Scope

**In scope:** temperature-driven range degradation prediction for battery
electric vehicles (BEVs), trip/charging simulation built on top of that
prediction, vehicle comparison, explainability, and reporting.

**Out of scope (for now):** plug-in hybrids, real-time OBD-II/telematics
ingestion, route-level (turn-by-turn) elevation modeling, and mobile
native apps. These are candidate future phases, not current requirements.

## 3. Functional Requirements

### FR-1 — Range Degradation Prediction
- FR-1.1: Given temperature, humidity, wind speed, precipitation,
  battery %, vehicle speed, HVAC state, terrain, battery age, and vehicle
  specs, the system MUST return a predicted % range degradation.
- FR-1.2: The prediction MUST be accompanied by a confidence score that
  varies with input conditions (not a constant).
- FR-1.3: The system MUST be able to state which published sources its
  temperature-degradation relationship is grounded in.
- FR-1.4: The system MUST fall back to a physics-based estimate if no
  trained ML model is available (e.g. first run before training).

### FR-2 — Weather Integration
- FR-2.1: The system MUST fetch real current weather for a given
  location when a valid API key is configured.
- FR-2.2: The system MUST clearly indicate when it is using demo/fallback
  weather data rather than real data (current gap — see
  `FEATURE_TICKET_LIST.md`, ticket ARCH-2).

### FR-3 — Vehicle Management
- FR-3.1: Users can view a database of EV models with specs (battery
  capacity, EPA/WLTP range, weight).
- FR-3.2: Users can compare two or more vehicles under the same
  conditions.

### FR-4 — Trip & Charging Simulation
- FR-4.1: Given a distance, starting battery %, and conditions, the
  system MUST estimate remaining battery %, number of charging stops,
  and energy used.

### FR-5 — Explainability
- FR-5.1: Every prediction MUST be accompanied by a human-readable
  explanation of the top contributing factors.
- FR-5.2: Feature importance MUST be derivable from the actual trained
  model (SHAP where available, model-native importances otherwise) —
  not a hardcoded value.

### FR-6 — Authentication & Access
- FR-6.1: Users MUST register/log in to save predictions and trips.
- FR-6.2: Admins MUST have a separate role with access to retraining,
  analytics, and dataset management.

### FR-7 — Reporting
- FR-7.1: Users can export predictions/comparisons as PDF or CSV.

### FR-8 — Model Lifecycle
- FR-8.1: The system MUST support retraining without code changes
  (admin-triggered).
- FR-8.2: Every training run MUST be versioned with metrics attached,
  so a regression can be identified and rolled back.
- FR-8.3: Every training run MUST report accuracy against real published
  benchmarks, not only against its own synthetic test split.

## 4. Non-Functional Requirements

### NFR-1 — Accuracy & Honesty
- The system's stated accuracy claims MUST be traceable to a real,
  citable source. Synthetic-data-only self-evaluation is not sufficient
  to claim "real-world accuracy."

### NFR-2 — Explainability
- Predictions must never be a pure black box; a plain-language reason
  must always accompany a number.

### NFR-3 — Performance
- A single prediction request should return in well under 1 second on
  typical hardware (all four models are lightweight; no external API
  call is on the prediction critical path).

### NFR-4 — Security
- See `SECURITY_AND_ACCESS.md` for the full model. Summary: no secrets
  in source control, passwords hashed, CSRF protection on state-changing
  routes, role-gated admin actions.

### NFR-5 — Maintainability
- ML training and prediction logic must be swappable/upgradable without
  touching API route code (achieved via the `backend/app/ml/` module
  boundary).

### NFR-6 — Portability
- Must run on SQLite for local/dev use and MySQL for production without
  code changes (already true via `SQLALCHEMY_DATABASE_URI`).

### FR-9 — AI-Generated Explanations (Phase 3)
- FR-9.1: The system MUST be able to generate a natural-language trip
  briefing for any saved prediction, using only that prediction's own
  computed values — never a number the LLM invents itself.
- FR-9.2: The system MUST allow free-form questions about a specific
  saved prediction, answered only from that prediction's facts.
- FR-9.3: The system MUST detect predictions that deviate unusually far
  from the real-world-calibrated baseline (FR-1.3) using a real
  computation, not an LLM judgment call — the LLM may only narrate an
  already-detected anomaly, never decide whether one exists.
- FR-9.4: All three of the above MUST degrade gracefully (template-based
  output, clearly labeled as such) when no LLM API key is configured,
  rather than failing the request.

## 5. Data Requirements

- DR-1: The temperature → degradation relationship used for training and
  validation MUST be grounded in real, cited sources
  (`data/real_world_calibration/temperature_range_benchmarks.csv`).
- DR-2: Where real row-level telemetry is not publicly available (this
  was the case for the combined feature set used here — see
  `TECHNICAL_ARCHITECTURE.md` §4 for what was checked), the system MUST
  clearly document which parts of the training data are engineering
  estimates vs. real benchmarks, rather than presenting all of it as
  equally "real."

## 6. Success Criteria (Phase 1)

1. The temperature-degradation curve is fit from real, cited data —
   not arbitrary if/elif thresholds. ✅ (`physics.py`)
2. Every training run is validated against the real benchmark table and
   the resulting error is reported, not hidden. ✅ (`train.py`,
   `real_world_calibration` in `training_results.json`)
3. Confidence is derived from model behavior on the given input, not a
   hardcoded constant. ✅ (`predict.py`, ensemble variance)
4. Models are versioned with metadata so a specific run's provenance is
   traceable. ✅ (`saved_models/v<N>_<timestamp>/`)
5. All of the above is documented clearly enough that someone who didn't
   build it can understand *why* each decision was made, not just *what*
   was built. ✅ (this `docs/` folder)

## 7. Success Criteria (Phase 2)

1. Terrain is derived from a real, measured elevation profile instead
   of a manual guess. ✅ (`services/geo.py`)
2. Trip predictions can run against a real route (geocoded + routed),
   not only a manually-entered distance. ✅ (`/trip/api/route-predict`)
3. The UI never silently substitutes demo weather without saying so.
   ✅ (`data_source` field + badge)
4. At least one vehicle spec entry error is found and corrected against
   a real cited source (not just re-affirmed as "probably fine"). ✅
   (Tesla Model 3 Long Range, Hyundai IONIQ 5 Long Range)

## 8. Success Criteria (Phase 3)

1. At least one real LLM call path exists and is grounded such that it
   cannot alter a computed number, only phrase it. ✅
   (`services/ai_features.py`, `GROUNDING_RULES`)
2. Anomaly detection is a real computation, not an LLM guess. ✅
   (`detect_anomaly()` — pure arithmetic against the Phase 1 physics
   baseline)
3. Every AI feature has a non-LLM fallback that still returns useful,
   clearly-labeled output. ✅ (template fallback path, tested end-to-end
   without network access — see `PROJECT_WORKFLOW.md`)
