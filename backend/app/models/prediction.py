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

    # FEAT-6: actual range the user later reports after really driving in
    # these conditions. Nullable/absent for the vast majority of rows
    # (most predictions never get a follow-up report) -- when present,
    # this is real ground truth that services/recalibration.py can use
    # to check and improve the model, instead of only ever validating
    # against the Phase 1 published-study benchmarks.
    actual_range_km = db.Column(db.Float, nullable=True)
    actual_range_reported_at = db.Column(db.DateTime, nullable=True)

    # Shareable public link: generated on-demand (not at prediction
    # time -- most predictions are never shared, so no reason to burn a
    # random token for every single one). NULL until the first time a
    # user clicks "Share". A prediction with a set token is viewable,
    # read-only, by anyone with the link -- no login required, same
    # tradeoff any "share link" feature makes (see MEMORY.md).
    share_token = db.Column(db.String(43), nullable=True, unique=True, index=True)

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
            'actual_range_km': self.actual_range_km,
            'actual_range_reported_at': self.actual_range_reported_at.isoformat() if self.actual_range_reported_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Prediction {self.id} - {self.range_degradation_pct}%>'


class SavedPrediction(db.Model):
    """A user-bookmarked prediction -- distinct from Prediction History
    (which is just "every prediction I've ever run") and from
    share_token (which is about a link an outsider can view). This is
    the "I want to keep this one handy" flag a user sets deliberately,
    same relationship FavoriteVehicle has to the full vehicle catalog
    (see models/vehicle_interactions.py) -- one small join table per
    "star this" interaction, not a boolean column on the parent model,
    so bookmarking never needs a migration on the (much larger,
    more-frequently-written) predictions table itself.
    """
    __tablename__ = 'saved_predictions'
    __table_args__ = (db.UniqueConstraint('user_id', 'prediction_id', name='uq_saved_user_prediction'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prediction_id = db.Column(db.Integer, db.ForeignKey('predictions.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='saved_predictions')
    prediction = db.relationship('Prediction')


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


class CommunityRangeReport(db.Model):
    """FEAT-4: standalone, crowdsourced real-world range reports -- not
    tied to any specific prediction the way Prediction.actual_range_km
    (FEAT-6) is. Anyone can submit "here's what my EV actually got in
    these conditions" without having made a prediction first. This is
    the real, direct fix for the row-level-real-data gap documented in
    TECHNICAL_ARCHITECTURE.md Sec 5/6 -- FEAT-6 improves accuracy for
    people who already used this app; this is how the app could
    eventually have real telemetry for vehicles/conditions nobody here
    has ever predicted for.
    """
    __tablename__ = 'community_range_reports'

    id = db.Column(db.Integer, primary_key=True)
    # Nullable so a deleted account's community reports can be
    # anonymized (user_id set to NULL) instead of either cascading the
    # delete (destroying real, still-useful shared data) or leaving a
    # dangling foreign key -- see the account-deletion endpoint in
    # auth.py and its reasoning in docs/MEMORY.md.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('ev_vehicles.id'), nullable=False)

    # Conditions during the real drive being reported
    temperature_c = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=True, default=50.0)
    wind_speed_kmh = db.Column(db.Float, nullable=True, default=10.0)
    precipitation = db.Column(db.String(20), nullable=True, default='none')
    vehicle_speed_kmh = db.Column(db.Float, nullable=True, default=60.0)
    hvac_usage = db.Column(db.Boolean, default=True)
    terrain_type = db.Column(db.String(20), nullable=True, default='flat')
    battery_age_years = db.Column(db.Float, nullable=True, default=0.0)

    # What actually happened
    starting_battery_pct = db.Column(db.Float, nullable=False)
    reported_range_km = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    # Lightweight moderation hook -- not enforced anywhere yet (no
    # review UI built), but having the column now means a future
    # moderation feature doesn't need a schema change; unreviewed
    # reports still count toward recalibration by default (see
    # services/recalibration.py) since gating on manual review would
    # make crowdsourcing this data much slower to ever accumulate
    # enough volume to matter.
    is_flagged = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='community_reports')
    vehicle = db.relationship('EVVehicle', backref='community_reports')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vehicle': self.vehicle.to_dict() if self.vehicle else None,
            'temperature_c': self.temperature_c,
            'humidity': self.humidity,
            'wind_speed_kmh': self.wind_speed_kmh,
            'precipitation': self.precipitation,
            'vehicle_speed_kmh': self.vehicle_speed_kmh,
            'hvac_usage': self.hvac_usage,
            'terrain_type': self.terrain_type,
            'battery_age_years': self.battery_age_years,
            'starting_battery_pct': self.starting_battery_pct,
            'reported_range_km': self.reported_range_km,
            'notes': self.notes,
            'is_flagged': self.is_flagged,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
