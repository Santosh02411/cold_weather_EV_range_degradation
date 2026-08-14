"""Notifications feature tests -- the in-app notification inbox,
per-user preferences, and the four alert-type checks: Low Battery
Alerts, Battery Health Warning (both synchronous), Charging Reminder,
and Maintenance Reminder (both scheduler-driven). Same fixture pattern
as the other Phase test files.
"""
import pytest

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.ev_vehicle import EVVehicle
from app.models.prediction import TripSimulation
from app.models.battery_health import BatteryHealthRecord
from app.models.charging_reservation import ChargingReservation
from app.models.notification import Notification, NotificationPreference


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


def _make_vehicle():
    vehicle = EVVehicle(
        model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=75,
        epa_range_km=400, vehicle_weight_kg=1900, battery_chemistry='NMC',
        charging_type='CCS', max_charging_power_kw=150, drivetrain='AWD', year=2024,
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle.id


# ─────────────────────── Access control ───────────────────────

PAGES = ['/notifications/', '/notifications/preferences']
API = ['/notifications/api/list', '/notifications/api/unread-count', '/notifications/api/preferences']


@pytest.mark.parametrize('path', PAGES + API)
def test_notification_routes_require_login(client, path):
    resp = client.get(path)
    assert resp.status_code in (302, 401)


@pytest.mark.parametrize('path', PAGES + API)
def test_notification_routes_work_when_logged_in(logged_in_client, path):
    resp = logged_in_client.get(path)
    assert resp.status_code == 200


# ─────────────────────── Preferences ───────────────────────

def test_preferences_created_with_defaults_on_first_access(logged_in_client):
    resp = logged_in_client.get('/notifications/api/preferences')
    assert resp.status_code == 200
    p = resp.get_json()
    assert p['low_battery_alerts_enabled'] is True
    assert p['low_battery_threshold_pct'] == 20.0
    assert p['maintenance_reminders_enabled'] is False  # opt-in, needs a baseline first
    assert p['in_app_notifications_enabled'] is True


def test_update_preferences(logged_in_client):
    resp = logged_in_client.post('/notifications/api/preferences', json={
        'low_battery_alerts_enabled': False,
        'low_battery_threshold_pct': 15,
        'charging_reminder_lead_minutes': 45,
        'email_notifications_enabled': False,
    })
    assert resp.status_code == 200
    p = resp.get_json()
    assert p['low_battery_alerts_enabled'] is False
    assert p['low_battery_threshold_pct'] == 15.0
    assert p['charging_reminder_lead_minutes'] == 45
    assert p['email_notifications_enabled'] is False  # lives on User, round-trips through here


def test_mark_serviced_sets_maintenance_baseline(logged_in_client):
    resp = logged_in_client.post('/notifications/api/maintenance/mark-serviced', json={'odometer_km': 12000})
    assert resp.status_code == 200
    p = resp.get_json()
    assert p['maintenance_last_service_odometer_km'] == 12000.0
    assert p['maintenance_last_service_at'] is not None


def test_mark_serviced_requires_odometer(logged_in_client):
    resp = logged_in_client.post('/notifications/api/maintenance/mark-serviced', json={})
    assert resp.status_code == 400


# ─────────────────────── In-app notification inbox ───────────────────────

def test_list_read_and_delete_notification(app, logged_in_client):
    with app.app_context():
        uid = _user_id(app)
        n = Notification(user_id=uid, type='low_battery', title='Test', message='msg')
        db.session.add(n)
        db.session.commit()
        nid = n.id

    resp = logged_in_client.get('/notifications/api/list')
    items = resp.get_json()
    assert len(items) == 1
    assert items[0]['is_read'] is False

    resp = logged_in_client.get('/notifications/api/unread-count')
    assert resp.get_json()['unread_count'] == 1

    resp = logged_in_client.post(f'/notifications/api/{nid}/read')
    assert resp.get_json()['is_read'] is True

    resp = logged_in_client.get('/notifications/api/unread-count')
    assert resp.get_json()['unread_count'] == 0

    resp = logged_in_client.delete(f'/notifications/api/{nid}')
    assert resp.get_json()['deleted'] is True
    assert logged_in_client.get('/notifications/api/list').get_json() == []


def test_mark_all_read(app, logged_in_client):
    with app.app_context():
        uid = _user_id(app)
        db.session.add_all([
            Notification(user_id=uid, type='low_battery', title='A', message='a'),
            Notification(user_id=uid, type='maintenance', title='B', message='b'),
        ])
        db.session.commit()

    resp = logged_in_client.post('/notifications/api/read-all')
    assert resp.get_json()['marked_read'] is True
    assert logged_in_client.get('/notifications/api/unread-count').get_json()['unread_count'] == 0


def test_cannot_access_another_users_notification(app, logged_in_client):
    with app.app_context():
        other = User(username='otheruser', email='other@example.com', role='user')
        other.set_password('pass12345')
        db.session.add(other)
        db.session.commit()
        n = Notification(user_id=other.id, type='low_battery', title='Private', message='msg')
        db.session.add(n)
        db.session.commit()
        nid = n.id

    resp = logged_in_client.post(f'/notifications/api/{nid}/read')
    assert resp.status_code == 404


# ─────────────────────── Low Battery Alerts (synchronous) ───────────────────────

def test_low_battery_alert_created_when_trip_arrival_below_threshold(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    resp = logged_in_client.post('/trip/api/simulate', json={
        'vehicle_id': vehicle_id, 'source': 'A', 'destination': 'B',
        'distance_km': 390, 'temperature_c': -15, 'speed_kmh': 100,
        'battery_percentage': 100,
    })
    assert resp.status_code == 200

    items = logged_in_client.get('/notifications/api/list').get_json()
    low_battery_items = [n for n in items if n['type'] == 'low_battery']
    # A 390km trip near a ~400km EPA-range vehicle in -15C should plausibly
    # arrive low, but the exact ML output isn't asserted here -- what matters
    # is that IF the trip's own estimated_arrival_battery_pct came back at or
    # below the default 20% threshold, a notification exists for it.
    trip = resp.get_json()['trip']
    if trip['estimated_arrival_battery_pct'] is not None and trip['estimated_arrival_battery_pct'] <= 20:
        assert len(low_battery_items) == 1


def test_low_battery_alert_respects_disabled_preference(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    logged_in_client.post('/notifications/api/preferences', json={'low_battery_alerts_enabled': False})

    logged_in_client.post('/trip/api/simulate', json={
        'vehicle_id': vehicle_id, 'source': 'A', 'destination': 'B',
        'distance_km': 390, 'temperature_c': -20, 'speed_kmh': 110,
        'battery_percentage': 100,
    })

    items = logged_in_client.get('/notifications/api/list').get_json()
    assert [n for n in items if n['type'] == 'low_battery'] == []


def test_low_battery_check_directly(app):
    """Exercise services.notifications directly with a known
    estimated_arrival_battery_pct, rather than depending on the ML
    model's output landing below threshold."""
    from app.services.notifications import check_low_battery_after_trip

    with app.app_context():
        user = User(username='directuser', email='direct@example.com', role='user')
        user.set_password('pass12345')
        db.session.add(user)
        db.session.commit()
        vehicle_id = _make_vehicle()

        trip = TripSimulation(
            user_id=user.id, vehicle_id=vehicle_id, source_location='A', destination='B',
            distance_km=300, temperature_c=-10, speed_kmh=100,
            estimated_arrival_battery_pct=5.0,
        )
        db.session.add(trip)
        db.session.commit()

        result = check_low_battery_after_trip(trip)
        assert result is not None
        assert result.type == 'low_battery'

        notifications = Notification.query.filter_by(user_id=user.id).all()
        assert len(notifications) == 1


# ─────────────────────── Battery Health Warning (synchronous) ───────────────────────

def test_battery_health_warning_created_below_threshold(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    resp = logged_in_client.post(f'/vehicles/api/{vehicle_id}/battery-health', json={'soh_pct': 75, 'odometer_km': 40000})
    assert resp.status_code == 201

    items = logged_in_client.get('/notifications/api/list').get_json()
    warnings = [n for n in items if n['type'] == 'battery_health']
    assert len(warnings) == 1
    assert '75' in warnings[0]['title']


def test_battery_health_warning_not_created_above_threshold(app, logged_in_client):
    with app.app_context():
        vehicle_id = _make_vehicle()

    resp = logged_in_client.post(f'/vehicles/api/{vehicle_id}/battery-health', json={'soh_pct': 95})
    assert resp.status_code == 201

    items = logged_in_client.get('/notifications/api/list').get_json()
    assert [n for n in items if n['type'] == 'battery_health'] == []


# ─────────────────────── Charging Reminder (scheduled) ───────────────────────

def test_charging_reminder_sent_within_lead_time(app):
    from app.services.notifications import check_and_send_charging_reminders

    with app.app_context():
        user = User(username='chargeuser', email='charge@example.com', role='user')
        user.set_password('pass12345')
        db.session.add(user)
        db.session.commit()
        vehicle_id = _make_vehicle()

        reservation = ChargingReservation(
            user_id=user.id, vehicle_id=vehicle_id, station_name='Test Station',
            reserved_start=datetime.utcnow() + timedelta(minutes=10),  # within default 30-min lead
            duration_minutes=30,
        )
        db.session.add(reservation)
        db.session.commit()

        results = check_and_send_charging_reminders(app)
        assert results['sent'] == 1

        notifications = Notification.query.filter_by(user_id=user.id, type='charging_reminder').all()
        assert len(notifications) == 1

        # Second run shouldn't double-send (reminder_sent_at now set).
        results2 = check_and_send_charging_reminders(app)
        assert results2['sent'] == 0


def test_charging_reminder_not_sent_outside_lead_time(app):
    from app.services.notifications import check_and_send_charging_reminders

    with app.app_context():
        user = User(username='chargeuser2', email='charge2@example.com', role='user')
        user.set_password('pass12345')
        db.session.add(user)
        db.session.commit()
        vehicle_id = _make_vehicle()

        reservation = ChargingReservation(
            user_id=user.id, vehicle_id=vehicle_id, station_name='Far Station',
            reserved_start=datetime.utcnow() + timedelta(hours=5),  # outside default 30-min lead
            duration_minutes=30,
        )
        db.session.add(reservation)
        db.session.commit()

        results = check_and_send_charging_reminders(app)
        assert results['sent'] == 0
        assert Notification.query.filter_by(user_id=user.id).count() == 0


# ─────────────────────── Maintenance Reminder (scheduled) ───────────────────────

def test_maintenance_reminder_sent_when_due(app):
    from app.services.notifications import check_and_send_maintenance_reminders

    with app.app_context():
        user = User(username='maintuser', email='maint@example.com', role='user')
        user.set_password('pass12345')
        db.session.add(user)
        db.session.commit()
        vehicle_id = _make_vehicle()

        prefs = NotificationPreference(
            user_id=user.id, maintenance_reminders_enabled=True,
            maintenance_interval_km=10000, maintenance_last_service_odometer_km=0,
        )
        db.session.add(prefs)
        db.session.add(BatteryHealthRecord(user_id=user.id, vehicle_id=vehicle_id, soh_pct=90, odometer_km=12000))
        db.session.commit()

        results = check_and_send_maintenance_reminders(app)
        assert results['sent'] == 1
        assert Notification.query.filter_by(user_id=user.id, type='maintenance').count() == 1


def test_maintenance_reminder_not_sent_without_baseline(app):
    """No maintenance_last_service_odometer_km set -- nothing to compare against."""
    from app.services.notifications import check_and_send_maintenance_reminders

    with app.app_context():
        user = User(username='maintuser2', email='maint2@example.com', role='user')
        user.set_password('pass12345')
        db.session.add(user)
        db.session.commit()
        vehicle_id = _make_vehicle()

        prefs = NotificationPreference(user_id=user.id, maintenance_reminders_enabled=True)
        db.session.add(prefs)
        db.session.add(BatteryHealthRecord(user_id=user.id, vehicle_id=vehicle_id, soh_pct=90, odometer_km=50050))
        db.session.commit()

        results = check_and_send_maintenance_reminders(app)
        assert results['sent'] == 0


def test_maintenance_reminder_not_sent_when_under_interval(app):
    from app.services.notifications import check_and_send_maintenance_reminders

    with app.app_context():
        user = User(username='maintuser3', email='maint3@example.com', role='user')
        user.set_password('pass12345')
        db.session.add(user)
        db.session.commit()
        vehicle_id = _make_vehicle()

        prefs = NotificationPreference(
            user_id=user.id, maintenance_reminders_enabled=True,
            maintenance_interval_km=10000, maintenance_last_service_odometer_km=5005,
        )
        db.session.add(prefs)
        db.session.add(BatteryHealthRecord(user_id=user.id, vehicle_id=vehicle_id, soh_pct=90, odometer_km=8000))
        db.session.commit()

        results = check_and_send_maintenance_reminders(app)
        assert results['sent'] == 0
