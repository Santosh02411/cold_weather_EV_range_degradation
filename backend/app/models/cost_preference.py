"""Cost Analysis models.

CostPreference: one row per user -- their own known electricity rates
(home / public fast), so every cost calculation in this app (the
calculator, Monthly Charging Cost, EV vs Petrol, Ownership, Savings)
can default to what THIS user actually pays instead of the generic
DEFAULT_RATES_USD_PER_KWH constants in services/charging_cost.py. Also
holds the petrol-side defaults (price per liter/gallon, car fuel
economy) used by the EV-vs-petrol comparisons, for the same reason --
set once, reused everywhere instead of re-entered on every calculator.

ChargingSession: an actual logged charging session (energy added, what
was paid, where, when) -- Charging Cost History. This is deliberately
separate from services/analytics.py's cost_analytics(), which
estimates spend from TripSimulation's *simulated* energy use.
ChargingSession is the real ledger of what a user says they actually
paid; cost_analytics is a projection from simulated driving. Neither
is a substitute for the other, and the UI is explicit about which is
which (see notes in api/cost.py).
"""
from datetime import datetime
from .. import db


class CostPreference(db.Model):
    __tablename__ = 'cost_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    # Electricity Price Integration -- null means "use the documented
    # DEFAULT_RATES_USD_PER_KWH estimate", same nullable-means-fallback
    # convention charging_cost.estimate_charging_cost() already uses
    # for its own custom_rate parameter.
    home_rate_usd_per_kwh = db.Column(db.Float, nullable=True)
    public_rate_usd_per_kwh = db.Column(db.Float, nullable=True)
    rate_region_label = db.Column(db.String(100), nullable=True)  # e.g. "US National Average" -- which regional lookup row (if any) was used to prefill the above

    # Sustainability: grid carbon intensity for this same region (see
    # services/grid_intensity.py) -- kept on this same table, and set
    # together with the rate fields above when a region is picked, so
    # "which region am I using" has one answer across Cost Analysis
    # and Sustainability rather than two separately-set preferences.
    grid_intensity_g_co2_per_kwh = db.Column(db.Float, nullable=True)

    # EV vs Petrol Cost Comparison / Ownership / Savings defaults
    petrol_price_per_liter = db.Column(db.Float, nullable=True)  # null -> service-level documented default
    petrol_l_per_100km = db.Column(db.Float, nullable=True)      # null -> service-level documented default
    annual_km = db.Column(db.Float, nullable=True)               # null -> service-level documented default

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('cost_preference', uselist=False))

    def to_dict(self):
        return {
            'home_rate_usd_per_kwh': self.home_rate_usd_per_kwh,
            'public_rate_usd_per_kwh': self.public_rate_usd_per_kwh,
            'rate_region_label': self.rate_region_label,
            'grid_intensity_g_co2_per_kwh': self.grid_intensity_g_co2_per_kwh,
            'petrol_price_per_liter': self.petrol_price_per_liter,
            'petrol_l_per_100km': self.petrol_l_per_100km,
            'annual_km': self.annual_km,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ChargingSession(db.Model):
    """Charging Cost History: a real, user-logged charging event."""
    __tablename__ = 'charging_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('ev_vehicles.id'), nullable=True)

    station_name = db.Column(db.String(200), nullable=True)  # null = home charging
    source = db.Column(db.String(20), nullable=False, default='home')  # home, level2, dc_fast
    energy_added_kwh = db.Column(db.Float, nullable=False)
    cost_usd = db.Column(db.Float, nullable=True)  # null = not entered; estimate() fills it from the user's saved/default rate
    is_cost_estimated = db.Column(db.Boolean, default=False)  # True when cost_usd was filled in rather than user-entered
    session_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(300), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='charging_sessions')
    vehicle = db.relationship('EVVehicle')

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'vehicle': f"{self.vehicle.manufacturer} {self.vehicle.model_name}" if self.vehicle else None,
            'station_name': self.station_name,
            'source': self.source,
            'energy_added_kwh': self.energy_added_kwh,
            'cost_usd': self.cost_usd,
            'is_cost_estimated': self.is_cost_estimated,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
