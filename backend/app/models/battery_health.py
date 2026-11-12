"""FEAT-1: battery health (State of Health) tracking over time.

Distinct from Prediction/CommunityRangeReport (which capture a single
trip's outcome) -- this tracks a vehicle's overall battery health as it
degrades across its whole life, independent of any specific trip or
weather condition. Most EVs expose an estimated SOH % somewhere in their
own app/dashboard (Tesla, most others via a third-party OBD app, etc.);
this lets a user log that number over time and see the real trend.
"""
from datetime import datetime
from .. import db


class BatteryHealthRecord(db.Model):
    __tablename__ = 'battery_health_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('ev_vehicles.id'), nullable=False)

    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    soh_pct = db.Column(db.Float, nullable=False)  # State of Health, 0-100
    odometer_km = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='battery_health_records')
    vehicle = db.relationship('EVVehicle', backref='battery_health_records')

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'soh_pct': self.soh_pct,
            'odometer_km': self.odometer_km,
            'notes': self.notes,
        }
