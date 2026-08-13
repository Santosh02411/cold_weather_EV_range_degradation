"""Notification creation + the check logic for each Notifications
sidebar alert type that didn't already have a home:

  - Low Battery Alerts: checked synchronously right after a trip
    simulation, against its real estimated_arrival_battery_pct.
  - Battery Health Warning: checked synchronously right after a new
    BatteryHealthRecord (SOH reading) is logged.
  - Charging Reminder: checked on a scheduler tick, against upcoming
    ChargingReservations within the user's lead time.
  - Maintenance Reminder: checked on a scheduler tick, against the
    latest logged odometer reading vs. the user's service baseline.

Severe Weather Alerts is NOT here -- see services/alerts.py, which
already does this (FEAT-3), unchanged.
"""
from datetime import datetime, timedelta


def get_or_create_preferences(user_id):
    from ..models.notification import NotificationPreference
    from .. import db

    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if not prefs:
        prefs = NotificationPreference(user_id=user_id)
        db.session.add(prefs)
        db.session.commit()
    return prefs


def create_notification(user_id, ntype, title, message, url=None, email_subject=None, app=None):
    """Creates an in-app Notification row (if the user has in-app
    notifications on) and sends an email (if the user has both email
    notifications on generally AND this specific alert type on).
    Mirrors services/alerts.py's "don't silently no-op when mail isn't
    configured -- log what would have been sent" convention.
    """
    from ..models.notification import Notification
    from ..models.user import User
    from .. import db

    prefs = get_or_create_preferences(user_id)
    user = User.query.get(user_id)
    if not user:
        return None

    notification = None
    if prefs.in_app_notifications_enabled:
        notification = Notification(user_id=user_id, type=ntype, title=title, message=message, url=url)
        db.session.add(notification)
        db.session.commit()

    if user.email_notifications_enabled and _email_enabled_for_type(prefs, ntype):
        _send_email(user, email_subject or title, message, app)

    return notification


def _email_enabled_for_type(prefs, ntype):
    return {
        'low_battery': prefs.low_battery_alerts_enabled,
        'battery_health': prefs.battery_health_warnings_enabled,
        'charging_reminder': prefs.charging_reminders_enabled,
        'maintenance': prefs.maintenance_reminders_enabled,
    }.get(ntype, True)


def _send_email(user, subject, body, app=None):
    from flask import current_app
    from flask_mail import Message
    from .. import mail

    app = app or current_app
    mail_configured = bool(app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'))
    if not mail_configured:
        print(f"[NOTIFICATION-EMAIL-WOULD-SEND] (MAIL_USERNAME/PASSWORD not configured) To: {user.email} | Subject: {subject}")
        return
    try:
        mail.send(Message(subject=subject, recipients=[user.email], body=body))
    except Exception as e:
        print(f"[ERROR] Failed to send notification email to user {user.id}: {e}")


# ─────────────────────── Low Battery Alerts ───────────────────────

def check_low_battery_after_trip(trip):
    """Called synchronously right after trip.py's /api/simulate saves a
    TripSimulation -- reuses the real, already-computed
    estimated_arrival_battery_pct rather than tracking any separate
    'current charge' state (this app has no live vehicle telemetry).
    """
    prefs = get_or_create_preferences(trip.user_id)
    if not prefs.low_battery_alerts_enabled:
        return None
    if trip.estimated_arrival_battery_pct is None:
        return None
    if trip.estimated_arrival_battery_pct > prefs.low_battery_threshold_pct:
        return None

    return create_notification(
        trip.user_id, 'low_battery',
        title=f"Low battery on arrival: {trip.estimated_arrival_battery_pct:.0f}%",
        message=(
            f"Your simulated trip from {trip.source_location} to {trip.destination} "
            f"is estimated to arrive with only {trip.estimated_arrival_battery_pct:.0f}% "
            f"battery remaining, at or below your {prefs.low_battery_threshold_pct:.0f}% alert threshold. "
            f"Consider adding a charging stop."
        ),
        url='/trip/',
        email_subject='Low battery alert on a simulated trip',
    )


# ─────────────────────── Battery Health Warning ───────────────────────

def check_battery_health_after_record(record):
    """Called synchronously right after vehicles.py's
    /api/<id>/battery-health saves a new BatteryHealthRecord."""
    prefs = get_or_create_preferences(record.user_id)
    if not prefs.battery_health_warnings_enabled:
        return None
    if record.soh_pct > prefs.battery_health_threshold_pct:
        return None

    vehicle_name = f"{record.vehicle.manufacturer} {record.vehicle.model_name}" if record.vehicle else "your vehicle"
    return create_notification(
        record.user_id, 'battery_health',
        title=f"Battery health warning: {record.soh_pct:.0f}% SOH",
        message=(
            f"The latest State of Health reading for {vehicle_name} is {record.soh_pct:.0f}%, "
            f"at or below your {prefs.battery_health_threshold_pct:.0f}% warning threshold."
        ),
        url=f'/vehicles/view/{record.vehicle_id}',
        email_subject='Battery health warning',
    )


# ─────────────────────── Charging Reminder (scheduled) ───────────────────────

def check_and_send_charging_reminders(app):
    from ..models.charging_reservation import ChargingReservation
    from ..models.notification import NotificationPreference
    from .. import db

    now = datetime.utcnow()
    results = {'checked': 0, 'sent': 0}

    upcoming = ChargingReservation.query.filter(
        ChargingReservation.cancelled.is_(False),
        ChargingReservation.reminder_sent_at.is_(None),
        ChargingReservation.reserved_start > now,
    ).all()

    for reservation in upcoming:
        results['checked'] += 1
        prefs = get_or_create_preferences(reservation.user_id)
        if not prefs.charging_reminders_enabled:
            continue

        lead = timedelta(minutes=prefs.charging_reminder_lead_minutes)
        if reservation.reserved_start - now > lead:
            continue  # not within this user's lead time yet

        create_notification(
            reservation.user_id, 'charging_reminder',
            title=f"Charging reminder: {reservation.station_name}",
            message=(
                f"Your planned charging stop at {reservation.station_name} is coming up at "
                f"{reservation.reserved_start.strftime('%H:%M on %b %d')} "
                f"(in about {prefs.charging_reminder_lead_minutes} minutes or less)."
            ),
            url='/charging/',
            email_subject=f"Charging reminder: {reservation.station_name}",
            app=app,
        )
        reservation.reminder_sent_at = now
        results['sent'] += 1

    db.session.commit()
    return results


# ─────────────────────── Maintenance Reminder (scheduled) ───────────────────────

def check_and_send_maintenance_reminders(app):
    """Grounded in the only mileage data this app actually tracks --
    BatteryHealthRecord.odometer_km -- compared against a user-set
    interval and service baseline (models/notification.py). A user who
    has never logged an odometer reading, or never set a baseline via
    /notifications/api/maintenance/mark-serviced, is simply never due
    -- there's nothing to guess at.
    """
    from ..models.notification import NotificationPreference
    from ..models.battery_health import BatteryHealthRecord
    from .. import db

    now = datetime.utcnow()
    results = {'checked': 0, 'sent': 0}

    cooldown = timedelta(days=app.config.get('MAINTENANCE_REMINDER_COOLDOWN_DAYS', 14))

    prefs_list = NotificationPreference.query.filter_by(maintenance_reminders_enabled=True).all()
    for prefs in prefs_list:
        results['checked'] += 1
        if prefs.maintenance_last_service_odometer_km is None:
            continue  # no baseline set -- nothing to compare against
        if prefs.maintenance_last_reminder_sent_at and (now - prefs.maintenance_last_reminder_sent_at) < cooldown:
            continue

        latest = BatteryHealthRecord.query.filter_by(user_id=prefs.user_id) \
            .filter(BatteryHealthRecord.odometer_km.isnot(None)) \
            .order_by(BatteryHealthRecord.odometer_km.desc()).first()
        if not latest or latest.odometer_km is None:
            continue

        due_at = prefs.maintenance_last_service_odometer_km + prefs.maintenance_interval_km
        if latest.odometer_km < due_at:
            continue

        create_notification(
            prefs.user_id, 'maintenance',
            title="Maintenance reminder",
            message=(
                f"Your logged odometer reading of {latest.odometer_km:.0f} km has passed your "
                f"maintenance interval ({prefs.maintenance_interval_km:.0f} km since your last "
                f"logged service at {prefs.maintenance_last_service_odometer_km:.0f} km)."
            ),
            url='/notifications/preferences',
            email_subject='Maintenance reminder',
            app=app,
        )
        prefs.maintenance_last_reminder_sent_at = now
        results['sent'] += 1

    db.session.commit()
    return results
