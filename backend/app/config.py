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

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload

    ML_MODELS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ml', 'saved_models')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'uploads')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
