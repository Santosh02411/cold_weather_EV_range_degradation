"""Cost Analysis feature tests -- Charging Cost Calculator, Electricity
Price Integration (CostPreference + regional lookup), Monthly Charging
Cost, EV vs Petrol Cost Comparison, Ownership Cost Analysis, Savings
Calculator, and Charging Cost History (ChargingSession log). Same
fixture pattern as the other Phase test files.
"""
import pytest

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.ev_vehicle import EVVehicle
from app.models.cost_preference import CostPreference, ChargingSession


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


def _make_vehicle(energy_consumption_wh_km=180, price_usd=None, epa_range_km=350):
    vehicle = EVVehicle(
        model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=70,
        epa_range_km=epa_range_km, vehicle_weight_kg=1800, battery_chemistry='NMC',
        charging_type='CCS', max_charging_power_kw=120, drivetrain='AWD', year=2024,
        energy_consumption_wh_km=energy_consumption_wh_km, price_usd=price_usd,
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle.id


# ─────────────────────── Access control ───────────────────────

PAGES = ['/cost/', '/cost/preferences', '/cost/monthly', '/cost/compare', '/cost/ownership', '/cost/savings', '/cost/history']
API_GET = ['/cost/api/preferences', '/cost/api/regional-rates', '/cost/api/monthly', '/cost/api/sessions']


@pytest.mark.parametrize('path', PAGES + API_GET)
def test_cost_routes_require_login(client, path):
    resp = client.get(path)
    assert resp.status_code in (302, 401)


@pytest.mark.parametrize('path', PAGES + API_GET)
def test_cost_routes_work_when_logged_in(logged_in_client, path):
    resp = logged_in_client.get(path)
    assert resp.status_code == 200


# ─────────────────────── Charging Cost Calculator ───────────────────────

def test_calculate_uses_default_when_no_custom_rate(logged_in_client):
    resp = logged_in_client.post('/cost/api/calculate', json={'energy_needed_kwh': 40, 'fast_charging': True})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['source'] == 'custom_rate'  # resolved from the user's (default) effective rate
    assert data['estimated_cost_usd'] == pytest.approx(40 * 0.42, abs=0.01)


def test_calculate_uses_explicit_custom_rate(logged_in_client):
    resp = logged_in_client.post('/cost/api/calculate', json={'energy_needed_kwh': 10, 'custom_rate': 0.50})
    data = resp.get_json()
    assert data['price_per_kwh_usd'] == 0.5
    assert data['estimated_cost_usd'] == 5.0


def test_calculate_uses_saved_home_rate(logged_in_client):
    logged_in_client.post('/cost/api/preferences', json={'home_rate_usd_per_kwh': 0.10})
    resp = logged_in_client.post('/cost/api/calculate', json={'energy_needed_kwh': 20, 'fast_charging': False})
    data = resp.get_json()
    assert data['price_per_kwh_usd'] == 0.10
    assert data['estimated_cost_usd'] == 2.0


def test_calculate_requires_energy(logged_in_client):
    resp = logged_in_client.post('/cost/api/calculate', json={})
    assert resp.status_code == 400


# ─────────────────────── Electricity Price Integration ───────────────────────

def test_preferences_default_to_none(logged_in_client):
    resp = logged_in_client.get('/cost/api/preferences')
    data = resp.get_json()
    assert data['home_rate_usd_per_kwh'] is None
    assert data['effective_rates']['home_rate_usd_per_kwh'] == 0.14
    assert data['effective_rates']['home_rate_source'] == 'default_estimate'


def test_update_preferences_manual_rate(logged_in_client):
    resp = logged_in_client.post('/cost/api/preferences', json={'home_rate_usd_per_kwh': 0.22, 'public_rate_usd_per_kwh': 0.55})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['home_rate_usd_per_kwh'] == 0.22
    assert data['effective_rates']['home_rate_source'] == 'user_saved'
    assert data['rate_region_label'] is None


def test_use_regional_rate(logged_in_client):
    resp = logged_in_client.post('/cost/api/preferences', json={'use_regional_rate': 'us_northeast'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['rate_region_label'] == 'US Northeast'
    assert data['home_rate_usd_per_kwh'] == 0.22


def test_use_unknown_region_rejected(logged_in_client):
    resp = logged_in_client.post('/cost/api/preferences', json={'use_regional_rate': 'atlantis'})
    assert resp.status_code == 400


def test_manual_rate_clears_region_label(logged_in_client):
    logged_in_client.post('/cost/api/preferences', json={'use_regional_rate': 'us_northeast'})
    resp = logged_in_client.post('/cost/api/preferences', json={'home_rate_usd_per_kwh': 0.99})
    assert resp.get_json()['rate_region_label'] is None


def test_regional_rates_list_has_expected_shape(logged_in_client):
    resp = logged_in_client.get('/cost/api/regional-rates')
    regions = resp.get_json()
    assert len(regions) > 0
    assert all({'key', 'label', 'home', 'public_fast'} <= set(r.keys()) for r in regions)


# ─────────────────────── Monthly Charging Cost ───────────────────────

def test_monthly_cost_reports_rate_sources(logged_in_client):
    resp = logged_in_client.get('/cost/api/monthly?period=monthly')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['rate_sources']['home'] == 'default_estimate'

    logged_in_client.post('/cost/api/preferences', json={'home_rate_usd_per_kwh': 0.30})
    resp = logged_in_client.get('/cost/api/monthly?period=monthly')
    assert resp.get_json()['rate_sources']['home'] == 'user_saved'


# ─────────────────────── EV vs Petrol Cost Comparison ───────────────────────

def test_compare_requires_vehicle_id(logged_in_client):
    resp = logged_in_client.post('/cost/api/compare', json={})
    assert resp.status_code == 400


def test_compare_unknown_vehicle(logged_in_client):
    resp = logged_in_client.post('/cost/api/compare', json={'vehicle_id': 9999})
    assert resp.status_code == 404


def test_compare_uses_vehicle_logged_efficiency(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle(energy_consumption_wh_km=150)

    resp = logged_in_client.post('/cost/api/compare', json={'vehicle_id': vehicle_id, 'years': 2})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['ev']['wh_per_km'] == 150
    assert data['ev']['wh_per_km_source'] == 'vehicle_logged'
    assert data['years'] == 2
    assert data['petrol']['total_cost_usd'] == pytest.approx(data['petrol']['annual_cost_usd'] * 2, abs=0.01)


def test_compare_falls_back_to_epa_estimate(app, logged_in_client):
    with app.app_context():
        vehicle = EVVehicle(
            model_name='NoConsumption', manufacturer='TestCo', battery_capacity_kwh=60,
            epa_range_km=300, vehicle_weight_kg=1700, battery_chemistry='LFP',
            charging_type='CCS', max_charging_power_kw=100,
        )
        db.session.add(vehicle)
        db.session.commit()
        vehicle_id = vehicle.id

    resp = logged_in_client.post('/cost/api/compare', json={'vehicle_id': vehicle_id})
    data = resp.get_json()
    assert data['ev']['wh_per_km_source'] == 'estimated_from_epa_range'
    assert data['ev']['wh_per_km'] == pytest.approx(200.0, abs=0.1)  # 60000Wh / 300km


def test_compare_overrides_defaults(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    resp = logged_in_client.post('/cost/api/compare', json={
        'vehicle_id': vehicle_id, 'petrol_price_per_liter': 2.0, 'petrol_l_per_100km': 10.0, 'annual_km': 10000,
    })
    data = resp.get_json()
    assert data['petrol']['price_per_liter_usd'] == 2.0
    assert data['petrol']['l_per_100km'] == 10.0
    assert data['petrol']['cost_per_100km_usd'] == 20.0
    assert data['annual_km'] == 10000


# ─────────────────────── Ownership Cost Analysis ───────────────────────

def test_ownership_uses_catalog_price_when_available(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle(price_usd=42000)

    resp = logged_in_client.post('/cost/api/ownership', json={'vehicle_id': vehicle_id, 'years': 5})
    data = resp.get_json()
    assert data['ev']['purchase_price_usd'] == 42000
    assert data['ev']['purchase_price_is_estimated'] is True
    assert data['ev']['total_ownership_cost_usd'] > 42000  # includes running + maintenance on top


def test_ownership_explicit_price_overrides_catalog(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle(price_usd=42000)

    resp = logged_in_client.post('/cost/api/ownership', json={'vehicle_id': vehicle_id, 'ev_purchase_price_usd': 39000})
    data = resp.get_json()
    assert data['ev']['purchase_price_usd'] == 39000
    assert data['ev']['purchase_price_is_estimated'] is False


def test_ownership_notes_missing_price(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle(price_usd=None)

    resp = logged_in_client.post('/cost/api/ownership', json={'vehicle_id': vehicle_id})
    data = resp.get_json()
    assert data['ev']['purchase_price_usd'] is None
    assert data['purchase_price_note'] is not None


def test_ownership_default_maintenance_figures(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle(price_usd=None)

    resp = logged_in_client.post('/cost/api/ownership', json={'vehicle_id': vehicle_id, 'years': 3})
    data = resp.get_json()
    assert data['ev']['annual_maintenance_usd'] == 400.0
    assert data['petrol']['annual_maintenance_usd'] == 700.0
    assert data['ev']['total_maintenance_usd'] == 1200.0


# ─────────────────────── Savings Calculator ───────────────────────

def test_savings_without_premium_has_no_payback(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    resp = logged_in_client.post('/cost/api/savings', json={'vehicle_id': vehicle_id, 'years': 3})
    data = resp.get_json()
    assert data['payback_period_years'] is None


def test_savings_with_premium_computes_payback(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    resp = logged_in_client.post('/cost/api/savings', json={
        'vehicle_id': vehicle_id, 'years': 5, 'ev_price_premium_usd': 3000,
    })
    data = resp.get_json()
    assert data['payback_period_years'] is not None
    assert data['payback_period_years'] == pytest.approx(3000 / data['annual_savings_usd'], abs=0.1)


def test_savings_negative_case_gives_payback_note(app, logged_in_client):
    """If petrol is set artificially cheap (or EV artificially expensive to run),
    annual_savings can go negative -- payback should stay None with an explanatory note."""
    with app.app_context():
        vehicle_id = _make_vehicle()

    logged_in_client.post('/cost/api/preferences', json={'home_rate_usd_per_kwh': 5.0})  # absurdly high electricity
    resp = logged_in_client.post('/cost/api/savings', json={
        'vehicle_id': vehicle_id, 'years': 3, 'ev_price_premium_usd': 3000,
        'petrol_price_per_liter': 0.10, 'petrol_l_per_100km': 1.0,
    })
    data = resp.get_json()
    assert data['annual_savings_usd'] < 0
    assert data['payback_period_years'] is None
    assert data['payback_note'] is not None


# ─────────────────────── Charging Cost History ───────────────────────

def test_create_session_with_explicit_cost(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    resp = logged_in_client.post('/cost/api/sessions', json={
        'vehicle_id': vehicle_id, 'energy_added_kwh': 25, 'cost_usd': 8.75, 'source': 'dc_fast', 'station_name': 'Test Station',
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['cost_usd'] == 8.75
    assert data['is_cost_estimated'] is False
    assert data['vehicle'] == 'TestCo Test Model'


def test_create_session_estimates_cost_when_omitted(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    resp = logged_in_client.post('/cost/api/sessions', json={'vehicle_id': vehicle_id, 'energy_added_kwh': 20, 'source': 'home'})
    data = resp.get_json()
    assert data['is_cost_estimated'] is True
    assert data['cost_usd'] == pytest.approx(20 * 0.14, abs=0.01)  # default home rate


def test_create_session_rejects_bad_source(logged_in_client):
    resp = logged_in_client.post('/cost/api/sessions', json={'energy_added_kwh': 10, 'source': 'nonsense'})
    assert resp.status_code == 400


def test_create_session_requires_energy(logged_in_client):
    resp = logged_in_client.post('/cost/api/sessions', json={'source': 'home'})
    assert resp.status_code == 400


def test_list_sessions_totals(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    logged_in_client.post('/cost/api/sessions', json={'vehicle_id': vehicle_id, 'energy_added_kwh': 10, 'cost_usd': 2.0, 'source': 'home'})
    logged_in_client.post('/cost/api/sessions', json={'vehicle_id': vehicle_id, 'energy_added_kwh': 15, 'cost_usd': 6.0, 'source': 'dc_fast'})

    resp = logged_in_client.get('/cost/api/sessions')
    data = resp.get_json()
    assert data['session_count'] == 2
    assert data['total_energy_kwh'] == 25.0
    assert data['total_cost_usd'] == 8.0


def test_delete_session(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    create_resp = logged_in_client.post('/cost/api/sessions', json={'vehicle_id': vehicle_id, 'energy_added_kwh': 10, 'source': 'home'})
    session_id = create_resp.get_json()['id']

    resp = logged_in_client.delete(f'/cost/api/sessions/{session_id}')
    assert resp.status_code == 200
    assert resp.get_json()['deleted'] is True
    assert logged_in_client.get('/cost/api/sessions').get_json()['sessions'] == []


def test_cannot_delete_another_users_session(app, logged_in_client):
    with app.app_context():
        other = User(username='otheruser', email='other@example.com', role='user')
        other.set_password('pass12345')
        db.session.add(other)
        db.session.commit()
        session = ChargingSession(user_id=other.id, energy_added_kwh=10, source='home', cost_usd=1.4)
        db.session.add(session)
        db.session.commit()
        session_id = session.id

    resp = logged_in_client.delete(f'/cost/api/sessions/{session_id}')
    assert resp.status_code == 404
