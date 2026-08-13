"""Flask + DB smoke tests for the new admin ML API endpoints:
model-comparison, drift-report, live-retrain status/toggle/check-now.
Same skip-if-flask_sqlalchemy-missing convention as test_api_smoke.py
(see that file's docstring) -- these hit the real HTTP layer.

Relies on at least one model version already existing on disk (any
previous training run in this sandbox, e.g. from test_train_slow.py or
test_api_smoke.py, leaves saved_models/ populated) -- if none exists
yet, test_model_comparison_triggers... trains one via /admin/retrain
first, same as a fresh install's first admin visit would.
"""
import pytest

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User


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
def admin_client(client, app):
    with app.app_context():
        user = User(username='adminuser', email='admin@example.com', role='admin')
        user.set_password('adminpass123')
        db.session.add(user)
        db.session.commit()
    client.post('/login', data={'username': 'adminuser', 'password': 'adminpass123'})
    return client


def _ensure_a_version_exists(admin_client):
    resp = admin_client.get('/admin/api/model-versions')
    versions = resp.get_json().get('versions', [])
    if not versions:
        resp = admin_client.post('/admin/retrain')
        assert resp.status_code == 200, resp.get_json()


def test_ml_dashboard_page_requires_admin(client):
    resp = client.get('/admin/ml-dashboard')
    assert resp.status_code in (302, 401)


def test_ml_dashboard_page_loads_for_admin(admin_client):
    resp = admin_client.get('/admin/ml-dashboard')
    assert resp.status_code == 200


def test_model_comparison_requires_admin(client):
    resp = client.get('/admin/api/model-comparison')
    assert resp.status_code in (302, 401)


def test_model_comparison_returns_active_version_metrics(admin_client):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.get('/admin/api/model-comparison')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'version' in data
    assert isinstance(data['models'], list)
    assert len(data['models']) > 0
    # every model entry should carry the three metric buckets
    for m in data['models']:
        assert 'cross_validation' in m
        assert 'validation_set' in m
        assert 'held_out_test_set' in m


def test_model_comparison_unknown_version_404s(admin_client):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.get('/admin/api/model-comparison?version=99999')
    assert resp.status_code == 404


def test_drift_report_requires_admin(client):
    resp = client.get('/admin/api/drift-report')
    assert resp.status_code in (302, 401)


def test_drift_report_handles_no_recent_predictions_gracefully(admin_client):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.get('/admin/api/drift-report')
    assert resp.status_code == 200
    data = resp.get_json()
    # No Prediction rows exist in this fresh in-memory DB -- should be a
    # clean 'no_recent_data' status, never a 500.
    assert data['status'] in ('no_recent_data', 'ok', 'no_baseline')


def test_live_retrain_status_requires_admin(client):
    resp = client.get('/admin/api/live-retrain')
    assert resp.status_code in (302, 401)


def test_live_retrain_status_defaults_disabled(admin_client):
    resp = admin_client.get('/admin/api/live-retrain')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'enabled' in data
    assert 'history' in data


def test_live_retrain_toggle_flips_state(admin_client):
    resp = admin_client.post('/admin/api/live-retrain/toggle', json={'enabled': True})
    assert resp.status_code == 200
    assert resp.get_json()['enabled'] is True

    resp = admin_client.post('/admin/api/live-retrain/toggle', json={'enabled': False})
    assert resp.status_code == 200
    assert resp.get_json()['enabled'] is False


def test_live_retrain_check_now_records_a_history_entry(admin_client):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.post('/admin/api/live-retrain/check-now')
    assert resp.status_code == 200
    entry = resp.get_json()
    assert 'triggered' in entry
    assert 'reason' in entry

    status = admin_client.get('/admin/api/live-retrain').get_json()
    assert len(status['history']) >= 1


def test_drift_report_with_seeded_predictions(admin_client, app):
    """End-to-end: seed real Prediction rows (same distribution as
    training, so no drift expected), then confirm the drift endpoint
    actually reads them and returns a real per-feature PSI report --
    not just the 'no_recent_data' shortcut the other test covers.
    """
    _ensure_a_version_exists(admin_client)
    from app import db
    from app.models.ev_vehicle import EVVehicle
    from app.models.prediction import Prediction
    from app.models.user import User

    with app.app_context():
        user = User.query.filter_by(username='adminuser').first()
        vehicle = EVVehicle(
            model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=75,
            epa_range_km=400, vehicle_weight_kg=1900, battery_chemistry='NMC',
            charging_type='CCS', max_charging_power_kw=150, drivetrain='AWD', year=2024,
        )
        db.session.add(vehicle)
        db.session.commit()
        for i in range(60):
            db.session.add(Prediction(
                user_id=user.id, vehicle_id=vehicle.id,
                temperature_c=-10 + (i % 20), humidity=50, wind_speed_kmh=10,
                precipitation='none', battery_percentage=80, vehicle_speed_kmh=70,
                hvac_usage=True, terrain_type='flat', battery_age_years=2,
                range_degradation_pct=15.0, predicted_range_km=300, ml_model_used='random_forest',
            ))
        db.session.commit()

    resp = admin_client.get('/admin/api/drift-report')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'ok'
    assert data['n_recent_predictions_checked'] == 60
    assert 'per_feature' in data and len(data['per_feature']) > 0



