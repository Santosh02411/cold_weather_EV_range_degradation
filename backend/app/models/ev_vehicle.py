from datetime import datetime
from .. import db

class EVVehicle(db.Model):
    __tablename__ = 'ev_vehicles'

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False, index=True)
    battery_capacity_kwh = db.Column(db.Float, nullable=False)
    epa_range_km = db.Column(db.Float, nullable=False)
    vehicle_weight_kg = db.Column(db.Float, nullable=False)
    battery_chemistry = db.Column(db.String(50), nullable=False)  # NMC, LFP, NCA, etc.
    charging_type = db.Column(db.String(100), nullable=False)  # CCS, CHAdeMO, Tesla Supercharger
    max_charging_power_kw = db.Column(db.Float, nullable=True)
    drivetrain = db.Column(db.String(20), nullable=True)  # AWD, FWD, RWD
    year = db.Column(db.Integer, nullable=True)
    energy_consumption_wh_km = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    predictions = db.relationship('Prediction', backref='vehicle', lazy='dynamic')

    @property
    def efficiency_rating(self):
        """Lower Wh/km = better efficiency"""
        if self.energy_consumption_wh_km:
            if self.energy_consumption_wh_km < 140:
                return 'Excellent'
            elif self.energy_consumption_wh_km < 170:
                return 'Good'
            elif self.energy_consumption_wh_km < 200:
                return 'Average'
            else:
                return 'Below Average'
        return 'Unknown'

    def to_dict(self):
        return {
            'id': self.id,
            'model_name': self.model_name,
            'manufacturer': self.manufacturer,
            'battery_capacity_kwh': self.battery_capacity_kwh,
            'epa_range_km': self.epa_range_km,
            'vehicle_weight_kg': self.vehicle_weight_kg,
            'battery_chemistry': self.battery_chemistry,
            'charging_type': self.charging_type,
            'max_charging_power_kw': self.max_charging_power_kw,
            'drivetrain': self.drivetrain,
            'year': self.year,
            'energy_consumption_wh_km': self.energy_consumption_wh_km,
            'efficiency_rating': self.efficiency_rating,
            'is_active': self.is_active,
        }

    def __repr__(self):
        return f'<EVVehicle {self.manufacturer} {self.model_name}>'
