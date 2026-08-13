from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from ..models.notification import Notification, NotificationPreference
from .. import db
from ..services.notifications import get_or_create_preferences

notifications_bp = Blueprint('notifications', __name__)


# ─────────────────────── Pages ───────────────────────

@notifications_bp.route('/')
@login_required
def index():
    """In-App Notifications: the actual notification center/inbox."""
    return render_template('notifications/index.html')


@notifications_bp.route('/preferences')
@login_required
def preferences_page():
    """Low Battery Alerts / Charging Reminder / Battery Health Warning /
    Maintenance Reminder / Email / Push / In-App toggles, all in one
    settings page. Severe Weather Alerts is deliberately not here --
    see alerts.index, which already has its own full subscription UI.
    """
    return render_template('notifications/preferences.html')


# ─────────────────────── Notification center API ───────────────────────

@notifications_bp.route('/api/list')
@login_required
def list_notifications():
    limit = min(request.args.get('limit', 50, type=int), 200)
    unread_only = request.args.get('unread_only') == 'on'

    query = Notification.query.filter_by(user_id=current_user.id)
    if unread_only:
        query = query.filter_by(is_read=False)
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return jsonify([n.to_dict() for n in notifications])


@notifications_bp.route('/api/unread-count')
@login_required
def unread_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'unread_count': count})


@notifications_bp.route('/api/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    notification.is_read = True
    db.session.commit()
    return jsonify({'is_read': True})


@notifications_bp.route('/api/read-all', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'marked_read': True})


@notifications_bp.route('/api/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    db.session.delete(notification)
    db.session.commit()
    return jsonify({'deleted': True})


# ─────────────────────── Preferences API ───────────────────────

@notifications_bp.route('/api/preferences', methods=['GET'])
@login_required
def get_preferences():
    prefs = get_or_create_preferences(current_user.id)
    return jsonify(prefs.to_dict())


@notifications_bp.route('/api/preferences', methods=['POST'])
@login_required
def update_preferences():
    prefs = get_or_create_preferences(current_user.id)
    data = request.get_json() or {}

    bool_fields = [
        'low_battery_alerts_enabled', 'battery_health_warnings_enabled',
        'charging_reminders_enabled', 'maintenance_reminders_enabled',
        'push_notifications_enabled', 'in_app_notifications_enabled',
    ]
    for field in bool_fields:
        if field in data:
            setattr(prefs, field, bool(data[field]))

    numeric_fields = [
        'low_battery_threshold_pct', 'battery_health_threshold_pct',
        'charging_reminder_lead_minutes', 'maintenance_interval_km',
    ]
    for field in numeric_fields:
        if field in data and data[field] is not None:
            try:
                setattr(prefs, field, float(data[field]))
            except (TypeError, ValueError):
                return jsonify({'error': f'{field} must be a number'}), 400

    # Email is a User-level field, kept here rather than duplicated on
    # NotificationPreference (see models/notification.py).
    if 'email_notifications_enabled' in data:
        current_user.email_notifications_enabled = bool(data['email_notifications_enabled'])

    db.session.commit()
    return jsonify(prefs.to_dict())


@notifications_bp.route('/api/maintenance/mark-serviced', methods=['POST'])
@login_required
def mark_serviced():
    """Resets the Maintenance Reminder baseline: 'as of this odometer
    reading (and right now), consider maintenance done.'"""
    prefs = get_or_create_preferences(current_user.id)
    data = request.get_json() or {}
    odometer_km = data.get('odometer_km')
    if odometer_km is None:
        return jsonify({'error': 'odometer_km is required'}), 400
    try:
        odometer_km = float(odometer_km)
    except (TypeError, ValueError):
        return jsonify({'error': 'odometer_km must be a number'}), 400

    prefs.maintenance_last_service_odometer_km = odometer_km
    prefs.maintenance_last_service_at = datetime.utcnow()
    prefs.maintenance_last_reminder_sent_at = None  # a fresh baseline clears any past-due reminder cooldown
    db.session.commit()
    return jsonify(prefs.to_dict())
