"""Driving Style Analysis.

DB-aware (queries Prediction + TripSimulation for a user's own history)
so this lives in services/, not ml/ -- same split rationale as
services/drift_monitor.py's docstring.

Classifies a user's typical driving style from the speed values
they've actually entered across past predictions/trips, and suggests
an energy-consumption multiplier to apply on top of the base
prediction -- consistently faster-than-typical driving costs more
energy than the model's average-conditions estimate accounts for on
its own, independent of the trip's speed feature already doing some of
that work (this is a personalization layer, not a replacement for the
model's own speed feature).
"""
from statistics import mean, pstdev

from ..models.prediction import Prediction, TripSimulation

MIN_SAMPLES_FOR_CLASSIFICATION = 5

# Style buckets by average recorded speed relative to a typical mixed
# city/highway baseline (~70 km/h) -- documented thresholds, not
# derived from a formal driving-behavior study (this app has no
# telemetry/acceleration data, only the speed value users type in per
# prediction/trip, so speed level + consistency is the best available
# proxy for style).
_STYLE_THRESHOLDS = [
    (0, 55, 'eco', 0.95),
    (55, 85, 'moderate', 1.0),
    (85, float('inf'), 'aggressive', 1.12),
]


def _classify_avg_speed(avg_speed_kmh):
    for lo, hi, label, multiplier in _STYLE_THRESHOLDS:
        if lo <= avg_speed_kmh < hi:
            return label, multiplier
    return 'moderate', 1.0


def analyze_driving_style(user_id, limit=100):
    """Look at a user's most recent predictions + trip simulations'
    recorded speeds and classify their driving style. Returns
    'insufficient_data' gracefully rather than guessing off too few
    samples.
    """
    pred_speeds = [
        p.vehicle_speed_kmh for p in
        Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).limit(limit).all()
        if p.vehicle_speed_kmh is not None
    ]
    trip_speeds = [
        t.speed_kmh for t in
        TripSimulation.query.filter_by(user_id=user_id).order_by(TripSimulation.created_at.desc()).limit(limit).all()
        if t.speed_kmh is not None
    ]
    speeds = pred_speeds + trip_speeds

    if len(speeds) < MIN_SAMPLES_FOR_CLASSIFICATION:
        return {
            'status': 'insufficient_data',
            'n_samples': len(speeds),
            'min_samples_required': MIN_SAMPLES_FOR_CLASSIFICATION,
            'reason': 'Not enough prediction/trip history yet to classify driving style.',
        }

    avg_speed = mean(speeds)
    consistency = pstdev(speeds) if len(speeds) > 1 else 0.0
    style, multiplier = _classify_avg_speed(avg_speed)

    return {
        'status': 'ok',
        'n_samples': len(speeds),
        'avg_speed_kmh': round(avg_speed, 1),
        'speed_std_dev_kmh': round(consistency, 1),
        'driving_style': style,
        'consumption_multiplier': multiplier,
        'note': f"Based on {len(speeds)} recorded trip/prediction speeds. "
                f"'{style}' driving is estimated to use "
                f"{'more' if multiplier > 1 else ('less' if multiplier < 1 else 'about the same')} "
                "energy than the model's baseline estimate.",
    }
