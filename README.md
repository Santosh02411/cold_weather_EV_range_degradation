# ❄️ Cold Weather Range Degradation Modeler for Electric Vehicles

An AI & Machine Learning powered web application that predicts Electric Vehicle (EV) range degradation in cold weather conditions using advanced machine learning algorithms and real-time weather analysis.

> **Phase 1-4 status (current):** the ML core was rebuilt to be
> grounded in real, cited, published cold-weather EV studies instead of
> arbitrary made-up thresholds (Phase 1); the manual terrain dropdown and
> single-point trip input were upgraded to use real geocoding, routing,
> and elevation data, plus a visible live-vs-demo weather indicator
> (Phase 2); real LLM involvement was added — grounded trip
> briefings, a Q&A assistant, and anomaly detection, all built on the
> app's own computed numbers rather than free generation (Phase 3); and
> Phase 4 added a real user-reported-data feedback loop (predictions and
> community reports can retrain the model with real outcomes, not just
> synthetic data), instant model-version rollback, real per-account
> credentials instead of hardcoded defaults, and production-hardening
> basics (rate limiting, CORS scoping, a self-hostable routing provider).
> Phase 4 also added: battery health/SOH tracking (FEAT-1), a real
> charging station finder via Open Charge Map (FEAT-2), cold-snap email
> alerts on an actual background scheduler (FEAT-3), an admin fleet
> dashboard (FEAT-5), opt-in multi-waypoint route weather (RT-6), and
> production-hardening infrastructure — Postgres/Alembic migrations,
> a 42-test automated test suite, and weather response caching
> (INFRA-1/2/3). Full write-up, design decisions, and a phase-by-phase
> build log (including real bugs hit and fixed, and what could/couldn't
> be verified without live network access) live in [`/docs`](./docs) —
> see especially
> [`docs/TECHNICAL_ARCHITECTURE.md`](./docs/TECHNICAL_ARCHITECTURE.md),
> [`docs/PROJECT_WORKFLOW.md`](./docs/PROJECT_WORKFLOW.md), and
> [`tests/README.md`](./tests/README.md).
>
> ⚠️ **Before relying on this in production:** every live HTTP
> integration (`services/geo.py`, `services/llm.py`,
> `services/charging_stations.py`, email sending, the background
> scheduler) was written against each provider's documented API but
> could not be executed in the sandbox this was built in (no outbound
> network there, and several packages — `flask_sqlalchemy`,
> `flask_limiter`, `flask_mail`, `apscheduler`, `pytest` — aren't
> installed there either). Everything that COULD be tested without
> those (pure logic: physics, ML training/prediction/rollback, trend
> math, terrain/waypoint classification) was — 42 passing tests, see
> `tests/README.md` for the exact, honest breakdown of what's verified
> vs. not. **Run `pytest`, then click through the app for real, before
> shipping.**

---

# 🚀 Features

### 🔐 Authentication & User Management

- User Registration & Login
- Secure Authentication System
- Admin & User Role Management
- User Profile Management

### 🚗 EV Vehicle Database

- 12+ Preloaded EV Models
- Tesla, BYD, Hyundai, Nissan & more
- Vehicle Comparison System

### 🌦️ Weather Integration

- Real-time Weather Data using OpenWeatherMap API
- Temperature-based Range Analysis
- Climate-aware Predictions

### 🤖 Machine Learning Predictions

- Linear Regression
- Random Forest
- XGBoost
- Gradient Boosting

### 🔋 Trip & Charging Simulation

- Battery Usage Estimation
- Charging Stop Prediction
- Arrival Battery Percentage
- Charging Time Analysis

### 🧠 Explainable AI (XAI)

- SHAP-based Prediction Explanations
- Feature Importance Visualization
- Transparent ML Results

### 📊 Analytics & Reports

- Comparative EV Analysis
- Dataset Upload & Processing
- Outlier Detection & Removal
- PDF & CSV Report Generation

### 🎨 UI/UX Features

- Responsive Premium Interface
- Dark / Light Mode
- Interactive Charts & Graphs

---

# 🛠️ Tech Stack

| Layer            | Technologies Used                 |
| ---------------- | --------------------------------- |
| Backend          | Python, Flask, SQLAlchemy         |
| Frontend         | HTML5, CSS3, JavaScript, Chart.js |
| Machine Learning | Scikit-learn, XGBoost, SHAP       |
| Database         | SQLite / MySQL                    |
| API Services     | OpenWeatherMap API                |

---

# 📂 Project Structure

```bash
Cold_Weather_EV/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask App Factory
│   │   ├── config.py            # Configuration File
│   │   ├── models/              # SQLAlchemy Models
│   │   ├── api/                 # API Route Blueprints
│   │   └── ml/                  # ML Training & Prediction
│   │
│   ├── seed_data.py             # Database Seeder
│   └── run.py                   # Application Entry Point
│
├── frontend/
│   ├── templates/               # Jinja2 Templates
│   └── static/                  # CSS, JavaScript, Images
│
├── data/
│   ├── real_world_calibration/  # Real, cited published study data (see below)
│   └── uploads/                 # User-uploaded datasets (gitignored)
├── docs/                        # Full project documentation (requirements,
│                                 # architecture, security, design, workflow log)
├── requirements.txt
├── .env.example                 # Copy to .env and fill in your own keys
└── .env                         # Your real keys (gitignored, never commit this)
```

---

# ⚡ Quick Start

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/cold_weather_EV_range_degradation.git
cd cold_weather_EV_range_degradation
```

## 2️⃣ Create a Virtual Environment

Keeps this project's packages separate from anything else on your
machine — recommended, and the only supported way if you don't have
(or don't want) permission to install packages system-wide.

```bash
python -m venv venv
```

Activate it (do this every time you open a new terminal to work on
the project):

```bash
# Windows PowerShell
venv\Scripts\Activate.ps1

# Windows cmd.exe
venv\Scripts\activate.bat

# macOS / Linux
source venv/bin/activate
```

Your prompt should now start with `(venv)`. If PowerShell refuses to
run the activation script with an "execution of scripts is disabled"
error, run this once in an **admin** PowerShell, then retry:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 3️⃣ Install Dependencies

With the virtual environment active:

```bash
pip install -r requirements.txt
```

## 4️⃣ Seed the Database

```bash
cd backend
python seed_data.py
```

This creates an admin account (and a demo account, unless
`SEED_DEMO_USER=false`) with either the `ADMIN_PASSWORD`/`DEMO_PASSWORD`
from your `.env`, or a freshly generated random password printed once to
the console — **copy it immediately**, see "Credentials" below.

## 5️⃣ Set up API keys (optional but recommended)

The app runs without any API key — `OPENWEATHERMAP_API_KEY` defaults to
`'demo'` in `backend/app/config.py`, which makes `backend/app/api/weather.py`
fall back to randomized demo weather instead of real conditions. To get
**real** current weather for predictions:

1. Create a free account at https://home.openweathermap.org/users/sign_up
2. Go to https://home.openweathermap.org/api_keys and copy your default API key
   (new keys can take up to a couple of hours to activate)
3. In the project root, copy the example env file and add your key:
   ```bash
   cp .env.example .env
   ```
   then open `.env` and set:
   ```
   OPENWEATHERMAP_API_KEY=your_real_key_here
   ```
4. Restart the app — `weather.py` will now call the real OpenWeatherMap API
   instead of returning demo data.

`.env` is already listed in `.gitignore`, so your key won't be committed.
**Never commit real API keys, database passwords, or the `SECRET_KEY`
value to a public repo** — always go through `.env`, which git ignores.

Other keys in `.env.example` (all optional):
- `WEATHERAPI_KEY` — alternate weather provider, same signup pattern at https://www.weatherapi.com/signup.aspx
- `GEMINI_API_KEY` — powers Phase 3's AI trip briefings, Q&A, and anomaly narration (see below). Without it, these features fall back to template-generated text instead of failing. Free tier, no billing account required.
- `SECRET_KEY` — set this to a long random string in any real/public deployment; the default in `config.py` is fine for local dev only

### Sending real emails (password reset, verification, cold-snap alerts, notifications)

Without `MAIL_USERNAME`/`MAIL_PASSWORD` set, this app never fails or
errors on an email step — it logs `[EMAIL-WOULD-SEND] (MAIL_USERNAME/
PASSWORD not configured) ...` to the console instead and carries on
(see `services/auth_email.py`, `services/alerts.py`,
`services/notifications.py`). That's the deliberate fail-soft default,
not a bug — but it does mean "I never received the reset email" is
expected behavior until you configure real SMTP credentials. To
actually send:

1. Turn on 2-Step Verification on the Gmail account you want to send
   from: https://myaccount.google.com/security (required — Gmail
   rejects a plain account password for SMTP from an app like this
   one, full stop, even if it's correct).
2. Generate an **App Password**: https://myaccount.google.com/apppasswords
   — pick any name (e.g. "Cold Weather EV"), then copy the 16-character
   password it shows you. This is different from your real Gmail
   password and is the only thing that will work here.
3. In `.env` (copy from `.env.example` first if you haven't), set:
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your_real_gmail_address@gmail.com
   MAIL_PASSWORD=the16charapppasswordfromstep2
   ```
   Use the App Password exactly as shown (spaces in the copied version
   are fine to remove or keep — Google accepts either).
4. Restart the app. Try "Forgot password" — you should get a real
   email within a few seconds, and the console log line changes from
   `[EMAIL-WOULD-SEND]` to nothing (a successful `flask_mail` send
   doesn't log by default).

If it still doesn't send after this, check the console output for the
actual SMTP error (`[ERROR] Failed to send email to <address>:
<reason>`) rather than assuming it's silent — common causes are a
typo'd address, an App Password copied with a missing character, or a
network/firewall blocking outbound port 587.

**If you're also seeing an `OperationalError: no such column` on
login/register/forgot-password specifically** (not just missing
emails), that error is crashing the request *before* it ever reaches
the email-sending code — fix that first (see "Database Migrations"
below); the email config above is unrelated to that error and won't
fix it by itself.

### Getting a Gemini API key (for Phase 3's AI features, free tier)

1. Go to https://aistudio.google.com/apikey and sign in with any Google
   account — no credit card or billing account needed.
2. Click **Create API key**, then copy it.
3. Add it to `.env`:
   ```
   GEMINI_API_KEY=your-real-key-here
   ```
4. (Optional) `GEMINI_MODEL` defaults to `gemini-2.0-flash`, a free-tier
   model — override it in `.env` if you want a different one. Free-tier
   Flash models have a per-minute and per-day request cap (check your
   current limits on the quota page in AI Studio); this app's Phase 3
   features are a handful of short calls per prediction, well within
   normal usage for one person testing locally.

A new key from Google AI Studio starts on the free tier automatically —
you don't need to opt into anything or attach a payment method to use
it at this level. Full docs: https://ai.google.dev/gemini-api/docs

## 6️⃣ (Optional) Train the ML models explicitly

Trained model files (`backend/app/ml/saved_models/`) are gitignored —
they're regenerated automatically on first prediction request if
missing, but running this explicitly first shows you the real
train/validation/test metrics and the real-world calibration check:

```bash
cd backend/app/ml
python train.py
```

## 7️⃣ Run the Application

```bash
python run.py
```

---

# 🗄️ Database Migrations (INFRA-1)

Flask-Migrate (Alembic) is wired in for real schema changes against an
existing database with real data — `db.create_all()` (used for a brand
new local dev DB) never alters an existing table, only creates missing
ones, so it can't handle a column rename or type change safely.

```bash
cd backend
export FLASK_APP=run.py        # Windows PowerShell: $env:FLASK_APP="run.py"
flask db init                  # once, creates the migrations/ folder
flask db migrate -m "initial"  # autogenerates a migration from the current models
flask db upgrade                # applies it
```

For any future model change: edit the model, then
`flask db migrate -m "describe the change"` followed by `flask db upgrade`.
**Always read the autogenerated migration file before running `upgrade`**
— Alembic's autogenerate is good but not perfect (it can miss some
index/constraint changes), especially the first time it's run against
an existing database that was previously only managed by `create_all()`.

To switch from the default MySQL/SQLite setup to Postgres, set
`DATABASE_URL` in `.env` to a `postgresql+psycopg2://...` URL (see
`.env.example`) — `psycopg2-binary` is already in `requirements.txt`.

### "no such column" errors (`OperationalError`)

This means your local SQLite file (`backend/cold_weather_ev.db` by
default) was created by `db.create_all()` before this project's models
gained the column it's now complaining about — `create_all()` only
creates missing *tables*, it never alters an *existing* table, so a
database created early on doesn't automatically pick up columns added
by later changes. This shows up as `sqlite3.OperationalError: no such
column: ...` on almost any page that touches that table (login,
register, forgot-password all touch `users`, so this can look like
"nothing works").

For a local dev database with no data you need to keep, the fastest
fix is to reset it:

```bash
cd backend
python ../scripts/reset_dev_db.py   # prompts for confirmation, then recreates every table fresh
python seed_data.py                 # re-seed the admin/demo accounts
```

If you do have real data you need to keep, use the proper migration
path above (`flask db init` / `migrate` / `upgrade`) instead of
resetting.

# 🌐 Application URL

Open in browser:

```bash
http://127.0.0.1:5000
```

---

# 🔋 Battery Intelligence

The Battery Health Dashboard (`/vehicles/<id>/battery-health`) now includes:

- **Battery Health / Degradation Prediction** — a research-cited generic
  SOH estimate (Geotab's ~2.3%/year calendar degradation figure) when
  you haven't logged real readings yet; prefers your real fitted trend
  once you have.
- **Aging Analysis** — compares your real logged decline rate against
  the typical cited rate (faster / typical / slower).
- **Battery Life Estimation** — projects years remaining until SOH
  crosses the commonly-used 70% end-of-life convention.
- **Efficiency Curve** — a real chart of energy use vs. temperature,
  generated by sweeping your vehicle's actual trained prediction model
  (not a separate formula).
- **Cold Start Efficiency** — an interactive estimate of the extra
  energy a short cold-weather trip uses before the pack/cabin warm up,
  grounded in published reporting (~2x energy on a ~6-mile winter trip,
  fading on longer trips).
- **Battery Heating Requirement** — shown on the prediction result
  card: an estimated kWh figure for cabin heating, derived from the
  SHAP/rule-based explanation's real HVAC contribution, not a separate
  thermal model.
- **Temperature Exposure** — real aggregate stats from this app's own
  logged weather history for a city (grows more meaningful with use).

**Two requested items were deliberately not implemented: Battery
Voltage Prediction and Internal Resistance Estimation.** Both would
need real per-chemistry, per-pack electrochemical data this project
doesn't have access to — producing numbers for either would mean
presenting an invented formula as a real prediction. See
`docs/MEMORY.md` for the full reasoning.

# 🚗 EV Vehicle Database

- **Search & filter** — by name/brand, chemistry, vehicle type, price
  range, battery capacity, range, and fast-charging support.
- **Detailed spec page** — `/vehicles/view/<id>` for full specs beyond
  the card view.
- **Vehicle images** — upload one when adding/editing a vehicle
  (validated as a real image via Pillow, same pattern as profile
  pictures).
- **Favorites** — heart-toggle any vehicle; "My favorites only" filter
  on the list page.
- **Recently viewed** — automatically tracked when you open a vehicle's
  detail page, shown as quick-access chips at the top of the vehicle
  list.
- **Pricing data honesty note:** only 2 of the 12 seeded vehicles have
  a verified `price_usd` (Tesla Model 3 Long Range, Model Y Long
  Range) — every other entry is `null` with a comment explaining why
  (BYD isn't sold new in the US; other search results matched a
  different trim than what's seeded). See `docs/PROJECT_WORKFLOW.md`.

# 🔐 Authentication & Account Features

Beyond basic login/register, the app now has:

- **Email verification** — sent on registration (or email change); a
  banner on the profile page offers to resend it. Soft gate by default
  (`REQUIRE_EMAIL_VERIFICATION=false`) — unverified users can still use
  the app.
- **Forgot / reset password** — real email-delivered reset links
  (1-hour expiry).
- **OTP login** — sign in with a 6-digit code emailed to you instead of
  a password (`/otp-login`). Rate-limited, 5-minute expiry, 5 wrong
  attempts locks the code.
- **Google / GitHub sign-in** — via [Authlib](https://docs.authlib.org).
  To enable:
  1. Google: create OAuth credentials at
     https://console.cloud.google.com/apis/credentials — authorized
     redirect URI: `http://localhost:5000/oauth/google/callback`
     (adjust host/port for your deployment)
  2. GitHub: create an OAuth App at
     https://github.com/settings/developers — callback URL:
     `http://localhost:5000/oauth/github/callback`
  3. Set the client ID/secret pairs in `.env` — the sign-in buttons only
     appear once configured, no code changes needed.
  Signing in with a provider whose email matches an existing account
  links that provider to the existing account rather than creating a
  duplicate.
- **Session & device management** (`/sessions`) — see every device
  currently signed into your account and revoke any of them
  individually; revoking takes effect on that device's very next
  request (not just cosmetically removed from a list — see
  `docs/TECHNICAL_ARCHITECTURE.md`).
- **Login history** — recent sign-in attempts (success/failure, method,
  IP, device) on the same page.
- **Profile picture upload** — validated for real image content (not
  just file extension) via Pillow, 5MB limit.
- **Notification preferences** — toggle cold-snap alert emails and
  "new device signed in" security emails independently.
- **Delete account** — deletes your personal data (predictions, trips,
  battery health records, alert subscriptions); community reports
  you've submitted are anonymized (kept, but no longer linked to you)
  rather than deleted, since that data remains useful to other users.

# 🔑 Credentials

There are no hardcoded default passwords anymore (see
`docs/PROJECT_WORKFLOW.md`, ticket SEC-3). `python seed_data.py`:

- Uses `ADMIN_PASSWORD` / `DEMO_PASSWORD` from `.env` if you set them
- Otherwise **generates a real random password** for each account and
  prints it to the console **once** — copy it immediately, it's hashed
  into the database and can't be recovered from the script again
- Skips creating the `demo` account entirely if `SEED_DEMO_USER=false`
  is set — recommended for anything beyond local dev, since a
  known-username public demo login is a bigger real risk than the admin
  account

---

# 📈 Machine Learning Workflow

1. Data Collection
2. Data Preprocessing
3. Feature Engineering
4. Model Training
5. Weather Integration
6. Prediction Generation
7. Explainable AI Analysis
8. Result Visualization

---

# 📊 Supported ML Algorithms

- Linear Regression
- Random Forest Regressor
- XGBoost Regressor
- Gradient Boosting Regressor

---

# 🌡️ Where the "cold weather" numbers actually come from

Row-level EV telemetry that simultaneously links temperature, HVAC use,
terrain, speed, and measured range loss for individual trips is **not**
available as a free, bulk-downloadable public dataset — this was checked
during Phase 1 (see `docs/TECHNICAL_ARCHITECTURE.md` for what was tried).
What *is* publicly available and genuinely real is a set of published,
citable field studies that report the aggregate relationship between
temperature and range retention. This project uses those directly:

| Source | What it published | Link |
|---|---|---|
| Geotab | Temperature vs. range curve from 5.2M real EV trips across 4,200 vehicles | https://www.geotab.com/blog/ev-range/ |
| Recurrent Auto | Winter range retention across 30,000+ real EVs, 34 models | https://www.recurrentauto.com/research/winter-ev-range-loss |
| AAA | Controlled cold-weather range test (with/without cabin heating) | AAA "Cold Weather EV Range Test" |
| U.S. DOE | Impact of Cold Ambient Temperature on BEV Performance (Sept 2024) | https://www.energy.gov/sites/default/files/2024-10/Impact_of_Cold_Ambient_Temperature_on_BEV_Performance_v15_TechEditFinal_12Sep2024__0.pdf |

These are compiled, with citations, in
[`data/real_world_calibration/temperature_range_benchmarks.csv`](./data/real_world_calibration/temperature_range_benchmarks.csv).
`backend/app/ml/physics.py` fits a monotonic curve through these points
and every ML model is trained to use that curve as a starting point,
then correct it using the other operating conditions. `train.py` also
scores the trained models directly against this benchmark table (not
just against its own synthetic test split) and reports the resulting
error in `saved_models/training_results.json` under
`real_world_calibration`, so the accuracy claim is traceable to real
sources rather than the model grading its own homework.

### Optional: real EV vehicle specs

For real (not estimated) battery capacity / rated range figures per
vehicle model, see the **OpenEV Data** project — a community-maintained,
versioned, CDLA-Permissive-2.0-licensed database of EV specifications:
https://github.com/open-ev-data/open-ev-data-dataset/releases/latest
(download the CSV or JSON asset from the latest release, no login
required). This isn't wired into the seed data automatically yet —
see `docs/FEATURE_TICKET_LIST.md` for that as a Phase-2/3 item — but it's
a legitimate source if you want to replace `seed_data.py`'s vehicle list
with real, current specs.

---

# 🗺️ Real routes, real elevation, real weather (Phase 2)

`POST /trip/api/route-predict` takes real place names (e.g. `"Chicago,
IL"` → `"Minneapolis, MN"`) instead of a manual distance + terrain
guess:

1. Geocodes both ends via **Nominatim** (OpenStreetMap)
2. Fetches a real driving route via **OSRM**
3. Samples the route's real elevation profile via **Open-Elevation** and
   classifies actual terrain (flat/hilly/mountainous) from measured
   elevation gain — no more guessing
4. Pulls real current weather at the origin (or demo data, clearly
   labeled — see the `data_source` field / badge below)
5. Runs the same prediction model as the manual simulator on top of all
   of the above

All three geo providers are free and require no API key, but each has
real usage limits — see `docs/TECHNICAL_ARCHITECTURE.md` §5 before
relying on this for production traffic (short version: the OSRM demo
server is evaluation-only; self-host it or switch providers for real
usage — tracked as ticket RT-4 in `docs/FEATURE_TICKET_LIST.md`).

**Live vs. demo weather is now visible, not silent:** every weather
response includes a `data_source` field (`"live"` or `"demo_fallback"`),
and the weather page shows a green/yellow badge accordingly instead of
quietly substituting random numbers.

# 🤖 Real AI involvement, grounded (Phase 3)

The original project claimed "AI & Machine Learning powered" with zero
actual language-model involvement anywhere — classical ML on synthetic
data isn't "AI" in the generative sense the branding implied. Phase 3
closes that gap, deliberately narrowly:

- **AI Trip Briefing** (`GET /predictions/api/<id>/briefing`) — a
  natural-language summary of a saved prediction, written by Gemini but
  grounded entirely in that prediction's own already-computed numbers.
  The model is explicitly instructed never to invent, adjust, or
  recompute a figure — only to phrase the given facts fluently.
- **Ask about a prediction** (`POST /predictions/api/<id>/ask`) — a
  free-form Q&A box grounded the same way; off-topic questions get
  politely redirected rather than answered from general knowledge.
- **Anomaly detection** (`GET /predictions/api/<id>/anomaly`) — a real,
  non-LLM check (implemented in `services/ai_features.py`) that flags
  predictions deviating more than 20 percentage points from the Phase 1
  real-world-calibrated physics baseline for that temperature. The LLM
  is only used afterward, optionally, to phrase an already-detected
  anomaly in plain language — it never decides what counts as anomalous.

**No `GEMINI_API_KEY` configured?** All three features still work —
they fall back to template-generated text built from the same
underlying data, clearly labeled `"source": "template"` in the API
response, rather than failing. See "Getting a Gemini API key" above
to enable the LLM-generated version — free tier, no billing account
required.

# 🔁 Real data feedback loop (Phase 4)

- **Report what actually happened** — every prediction result now has a
  "Report What Actually Happened" box. Enter the real range you got and
  it's stored against that prediction (`Prediction.actual_range_km`).
- **Community Range Reports** (`/community`) — anyone can report a real
  drive's outcome directly, no prior prediction needed. Browse recent
  reports and see how much real data has been collected so far.
- **Retrain with real data** (`/admin` → "Real User-Reported Data") —
  once at least 10 real outcomes exist, an admin can retrain blending
  real data (oversampled 5x) into the synthetic training set, producing
  a new model version. This is the actual mechanism that makes the
  model *more accurate over time*, not just better-labeled — see
  `docs/TECHNICAL_ARCHITECTURE.md` §5/6 for why this matters (there's no
  free public row-level dataset for this domain; this is how one gets
  built).
- **Model version rollback** (`/admin` → "Model Versions") — every
  training run (regular or real-data-blended) is versioned. Activating
  an older version is instant, no retraining required.

# 🔒 Production hardening (Phase 4)

- **Rate limiting** — Flask-Limiter on auth (`RATELIMIT_AUTH`),
  predictions (`RATELIMIT_PREDICT`), and AI endpoints (`RATELIMIT_AI`),
  all configurable via `.env`.
- **CORS scoping** — set `CORS_ALLOWED_ORIGINS` before deploying
  anywhere public; left at the permissive local-dev default (`*`) it
  now logs a loud warning instead of staying silently open.
- **Configurable routing provider** — `ROUTING_PROVIDER=osrm` (default,
  point `OSRM_BASE_URL` at a self-hosted instance) or
  `ROUTING_PROVIDER=ors` with an `ORS_API_KEY` (OpenRouteService free
  tier) instead of relying on OSRM's public demo server, which its own
  usage policy describes as evaluation-only.
- **Real credentials** — see "Credentials" above (SEC-3, done in an
  earlier round of Phase 4).

# 🔋🔌🚙🔔 More Phase 4 features

- **Battery Health Tracking** (FEAT-1, `/vehicles/<id>/battery-health`)
  — log real SOH% readings over time, see an actual fitted degradation
  trend (%/year) and a projection, not an estimate.
- **Real Charging Station Finder** (FEAT-2, on the Charging page) —
  real stations via Open Charge Map: address, connector types, max
  power, operator.
- **Cold Snap Alerts** (FEAT-3, `/alerts`) — subscribe a location +
  temperature threshold, get an email when it's crossed. Runs on an
  in-process APScheduler background job (checked every
  `ALERT_CHECK_INTERVAL_MINUTES`, default 60). Flask-Mail is now
  actually wired up (it was a declared dependency since v1 but never
  initialized) — without `MAIL_USERNAME`/`MAIL_PASSWORD` set, alerts are
  logged instead of sent, same fail-soft-and-say-so pattern as
  everywhere else in this app.
- **Fleet Dashboard** (FEAT-5, `/admin`) — totals, predictions by
  vehicle, most active users. Only matters once more than one person
  uses this app, which is exactly the condition it's gated behind
  (admin-only).
- **Multi-waypoint route weather** (RT-6) — opt-in
  (`WEATHER_MULTI_WAYPOINT_ENABLED=true`) upgrade from the default
  2-point (origin+destination) sampling to N real waypoints along a
  route. Off by default — real added API-call cost.

# 🔎 Plan ahead, compare, and share

- **Plan for a future date** (predictions page) — load a real forecast
  for a city and pick a time slot to auto-fill temperature/humidity/
  wind/precipitation, instead of only ever predicting for right now.
- **Model comparison** — every prediction now shows what each
  individual ML model predicted, not just the blended ensemble result,
  so you can see why confidence is high or low.
- **Confidence, explained** — hover the ⓘ next to "Model Confidence"
  for a plain-language explanation of what it actually measures.
- **Share a briefing** — generate a public, read-only link to a
  prediction + its AI briefing (no login needed to view), or download
  it as a PDF.

# 🏗️ Production Infrastructure (INFRA-1/2/3)

- **Database migrations** — Flask-Migrate wired in; see "Database
  Migrations" above for the real `flask db` commands (not run in this
  project's build sandbox — no live DB there).
- **Automated test suite** — `tests/`, 42 passing tests covering the
  physics baseline, ML training/prediction/rollback, terrain/waypoint
  math, and battery trend calculations, run with `pytest`. See
  `tests/README.md` for exactly what's verified vs. not.
- **Weather response caching** — in-memory TTL cache
  (`WEATHER_CACHE_TTL_SECONDS`, default 600s) so repeated requests for
  the same city don't re-hit the weather API every time.

---

# 🔮 Future Enhancements

Updated to reflect what Phase 4 actually shipped — several items from
the original list are done now (marked below) rather than silently
left on a stale wishlist:

- ~~Live EV Charging Station Integration~~ — ✅ done (FEAT-2)
- ~~Real-time Battery Health Monitoring~~ — ✅ done (FEAT-1)
- ~~GPS-based Route Optimization~~ — ✅ real routing done (Phase 2/RT-4); full turn-by-turn optimization beyond single-route prediction is still open
- Deep Learning-based Predictions (neural network models beyond the current RF/GB/XGBoost/linear ensemble)
- Mobile Application Support

---

# 👨‍💻 Developed For

Cold Weather EV Range Prediction & Analysis using Artificial Intelligence and Machine Learning.

---
