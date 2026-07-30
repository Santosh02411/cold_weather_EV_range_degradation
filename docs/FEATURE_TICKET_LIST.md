# Feature Ticket List

Tracked by phase. "Phase 1" tickets below are resolved (this delivery);
everything else is queued for future phases per the roadmap discussed
with the project owner. Ticket IDs are referenced from other docs in
this folder — keep IDs stable if you reorder/reprioritize.

## Phase 1 — ML & Data Authenticity (this delivery)

| ID | Title | Status |
|---|---|---|
| ML-1 | Replace arbitrary temperature thresholds with a real-data-calibrated curve | ✅ Done (`physics.py`) |
| ML-2 | Real train/validation/test split + cross-validation, reported per model | ✅ Done (`train.py`) |
| ML-3 | Real confidence score derived from model behavior, not a constant | ✅ Done (`predict.py`, ensemble variance) |
| ML-5 | Model versioning with metadata (timestamp, metrics, calibration report) | ✅ Done (`saved_models/v<N>_<timestamp>/`) |
| ML-6 | Validate trained models against real published benchmarks, not just synthetic test data | ✅ Done (`run_calibration_check`) |
| ML-4 | Make `predict.py` read `current_version.json` directly instead of the flat `saved_models/*.pkl` copy, to support instant rollback | 🔲 Queued (Phase 2) — see `TECHNICAL_ARCHITECTURE.md` §3 |

## Phase 2 — Real-Time & Data-Source Accuracy

| ID | Title | Status |
|---|---|---|
| ARCH-2 | Surface in the UI when weather data is demo/fallback vs. real (currently silent — `weather.py` falls back without a visible indicator) | ✅ Done — `data_source` field on all weather responses + live/demo badge in `weather/index.html` UI |
| RT-1 | Elevation/terrain data via a real API (Open-Elevation or Google Elevation) instead of a manual flat/hilly/mountainous dropdown | ✅ Done — `services/geo.py`, terrain derived from real elevation gain, not a guess |
| RT-2 | Route-based prediction: real route (OSRM/Google Maps) with elevation profile + segment-by-segment weather, instead of one static input | 🟡 Partial — `/trip/api/route-predict` uses a real route + real elevation-derived terrain + real weather at the origin. True *segment-by-segment* weather along a long multi-city route is still a single origin-point lookup — see RT-5 below. |
| RT-3 | Real-time vehicle telemetry integration (OBD-II / manufacturer APIs) where available, instead of manually entered battery %/speed | 🔲 Deferred — requires either physical OBD-II hardware access or manufacturer API partnerships (e.g. Tesla Fleet API approval), neither of which is obtainable inside a development sandbox. Revisit when there's a real vehicle/account to integrate against. |
| DATA-1 | Wire OpenEV Data's real vehicle specs (battery capacity, rated range) into `seed_data.py` in place of the current hand-entered vehicle list | 🟡 Partial — `scripts/sync_openev_data.py` is written and ready, but couldn't be *executed* in this sandbox (no outbound network). Two entries (Tesla Model 3 Long Range, Hyundai IONIQ 5 Long Range) were spot-checked against cited real sources by hand and corrected in `seed_data.py`; the other 9 entries are unverified estimates, labeled as such in a comment at the top of `VEHICLES`. |
| RT-4 | Replace the public OSRM demo server with a self-hosted instance or paid routing provider before any real deployment (the demo server's usage policy is "light use / evaluation only") | 🔲 Queued (Phase 5, alongside other production-hardening tickets) |

## Phase 3 — AI/GenAI Layer

| ID | Title | Status |
|---|---|---|
| AI-1 | LLM-generated natural-language trip briefing, grounded in the real prediction output (RAG-style against SHAP explanation, not free generation) | ✅ Done — `services/ai_features.py::generate_trip_briefing`, `GET /predictions/api/<id>/briefing` |
| AI-2 | Conversational "why is my range degraded" assistant, grounded in the same explanation data `xai.py` already produces | ✅ Done — `services/ai_features.py::answer_question`, `POST /predictions/api/<id>/ask` |
| AI-3 | Anomaly detection + plain-language narration for unusual degradation patterns per vehicle | ✅ Done — `services/ai_features.py::detect_anomaly` (real, non-LLM check against the Phase 1 physics baseline) + `narrate_anomaly` (LLM phrasing only) |
| RT-5 | True segment-by-segment weather along a route (fetch conditions at multiple waypoints, not just the origin) | 🟡 Partial — `/trip/api/route-predict` now samples weather at BOTH origin and destination and uses the colder (worst-case) reading; full multi-waypoint sampling for long routes is RT-6 below |
| RT-6 | Full multi-waypoint weather sampling along long routes (beyond the current 2-point origin/destination sampling) | 🔲 Queued — real cost/rate-limit tradeoff against the free OpenWeatherMap tier; revisit if a paid weather tier is adopted |

## Phase 4 — New Features

| ID | Title |
|---|---|
| FEAT-1 | Battery health/SOH trend tracking over time, not just instantaneous cold-weather effect |
| FEAT-2 | Charging station finder with real-time availability (Open Charge Map API) |
| FEAT-3 | Push/email alerts for extreme cold days affecting a saved vehicle/route |
| FEAT-4 | Crowdsourced real-world range reports — lets the app slowly build its own real telemetry dataset over time, which is the most direct fix for the "no row-level real data" gap documented in `TECHNICAL_ARCHITECTURE.md` §5 |
| FEAT-5 | Multi-vehicle fleet dashboard for admins |
| FEAT-6 | Historical accuracy tracking: compare predicted vs. user-reported actual range, feed back into recalibration |

## Phase 5 — Production Hardening

| ID | Title |
|---|---|
| SEC-1 | Add rate limiting (Flask-Limiter) to all API endpoints, especially auth |
| SEC-2 | Scope CORS to explicit allowed origins instead of permissive default |
| SEC-3 | Rotate/disable default seeded admin/demo credentials before any public deployment |
| INFRA-1 | Move default local dev DB from SQLite to Postgres for production; add Alembic migrations |
| INFRA-2 | Add a real automated test suite (`test_charging.py` currently exists but is not part of a full suite) |
| INFRA-3 | Add response caching for weather calls to avoid hitting API rate limits |

## UX Follow-ups (from Phase 1 response-shape changes)

| ID | Title |
|---|---|
| UX-1 | Add a visible confidence indicator to the prediction result card now that `confidence` genuinely varies (was previously always `0.85`, not worth surfacing) |
| UX-3 | Surface `physics_baseline_degradation_pct` alongside the final prediction as a "baseline vs. adjusted for your trip" comparison |
