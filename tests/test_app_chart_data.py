"""Flask + DB integration tests for services/app_chart_data.py. Same
skip-if-flask_sqlalchemy-missing convention as the other DB-backed
test files. The one network call (geocode_place, inside
geographic_weather_map_data) is mocked -- never executed against the
live internet in this sandbox, same convention as geo.py's own tests.
"""
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.ev_vehicle import EVVehicle
from app.models.prediction import Prediction
from app.models.battery_health import BatteryHealthRecord
from app.models.dataset import WeatherLog
from app.services import app_chart_data


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
        user = User(username='vizuser', email='vizuser@example.com')
        user.set_password('pass12345')
        vehicle = EVVehicle(
            model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=75,
            epa_range_km=400, vehicle_weight_kg=1900, battery_chemistry='NMC',
            charging_type='CCS', max_charging_power_kw=150, drivetrain='AWD', year=2024,
        )
        db.session.add_all([user, vehicle])
        db.session.commit()
        return user.id, vehicle.id


def _add_prediction(app, user_id, vehicle_id, days_ago, degradation=20.0, temp=-10):
    with app.app_context():
        p = Prediction(
            user_id=user_id, vehicle_id=vehicle_id, temperature_c=temp, humidity=50,
            wind_speed_kmh=10, precipitation='none', battery_percentage=80,
            vehicle_speed_kmh=70, hvac_usage=True, terrain_type='flat', battery_age_years=1,
            range_degradation_pct=degradation, predicted_range_km=300, energy_consumption_wh_km=190,
            charging_slowdown_pct=15.0, ml_model_used='random_forest', prediction_confidence=0.85,
        )
        p.created_at = datetime.utcnow() - timedelta(days=days_ago)
        db.session.add(p)
        db.session.commit()


# --- line_chart_data ---

def test_line_chart_data_valid_field(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_prediction(app, user_id, vehicle_id, 1, degradation=20)
    _add_prediction(app, user_id, vehicle_id, 0, degradation=25)
    with app.app_context():
        result = app_chart_data.line_chart_data(user_id, 'range_degradation_pct')
    assert result['available'] is True
    assert len(result['points']) == 2
    assert result['points'][0]['value'] == 20  # oldest first (chronological)


def test_line_chart_data_invalid_field(app, user_and_vehicle):
    user_id, _ = user_and_vehicle
    with app.app_context():
        result = app_chart_data.line_chart_data(user_id, 'bogus_field')
    assert result['available'] is False


def test_line_chart_data_no_predictions(app, user_and_vehicle):
    user_id, _ = user_and_vehicle
    with app.app_context():
        result = app_chart_data.line_chart_data(user_id, 'temperature_c')
    assert result['available'] is False


# --- geographic_weather_map_data ---

def test_geographic_weather_map_data_geocodes_and_colors(app):
    with app.app_context():
        db.session.add(WeatherLog(city='Chicago', country='US', temperature_c=-10, severity='severe'))
        db.session.add(WeatherLog(city='Miami', country='US', temperature_c=25, severity='mild'))
        db.session.commit()

        with patch('app.services.app_chart_data.geocode_place', return_value=(41.88, -87.63, 'Chicago, IL, US')):
            result = app_chart_data.geographic_weather_map_data()

    assert result['available'] is True
    assert result['n_points'] == 2
    chicago = next(p for p in result['points'] if p['city'] == 'Chicago')
    assert chicago['color'] == '#f87171'  # severe


def test_geographic_weather_map_data_caches_geocoding_per_city(app):
    with app.app_context():
        db.session.add(WeatherLog(city='Chicago', country='US', temperature_c=-10, severity='mild'))
        db.session.add(WeatherLog(city='Chicago', country='US', temperature_c=-12, severity='mild'))
        db.session.commit()

        with patch('app.services.app_chart_data.geocode_place', return_value=(41.88, -87.63, 'Chicago, IL, US')) as mock_geocode:
            app_chart_data.geographic_weather_map_data()
        assert mock_geocode.call_count == 1  # same city, geocoded once


def test_geographic_weather_map_data_no_logs(app):
    with app.app_context():
        result = app_chart_data.geographic_weather_map_data()
    assert result['available'] is False


def test_geographic_weather_map_data_skips_failed_geocodes(app):
    with app.app_context():
        db.session.add(WeatherLog(city='Nowhere', country='XX', temperature_c=0, severity='mild'))
        db.session.commit()
        with patch('app.services.app_chart_data.geocode_place', return_value=(None, None, None)):
            result = app_chart_data.geographic_weather_map_data()
    assert result['available'] is False
    assert result['n_points'] == 0


# --- battery_performance_chart_data ---

def test_battery_performance_chart_data_groups_by_vehicle(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    with app.app_context():
        db.session.add(BatteryHealthRecord(user_id=user_id, vehicle_id=vehicle_id, soh_pct=98.0))
        db.session.add(BatteryHealthRecord(user_id=user_id, vehicle_id=vehicle_id, soh_pct=97.0))
        db.session.commit()
        result = app_chart_data.battery_performance_chart_data(user_id)
    assert result['available'] is True
    assert len(result['series']) == 1
    assert len(result['series'][0]['points']) == 2


def test_battery_performance_chart_data_no_records(app, user_and_vehicle):
    user_id, _ = user_and_vehicle
    with app.app_context():
        result = app_chart_data.battery_performance_chart_data(user_id)
    assert result['available'] is False


def test_battery_performance_chart_data_filters_by_vehicle_id(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    with app.app_context():
        other_vehicle = EVVehicle(
            model_name='Other', manufacturer='OtherCo', battery_capacity_kwh=60,
            epa_range_km=300, vehicle_weight_kg=1700, battery_chemistry='LFP',
            charging_type='CCS', max_charging_power_kw=100, drivetrain='FWD', year=2023,
        )
        db.session.add(other_vehicle)
        db.session.commit()
        other_vehicle_id = other_vehicle.id

        db.session.add(BatteryHealthRecord(user_id=user_id, vehicle_id=vehicle_id, soh_pct=98.0))
        db.session.add(BatteryHealthRecord(user_id=user_id, vehicle_id=other_vehicle_id, soh_pct=95.0))
        db.session.commit()

        result = app_chart_data.battery_performance_chart_data(user_id, vehicle_id=vehicle_id)
    assert len(result['series']) == 1
    assert result['series'][0]['vehicle_id'] == vehicle_id


# --- prediction_timeline_data ---

def test_prediction_timeline_data_ordered_most_recent_first(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_prediction(app, user_id, vehicle_id, 2, degradation=10)
    _add_prediction(app, user_id, vehicle_id, 0, degradation=30)
    with app.app_context():
        result = app_chart_data.prediction_timeline_data(user_id)
    assert result['available'] is True
    assert result['entries'][0]['degradation_pct'] == 30  # most recent first


def test_prediction_timeline_data_no_predictions(app, user_and_vehicle):
    user_id, _ = user_and_vehicle
    with app.app_context():
        result = app_chart_data.prediction_timeline_data(user_id)
    assert result['available'] is False
