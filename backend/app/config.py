import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cold-weather-ev-secret-2024')
    _db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cold_weather_ev.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{_db_path}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY', 'demo')
    WEATHERAPI_KEY = os.environ.get('WEATHERAPI_KEY', 'demo')

    # Phase 3: LLM-grounded trip briefings / assistant (see services/llm.py).
    # Uses Google's free-tier Gemini API rather than a paid provider, so
    # this works entirely on a no-billing-required key from
    # https://aistudio.google.com/apikey. No key -> features fall back
    # to template-based text, same fail-soft-and-say-so pattern as the
    # weather demo fallback.
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')

    # SEC-2: CORS is permissive ('*') by default for local dev, matching
    # the original project's behavior. Set CORS_ALLOWED_ORIGINS to a
    # comma-separated list (e.g. "https://myapp.com,https://www.myapp.com")
    # before deploying anywhere public -- see docs/SECURITY_AND_ACCESS.md.
    _cors_env = os.environ.get('CORS_ALLOWED_ORIGINS', '*')
    CORS_ALLOWED_ORIGINS = '*' if _cors_env == '*' else [o.strip() for o in _cors_env.split(',') if o.strip()]

    # SEC-1: rate limiting (see Flask-Limiter init in __init__.py).
    # In-memory storage by default -- fine for a single-process deploy;
    # switch to Redis (RATELIMIT_STORAGE_URI=redis://...) for anything
    # running more than one worker process, since in-memory limits don't
    # share state across processes.
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day;50 per hour')
    RATELIMIT_AUTH = os.environ.get('RATELIMIT_AUTH', '10 per minute')
    RATELIMIT_PREDICT = os.environ.get('RATELIMIT_PREDICT', '30 per minute')
    RATELIMIT_AI = os.environ.get('RATELIMIT_AI', '15 per minute')

    # INFRA-3: weather response caching. 0 disables caching entirely.
    WEATHER_CACHE_TTL_SECONDS = int(os.environ.get('WEATHER_CACHE_TTL_SECONDS', '600'))

    # RT-4: routing provider. Defaults to OSRM's public demo server
    # (explicitly "light usage / evaluation only" per its own usage
    # policy -- see docs/TECHNICAL_ARCHITECTURE.md). Point OSRM_BASE_URL
    # at a self-hosted OSRM instance, or set ROUTING_PROVIDER=ors with an
    # ORS_API_KEY to use OpenRouteService's free tier instead, before any
    # real traffic.
    ROUTING_PROVIDER = os.environ.get('ROUTING_PROVIDER', 'osrm')
    OSRM_BASE_URL = os.environ.get('OSRM_BASE_URL', 'http://router.project-osrm.org')
    ORS_API_KEY = os.environ.get('ORS_API_KEY', '')

    # RT-6: full multi-waypoint weather sampling along a route, instead
    # of Phase 3's fixed 2-point (origin+destination) sampling. OFF by
    # default -- each extra waypoint is a real extra weather-API call,
    # and the free OpenWeatherMap tier this app defaults to has a real
    # daily cap. Only worth turning on once on a paid weather tier (or
    # for genuinely long routes where 2-point sampling is misleading).
    WEATHER_MULTI_WAYPOINT_ENABLED = os.environ.get('WEATHER_MULTI_WAYPOINT_ENABLED', 'false').lower() == 'true'
    WEATHER_WAYPOINT_INTERVAL_KM = int(os.environ.get('WEATHER_WAYPOINT_INTERVAL_KM', '150'))
    WEATHER_MAX_WAYPOINTS = int(os.environ.get('WEATHER_MAX_WAYPOINTS', '6'))

    # FEAT-2: Open Charge Map -- works keyless for light usage; set a
    # free key (https://openchargemap.org/site/develop/api) for higher
    # rate limits before any real deployment.
    OCM_API_KEY = os.environ.get('OCM_API_KEY', '')

    # Google / GitHub sign-in (Authlib). Both are None-safe -- the
    # "Sign in with Google/GitHub" buttons only appear when the
    # corresponding client ID is actually configured, rather than
    # showing a button that errors out on click. See README for how to
    # register an OAuth app with each provider.
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', '')

    # Profile picture uploads
    PROFILE_PICTURE_MAX_BYTES = int(os.environ.get('PROFILE_PICTURE_MAX_BYTES', str(5 * 1024 * 1024)))  # 5MB
    PROFILE_PICTURE_ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

    # Email verification gate: if true, unverified users see a banner
    # but can still use the app (soft gate) rather than being locked
    # out -- avoids bricking access for anyone testing this without
    # MAIL_USERNAME/PASSWORD configured. Set to a hard gate at the
    # route level later if a real deployment wants to enforce it.
    REQUIRE_EMAIL_VERIFICATION = os.environ.get('REQUIRE_EMAIL_VERIFICATION', 'false').lower() == 'true'

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME')

    # FEAT-3: cold-snap alerts. Requires MAIL_USERNAME/MAIL_PASSWORD to
    # actually send anything -- without them, the scheduler still runs
    # and logs what it WOULD have sent, rather than silently doing
    # nothing (see services/alerts.py).
    ALERTS_ENABLED = os.environ.get('ALERTS_ENABLED', 'true').lower() == 'true'
    ALERT_CHECK_INTERVAL_MINUTES = int(os.environ.get('ALERT_CHECK_INTERVAL_MINUTES', '60'))
    ALERT_COOLDOWN_HOURS = int(os.environ.get('ALERT_COOLDOWN_HOURS', '12'))

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload

    ML_MODELS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ml', 'saved_models')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'uploads')

    # Live Model Retraining / data-drift monitoring (see
    # services/drift_monitor.py, services/scheduler.py). Same pattern
    # as ALERTS_ENABLED above: this only controls whether the periodic
    # background CHECK runs at all. Whether a detected drift actually
    # triggers a retrain is a separate, runtime-toggleable admin
    # setting (services/drift_monitor.py's live-retrain state file) so
    # an admin can pause auto-retraining without restarting the app.
    # Off by default -- auto-retraining production models unattended
    # is a real operational decision, not something to default to on.
    LIVE_RETRAIN_ENABLED = os.environ.get('LIVE_RETRAIN_ENABLED', 'false').lower() == 'true'
    LIVE_RETRAIN_CHECK_INTERVAL_MINUTES = int(os.environ.get('LIVE_RETRAIN_CHECK_INTERVAL_MINUTES', '360'))
    LIVE_RETRAIN_DRIFT_PSI_THRESHOLD = float(os.environ.get('LIVE_RETRAIN_DRIFT_PSI_THRESHOLD', '0.25'))
    LIVE_RETRAIN_MIN_RECENT_PREDICTIONS = int(os.environ.get('LIVE_RETRAIN_MIN_RECENT_PREDICTIONS', '50'))

    # Trip Planning phase: Google Maps as an optional geo provider
    # (geocoding, routing with real traffic, elevation) alongside the
    # free defaults above -- opt-in, since Google's APIs are paid
    # beyond a free monthly credit (see services/geo.py's module
    # docstring for the full rationale). Setting ROUTING_PROVIDER to
    # 'google' (with a key) is the switch for routing; GEOCODE_PROVIDER
    # / ELEVATION_PROVIDER separately opt geocoding/elevation into
    # Google too, so a deployment can mix free + paid per capability.
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    GEOCODE_PROVIDER = os.environ.get('GEOCODE_PROVIDER', 'nominatim')
    ELEVATION_PROVIDER = os.environ.get('ELEVATION_PROVIDER', 'open_elevation')

    # Trip Planning: safety margin kept in reserve when planning multi-
    # stop/round trips and when computing a "safe" destination-
    # recommendation radius (see services/route_planning.py).
    TRIP_SAFETY_MARGIN_PCT = float(os.environ.get('TRIP_SAFETY_MARGIN_PCT', '15'))

    # Reports phase: Scheduled Reports periodic check, gated the same
    # way as the alerts/live-retrain jobs above. A schedule's own
    # frequency (daily/weekly/monthly, see models/report.py) controls
    # how often a given user's report actually goes out -- this
    # interval only controls how often the background job checks
    # whether anything is due, so it should stay small relative to the
    # shortest supported frequency (daily).
    SCHEDULED_REPORTS_ENABLED = os.environ.get('SCHEDULED_REPORTS_ENABLED', 'false').lower() == 'true'
    SCHEDULED_REPORTS_CHECK_INTERVAL_MINUTES = int(os.environ.get('SCHEDULED_REPORTS_CHECK_INTERVAL_MINUTES', '60'))

    CHARGING_REMINDERS_ENABLED = os.environ.get('CHARGING_REMINDERS_ENABLED', 'true').lower() == 'true'
    CHARGING_REMINDER_CHECK_INTERVAL_MINUTES = int(os.environ.get('CHARGING_REMINDER_CHECK_INTERVAL_MINUTES', '10'))
    MAINTENANCE_REMINDERS_ENABLED = os.environ.get('MAINTENANCE_REMINDERS_ENABLED', 'true').lower() == 'true'
    MAINTENANCE_REMINDER_CHECK_INTERVAL_MINUTES = int(os.environ.get('MAINTENANCE_REMINDER_CHECK_INTERVAL_MINUTES', '360'))
    MAINTENANCE_REMINDER_COOLDOWN_DAYS = int(os.environ.get('MAINTENANCE_REMINDER_COOLDOWN_DAYS', '14'))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    """INFRA-2: used by tests/test_api_smoke.py. In-memory SQLite,
    CSRF and rate limiting off (both would need extra fixture setup to
    test around otherwise, and neither is what these tests are for)."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    ALERTS_ENABLED = False  # don't start the background scheduler during tests
    LIVE_RETRAIN_ENABLED = False  # ditto -- don't start the drift-check scheduler during tests
    SCHEDULED_REPORTS_ENABLED = False  # ditto -- don't start the scheduled-reports scheduler during tests
    CHARGING_REMINDERS_ENABLED = False  # ditto -- don't start the charging-reminder scheduler during tests
    MAINTENANCE_REMINDERS_ENABLED = False  # ditto -- don't start the maintenance-reminder scheduler during tests

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
