"""Flask + DB integration tests for the Explainable AI API endpoints.
Same skip-if-flask_sqlalchemy-missing convention as the other API test
files. These need a real trained model on disk (every endpoint here
loads and runs actual sklearn models via ml/explainability.py), so
_ensure_a_version_exists() trains one via /admin/retrain if none
exists yet -- same pattern as test_admin_ml_api.py.
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
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def vehicle_id(app):
    with app.app_context():
        v = EVVehicle(
            model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=75,
            epa_range_km=400, vehicle_weight_kg=1900, battery_chemistry='NMC',
            charging_type='CCS', max_charging_power_kw=150, drivetrain='AWD', year=2024,
        )
        db.session.add(v)
        db.session.commit()
        return v.id


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client, app):
    with app.app_context():
        user = User(username='adminuser', email='explainadmin@example.com', role='admin')
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


_SCENARIO_EXTRA = {
    'temperature_c': -15, 'vehicle_speed_kmh': 90, 'terrain_type': 'hilly',
    'battery_percentage': 60, 'battery_age_years': 3, 'hvac_usage': True,
}


def test_explain_page_requires_login(client):
    resp = client.get('/explain/')
    assert resp.status_code in (302, 401)


def test_explain_page_loads_for_logged_in_user(admin_client):
    resp = admin_client.get('/explain/')
    assert resp.status_code == 200


def test_pdp_features_endpoint(admin_client):
    resp = admin_client.get('/explain/api/pdp/features')
    assert resp.status_code == 200
    features = resp.get_json()['features']
    assert any(f['name'] == 'temperature_c' for f in features)
    assert not any(f['name'] == 'wind_chill_index' for f in features)  # engineered, excluded


def test_confidence_endpoint_unknown_vehicle_404s(admin_client):
    resp = admin_client.post('/explain/api/confidence', json={'vehicle_id': 99999})
    assert resp.status_code == 404


def test_confidence_endpoint_end_to_end(admin_client, vehicle_id):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.post('/explain/api/confidence', json={'vehicle_id': vehicle_id, **_SCENARIO_EXTRA})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is True
    assert 0 <= data['confidence'] <= 1


def test_counterfactual_endpoint_end_to_end(admin_client, vehicle_id):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.post('/explain/api/counterfactual', json={'vehicle_id': vehicle_id, **_SCENARIO_EXTRA})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is True
    assert len(data['scenarios']) > 0


def test_lime_endpoint_end_to_end(admin_client, vehicle_id):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.post('/explain/api/lime', json={'vehicle_id': vehicle_id, 'model_name': 'random_forest', **_SCENARIO_EXTRA})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is True
    assert len(data['explanations']) > 0


def test_pdp_endpoint_missing_feature_400s(admin_client, vehicle_id):
    resp = admin_client.post('/explain/api/pdp', json={'vehicle_id': vehicle_id, **_SCENARIO_EXTRA})
    assert resp.status_code == 400


def test_pdp_endpoint_end_to_end(admin_client, vehicle_id):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.post('/explain/api/pdp', json={'vehicle_id': vehicle_id, 'feature': 'temperature_c', **_SCENARIO_EXTRA})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is True
    assert len(data['pdp']) > 0


def test_shap_waterfall_endpoint_end_to_end(admin_client, vehicle_id):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.post('/explain/api/shap-waterfall', json={'vehicle_id': vehicle_id, 'model_name': 'random_forest', **_SCENARIO_EXTRA})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is True
    assert len(data['steps']) > 0


def test_shap_force_endpoint_end_to_end(admin_client, vehicle_id):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.post('/explain/api/shap-force', json={'vehicle_id': vehicle_id, 'model_name': 'random_forest', **_SCENARIO_EXTRA})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is True


def test_shap_endpoints_report_unavailable_for_neural_network(admin_client, vehicle_id):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.post('/explain/api/shap-waterfall', json={'vehicle_id': vehicle_id, 'model_name': 'neural_network', **_SCENARIO_EXTRA})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is False
    assert 'reason' in data


def test_global_dashboard_endpoint(admin_client, vehicle_id):
    _ensure_a_version_exists(admin_client)
    resp = admin_client.get('/explain/api/global?model_name=random_forest&n_samples=30')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is True
    assert len(data['global_importance']) > 0
