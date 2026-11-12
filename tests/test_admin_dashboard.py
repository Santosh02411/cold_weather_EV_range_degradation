"""Admin Dashboard feature tests -- Vehicle Management, Weather API
Monitoring, Feedback Management (community report moderation), System
Logs, the Analytics/Fleet Dashboard page, and admin-wide Report
Management. Same fixture pattern as test_api_smoke.py /
test_user_dashboard.py.
"""
import pytest

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.ev_vehicle import EVVehicle
from app.models.prediction import CommunityRangeReport
from app.models.dataset import WeatherLog
from app.models.session import LoginHistory
from app.models.report import ReportSchedule, ReportHistory


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
    """A regular (non-admin) user -- used to confirm admin routes reject them."""
    with app.app_context():
        user = User(username='regularuser', email='regular@example.com', role='user')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
    client.post('/login', data={'username': 'regularuser', 'password': 'testpass123'})
    return client


@pytest.fixture
def admin_client(client, app):
    with app.app_context():
        admin = User(username='adminuser', email='admin@example.com', role='admin')
        admin.set_password('adminpass123')
        db.session.add(admin)
        db.session.commit()
    client.post('/login', data={'username': 'adminuser', 'password': 'adminpass123'})
    return client


def _make_vehicle(active=True):
    vehicle = EVVehicle(
        model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=75,
        epa_range_km=400, vehicle_weight_kg=1900, battery_chemistry='NMC',
        charging_type='CCS', max_charging_power_kw=150, drivetrain='AWD', year=2024,
        is_active=active,
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle.id


# ─────────────────────── Access control ───────────────────────

ADMIN_PAGES = [
    '/admin/vehicles',
    '/admin/weather-monitoring',
    '/admin/feedback',
    '/admin/system-logs',
    '/admin/fleet-dashboard',
    '/admin/reports',
]

ADMIN_API = [
    '/admin/api/weather-monitoring',
    '/admin/api/community-reports',
    '/admin/api/system-logs',
    '/admin/api/reports/history',
    '/admin/api/reports/schedules',
]


@pytest.mark.parametrize('path', ADMIN_PAGES + ADMIN_API)
def test_admin_routes_require_login(client, path):
    resp = client.get(path)
    assert resp.status_code in (302, 401)


@pytest.mark.parametrize('path', ADMIN_PAGES + ADMIN_API)
def test_admin_routes_reject_non_admin(logged_in_client, path):
    resp = logged_in_client.get(path)
    # admin_required redirects non-admins back to the dashboard (302), never lets them through (200)
    assert resp.status_code == 302


@pytest.mark.parametrize('path', ADMIN_PAGES + ADMIN_API)
def test_admin_routes_work_for_admin(app, admin_client, path):
    resp = admin_client.get(path)
    assert resp.status_code == 200


# ─────────────────────── Vehicle Management ───────────────────────

def test_vehicle_management_lists_inactive_vehicles(app, admin_client):
    """The public catalog hides inactive vehicles; the admin view must not."""
    with app.app_context():
        _make_vehicle(active=True)
        _make_vehicle(active=False)

    resp = admin_client.get('/admin/vehicles')
    assert resp.status_code == 200
    assert b'Inactive' in resp.data


def test_toggle_vehicle_active(app, admin_client):
    with app.app_context():
        vehicle_id = _make_vehicle(active=True)

    resp = admin_client.post(f'/admin/vehicles/toggle/{vehicle_id}')
    assert resp.status_code == 302
    with app.app_context():
        assert EVVehicle.query.get(vehicle_id).is_active is False

    admin_client.post(f'/admin/vehicles/toggle/{vehicle_id}')
    with app.app_context():
        assert EVVehicle.query.get(vehicle_id).is_active is True


def test_toggle_vehicle_requires_admin(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle(active=True)
    resp = logged_in_client.post(f'/admin/vehicles/toggle/{vehicle_id}')
    assert resp.status_code == 302
    with app.app_context():
        assert EVVehicle.query.get(vehicle_id).is_active is True  # unchanged


# ─────────────────────── Weather API Monitoring ───────────────────────

def test_weather_monitoring_aggregates_by_data_source(app, admin_client):
    with app.app_context():
        db.session.add_all([
            WeatherLog(city='Chicago', temperature_c=-5.0, data_source='live'),
            WeatherLog(city='Chicago', temperature_c=-6.0, data_source='live'),
            WeatherLog(city='Denver', temperature_c=2.0, data_source='demo_fallback', error_note='timeout'),
        ])
        db.session.commit()

    resp = admin_client.get('/admin/api/weather-monitoring')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total_fetches_logged'] == 3
    assert data['live_fetches'] == 2
    assert data['demo_fallback_fetches'] == 1
    assert data['live_success_rate_pct'] == pytest.approx(66.7, abs=0.1)
    assert len(data['recent_errors']) == 1
    assert data['recent_errors'][0]['city'] == 'Denver'
    assert data['top_cities'][0]['city'] == 'Chicago'
    assert data['top_cities'][0]['fetch_count'] == 2


def test_weather_monitoring_handles_no_data(admin_client):
    resp = admin_client.get('/admin/api/weather-monitoring')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total_fetches_logged'] == 0
    assert data['live_success_rate_pct'] is None


# ─────────────────────── Feedback Management ───────────────────────

def test_flag_and_unflag_community_report(app, admin_client):
    with app.app_context():
        vehicle_id = _make_vehicle()
        report = CommunityRangeReport(
            vehicle_id=vehicle_id, temperature_c=-10, starting_battery_pct=90, reported_range_km=250,
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    resp = admin_client.post(f'/admin/api/community-reports/{report_id}/flag')
    assert resp.status_code == 200
    assert resp.get_json()['is_flagged'] is True

    resp = admin_client.get('/admin/api/community-reports?flagged_only=on')
    assert len(resp.get_json()) == 1

    resp = admin_client.post(f'/admin/api/community-reports/{report_id}/unflag')
    assert resp.get_json()['is_flagged'] is False

    resp = admin_client.get('/admin/api/community-reports?flagged_only=on')
    assert resp.get_json() == []


def test_flagging_hides_report_from_public_feed(app, admin_client):
    """The whole point of Feedback Management: flagging here has to
    actually take effect on community.list_reports(). That endpoint
    has no login requirement (community reports are meant to be
    public), so the already-authenticated admin_client can hit it
    directly -- no second client needed.
    """
    with app.app_context():
        vehicle_id = _make_vehicle()
        report = CommunityRangeReport(
            vehicle_id=vehicle_id, temperature_c=-10,
            starting_battery_pct=90, reported_range_km=250,
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    resp = admin_client.get('/community/api/reports')
    assert resp.get_json()['total'] == 1

    admin_client.post(f'/admin/api/community-reports/{report_id}/flag')

    resp = admin_client.get('/community/api/reports')
    assert resp.status_code == 200
    assert resp.get_json()['total'] == 0


def test_delete_community_report(app, admin_client):
    with app.app_context():
        vehicle_id = _make_vehicle()
        report = CommunityRangeReport(
            vehicle_id=vehicle_id, temperature_c=-10, starting_battery_pct=90, reported_range_km=250,
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    resp = admin_client.delete(f'/admin/api/community-reports/{report_id}')
    assert resp.status_code == 200
    assert resp.get_json()['deleted'] is True
    with app.app_context():
        assert CommunityRangeReport.query.get(report_id) is None


# ─────────────────────── System Logs ───────────────────────

def test_system_logs_includes_login_history(app, admin_client):
    with app.app_context():
        # Exercise the real write path (log_failed_login), not just the ORM,
        # but via a single already-isolated client rather than spinning up a
        # second test_client() -- two test_client() instances against the
        # same app leak auth state in this sandbox's Flask/Werkzeug setup
        # (reproduced independent of any code in this PR), which none of
        # this project's existing tests ever needed to do.
        from app.services.session_manager import log_failed_login
        with app.test_request_context('/login', method='POST'):
            log_failed_login('nonexistentuser', 'invalid credentials')

    resp = admin_client.get('/admin/api/system-logs')
    assert resp.status_code == 200
    events = resp.get_json()
    types = {e['type'] for e in events}
    assert 'login_success' in types  # the admin's own login
    assert 'login_failed' in types   # the bad attempt above


def test_system_logs_sorted_newest_first(admin_client):
    resp = admin_client.get('/admin/api/system-logs')
    events = resp.get_json()
    timestamps = [e['timestamp'] for e in events]
    assert timestamps == sorted(timestamps, reverse=True)


# ─────────────────────── Report Management (admin-wide) ───────────────────────

def test_admin_sees_reports_across_all_users(app, admin_client):
    with app.app_context():
        u1 = User(username='u1', email='u1@example.com', role='user'); u1.set_password('pass12345')
        u2 = User(username='u2', email='u2@example.com', role='user'); u2.set_password('pass12345')
        db.session.add_all([u1, u2])
        db.session.commit()
        db.session.add_all([
            ReportSchedule(user_id=u1.id, name='Weekly CSV', report_type='predictions', format='csv', frequency='weekly'),
            ReportSchedule(user_id=u2.id, name='Monthly Summary', report_type='summary', format='pdf', frequency='monthly'),
            ReportHistory(user_id=u1.id, report_type='predictions', format='csv', source='manual', row_count=12),
        ])
        db.session.commit()

    resp = admin_client.get('/admin/api/reports/schedules')
    assert resp.status_code == 200
    schedules = resp.get_json()
    assert len(schedules) == 2
    usernames = {s['username'] for s in schedules}
    assert usernames == {'u1', 'u2'}

    resp = admin_client.get('/admin/api/reports/history')
    history = resp.get_json()
    assert len(history) == 1
    assert history[0]['username'] == 'u1'
    assert history[0]['row_count'] == 12
