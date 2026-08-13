from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from .config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()
migrate = Migrate()
oauth = OAuth()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'frontend', 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'frontend', 'static')
    )
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    # SEC-2: CORS scoped to CORS_ALLOWED_ORIGINS (defaults to '*' for
    # local dev, matching the original project -- set a real origin list
    # via the env var before any public deployment; see
    # docs/SECURITY_AND_ACCESS.md).
    cors_origins = app.config.get('CORS_ALLOWED_ORIGINS', '*')
    if cors_origins == '*':
        app.logger.warning(
            "CORS_ALLOWED_ORIGINS not set -- allowing all origins ('*'). "
            "This is fine for local dev but must be scoped to real "
            "origin(s) before any public deployment."
        )
    CORS(app, origins=cors_origins, supports_credentials=True)

    csrf.init_app(app)

    # SEC-1: rate limiting. In-memory by default (see RATELIMIT_STORAGE_URI
    # in config.py for switching to Redis under multiple worker processes).
    app.config.setdefault('RATELIMIT_STORAGE_URI', 'memory://')
    limiter.init_app(app)

    # FEAT-3: was declared as a dependency (Flask-Mail in
    # requirements.txt) but never actually initialized -- wiring it now
    # so alert emails (and any future email feature, e.g. password
    # reset) can actually be sent.
    mail.init_app(app)

    # OAuth (Google / GitHub sign-in). Each provider is only registered
    # if its client ID is actually set -- Authlib errors on `authorize_redirect`
    # for an unregistered/misconfigured provider, so auth.py checks
    # `oauth.google`/`oauth.github` truthiness before rendering the
    # sign-in buttons, keeping "not configured" a clean no-button state
    # rather than a broken-button state.
    oauth.init_app(app)
    if app.config.get('GOOGLE_CLIENT_ID'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
        )
    if app.config.get('GITHUB_CLIENT_ID'):
        oauth.register(
            name='github',
            client_id=app.config['GITHUB_CLIENT_ID'],
            client_secret=app.config['GITHUB_CLIENT_SECRET'],
            access_token_url='https://github.com/login/oauth/access_token',
            authorize_url='https://github.com/login/oauth/authorize',
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'read:user user:email'},
        )

    # Ensure directories exist
    os.makedirs(app.config.get('ML_MODELS_PATH', 'ml/saved_models'), exist_ok=True)
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'data/uploads'), exist_ok=True)

    # Register blueprints
    from .api.auth import auth_bp
    from .api.vehicles import vehicles_bp
    from .api.weather import weather_bp
    from .api.predictions import predictions_bp
    from .api.trip import trip_bp
    from .api.charging import charging_bp
    from .api.recommendations import recommendations_bp
    from .api.compare import compare_bp
    from .api.datasets import datasets_bp
    from .api.reports import reports_bp
    from .api.admin import admin_bp
    from .api.dashboard import dashboard_bp
    from .api.community import community_bp
    from .api.alerts import alerts_bp
    from .api.explain import explain_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(vehicles_bp, url_prefix='/vehicles')
    app.register_blueprint(weather_bp, url_prefix='/weather')
    app.register_blueprint(predictions_bp, url_prefix='/predictions')
    app.register_blueprint(trip_bp, url_prefix='/trip')
    app.register_blueprint(charging_bp, url_prefix='/charging')
    app.register_blueprint(recommendations_bp, url_prefix='/recommendations')
    app.register_blueprint(compare_bp, url_prefix='/compare')
    app.register_blueprint(datasets_bp, url_prefix='/datasets')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(community_bp, url_prefix='/community')
    app.register_blueprint(alerts_bp, url_prefix='/alerts')
    app.register_blueprint(explain_bp, url_prefix='/explain')

    # Create tables. Coexists with Flask-Migrate (INFRA-1) deliberately:
    # create_all() is a convenience for a brand-new local dev DB (never
    # overwrites or alters an existing table), while real schema CHANGES
    # to an existing database should go through `flask db migrate` /
    # `flask db upgrade` instead -- see README "Database Migrations" for
    # the actual commands. create_all() staying here means a fresh clone
    # still works with zero migration commands; it just isn't how you
    # evolve a database that already has real data in it.
    with app.app_context():
        from .models import user, ev_vehicle, prediction, dataset, battery_health, alert_subscription, session as user_session_model, vehicle_interactions, trip_plan, charging_reservation
        db.create_all()

    # Real session revocation: check the current request's session
    # cookie against the server-side UserSession table (see
    # services/session_manager.py) and force-logout if it was
    # explicitly revoked (e.g. "log out this device" from the sessions
    # page). Runs on every request, but is a single indexed lookup by
    # session_token, not a meaningful cost.
    @app.before_request
    def _check_session_revocation():
        from flask_login import current_user, logout_user
        if current_user.is_authenticated:
            from .services.session_manager import validate_current_session
            if not validate_current_session():
                logout_user()

    # FEAT-3: start the cold-snap alert scheduler (no-op if
    # ALERTS_ENABLED=false or apscheduler isn't installed -- see
    # services/scheduler.py for both guards).
    from .services.scheduler import init_scheduler
    init_scheduler(app)

    return app
