"""Flask + DB integration tests for the Trip Planning phase's API
endpoints and templates. Same skip-if-flask_sqlalchemy-missing
convention as test_api_smoke.py / test_admin_ml_api.py. Network-
dependent endpoints (route-optimize, plan, recommend-destinations --
all of which call out to geo/Overpass) are NOT exercised here with
real network calls; this file covers auth gating, saved-trips CRUD,
template rendering, and the non-network endpoints (driving-style,
energy-curve, plans history) end-to-end.
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
            energy_consumption_wh_km=170,
        )
        db.session.add(v)
        db.session.commit()
        return v.id


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    with app.app_context():
        user = User(username='tripuser', email='tripuser@example.com')
        user.set_password('pass12345')
        db.session.add(user)
        db.session.commit()
    client.post('/login', data={'username': 'tripuser', 'password': 'pass12345'})
    return client


def test_trip_plan_page_requires_login(client):
    resp = client.get('/trip/plan')
    assert resp.status_code in (302, 401)


def test_trip_plan_page_renders(auth_client):
    resp = auth_client.get('/trip/plan')
    assert resp.status_code == 200


def test_trip_simulate_page_still_renders(auth_client):
    resp = auth_client.get('/trip/')
    assert resp.status_code == 200


def test_saved_trip_crud_flow(auth_client, vehicle_id):
    resp = auth_client.post('/trip/api/saved-trips', json={
        'name': 'My Trip', 'stops': ['Chicago', 'Detroit'], 'vehicle_id': vehicle_id, 'round_trip': False,
    })
    assert resp.status_code == 201
    trip_id = resp.get_json()['id']

    resp = auth_client.get('/trip/api/saved-trips')
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1

    # Plan page renders correctly with a real saved trip present
    # (exercises the Jinja tojson branch).
    resp = auth_client.get('/trip/plan')
    assert resp.status_code == 200
    assert b'My Trip' in resp.data

    resp = auth_client.delete(f'/trip/api/saved-trips/{trip_id}')
    assert resp.status_code == 200

    resp = auth_client.get('/trip/api/saved-trips')
    assert len(resp.get_json()) == 0


def test_saved_trip_requires_at_least_two_stops(auth_client, vehicle_id):
    resp = auth_client.post('/trip/api/saved-trips', json={
        'name': 'Bad Trip', 'stops': ['OnlyOne'], 'vehicle_id': vehicle_id,
    })
    assert resp.status_code == 400


def test_saved_trip_unknown_vehicle_404s(auth_client):
    resp = auth_client.post('/trip/api/saved-trips', json={
        'name': 'Trip', 'stops': ['A', 'B'], 'vehicle_id': 99999,
    })
    assert resp.status_code == 404


def test_delete_someone_elses_saved_trip_404s(auth_client, app, vehicle_id):
    with app.app_context():
        other = User(username='otheruser', email='other@example.com')
        other.set_password('pass12345')
        db.session.add(other)
        db.session.commit()
        other_id = other.id

    from app.models.trip_plan import SavedTrip
    with app.app_context():
        t = SavedTrip(user_id=other_id, vehicle_id=vehicle_id, name='Not yours')
        t.stops = ['A', 'B']
        db.session.add(t)
        db.session.commit()
        trip_id = t.id

    resp = auth_client.delete(f'/trip/api/saved-trips/{trip_id}')
    assert resp.status_code == 404


def test_energy_curve_endpoint(auth_client, vehicle_id):
    resp = auth_client.get(f'/trip/api/energy-curve?vehicle_id={vehicle_id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['base_wh_per_km'] == 170
    assert len(data['curve']) > 0


def test_energy_curve_unknown_vehicle_404s(auth_client):
    resp = auth_client.get('/trip/api/energy-curve?vehicle_id=99999')
    assert resp.status_code == 404


def test_driving_style_endpoint_insufficient_data(auth_client):
    resp = auth_client.get('/trip/api/driving-style')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'insufficient_data'


def test_plans_history_empty_initially(auth_client):
    resp = auth_client.get('/trip/api/plans')
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_plan_detail_unknown_id_404s(auth_client):
    resp = auth_client.get('/trip/api/plans/99999')
    assert resp.status_code == 404


def test_plan_endpoint_requires_two_stops(auth_client, vehicle_id):
    resp = auth_client.post('/trip/api/plan', json={'vehicle_id': vehicle_id, 'stops': ['OnlyOne']})
    assert resp.status_code == 400


def test_plan_endpoint_unknown_vehicle_404s(auth_client):
    resp = auth_client.post('/trip/api/plan', json={'vehicle_id': 99999, 'stops': ['A', 'B']})
    assert resp.status_code == 404
