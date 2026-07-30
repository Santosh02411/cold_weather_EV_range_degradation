# ❄️ Cold Weather Range Degradation Modeler for Electric Vehicles

An AI & Machine Learning powered web application that predicts Electric Vehicle (EV) range degradation in cold weather conditions using advanced machine learning algorithms and real-time weather analysis.

> **Phase 1, 2 & 3 status (current):** the ML core was rebuilt to be
> grounded in real, cited, published cold-weather EV studies instead of
> arbitrary made-up thresholds (Phase 1); the manual terrain dropdown and
> single-point trip input were upgraded to use real geocoding, routing,
> and elevation data, plus a visible live-vs-demo weather indicator
> (Phase 2); and real LLM involvement was added — grounded trip
> briefings, a Q&A assistant, and anomaly detection, all built on the
> app's own computed numbers rather than free generation (Phase 3). Full
> write-up, design decisions, and a phase-by-phase build log (including
> real bugs hit and fixed, and what could/couldn't be verified without
> live network access) live in [`/docs`](./docs) — see especially
> [`docs/TECHNICAL_ARCHITECTURE.md`](./docs/TECHNICAL_ARCHITECTURE.md) and
> [`docs/PROJECT_WORKFLOW.md`](./docs/PROJECT_WORKFLOW.md).
>
> ⚠️ **Before relying on this in production:** the live HTTP calls added
> in Phase 2 (`backend/app/services/geo.py`) and Phase 3
> (`backend/app/services/llm.py`) were written against each provider's
> documented API but could not be executed in the sandbox this was built
> in (no outbound network there). Run them for real and confirm before
> shipping — see `docs/PROJECT_WORKFLOW.md`'s Phase 2/3 sections for
> exactly what is and isn't verified yet.

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

## 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

## 3️⃣ Seed the Database

```bash
cd backend
python seed_data.py
```

## 4️⃣ Set up API keys (optional but recommended)

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
- `ANTHROPIC_API_KEY` — powers Phase 3's AI trip briefings, Q&A, and anomaly narration (see below). Without it, these features fall back to template-generated text instead of failing.
- `MAIL_USERNAME` / `MAIL_PASSWORD` — only needed if you enable email features (e.g. password reset); for Gmail, use an [App Password](https://myaccount.google.com/apppasswords), not your real password
- `SECRET_KEY` — set this to a long random string in any real/public deployment; the default in `config.py` is fine for local dev only

### Getting an Anthropic API key (for Phase 3's AI features)

1. Create an account at https://console.anthropic.com
2. Go to **API Keys** in the console and create a new key
3. Add it to `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-real-key-here
   ```
4. (Optional) `ANTHROPIC_MODEL` defaults to `claude-sonnet-5` — override it in `.env` if you want a different model. Full docs: https://docs.claude.com/en/api/overview

This key is billed per API call by Anthropic (separate from any claude.ai
subscription) — see https://docs.claude.com for current pricing before
enabling this in a public deployment with real traffic.

## 5️⃣ (Optional) Train the ML models explicitly

Trained model files (`backend/app/ml/saved_models/`) are gitignored —
they're regenerated automatically on first prediction request if
missing, but running this explicitly first shows you the real
train/validation/test metrics and the real-world calibration check:

```bash
cd backend/app/ml
python train.py
```

## 6️⃣ Run the Application

```bash
python run.py
```

---

# 🌐 Application URL

Open in browser:

```bash
http://127.0.0.1:5000
```

---

# 🔑 Default Credentials

| Role  | Username | Password |
| ----- | -------- | -------- |
| Admin | admin    | admin123 |
| User  | demo     | demo123  |

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
  natural-language summary of a saved prediction, written by Claude but
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

**No `ANTHROPIC_API_KEY` configured?** All three features still work —
they fall back to template-generated text built from the same
underlying data, clearly labeled `"source": "template"` in the API
response, rather than failing. See "Getting an Anthropic API key" above
to enable the LLM-generated version.

# 🔮 Future Enhancements

- Live EV Charging Station Integration
- Deep Learning-based Predictions
- Mobile Application Support
- GPS-based Route Optimization
- Real-time Battery Health Monitoring

---

# 👨‍💻 Developed For

Cold Weather EV Range Prediction & Analysis using Artificial Intelligence and Machine Learning.

---
