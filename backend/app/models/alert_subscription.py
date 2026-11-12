"""FEAT-3: push/email alerts for cold snaps affecting a saved location."""
from datetime import datetime
from .. import db


class AlertSubscription(db.Model):
    __tablename__ = 'alert_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    location = db.Column(db.String(120), nullable=False)  # city name, passed to the weather API
    temperature_threshold_c = db.Column(db.Float, nullable=False, default=-10.0)
    enabled = db.Column(db.Boolean, default=True)

    # Cooldown bookkeeping so a persistent cold snap doesn't spam an
    # email every time the scheduler runs (see ALERT_COOLDOWN_HOURS).
    last_alert_sent_at = db.Column(db.DateTime, nullable=True)
    last_checked_at = db.Column(db.DateTime, nullable=True)
    last_checked_temperature_c = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='alert_subscriptions')

    def to_dict(self):
        return {
            'id': self.id,
            'location': self.location,
            'temperature_threshold_c': self.temperature_threshold_c,
            'enabled': self.enabled,
            'last_alert_sent_at': self.last_alert_sent_at.isoformat() if self.last_alert_sent_at else None,
            'last_checked_at': self.last_checked_at.isoformat() if self.last_checked_at else None,
            'last_checked_temperature_c': self.last_checked_temperature_c,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
