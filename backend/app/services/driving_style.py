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


# Green Driving Score: a 0-100 translation of analyze_driving_style()'s
# real classification (average recorded speed + consistency across a
# user's actual prediction/trip history) -- not a new metric computed
# from different data, just a friendlier framing of the same analysis.
# Consistency matters here too: a driver who's always steady at 60km/h
# scores better than one who averages 60 but swings wildly between 30
# and 100, since that swinginess itself burns extra energy (harsh
# acceleration/braking) that a bare average speed doesn't capture.
_STYLE_BASE_SCORE = {'eco': 90, 'moderate': 70, 'aggressive': 45}
CONSISTENCY_PENALTY_PER_KMH_STDDEV = 1.5  # points off per km/h of speed std-dev, capped below
MAX_CONSISTENCY_PENALTY = 25


def green_driving_score(user_id, limit=100):
    """Returns a 0-100 Green Driving Score plus the breakdown it came
    from. Returns 'insufficient_data' gracefully (same as
    analyze_driving_style()) rather than guessing off too few samples.
    """
    analysis = analyze_driving_style(user_id, limit=limit)
    if analysis['status'] != 'ok':
        return analysis

    base = _STYLE_BASE_SCORE[analysis['driving_style']]
    consistency_penalty = min(MAX_CONSISTENCY_PENALTY, round(analysis['speed_std_dev_kmh'] * CONSISTENCY_PENALTY_PER_KMH_STDDEV))
    score = max(0, min(100, base - consistency_penalty))

    if score >= 80:
        grade = 'A'
    elif score >= 65:
        grade = 'B'
    elif score >= 50:
        grade = 'C'
    else:
        grade = 'D'

    return {
        'status': 'ok',
        'score': score,
        'grade': grade,
        'driving_style': analysis['driving_style'],
        'avg_speed_kmh': analysis['avg_speed_kmh'],
        'speed_std_dev_kmh': analysis['speed_std_dev_kmh'],
        'consistency_penalty': consistency_penalty,
        'n_samples': analysis['n_samples'],
        'note': (
            f"Base score for '{analysis['driving_style']}' driving is {base}/100; "
            f"{consistency_penalty} points deducted for speed consistency "
            f"(±{analysis['speed_std_dev_kmh']} km/h across your recent trips/predictions)."
        ),
    }
