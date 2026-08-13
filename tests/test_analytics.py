"""Flask + DB integration tests for the Analytics Dashboard: both the
services/analytics.py functions directly (seeded data, precise
assertions) and the /dashboard/api/analytics/* endpoints (auth gating
+ end-to-end shape). Same skip-if-flask_sqlalchemy-missing convention
as the other DB-backed test files.
"""
import pytest
from datetime import datetime, timedelta

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.ev_vehicle import EVVehicle
from app.models.prediction import Prediction, TripSimulation
from app.models.battery_health import BatteryHealthRecord
from app.models.charging_reservation import ChargingReservation
from app.models.vehicle_interactions import FavoriteVehicle
from app.services import analytics


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_and_vehicle(app):
    with app.app_context():
        user = User(username='analyticsuser', email='analytics@example.com')
        user.set_password('pass12345')
        vehicle = EVVehicle(
            model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=75,
            epa_range_km=400, vehicle_weight_kg=1900, battery_chemistry='NMC',
            charging_type='CCS', max_charging_power_kw=150, drivetrain='AWD', year=2024,
        )
        db.session.add_all([user, vehicle])
        db.session.commit()
        return user.id, vehicle.id


@pytest.fixture
def auth_client(client, app, user_and_vehicle):
    client.post('/login', data={'username': 'analyticsuser', 'password': 'pass12345'})
    return client


def _add_prediction(app, user_id, vehicle_id, days_ago, temp, degradation, model='random_forest', confidence=0.85, energy=180):
    with app.app_context():
        p = Prediction(
            user_id=user_id, vehicle_id=vehicle_id, temperature_c=temp, humidity=50,
            wind_speed_kmh=10, precipitation='none', battery_percentage=80,
            vehicle_speed_kmh=70, hvac_usage=True, terrain_type='flat', battery_age_years=1,
            range_degradation_pct=degradation, predicted_range_km=300, energy_consumption_wh_km=energy,
            charging_slowdown_pct=15.0, ml_model_used=model, prediction_confidence=confidence,
        )
        p.created_at = datetime.utcnow() - timedelta(days=days_ago)
        db.session.add(p)
        db.session.commit()


def _add_trip(app, user_id, vehicle_id, days_ago, energy_kwh):
    with app.app_context():
        t = TripSimulation(
            user_id=user_id, vehicle_id=vehicle_id, source_location='A', destination='B',
            distance_km=100, temperature_c=-5, speed_kmh=80, heater_usage=True,
            estimated_energy_kwh=energy_kwh,
        )
        t.created_at = datetime.utcnow() - timedelta(days=days_ago)
        db.session.add(t)
        db.session.commit()


# --- services/analytics.py direct tests ---

def test_activity_analytics_buckets_by_day(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_prediction(app, user_id, vehicle_id, days_ago=0, temp=-10, degradation=20)
    _add_prediction(app, user_id, vehicle_id, days_ago=0, temp=-12, degradation=22)
    _add_prediction(app, user_id, vehicle_id, days_ago=1, temp=5, degradation=8)

    with app.app_context():
        result = analytics.activity_analytics(user_id, period='daily')
    assert result['total_predictions'] == 3
    assert len(result['series']) == 2
    today_bucket = result['series'][-1]
    assert today_bucket['prediction_count'] == 2
    assert today_bucket['avg_degradation_pct'] == 21.0


def test_activity_analytics_invalid_period_raises(app, user_and_vehicle):
    user_id, _ = user_and_vehicle
    with app.app_context():
        with pytest.raises(ValueError):
            analytics.activity_analytics(user_id, period='yearly')


def test_battery_health_trends_needs_two_readings(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    with app.app_context():
        db.session.add(BatteryHealthRecord(user_id=user_id, vehicle_id=vehicle_id, soh_pct=98.0))
        db.session.commit()
        result = analytics.battery_health_trends(user_id)
    assert result['vehicles'][0]['num_readings'] == 1
    assert result['vehicles'][0]['trend'] is None


def test_battery_health_trends_computes_slope_with_two_readings(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    with app.app_context():
        old = BatteryHealthRecord(user_id=user_id, vehicle_id=vehicle_id, soh_pct=100.0)
        old.recorded_at = datetime.utcnow() - timedelta(days=365)
        recent = BatteryHealthRecord(user_id=user_id, vehicle_id=vehicle_id, soh_pct=97.0)
        recent.recorded_at = datetime.utcnow()
        db.session.add_all([old, recent])
        db.session.commit()
        result = analytics.battery_health_trends(user_id)
    trend = result['vehicles'][0]['trend']
    assert trend is not None
    assert trend['slope_pct_per_year'] < 0  # declining


def test_weather_impact_trends_correlation_and_buckets(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_prediction(app, user_id, vehicle_id, 0, temp=-20, degradation=35)
    _add_prediction(app, user_id, vehicle_id, 0, temp=25, degradation=2)
    with app.app_context():
        result = analytics.weather_impact_trends(user_id, period='daily')
    assert result['correlation'] is not None
    assert result['correlation'] < 0  # colder -> more degradation
    extreme_cold = next(b for b in result['temperature_buckets'] if 'Extreme Cold' in b['label'])
    assert extreme_cold['count'] == 1


def test_weather_impact_trends_empty_when_no_predictions(app, user_and_vehicle):
    user_id, _ = user_and_vehicle
    with app.app_context():
        result = analytics.weather_impact_trends(user_id)
    assert result['series'] == []
    assert result['correlation'] is None


def test_energy_consumption_trends(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_prediction(app, user_id, vehicle_id, 0, temp=-10, degradation=20, energy=220)
    _add_prediction(app, user_id, vehicle_id, 0, temp=-10, degradation=20, energy=200)
    with app.app_context():
        result = analytics.energy_consumption_trends(user_id, period='daily')
    assert result['series'][-1]['avg_energy_wh_km'] == 210.0


def test_charging_statistics_aggregates_reservations_and_trip_energy(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    with app.app_context():
        db.session.add(ChargingReservation(user_id=user_id, vehicle_id=vehicle_id, station_name='X',
                                            reserved_start=datetime.utcnow() + timedelta(days=1), duration_minutes=30))
        db.session.commit()
    _add_trip(app, user_id, vehicle_id, 0, energy_kwh=40)
    _add_trip(app, user_id, vehicle_id, 0, energy_kwh=20)
    with app.app_context():
        result = analytics.charging_statistics(user_id)
    assert result['reservations']['upcoming'] == 1
    assert result['total_logged_trip_energy_kwh'] == 60.0
    assert result['estimated_total_charging_cost']['estimated_cost_usd'] > 0


def test_vehicle_ranking_respects_min_predictions_threshold(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_prediction(app, user_id, vehicle_id, 0, temp=-10, degradation=20)  # only 1 prediction
    with app.app_context():
        result = analytics.vehicle_ranking(min_predictions=3)
    # popularity always includes it (no threshold)
    assert any(v['vehicle_id'] == vehicle_id for v in result['most_predicted'])
    # resilience/efficiency require >= 3 predictions -- shouldn't appear yet
    assert not any(v['vehicle_id'] == vehicle_id for v in result['best_cold_weather_resilience'])


def test_vehicle_ranking_includes_favorites(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    with app.app_context():
        db.session.add(FavoriteVehicle(user_id=user_id, vehicle_id=vehicle_id))
        db.session.commit()
        result = analytics.vehicle_ranking()
    assert result['most_favorited'][0]['vehicle_id'] == vehicle_id
    assert result['most_favorited'][0]['favorite_count'] == 1


def test_cost_analytics_home_cheaper_than_public(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_trip(app, user_id, vehicle_id, 0, energy_kwh=50)
    with app.app_context():
        result = analytics.cost_analytics(user_id, period='daily')
    assert result['total_estimated_cost_if_home_usd'] < result['total_estimated_cost_if_public_usd']
    assert result['total_energy_kwh'] == 50.0


def test_user_analytics_streak_and_totals(app, user_and_vehicle):
    user_id, vehicle_id = user_and_vehicle
    _add_prediction(app, user_id, vehicle_id, 0, temp=-10, degradation=20)
    _add_prediction(app, user_id, vehicle_id, 1, temp=-5, degradation=15)
    with app.app_context():
        result = analytics.user_analytics(user_id)
    assert result['total_predictions'] == 2
    assert result['current_activity_streak_days'] == 2
    assert result['most_used_model'] == 'random_forest'


def test_user_analytics_unknown_user_returns_none(app):
    with app.app_context():
        assert analytics.user_analytics(99999) is None


# --- API endpoint tests ---

def test_analytics_page_requires_login(client):
    resp = client.get('/dashboard/analytics')
    assert resp.status_code in (302, 401)


def test_analytics_page_loads(auth_client):
    resp = auth_client.get('/dashboard/analytics')
    assert resp.status_code == 200


def test_activity_endpoint_invalid_period_400s(auth_client):
    resp = auth_client.get('/dashboard/api/analytics/activity?period=bogus')
    assert resp.status_code == 400


def test_activity_endpoint_default_period(auth_client):
    resp = auth_client.get('/dashboard/api/analytics/activity')
    assert resp.status_code == 200
    assert resp.get_json()['period'] == 'daily'


def test_battery_health_endpoint(auth_client):
    resp = auth_client.get('/dashboard/api/analytics/battery-health')
    assert resp.status_code == 200
    assert 'vehicles' in resp.get_json()


def test_weather_impact_endpoint(auth_client):
    resp = auth_client.get('/dashboard/api/analytics/weather-impact?period=monthly')
    assert resp.status_code == 200


def test_energy_endpoint(auth_client):
    resp = auth_client.get('/dashboard/api/analytics/energy?period=weekly')
    assert resp.status_code == 200


def test_charging_endpoint(auth_client):
    resp = auth_client.get('/dashboard/api/analytics/charging')
    assert resp.status_code == 200
    assert 'reservations' in resp.get_json()


def test_vehicle_ranking_endpoint(auth_client):
    resp = auth_client.get('/dashboard/api/analytics/vehicle-ranking')
    assert resp.status_code == 200
    assert 'most_predicted' in resp.get_json()


def test_cost_endpoint(auth_client):
    resp = auth_client.get('/dashboard/api/analytics/cost')
    assert resp.status_code == 200


def test_user_endpoint(auth_client):
    resp = auth_client.get('/dashboard/api/analytics/user')
    assert resp.status_code == 200
    assert resp.get_json()['username'] == 'analyticsuser'
