from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from .config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

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
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    CORS(app)
    csrf.init_app(app)

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

    # Create tables
    with app.app_context():
        from .models import user, ev_vehicle, prediction, dataset
        db.create_all()

    return app
