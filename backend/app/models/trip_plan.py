"""Trip Planning phase: Saved Trips (a user's bookmarked trip
configurations, for quick reuse) and Trip Plans (a computed multi-stop
/ round-trip planning result, logged the same way TripSimulation logs
single-leg trips -- see models/prediction.py).

Kept as their own model file rather than added to models/prediction.py
since they're conceptually about PLANNING a trip (before it happens),
not a completed simulation/prediction result.
"""
import json
from datetime import datetime
from .. import db


class SavedTrip(db.Model):
    """A bookmarked trip configuration (stops + vehicle + round-trip
    flag) a user wants to quickly re-plan later with CURRENT
    conditions -- distinct from TripPlan below, which is a snapshot of
    one specific planning run's computed results at the time it ran.
    """
    __tablename__ = 'saved_trips'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('ev_vehicles.id'), nullable=False)

    name = db.Column(db.String(120), nullable=False)
    stops_json = db.Column(db.Text, nullable=False)  # JSON list of place name strings, in order
    round_trip = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='saved_trips')
    vehicle = db.relationship('EVVehicle', backref='saved_trips')

    @property
    def stops(self):
        try:
            return json.loads(self.stops_json)
        except (TypeError, ValueError):
            return []

    @stops.setter
    def stops(self, value):
        self.stops_json = json.dumps(value)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'vehicle_id': self.vehicle_id,
            'stops': self.stops,
            'round_trip': self.round_trip,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class TripPlan(db.Model):
    """A computed multi-stop (or round-trip) plan -- one row per
    /trip/api/plan run, analogous to TripSimulation but for a full
    itinerary instead of a single origin->destination leg. `legs_json`
    holds the full per-leg breakdown (distance, energy, charging stops,
    ETA contribution); the top-level columns are the aggregate totals a
    history list view wants without parsing JSON.
    """
    __tablename__ = 'trip_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('ev_vehicles.id'), nullable=False)

    stops_json = db.Column(db.Text, nullable=False)
    round_trip = db.Column(db.Boolean, default=False)
    driving_style = db.Column(db.String(20), nullable=True)

    total_distance_km = db.Column(db.Float, nullable=True)
    total_driving_duration_min = db.Column(db.Float, nullable=True)
    total_charging_time_min = db.Column(db.Float, nullable=True)
    total_eta_min = db.Column(db.Float, nullable=True)
    num_charging_stops = db.Column(db.Integer, nullable=True)
    feasible = db.Column(db.Boolean, nullable=True)  # False if even with charging stops the plan can't be completed

    legs_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='trip_plans')
    vehicle = db.relationship('EVVehicle', backref='trip_plans')

    @property
    def stops(self):
        try:
            return json.loads(self.stops_json)
        except (TypeError, ValueError):
            return []

    @stops.setter
    def stops(self, value):
        self.stops_json = json.dumps(value)

    @property
    def legs(self):
        try:
            return json.loads(self.legs_json) if self.legs_json else []
        except (TypeError, ValueError):
            return []

    @legs.setter
    def legs(self, value):
        self.legs_json = json.dumps(value)

    def to_dict(self, include_legs=True):
        d = {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'stops': self.stops,
            'round_trip': self.round_trip,
            'driving_style': self.driving_style,
            'total_distance_km': self.total_distance_km,
            'total_driving_duration_min': self.total_driving_duration_min,
            'total_charging_time_min': self.total_charging_time_min,
            'total_eta_min': self.total_eta_min,
            'num_charging_stops': self.num_charging_stops,
            'feasible': self.feasible,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_legs:
            d['legs'] = self.legs
        return d
