from datetime import datetime
from .. import db
import json

class Prediction(db.Model):
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('ev_vehicles.id'), nullable=False)

    # Weather inputs
    temperature_c = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=True)
    wind_speed_kmh = db.Column(db.Float, nullable=True)
    precipitation = db.Column(db.String(20), nullable=True)  # none, rain, snow
    atmospheric_pressure = db.Column(db.Float, nullable=True)

    # Vehicle state inputs
    battery_percentage = db.Column(db.Float, nullable=True, default=100.0)
    vehicle_speed_kmh = db.Column(db.Float, nullable=True, default=60.0)
    hvac_usage = db.Column(db.Boolean, default=True)
    terrain_type = db.Column(db.String(20), nullable=True, default='flat')  # flat, hilly, mountainous
    battery_age_years = db.Column(db.Float, nullable=True, default=0.0)

    # ML Predictions
    range_degradation_pct = db.Column(db.Float, nullable=True)
    predicted_range_km = db.Column(db.Float, nullable=True)
    energy_consumption_wh_km = db.Column(db.Float, nullable=True)
    charging_slowdown_pct = db.Column(db.Float, nullable=True)

    # ML model used
    ml_model_used = db.Column(db.String(50), nullable=True)
    prediction_confidence = db.Column(db.Float, nullable=True)

    # XAI explanations (stored as JSON)
    shap_explanation = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_shap_explanation(self):
        if self.shap_explanation:
            return json.loads(self.shap_explanation)
        return None

    def set_shap_explanation(self, explanation_dict):
        self.shap_explanation = json.dumps(explanation_dict)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vehicle_id': self.vehicle_id,
            'temperature_c': self.temperature_c,
            'humidity': self.humidity,
            'wind_speed_kmh': self.wind_speed_kmh,
            'precipitation': self.precipitation,
            'battery_percentage': self.battery_percentage,
            'vehicle_speed_kmh': self.vehicle_speed_kmh,
            'hvac_usage': self.hvac_usage,
            'terrain_type': self.terrain_type,
            'battery_age_years': self.battery_age_years,
            'range_degradation_pct': self.range_degradation_pct,
            'predicted_range_km': self.predicted_range_km,
            'energy_consumption_wh_km': self.energy_consumption_wh_km,
            'charging_slowdown_pct': self.charging_slowdown_pct,
            'ml_model_used': self.ml_model_used,
            'prediction_confidence': self.prediction_confidence,
            'shap_explanation': self.get_shap_explanation(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Prediction {self.id} - {self.range_degradation_pct}%>'


class TripSimulation(db.Model):
    __tablename__ = 'trip_simulations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('ev_vehicles.id'), nullable=False)

    # Trip inputs
    source_location = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    temperature_c = db.Column(db.Float, nullable=False)
    speed_kmh = db.Column(db.Float, nullable=False, default=60)
    heater_usage = db.Column(db.Boolean, default=True)
    num_passengers = db.Column(db.Integer, default=1)

    # Trip outputs
    estimated_battery_usage_pct = db.Column(db.Float, nullable=True)
    predicted_remaining_range_km = db.Column(db.Float, nullable=True)
    charging_stops_required = db.Column(db.Integer, nullable=True)
    estimated_arrival_battery_pct = db.Column(db.Float, nullable=True)
    estimated_energy_kwh = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='trips')
    vehicle = db.relationship('EVVehicle', backref='trips')

    def to_dict(self):
        return {
            'id': self.id,
            'source_location': self.source_location,
            'destination': self.destination,
            'distance_km': self.distance_km,
            'temperature_c': self.temperature_c,
            'speed_kmh': self.speed_kmh,
            'heater_usage': self.heater_usage,
            'num_passengers': self.num_passengers,
            'estimated_battery_usage_pct': self.estimated_battery_usage_pct,
            'predicted_remaining_range_km': self.predicted_remaining_range_km,
            'charging_stops_required': self.charging_stops_required,
            'estimated_arrival_battery_pct': self.estimated_arrival_battery_pct,
            'estimated_energy_kwh': self.estimated_energy_kwh,
            'vehicle': self.vehicle.to_dict() if self.vehicle else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
