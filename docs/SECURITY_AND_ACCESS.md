# Security & Access Model

## 1. Authentication

- Flask-Login manages session-based authentication (`login_manager` in
  `backend/app/__init__.py`).
- Passwords are hashed at rest (see `backend/app/models/user.py` for the
  hashing scheme in use) — never stored or logged in plaintext.
- `login_manager.login_view = 'auth.login'` — unauthenticated access to
  protected routes redirects to login rather than erroring.

## 2. Authorization / Roles

- Two roles: `admin` and standard user. Admin-only routes (retrain
  models, view analytics, manage datasets) are gated with an
  `@admin_required` decorator in `backend/app/api/admin.py`.
- Default seeded credentials (`admin` / `admin123`, `demo` / `demo123`
  from `seed_data.py`) are for **local development only**. These MUST be
  changed (or the seed accounts removed/disabled) before any public or
  production deployment — this is a known v1 limitation carried into
  Phase 1 and not yet fixed; see §5.

## 3. Secrets Management

- All secrets (`SECRET_KEY`, `OPENWEATHERMAP_API_KEY`, `WEATHERAPI_KEY`,
  `MAIL_USERNAME`/`MAIL_PASSWORD`, `DATABASE_URL`) are read from
  environment variables via `python-dotenv`, never hardcoded in source.
- `.env` is gitignored (see repository root `.gitignore`). `.env.example`
  documents the expected variable names with placeholder values only —
  it is safe to commit and intentionally contains no real credentials.
- `config.py`'s `SECRET_KEY` default (`'cold-weather-ev-secret-2024'`) is
  a **local-dev-only fallback**. Any real/public deployment MUST set a
  real `SECRET_KEY` via `.env` — Flask's session signing and CSRF
  protection are only as strong as this value.
- See README "Set up API keys" section for exactly how to obtain and
  configure each key.

## 4. Web-Layer Protections

- **CSRF:** `Flask-WTF`'s `CSRFProtect` is initialized globally
  (`csrf.init_app(app)`), protecting all state-changing form
  submissions.
- **CORS:** `Flask-CORS`'s `CORS(app)` is applied with default
  (permissive) settings. This is acceptable for local development but
  is a known v1 limitation for production — see §5.
- **File uploads:** `MAX_CONTENT_LENGTH` caps uploads at 50MB
  (`config.py`). Uploaded datasets go to `UPLOAD_FOLDER`
  (`data/uploads/`, gitignored) — see `FEATURE_TICKET_LIST.md` for
  hardening this further (content-type validation, virus scanning) as a
  future ticket.

## 5. Known v1 Limitations (carried into Phase 1, not yet resolved)

These are documented honestly rather than silently left out, per this
project's approach to accuracy claims in general:

1. **Permissive CORS** — `CORS(app)` with no explicit origin allowlist.
   Fine for local dev; must be scoped to specific origins before any
   public deployment.
2. **Default seeded admin/demo credentials** — must be rotated/disabled
   before production use.
3. **No rate limiting** — API endpoints (including auth) have no
   throttling. A future ticket (see `FEATURE_TICKET_LIST.md`, SEC-1)
   covers adding `Flask-Limiter`.
4. **No API key rotation/expiry tracking** — `OPENWEATHERMAP_API_KEY`
   etc. are static env values with no rotation reminder built in.
5. **SQLite for default local dev** — fine for development; `DATABASE_URL`
   supports switching to MySQL/Postgres for anything beyond that, but no
   connection-level encryption is enforced by the app itself (relies on
   the deployment environment).
6. **No distributed lock on model retraining** — see
   `TECHNICAL_ARCHITECTURE.md` §3 for the current (acceptable for
   single-process deployment) behavior if two admins retrain
   concurrently.
7. **Model files are not signed/verified** — `joblib.load()` on the
   `saved_models/*.pkl` files trusts the file contents. This is fine
   when models are only ever produced by this project's own `train.py`
   and never accepted from an untrusted upload path, but if a future
   feature allows uploading pretrained models, this needs
   `joblib.load` output validation before it ships (flagged for
   awareness, not currently in scope since no such upload path exists).

## 6. Data Sensitivity

- User accounts, saved predictions, and trip simulations are considered
  personal data tied to a `user_id`. No data is currently sent to any
  third party other than the configured weather API (which only
  receives a location, not user identity).
- No payment, government ID, or other high-sensitivity data is
  collected by this application.
