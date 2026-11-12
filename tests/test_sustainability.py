"""Sustainability feature tests -- CO2 Savings Calculator, Carbon
Footprint Analysis, Fuel Savings, Environmental Impact Dashboard, and
Green Driving Score. Same fixture pattern as the other Phase test
files.
"""
import pytest

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.ev_vehicle import EVVehicle
from app.models.prediction import TripSimulation, Prediction


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


def _user_id(app, username='testuser'):
    with app.app_context():
        return User.query.filter_by(username=username).first().id


def _make_vehicle(energy_consumption_wh_km=180, epa_range_km=350):
    vehicle = EVVehicle(
        model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=70,
        epa_range_km=epa_range_km, vehicle_weight_kg=1800, battery_chemistry='NMC',
        charging_type='CCS', max_charging_power_kw=120, drivetrain='AWD', year=2024,
        energy_consumption_wh_km=energy_consumption_wh_km,
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle.id


# ─────────────────────── Access control ───────────────────────

PAGES = [
    '/sustainability/', '/sustainability/footprint', '/sustainability/fuel-savings',
    '/sustainability/dashboard', '/sustainability/green-score',
]
API_GET = [
    '/sustainability/api/regional-grid-intensity', '/sustainability/api/footprint',
    '/sustainability/api/impact-summary', '/sustainability/api/green-score',
]


@pytest.mark.parametrize('path', PAGES + API_GET)
def test_sustainability_routes_require_login(client, path):
    resp = client.get(path)
    assert resp.status_code in (302, 401)


@pytest.mark.parametrize('path', PAGES + API_GET)
def test_sustainability_routes_work_when_logged_in(logged_in_client, path):
    resp = logged_in_client.get(path)
    assert resp.status_code == 200


# ─────────────────────── CO2 Savings Calculator ───────────────────────

def test_co2_savings_requires_vehicle_id(logged_in_client):
    resp = logged_in_client.post('/sustainability/api/co2-savings', json={})
    assert resp.status_code == 400


def test_co2_savings_unknown_vehicle(logged_in_client):
    resp = logged_in_client.post('/sustainability/api/co2-savings', json={'vehicle_id': 9999})
    assert resp.status_code == 404


def test_co2_savings_uses_vehicle_logged_efficiency(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle(energy_consumption_wh_km=150)

    resp = logged_in_client.post('/sustainability/api/co2-savings', json={'vehicle_id': vehicle_id, 'years': 2})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['ev']['wh_per_km'] == 150
    assert data['ev']['wh_per_km_source'] == 'vehicle_logged'
    assert data['years'] == 2
    # EV emits less than petrol at any sane grid intensity/petrol combo
    assert data['ev']['g_co2_per_km'] < data['petrol']['g_co2_per_km']
    assert data['total_savings_kg_co2'] == pytest.approx(data['annual_savings_kg_co2'] * 2, abs=0.1)


def test_co2_savings_falls_back_to_epa_estimate(app, logged_in_client):
    with app.app_context():
        vehicle = EVVehicle(
            model_name='NoConsumption', manufacturer='TestCo', battery_capacity_kwh=60,
            epa_range_km=300, vehicle_weight_kg=1700, battery_chemistry='LFP',
            charging_type='CCS', max_charging_power_kw=100,
        )
        db.session.add(vehicle)
        db.session.commit()
        vehicle_id = vehicle.id

    resp = logged_in_client.post('/sustainability/api/co2-savings', json={'vehicle_id': vehicle_id})
    data = resp.get_json()
    assert data['ev']['wh_per_km_source'] == 'estimated_from_epa_range'


def test_co2_savings_uses_saved_grid_intensity(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    logged_in_client.post('/cost/api/preferences', json={'grid_intensity_g_co2_per_kwh': 100})
    resp = logged_in_client.post('/sustainability/api/co2-savings', json={'vehicle_id': vehicle_id})
    data = resp.get_json()
    assert data['ev']['grid_intensity_g_co2_per_kwh'] == 100


def test_regional_grid_intensity_list_has_expected_shape(logged_in_client):
    resp = logged_in_client.get('/sustainability/api/regional-grid-intensity')
    regions = resp.get_json()
    assert len(regions) > 0
    assert all({'key', 'label', 'intensity'} <= set(r.keys()) for r in regions)


def test_regional_rate_also_sets_grid_intensity(logged_in_client):
    """Picking a region on the Electricity Price Integration page should
    set both the $/kWh rate AND the grid intensity together."""
    resp = logged_in_client.post('/cost/api/preferences', json={'use_regional_rate': 'uk_average'})
    data = resp.get_json()
    assert data['rate_region_label'] == 'UK Average'
    assert data['grid_intensity_g_co2_per_kwh'] == 210


# ─────────────────────── Carbon Footprint Analysis ───────────────────────

def test_footprint_uses_real_trip_energy(app, logged_in_client):
    with app.app_context():
        uid = _user_id(app)
        vehicle_id = _make_vehicle()
        db.session.add(TripSimulation(
            user_id=uid, vehicle_id=vehicle_id, source_location='A', destination='B',
            distance_km=200, temperature_c=-5, speed_kmh=80, estimated_energy_kwh=45,
        ))
        db.session.commit()

    resp = logged_in_client.get('/sustainability/api/footprint?period=monthly')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['series']) == 1
    assert data['series'][0]['total_energy_kwh'] == 45.0
    assert data['series'][0]['total_km'] == 200.0
    assert data['total_ev_kg_co2'] > 0


def test_footprint_empty_for_new_user(logged_in_client):
    resp = logged_in_client.get('/sustainability/api/footprint?period=monthly')
    data = resp.get_json()
    assert data['series'] == []
    assert data['total_ev_kg_co2'] == 0


def test_footprint_rejects_bad_period(logged_in_client):
    resp = logged_in_client.get('/sustainability/api/footprint?period=yearly')
    assert resp.status_code == 400


# ─────────────────────── Fuel Savings ───────────────────────

def test_fuel_savings_default_and_override(logged_in_client):
    resp = logged_in_client.post('/sustainability/api/fuel-savings', json={})
    data = resp.get_json()
    assert data['years'] == 1
    assert data['annual_liters_saved'] > 0

    resp2 = logged_in_client.post('/sustainability/api/fuel-savings', json={
        'petrol_l_per_100km': 10, 'annual_km': 10000, 'years': 3,
    })
    data2 = resp2.get_json()
    assert data2['annual_liters_saved'] == 1000.0
    assert data2['total_liters_saved'] == 3000.0


# ─────────────────────── Environmental Impact Dashboard ───────────────────────

def test_impact_summary_aggregates_all_trips(app, logged_in_client):
    with app.app_context():
        uid = _user_id(app)
        vehicle_id = _make_vehicle()
        db.session.add_all([
            TripSimulation(user_id=uid, vehicle_id=vehicle_id, source_location='A', destination='B',
                            distance_km=100, temperature_c=-5, speed_kmh=80, estimated_energy_kwh=20),
            TripSimulation(user_id=uid, vehicle_id=vehicle_id, source_location='C', destination='D',
                            distance_km=150, temperature_c=0, speed_kmh=90, estimated_energy_kwh=30),
        ])
        db.session.commit()

    resp = logged_in_client.get('/sustainability/api/impact-summary')
    data = resp.get_json()
    assert data['trip_count'] == 2
    assert data['total_km'] == 250.0
    assert data['total_kg_co2_saved'] > 0
    assert data['equivalent_trees_planted_per_year'] > 0


def test_impact_summary_zero_for_new_user(logged_in_client):
    resp = logged_in_client.get('/sustainability/api/impact-summary')
    data = resp.get_json()
    assert data['trip_count'] == 0
    assert data['total_kg_co2_saved'] == 0
    assert data['equivalent_trees_planted_per_year'] == 0.0


def test_impact_summary_ignores_trips_missing_energy(app, logged_in_client):
    """A trip with no estimated_energy_kwh (e.g. simulation failed)
    shouldn't be silently counted as zero-emission."""
    with app.app_context():
        uid = _user_id(app)
        vehicle_id = _make_vehicle()
        db.session.add(TripSimulation(
            user_id=uid, vehicle_id=vehicle_id, source_location='A', destination='B',
            distance_km=100, temperature_c=-5, speed_kmh=80, estimated_energy_kwh=None,
        ))
        db.session.commit()

    resp = logged_in_client.get('/sustainability/api/impact-summary')
    data = resp.get_json()
    assert data['trip_count'] == 0


# ─────────────────────── Green Driving Score ───────────────────────

def test_green_score_insufficient_data(logged_in_client):
    resp = logged_in_client.get('/sustainability/api/green-score')
    data = resp.get_json()
    assert data['status'] == 'insufficient_data'


def test_green_score_eco_driver(app, logged_in_client):
    with app.app_context():
        uid = _user_id(app)
        vehicle_id = _make_vehicle()
        for _ in range(6):
            db.session.add(TripSimulation(
                user_id=uid, vehicle_id=vehicle_id, source_location='A', destination='B',
                distance_km=50, temperature_c=0, speed_kmh=45, estimated_energy_kwh=10,
            ))
        db.session.commit()

    resp = logged_in_client.get('/sustainability/api/green-score')
    data = resp.get_json()
    assert data['status'] == 'ok'
    assert data['driving_style'] == 'eco'
    assert data['grade'] in ('A', 'B')
    assert 0 <= data['score'] <= 100
    # Perfectly consistent speeds -> no consistency penalty
    assert data['consistency_penalty'] == 0
    assert data['score'] == 90


def test_green_score_aggressive_driver_scores_lower(app, logged_in_client):
    with app.app_context():
        uid = _user_id(app)
        vehicle_id = _make_vehicle()
        for _ in range(6):
            db.session.add(TripSimulation(
                user_id=uid, vehicle_id=vehicle_id, source_location='A', destination='B',
                distance_km=50, temperature_c=0, speed_kmh=110, estimated_energy_kwh=15,
            ))
        db.session.commit()

    resp = logged_in_client.get('/sustainability/api/green-score')
    data = resp.get_json()
    assert data['driving_style'] == 'aggressive'
    assert data['score'] < 60


def test_green_score_penalizes_inconsistent_speed(app, logged_in_client):
    with app.app_context():
        uid = _user_id(app)
        vehicle_id = _make_vehicle()
        # Same average speed as the eco test (45), but wildly inconsistent.
        speeds = [10, 80, 20, 90, 15, 75]
        for s in speeds:
            db.session.add(TripSimulation(
                user_id=uid, vehicle_id=vehicle_id, source_location='A', destination='B',
                distance_km=50, temperature_c=0, speed_kmh=s, estimated_energy_kwh=10,
            ))
        db.session.commit()

    resp = logged_in_client.get('/sustainability/api/green-score')
    data = resp.get_json()
    assert data['consistency_penalty'] > 0
    assert data['score'] < 90  # lower than the perfectly-steady eco driver above
