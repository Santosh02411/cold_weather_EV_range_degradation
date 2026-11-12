# Design & Frontend Specs

## 1. Design System (as implemented in `frontend/static/css/style.css`)

**Theme:** Premium dark theme, "Inter" typeface (Google Fonts, weights
300–800).

**Palette (CSS custom properties, `:root`):**

| Token | Value | Use |
|---|---|---|
| `--bg-primary` | `#0a0e17` | Page background |
| `--bg-secondary` | `#111827` | Section background |
| `--bg-card` | `#1a2234` | Card surfaces |
| `--bg-card-hover` | `#1f2a40` | Card hover state |
| `--bg-glass` | `rgba(26, 34, 52, 0.8)` | Glassmorphism overlays |
| `--border-color` | `rgba(99, 140, 255, 0.15)` | Default borders |
| `--border-glow` | `rgba(99, 140, 255, 0.3)` | Focus/hover borders |
| `--text-primary` | `#e8ecf4` | Primary text |
| `--text-secondary` | `#8892a8` | Secondary text |
| `--text-muted` | `#5a6478` | Muted/caption text |

A cool blue accent (`rgba(99, 140, 255, ...)` family) is used throughout
for interactive/glow states, consistent with a "cold weather" visual
theme (frost/ice blue rather than a generic brand blue).

## 2. Page Inventory (from `frontend/templates/`)

| Area | Templates | Purpose |
|---|---|---|
| Auth | `auth/login.html`, `register.html`, `forgot_password.html`, `profile.html` | Account access & management |
| Dashboard | `dashboard/index.html` | Landing page after login; summary widgets |
| Vehicles | `vehicles/list.html`, `add.html`, `edit.html` | EV database CRUD |
| Weather | `weather/index.html` | Current conditions lookup |
| Predictions | `predictions/index.html` | Core degradation prediction UI |
| Trip | `trip/simulate.html` | Trip/charging-stop simulation |
| Charging | `charging/index.html` | Charging-specific estimates |
| Compare | `compare/index.html` | Side-by-side vehicle comparison |
| Datasets | `datasets/index.html` | Upload/manage training datasets |
| Reports | `reports/index.html` | PDF/CSV export |
| Admin | `admin/panel.html`, `analytics.html`, `users.html` | Admin-only: retraining, analytics, user management |

All pages extend `base.html`, which owns the shared sidebar/nav and
theme variables.

## 3. Phase 1 Frontend-Relevant Changes

Phase 1 was primarily a backend/ML rebuild, but two response-shape
changes affect any frontend code reading prediction results
(`predictions/index.html` and its JS):

1. **`confidence` is no longer always `0.85`** — it now varies per
   request (0.15–0.98 range). Any UI that visually represents
   confidence (e.g. a badge or progress bar) will now show real
   movement instead of a static number — this is a genuine UX
   improvement opportunity for Phase 2/3 (see `FEATURE_TICKET_LIST.md`,
   ticket UX-1: add a confidence indicator to the prediction result
   card, since the backend now actually provides a meaningful signal).
2. **New response fields**: `confidence_note`, `models_in_ensemble`,
   `physics_baseline_degradation_pct` are now present in the
   `get_prediction()` response (see `predict.py`). These are additive
   (existing fields are unchanged), so no existing template rendering
   breaks — but they're currently unused in the UI. Surfacing
   `physics_baseline_degradation_pct` next to the final prediction (as
   a "starting point vs. adjusted for your trip" comparison) is a good
   Phase 3 UX addition, tracked in `FEATURE_TICKET_LIST.md`.

## 4. Design Principles Carried Forward

- Dark theme is the default (`base.html` sets `data-theme="dark"`), with
  a working light theme available via `[data-theme="light"]` in
  `style.css` and a toggle (`toggleTheme()` in `main.js`, persisted via
  `localStorage`, wired to the header button in `base.html`) — so the
  README's "Dark / Light Mode" feature claim checks out; this was
  verified against the actual CSS/JS rather than assumed.
- Card-based layout (`--bg-card` / `--bg-card-hover`) for all data
  displays (predictions, comparisons, vehicle specs).
- Glassmorphism (`--bg-glass`) reserved for overlays/modals, not base
  page chrome.
