"""DB-integration tests for services/driving_style.py. Needs
flask_sqlalchemy (unlike the pure-logic services tests) since it
queries the Prediction/TripSimulation models directly -- same
skip-if-missing convention as test_api_smoke.py / test_admin_ml_api.py.
"""
import pytest

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.ev_vehicle import EVVehicle
from app.models.prediction import Prediction, TripSimulation
from app.services.driving_style import analyze_driving_style, MIN_SAMPLES_FOR_CLASSIFICATION


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def user_and_vehicle(app):
    with app.app_context():
        user = User(username='driver1', email='driver1@example.com')
        user.set_password('pass12345')
        vehicle = EVVehicle(
            model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=75,
            epa_range_km=400, vehicle_weight_kg=1900, battery_chemistry='NMC',
            charging_type='CCS', max_charging_power_kw=150, drivetrain='AWD', year=2024,
        )
        db.session.add_all([user, vehicle])
        db.session.commit()
        return user.id, vehicle.id


def _add_predictions(app, user_id, vehicle_id, speeds):
    with app.app_context():
        for s in speeds:
            db.session.add(Prediction(
                user_id=user_id, vehicle_id=vehicle_id, temperature_c=0, humidity=50,
                wind_speed_kmh=10, precipitation='none', battery_percentage=80,
                vehicle_speed_kmh=s, hvac_usage=True, terrain_type='flat', battery_age_years=1,
                range_degradation_pct=15.0, predicted_range_km=300, ml_model_used='random_forest',
            ))
        db.session.commit()


def test_insufficient_data_returns_status(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    result = analyze_driving_style(user_id)
    assert result['status'] == 'insufficient_data'
    assert result['n_samples'] == 0


def test_eco_driving_style_classified_from_low_speeds(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_predictions(app, user_id, vehicle_id, [40, 42, 38, 45, 41, 39])
    with app.app_context():
        result = analyze_driving_style(user_id)
    assert result['status'] == 'ok'
    assert result['driving_style'] == 'eco'
    assert result['consumption_multiplier'] < 1.0


def test_aggressive_driving_style_classified_from_high_speeds(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_predictions(app, user_id, vehicle_id, [110, 115, 120, 105, 112, 118])
    with app.app_context():
        result = analyze_driving_style(user_id)
    assert result['status'] == 'ok'
    assert result['driving_style'] == 'aggressive'
    assert result['consumption_multiplier'] > 1.0


def test_moderate_driving_style_classified_from_mid_speeds(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_predictions(app, user_id, vehicle_id, [65, 70, 68, 72, 66, 71])
    with app.app_context():
        result = analyze_driving_style(user_id)
    assert result['status'] == 'ok'
    assert result['driving_style'] == 'moderate'
    assert result['consumption_multiplier'] == 1.0


def test_exactly_min_samples_still_classifies(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_predictions(app, user_id, vehicle_id, [70] * MIN_SAMPLES_FOR_CLASSIFICATION)
    with app.app_context():
        result = analyze_driving_style(user_id)
    assert result['status'] == 'ok'
    assert result['n_samples'] == MIN_SAMPLES_FOR_CLASSIFICATION


def test_only_counts_requesting_users_own_history(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    with app.app_context():
        other = User(username='driver2', email='driver2@example.com')
        other.set_password('pass12345')
        db.session.add(other)
        db.session.commit()
        other_id = other.id
    _add_predictions(app, other_id, vehicle_id, [120, 125, 118, 122, 130, 119])
    with app.app_context():
        result = analyze_driving_style(user_id)
    assert result['status'] == 'insufficient_data'
