"""Charging Reservation.

An internal, personal planning entry -- "I intend to charge at this
station at this time" -- NOT a real booking made with any charging
network. No major public charging network exposes a free reservation
API this app could integrate with (a handful of individual networks
have their own proprietary reservation systems inside their own apps,
not something a third party can book through), so this is scoped
honestly as a personal charging-plan calendar: it helps a user track
their own intended stops (and avoids double-booking themselves across
overlapping plans), but arriving at the station still works the same
as it would without a reservation.
"""
import json
from datetime import datetime, timedelta
from .. import db


class ChargingReservation(db.Model):
    __tablename__ = 'charging_reservations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('ev_vehicles.id'), nullable=False)

    station_name = db.Column(db.String(200), nullable=False)
    station_ocm_id = db.Column(db.Integer, nullable=True)  # Open Charge Map station ID, if booked from a real search result
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    reserved_start = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    target_pct = db.Column(db.Float, nullable=True)
    notes = db.Column(db.String(500), nullable=True)

    cancelled = db.Column(db.Boolean, default=False)
    # Charging Reminder: set once a reminder email/notification has gone
    # out for this reservation, so the scheduler tick doesn't re-send on
    # every pass through its lead-time window. Nullable/unset for every
    # reservation made before this feature existed -- those just won't
    # get a (now-moot, since they're in the past) retroactive reminder.
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='charging_reservations')
    vehicle = db.relationship('EVVehicle', backref='charging_reservations')

    @property
    def reserved_end(self):
        return self.reserved_start + timedelta(minutes=self.duration_minutes)

    @property
    def status(self):
        """Derived, not stored -- always consistent with the current
        time and duration without needing a background job to update
        it."""
        if self.cancelled:
            return 'cancelled'
        if datetime.utcnow() > self.reserved_end:
            return 'completed'
        return 'upcoming'

    def overlaps(self, other_start, other_duration_minutes):
        """True if [other_start, other_start+duration) overlaps this
        reservation's window -- used to warn a user double-booking
        themselves across two of their own planned stops (not a claim
        about the station's real capacity)."""
        other_end = other_start + timedelta(minutes=other_duration_minutes)
        return self.reserved_start < other_end and other_start < self.reserved_end

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'station_name': self.station_name,
            'station_ocm_id': self.station_ocm_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'reserved_start': self.reserved_start.isoformat() if self.reserved_start else None,
            'reserved_end': self.reserved_end.isoformat() if self.reserved_start else None,
            'duration_minutes': self.duration_minutes,
            'target_pct': self.target_pct,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
