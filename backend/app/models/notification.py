"""In-app notifications + per-user notification preferences.

Two separate concerns, two tables:
  - Notification: the actual inbox -- one row per event a user was
    told about, persisted so "In-App Notifications" has something real
    to show (not just a toast that vanishes).
  - NotificationPreference: one row per user, the on/off switches (and
    thresholds) that gate whether a given event creates a Notification
    row and/or an email at all.

Severe Weather Alerts deliberately has NO toggle here -- it already has
its own richer subscription model (AlertSubscription: per-location,
per-threshold, multiple subscriptions per user) that predates this and
does a strictly better job than a single boolean could. This file is
for the alert types that didn't have a home yet.
"""
from datetime import datetime
from .. import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    type = db.Column(db.String(30), nullable=False)  # low_battery, battery_health, charging_reminder, maintenance
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(300), nullable=True)  # where "view" should take the user, if anywhere

    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'url': self.url,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    # --- Alert types (Severe Weather Alerts lives in AlertSubscription, not here) ---
    low_battery_alerts_enabled = db.Column(db.Boolean, default=True)
    low_battery_threshold_pct = db.Column(db.Float, default=20.0)  # trip-simulation arrival battery %

    battery_health_warnings_enabled = db.Column(db.Boolean, default=True)
    battery_health_threshold_pct = db.Column(db.Float, default=80.0)  # SOH % floor

    charging_reminders_enabled = db.Column(db.Boolean, default=True)
    charging_reminder_lead_minutes = db.Column(db.Integer, default=30)

    maintenance_reminders_enabled = db.Column(db.Boolean, default=False)  # opt-in: needs the user to set a baseline first
    maintenance_interval_km = db.Column(db.Float, default=10000.0)
    maintenance_last_service_odometer_km = db.Column(db.Float, nullable=True)
    maintenance_last_service_at = db.Column(db.DateTime, nullable=True)
    maintenance_last_reminder_sent_at = db.Column(db.DateTime, nullable=True)

    # --- Delivery channels ---
    # Email is User.email_notifications_enabled (already existed, reused rather than duplicated).
    push_notifications_enabled = db.Column(db.Boolean, default=False)  # browser Notification API, tab must be open -- see notifications/preferences.html
    in_app_notifications_enabled = db.Column(db.Boolean, default=True)  # master switch for creating Notification rows at all

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notification_preference', uselist=False))

    def to_dict(self):
        return {
            'low_battery_alerts_enabled': self.low_battery_alerts_enabled,
            'low_battery_threshold_pct': self.low_battery_threshold_pct,
            'battery_health_warnings_enabled': self.battery_health_warnings_enabled,
            'battery_health_threshold_pct': self.battery_health_threshold_pct,
            'charging_reminders_enabled': self.charging_reminders_enabled,
            'charging_reminder_lead_minutes': self.charging_reminder_lead_minutes,
            'maintenance_reminders_enabled': self.maintenance_reminders_enabled,
            'maintenance_interval_km': self.maintenance_interval_km,
            'maintenance_last_service_odometer_km': self.maintenance_last_service_odometer_km,
            'maintenance_last_service_at': self.maintenance_last_service_at.isoformat() if self.maintenance_last_service_at else None,
            'push_notifications_enabled': self.push_notifications_enabled,
            'in_app_notifications_enabled': self.in_app_notifications_enabled,
            'email_notifications_enabled': self.user.email_notifications_enabled if self.user else True,
        }
