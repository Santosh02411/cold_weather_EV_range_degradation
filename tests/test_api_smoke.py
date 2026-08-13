"""
Flask + DB smoke tests -- these exercise the actual HTTP layer (routes,
request/response, real SQLAlchemy models) rather than the pure-logic
modules the rest of this suite covers.

HONESTLY: these were written but NEVER EXECUTED as part of building
this project. `flask_sqlalchemy` (and several other Flask extensions)
are not installed in the sandbox this project was built in -- see
docs/PROJECT_WORKFLOW.md for the full explanation, repeated at every
phase this limitation applied to. `pytest.importorskip` below means
this file skips cleanly (not an error) in that environment; running it
for real, with `pip install -r requirements.txt` in a proper
environment, is the single most valuable thing left to verify about
this whole project. Please run it.
"""
import pytest

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.ev_vehicle import EVVehicle


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


def test_health_check_unauthenticated_redirects_to_login(client):
    resp = client.get('/predictions/')
    assert resp.status_code in (302, 401)


def test_login_with_valid_credentials(app, client):
    with app.app_context():
        user = User(username='testuser', email='test@example.com', role='user')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
    resp = client.post('/login', data={'username': 'testuser', 'password': 'testpass123'}, follow_redirects=True)
    assert resp.status_code == 200


def test_login_with_wrong_password_fails(app, client):
    with app.app_context():
        user = User(username='testuser', email='test@example.com', role='user')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
    resp = client.post('/login', data={'username': 'testuser', 'password': 'wrongpassword'})
    assert b'Invalid' in resp.data or resp.status_code == 200  # stays on login page with a flash message


def test_prediction_endpoint_requires_login(client):
    resp = client.post('/predictions/api/predict', json={})
    assert resp.status_code in (302, 401)


def test_prediction_endpoint_with_valid_input(app, logged_in_client):
    with app.app_context():
        vehicle = EVVehicle(
            model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=75,
            epa_range_km=400, vehicle_weight_kg=1900, battery_chemistry='NMC',
            charging_type='CCS', max_charging_power_kw=150, drivetrain='AWD', year=2024,
        )
        db.session.add(vehicle)
        db.session.commit()
        vehicle_id = vehicle.id

    resp = logged_in_client.post('/predictions/api/predict', json={
        'vehicle_id': vehicle_id, 'temperature_c': -10, 'humidity': 60, 'wind_speed_kmh': 15,
        'precipitation': 'none', 'battery_percentage': 80, 'vehicle_speed_kmh': 70,
        'hvac_usage': True, 'terrain_type': 'flat', 'battery_age_years': 2,
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'prediction' in data
    assert 0 <= data['prediction']['range_degradation_pct'] <= 65
    assert 'anomaly' in data  # Phase 3 addition
    assert 'model_details' in data  # Phase 4 (UX-1/UX-3) addition


def test_community_report_requires_login(client):
    resp = client.post('/community/api/reports', json={})
    assert resp.status_code in (302, 401)


def test_admin_endpoints_reject_non_admin_user(app, logged_in_client):
    resp = logged_in_client.get('/admin/api/model-versions')
    assert resp.status_code in (302, 403)
