"""Flask + DB integration tests for the Charging Management phase's
API endpoints. Same skip-if-flask_sqlalchemy-missing convention as
test_trip_planning_api.py. Endpoints that hit real network APIs
(/api/stations, /api/recommend -- both call Open Charge Map) are
exercised with a mocked find_charging_stations rather than live
network, consistent with this project's "written but not executed
against the live internet in this sandbox" convention.
"""
import pytest
from unittest.mock import patch

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
def auth_client(client, app):
    with app.app_context():
        user = User(username='chargeuser', email='chargeuser@example.com')
        user.set_password('pass12345')
        db.session.add(user)
        db.session.commit()
    client.post('/login', data={'username': 'chargeuser', 'password': 'pass12345'})
    return client


def _fake_stations():
    # A fresh list/dicts every call -- annotate_compatibility() and
    # evaluate_stations() mutate station dicts in place, so a shared
    # module-level list would leak annotations from one test into the
    # next (test order/pollution bug caught while writing these tests).
    return [
        {'id': 1, 'name': 'Fast CCS Station', 'address': '123 Main St', 'latitude': 41.88, 'longitude': -87.63,
         'distance_km': 2.0, 'operator': 'ChargePoint', 'num_points': 4, 'connector_types': ['CCS (Type 2)'],
         'max_power_kw': 150, 'usage_cost': '$0.40/kWh', 'status': 'Operational'},
        {'id': 2, 'name': 'Cheap Slow Station', 'address': '456 Oak Ave', 'latitude': 41.90, 'longitude': -87.65,
         'distance_km': 5.0, 'operator': 'EVgo', 'num_points': 8, 'connector_types': ['CCS (Type 2)'],
         'max_power_kw': 25, 'usage_cost': '$0.10/kWh', 'status': 'Operational'},
    ]


def test_home_recommendation_endpoint(auth_client, vehicle_id):
    resp = auth_client.post('/charging/api/home-recommendation', json={
        'vehicle_id': vehicle_id, 'current_pct': 20, 'target_pct': 80,
        'temperature_c': 10, 'hours_available_at_home': 10,
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['recommendation'] in ('home', 'public_fast')
    assert 'estimated_savings_charging_at_home_usd' in data


def test_home_recommendation_unknown_vehicle_404s(auth_client):
    resp = auth_client.post('/charging/api/home-recommendation', json={'vehicle_id': 99999})
    assert resp.status_code == 404


def test_stations_endpoint_annotates_compatibility_with_vehicle(auth_client, vehicle_id):
    with patch('app.api.charging.find_charging_stations', side_effect=lambda *a, **kw: _fake_stations()), \
         patch('app.api.charging.geocode_place', return_value=(41.88, -87.63, 'Chicago, IL')):
        resp = auth_client.get(f'/charging/api/stations?place=Chicago&vehicle_id={vehicle_id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['count'] == 2
    assert all('compatible' in s for s in data['stations'])
    assert all('availability' in s for s in data['stations'])


def test_stations_endpoint_without_vehicle_id_skips_annotation(auth_client):
    with patch('app.api.charging.find_charging_stations', side_effect=lambda *a, **kw: _fake_stations()), \
         patch('app.api.charging.geocode_place', return_value=(41.88, -87.63, 'Chicago, IL')):
        resp = auth_client.get('/charging/api/stations?place=Chicago')
    assert resp.status_code == 200
    assert 'compatible' not in resp.get_json()['stations'][0]


def test_recommend_fastest_endpoint(auth_client, vehicle_id):
    with patch('app.api.charging.find_charging_stations', side_effect=lambda *a, **kw: _fake_stations()), \
         patch('app.api.charging.geocode_place', return_value=(41.88, -87.63, 'Chicago, IL')):
        resp = auth_client.get(f'/charging/api/recommend?place=Chicago&vehicle_id={vehicle_id}&priority=fastest')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['recommendation']['name'] == 'Fast CCS Station'


def test_recommend_cheapest_endpoint(auth_client, vehicle_id):
    with patch('app.api.charging.find_charging_stations', side_effect=lambda *a, **kw: _fake_stations()), \
         patch('app.api.charging.geocode_place', return_value=(41.88, -87.63, 'Chicago, IL')):
        resp = auth_client.get(f'/charging/api/recommend?place=Chicago&vehicle_id={vehicle_id}&priority=cheapest')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['recommendation']['name'] == 'Cheap Slow Station'


def test_recommend_invalid_priority_400s(auth_client, vehicle_id):
    resp = auth_client.get(f'/charging/api/recommend?place=Chicago&vehicle_id={vehicle_id}&priority=bogus')
    assert resp.status_code == 400


def test_recommend_unknown_vehicle_404s(auth_client):
    resp = auth_client.get('/charging/api/recommend?place=Chicago&vehicle_id=99999')
    assert resp.status_code == 404


def test_reservation_crud_flow(auth_client, vehicle_id):
    resp = auth_client.post('/charging/api/reservations', json={
        'vehicle_id': vehicle_id, 'station_name': 'Fast CCS Station',
        'reserved_start': '2027-01-05T08:00:00', 'duration_minutes': 30,
    })
    assert resp.status_code == 201
    reservation = resp.get_json()
    assert reservation['status'] == 'upcoming'
    reservation_id = reservation['id']

    resp = auth_client.get('/charging/api/reservations')
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1

    resp = auth_client.delete(f'/charging/api/reservations/{reservation_id}')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'cancelled'


def test_reservation_overlap_rejected(auth_client, vehicle_id):
    auth_client.post('/charging/api/reservations', json={
        'vehicle_id': vehicle_id, 'station_name': 'Station A',
        'reserved_start': '2027-01-05T08:00:00', 'duration_minutes': 60,
    })
    resp = auth_client.post('/charging/api/reservations', json={
        'vehicle_id': vehicle_id, 'station_name': 'Station B',
        'reserved_start': '2027-01-05T08:30:00', 'duration_minutes': 30,
    })
    assert resp.status_code == 409


def test_reservation_missing_fields_400s(auth_client, vehicle_id):
    resp = auth_client.post('/charging/api/reservations', json={'vehicle_id': vehicle_id})
    assert resp.status_code == 400


def test_reservation_bad_datetime_400s(auth_client, vehicle_id):
    resp = auth_client.post('/charging/api/reservations', json={
        'vehicle_id': vehicle_id, 'station_name': 'X', 'reserved_start': 'not-a-date',
    })
    assert resp.status_code == 400


def test_cancel_someone_elses_reservation_404s(auth_client, app, vehicle_id):
    with app.app_context():
        other = User(username='otherchargeuser', email='other2@example.com')
        other.set_password('pass12345')
        db.session.add(other)
        db.session.commit()
        other_id = other.id

    from app.models.charging_reservation import ChargingReservation
    from datetime import datetime
    with app.app_context():
        r = ChargingReservation(user_id=other_id, vehicle_id=vehicle_id, station_name='Not yours',
                                 reserved_start=datetime(2027, 1, 5, 8, 0), duration_minutes=30)
        db.session.add(r)
        db.session.commit()
        rid = r.id

    resp = auth_client.delete(f'/charging/api/reservations/{rid}')
    assert resp.status_code == 404


def test_predict_endpoint_still_works(auth_client, vehicle_id):
    resp = auth_client.post('/charging/api/predict', json={
        'vehicle_id': vehicle_id, 'temperature_c': -10, 'current_pct': 20, 'target_pct': 80,
    })
    assert resp.status_code == 200
    assert 'charging_time_minutes' in resp.get_json()
