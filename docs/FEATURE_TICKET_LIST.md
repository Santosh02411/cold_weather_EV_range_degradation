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
| ML-4 | Make `predict.py` read `current_version.json` directly instead of the flat `saved_models/*.pkl` copy, to support instant rollback | ✅ Done — `get_active_model_dir()`, `set_active_version()`, admin UI at `/admin` "Model Versions". Also surfaced and fixed a real bug found while testing this: `load_model()` was silently retraining on every single prediction whenever an optional model (e.g. xgboost, if not installed) was missing — see `PROJECT_WORKFLOW.md`. |

## Phase 2 — Real-Time & Data-Source Accuracy

| ID | Title | Status |
|---|---|---|
| ARCH-2 | Surface in the UI when weather data is demo/fallback vs. real (currently silent — `weather.py` falls back without a visible indicator) | ✅ Done — `data_source` field on all weather responses + live/demo badge in `weather/index.html` UI |
| RT-1 | Elevation/terrain data via a real API (Open-Elevation or Google Elevation) instead of a manual flat/hilly/mountainous dropdown | ✅ Done — `services/geo.py`, terrain derived from real elevation gain, not a guess |
| RT-2 | Route-based prediction: real route (OSRM/Google Maps) with elevation profile + segment-by-segment weather, instead of one static input | 🟡 Partial — `/trip/api/route-predict` uses a real route + real elevation-derived terrain + real weather at the origin. True *segment-by-segment* weather along a long multi-city route is still a single origin-point lookup — see RT-5 below. |
| RT-3 | Real-time vehicle telemetry integration (OBD-II / manufacturer APIs) where available, instead of manually entered battery %/speed | 🔲 Deferred — requires either physical OBD-II hardware access or manufacturer API partnerships (e.g. Tesla Fleet API approval), neither of which is obtainable inside a development sandbox. Revisit when there's a real vehicle/account to integrate against. |
| DATA-1 | Wire OpenEV Data's real vehicle specs (battery capacity, rated range) into `seed_data.py` in place of the current hand-entered vehicle list | 🟡 Partial — `scripts/sync_openev_data.py` is written and ready, but couldn't be *executed* in this sandbox (no outbound network). Two entries (Tesla Model 3 Long Range, Hyundai IONIQ 5 Long Range) were spot-checked against cited real sources by hand and corrected in `seed_data.py`; the other 9 entries are unverified estimates, labeled as such in a comment at the top of `VEHICLES`. |
| RT-4 | Replace the public OSRM demo server with a self-hosted instance or paid routing provider before any real deployment (the demo server's usage policy is "light use / evaluation only") | ✅ Done — `ROUTING_PROVIDER`/`OSRM_BASE_URL`/`ORS_API_KEY` config; `get_route()` supports self-hosted OSRM or OpenRouteService with fallback |

## Phase 3 — AI/GenAI Layer

| ID | Title | Status |
|---|---|---|
| AI-1 | LLM-generated natural-language trip briefing, grounded in the real prediction output (RAG-style against SHAP explanation, not free generation) | ✅ Done — `services/ai_features.py::generate_trip_briefing`, `GET /predictions/api/<id>/briefing` |
| AI-2 | Conversational "why is my range degraded" assistant, grounded in the same explanation data `xai.py` already produces | ✅ Done — `services/ai_features.py::answer_question`, `POST /predictions/api/<id>/ask` |
| AI-3 | Anomaly detection + plain-language narration for unusual degradation patterns per vehicle | ✅ Done — `services/ai_features.py::detect_anomaly` (real, non-LLM check against the Phase 1 physics baseline) + `narrate_anomaly` (LLM phrasing only) |
| RT-5 | True segment-by-segment weather along a route (fetch conditions at multiple waypoints, not just the origin) | 🟡 Partial — `/trip/api/route-predict` now samples weather at BOTH origin and destination and uses the colder (worst-case) reading; full multi-waypoint sampling for long routes is RT-6 below |
| RT-6 | Full multi-waypoint weather sampling along long routes (beyond the current 2-point origin/destination sampling) | ✅ Done — opt-in via `WEATHER_MULTI_WAYPOINT_ENABLED` (off by default, real cost tradeoff against the free tier stays real); `select_route_waypoints()` + coordinate-based weather lookup |

## Phase 4 — New Features

| ID | Title |
|---|---|
| FEAT-1 | Battery health/SOH trend tracking over time, not just instantaneous cold-weather effect | ✅ Done — `BatteryHealthRecord` model, `/vehicles/<id>/battery-health` page, linear trend + projection |
| FEAT-2 | Charging station finder with real-time availability (Open Charge Map API) | ✅ Done — `services/charging_stations.py`, `/charging/api/stations`, wired into the charging page |
| FEAT-3 | Push/email alerts for extreme cold days affecting a saved vehicle/route | ✅ Done — `AlertSubscription` model, APScheduler-driven background checks, Flask-Mail actually wired for the first time (was declared but unused since v1), `/alerts` page |
| FEAT-4 | Crowdsourced real-world range reports — lets the app slowly build its own real telemetry dataset over time, which is the most direct fix for the "no row-level real data" gap documented in `TECHNICAL_ARCHITECTURE.md` §5 | ✅ Done — `CommunityRangeReport` model, `/community` page + blueprint, feeds `services/recalibration.py` |
| FEAT-5 | Multi-vehicle fleet dashboard for admins | ✅ Done — `/admin/api/fleet-stats`, "Fleet Dashboard" section in the admin panel |
| FEAT-6 | Historical accuracy tracking: compare predicted vs. user-reported actual range, feed back into recalibration | ✅ Done — `Prediction.actual_range_km`, report-actual endpoint, `services/recalibration.py::retrain_with_real_data()` |

## Phase 5 — Production Hardening

| ID | Title |
|---|---|
| SEC-1 | Add rate limiting (Flask-Limiter) to all API endpoints, especially auth | ✅ Done — Flask-Limiter with per-tier limits (auth/predict/AI); see config.py `RATELIMIT_*` |
| SEC-2 | Scope CORS to explicit allowed origins instead of permissive default | ✅ Done — `CORS_ALLOWED_ORIGINS` env var, warns loudly when left at the permissive default |
| SEC-3 | Rotate/disable default seeded admin/demo credentials before any public deployment | ✅ Done — `seed_data.py` no longer hardcodes passwords; generates random ones via `secrets` (printed once) or uses `ADMIN_PASSWORD`/`DEMO_PASSWORD`; demo account is skippable via `SEED_DEMO_USER=false` |
| INFRA-1 | Move default local dev DB from SQLite to Postgres for production; add Alembic migrations | ✅ Done — Flask-Migrate wired, `psycopg2-binary` added, Postgres `DATABASE_URL` documented. Actual migration files weren't generated here (needs `flask db init` against a real DB) — see README "Database Migrations" for the exact commands to run |
| INFRA-2 | Add a real automated test suite (`test_charging.py` currently exists but is not part of a full suite) | ✅ Done — `tests/` with 42 passing tests across 6 files (physics, train, geo, battery trend, recalibration math, end-to-end train+predict+rollback) plus a Flask/DB smoke-test file that skips cleanly where `flask_sqlalchemy` isn't installed. See `tests/README.md` for exactly what was and wasn't run |
| INFRA-3 | Add response caching for weather calls to avoid hitting API rate limits | ✅ Done — `services/cache.py`, in-memory TTL cache (documented as per-process only; note for multi-worker deployments), tested offline |

## UX Follow-ups (from Phase 1 response-shape changes)

| ID | Title |
|---|---|
| UX-1 | Add a visible confidence indicator to the prediction result card now that `confidence` genuinely varies (was previously always `0.85`, not worth surfacing) | ✅ Done — color-coded bar + ensemble-size note on the prediction card |
| UX-3 | Surface `physics_baseline_degradation_pct` alongside the final prediction as a "baseline vs. adjusted for your trip" comparison | ✅ Done — "typical for this temperature" vs. "your conditions" comparison, with the delta attributed to other factors |
| UX-4 | Forecast-based ("plan for a future date") predictions using the existing `/weather/api/forecast` route | ✅ Done — forecast picker on the predictions page auto-fills temperature/humidity/wind/precipitation from a selected forecast slot. Found and fixed a real bug along the way: demo-mode forecast dates were hardcoded to Jan 2024 regardless of the actual date |
| UX-5 | Export a trip briefing as a shareable link and/or PDF | ✅ Done — `Prediction.share_token` (generated on demand), public read-only `/predictions/share/<token>` view (no login), revoke endpoint, and a PDF export reusing `reports.py`'s existing reportlab pattern |
| UX-6 | Model comparison view — show each model's individual prediction, not just the ensemble result | ✅ Done — `predict.py` now returns `individual_predictions` per model; rendered as a small comparison bar chart under the confidence section |
| UX-7 | "Confidence explains itself" — a tooltip explaining what the confidence score actually measures | ✅ Done — hover tooltip on the confidence label explaining ensemble disagreement in plain language |

## Phase 6 — User Dashboard

| ID | Title | Status |
|---|---|---|
| UD-1 | "User Dashboard" sidebar section with Personalized Dashboard hub page | ✅ Done — `/dashboard/me`, quick stats + jump-links + activity preview |
| UD-2 | Prediction History as a real page (was API-only) | ✅ Done — `/predictions/history` |
| UD-3 | Saved Predictions (bookmark a prediction) | ✅ Done — new `SavedPrediction` model, save/unsave endpoints, `/predictions/saved` |
| UD-4 | Saved Vehicles page | ✅ Done — `/vehicles/saved`, backed by existing `RecentlyViewedVehicle` data |
| UD-5 | Favorite Vehicles as a dedicated page (was filter-only on the catalog) | ✅ Done — `/vehicles/favorites` |
| UD-6 | Saved Reports nav entry | ✅ Done — links to existing Reports page (already has Report History) |
| UD-7 | Usage Statistics page | ✅ Done — `/dashboard/usage-stats`, renders existing `user_analytics()` data |
| UD-8 | Recent Activity feed | ✅ Done — `analytics.recent_activity()` merges predictions/trips/favorites/saves/reports; `/dashboard/activity` page + `/dashboard/api/activity` |

See `docs/MEMORY.md` "Phase 6" for the reasoning behind each data-source choice.

## Phase 7 — Admin Dashboard

| ID | Title | Status |
|---|---|---|
| AD-1 | "Admin Dashboard" sidebar section (admin-only) | ✅ Done — 10 links added to `base.html`, gated on `current_user.is_admin` |
| AD-2 | User Management nav entry | ✅ Done — links to existing `/admin/users` |
| AD-3 | Vehicle Management page | ✅ Done — `/admin/vehicles`, shows soft-deleted vehicles too, with reactivate toggle |
| AD-4 | Dataset Management nav entry | ✅ Done — links to existing `/datasets/` |
| AD-5 | ML Model Management nav entry | ✅ Done — links to existing `/admin/ml-dashboard` |
| AD-6 | Weather API Monitoring | ✅ Done — new `WeatherLog.data_source`/`error_note` columns, `/admin/weather-monitoring` |
| AD-7 | Feedback Management | ✅ Done — moderation UI for `CommunityRangeReport.is_flagged` (flag/unflag/delete), `/admin/feedback` |
| AD-8 | Prediction Statistics nav entry | ✅ Done — links to existing `/admin/analytics` |
| AD-9 | System Logs | ✅ Done — merged `LoginHistory` + drift-check feed, `/admin/system-logs` |
| AD-10 | Analytics Dashboard (fleet-wide) | ✅ Done — `/admin/fleet-dashboard`, reuses existing `/admin/api/fleet-stats` |
| AD-11 | Report Management (admin-wide) | ✅ Done — read-only cross-user view, `/admin/reports` |

See `docs/MEMORY.md` "Phase 7" for the reasoning behind each data-source choice.

## Phase 8 — Notifications

| ID | Title | Status |
|---|---|---|
| NOT-1 | "Notifications" sidebar section | ✅ Done — 8 links added to `base.html` |
| NOT-2 | Low Battery Alerts | ✅ Done — synchronous check after trip simulation, against real `estimated_arrival_battery_pct` |
| NOT-3 | Severe Weather Alerts nav entry | ✅ Done — links to existing `/alerts` (FEAT-3), not duplicated |
| NOT-4 | Charging Reminder | ✅ Done — new scheduler job, checks upcoming `ChargingReservation`s within lead time |
| NOT-5 | Battery Health Warning | ✅ Done — synchronous check after a SOH reading is logged |
| NOT-6 | Maintenance Reminder | ✅ Done — new scheduler job, grounded in logged odometer readings + user-set baseline |
| NOT-7 | Email Notifications | ✅ Done — reuses existing `User.email_notifications_enabled`, control moved to `/notifications/preferences` |
| NOT-8 | Push Notifications | ✅ Done — real browser `Notification` API + permission flow, honestly scoped to tab-open-only |
| NOT-9 | In-App Notifications | ✅ Done — new `Notification`/`NotificationPreference` models, full inbox at `/notifications/` |

See `docs/MEMORY.md` "Phase 8" for the reasoning behind each data-source and scoping choice.

## Phase 9 — Cost Analysis

| ID | Title | Status |
|---|---|---|
| COST-1 | "Cost Analysis" sidebar section | ✅ Done — 7 links added to `base.html` |
| COST-2 | Charging Cost Calculator | ✅ Done — `/cost/`, wraps existing `charging_cost.estimate_charging_cost()`, defaults to the user's saved rate |
| COST-3 | Electricity Price Integration | ✅ Done — new `CostPreference` model + `services/electricity_rates.py` regional-average lookup table, `/cost/preferences` |
| COST-4 | Monthly Charging Cost | ✅ Done — dedicated page over existing `analytics_service.cost_analytics()`, now rate-preference-aware, `/cost/monthly` |
| COST-5 | EV vs Petrol Cost Comparison | ✅ Done — new `services/fuel_cost.py::compare_ev_vs_petrol()`, `/cost/compare` |
| COST-6 | Ownership Cost Analysis | ✅ Done — same engine + purchase price/maintenance, `/cost/ownership` |
| COST-7 | Savings Calculator | ✅ Done — same engine + optional payback period, `/cost/savings` |
| COST-8 | Charging Cost History | ✅ Done — new `ChargingSession` model, a real logged ledger distinct from Monthly Charging Cost's projection, `/cost/history` |

See `docs/MEMORY.md` "Phase 9" for the reasoning behind each data-source and scoping choice.
