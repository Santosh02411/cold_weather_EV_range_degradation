"""User Dashboard feature tests -- Saved Predictions (bookmarking),
Recent Activity feed, and the new page routes added for the
Personalized Dashboard / Prediction History / Saved Vehicles /
Favorite Vehicles / Usage Statistics sidebar section.

Same rationale and fixture pattern as test_api_smoke.py: these need a
real Flask app + DB, so they're skipped cleanly (not an error) in any
environment without flask_sqlalchemy installed, via
pytest.importorskip below.
"""
import pytest

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.ev_vehicle import EVVehicle
from app.models.prediction import Prediction, SavedPrediction


@pytest.fixture
def app():
    app = create_app('testing')
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        RATELIMIT_ENABLED=False,
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in_client(client, app):
    with app.app_context():
        user = User(username='testuser', email='test@example.com', role='user')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
    client.post('/login', data={'username': 'testuser', 'password': 'testpass123'})
    return client


def _make_vehicle():
    vehicle = EVVehicle(
        model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=75,
        epa_range_km=400, vehicle_weight_kg=1900, battery_chemistry='NMC',
        charging_type='CCS', max_charging_power_kw=150, drivetrain='AWD', year=2024,
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle.id


def _make_prediction(user_id, vehicle_id, temperature_c=-10):
    prediction = Prediction(
        user_id=user_id, vehicle_id=vehicle_id, temperature_c=temperature_c,
        range_degradation_pct=20.0, predicted_range_km=300.0,
        energy_consumption_wh_km=180.0, ml_model_used='random_forest',
        prediction_confidence=0.8,
    )
    db.session.add(prediction)
    db.session.commit()
    return prediction.id


def _login_user_id(app):
    with app.app_context():
        return User.query.filter_by(username='testuser').first().id


# ─────────────────────── Saved Predictions (bookmarking) ───────────────────────

def test_save_prediction_requires_login(client):
    resp = client.post('/predictions/api/1/save')
    assert resp.status_code in (302, 401)


def test_save_and_list_saved_prediction(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()
        user_id = _login_user_id(app)
        prediction_id = _make_prediction(user_id, vehicle_id)

    resp = logged_in_client.post(f'/predictions/api/{prediction_id}/save')
    assert resp.status_code == 200
    assert resp.get_json()['saved'] is True

    resp = logged_in_client.get('/predictions/api/saved')
    assert resp.status_code == 200
    saved = resp.get_json()
    assert len(saved) == 1
    assert saved[0]['id'] == prediction_id
    assert saved[0]['is_saved'] is True
    assert saved[0]['vehicle']['manufacturer'] == 'TestCo'


def test_save_prediction_is_idempotent(app, logged_in_client):
    """Saving the same prediction twice shouldn't create two rows --
    the UniqueConstraint on (user_id, prediction_id) backs this, but
    the endpoint itself also guards it before ever hitting the DB."""
    with app.app_context():
        vehicle_id = _make_vehicle()
        user_id = _login_user_id(app)
        prediction_id = _make_prediction(user_id, vehicle_id)

    logged_in_client.post(f'/predictions/api/{prediction_id}/save')
    logged_in_client.post(f'/predictions/api/{prediction_id}/save')

    with app.app_context():
        assert SavedPrediction.query.filter_by(prediction_id=prediction_id).count() == 1


def test_unsave_prediction(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()
        user_id = _login_user_id(app)
        prediction_id = _make_prediction(user_id, vehicle_id)

    logged_in_client.post(f'/predictions/api/{prediction_id}/save')
    resp = logged_in_client.delete(f'/predictions/api/{prediction_id}/save')
    assert resp.status_code == 200
    assert resp.get_json()['saved'] is False

    resp = logged_in_client.get('/predictions/api/saved')
    assert resp.get_json() == []


def test_cannot_save_another_users_prediction(app, logged_in_client):
    """_load_owned_prediction() ownership check (already used by the
    briefing/ask/anomaly endpoints) applies to /save too."""
    with app.app_context():
        vehicle_id = _make_vehicle()
        other_user = User(username='otheruser', email='other@example.com', role='user')
        other_user.set_password('pass12345')
        db.session.add(other_user)
        db.session.commit()
        prediction_id = _make_prediction(other_user.id, vehicle_id)

    resp = logged_in_client.post(f'/predictions/api/{prediction_id}/save')
    assert resp.status_code == 404


def test_history_includes_is_saved_flag(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()
        user_id = _login_user_id(app)
        prediction_id = _make_prediction(user_id, vehicle_id)

    logged_in_client.post(f'/predictions/api/{prediction_id}/save')
    resp = logged_in_client.get('/predictions/api/history')
    data = resp.get_json()
    assert data[0]['is_saved'] is True
    assert data[0]['vehicle']['manufacturer'] == 'TestCo'


# ─────────────────────── Recent Activity feed ───────────────────────

def test_activity_feed_requires_login(client):
    resp = client.get('/dashboard/api/activity')
    assert resp.status_code in (302, 401)


def test_activity_feed_merges_predictions_and_saves(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()
        user_id = _login_user_id(app)
        prediction_id = _make_prediction(user_id, vehicle_id)

    logged_in_client.post(f'/predictions/api/{prediction_id}/save')

    resp = logged_in_client.get('/dashboard/api/activity')
    assert resp.status_code == 200
    items = resp.get_json()
    types = {i['type'] for i in items}
    assert 'prediction' in types
    assert 'saved_prediction' in types
    # Reverse-chronological: newest first.
    timestamps = [i['timestamp'] for i in items]
    assert timestamps == sorted(timestamps, reverse=True)


def test_activity_feed_empty_for_new_user(app, logged_in_client):
    resp = logged_in_client.get('/dashboard/api/activity')
    assert resp.status_code == 200
    assert resp.get_json() == []


# ─────────────────────── New page routes ───────────────────────

@pytest.mark.parametrize('path', [
    '/dashboard/me',
    '/dashboard/usage-stats',
    '/dashboard/activity',
    '/predictions/history',
    '/predictions/saved',
    '/vehicles/favorites',
    '/vehicles/saved',
])
def test_new_pages_require_login(client, path):
    resp = client.get(path)
    assert resp.status_code in (302, 401)


@pytest.mark.parametrize('path', [
    '/dashboard/me',
    '/dashboard/usage-stats',
    '/dashboard/activity',
    '/predictions/history',
    '/predictions/saved',
    '/vehicles/favorites',
    '/vehicles/saved',
])
def test_new_pages_render_for_logged_in_user(logged_in_client, path):
    resp = logged_in_client.get(path)
    assert resp.status_code == 200
