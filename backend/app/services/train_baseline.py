"""Small helper: build a full ml/predict.py feature dict for a specific
vehicle using Phase 1's neutral BASELINE_TRIP_CONDITIONS for everything
that isn't vehicle-specific. Used by Battery Intelligence's efficiency
curve (and available for any future feature needing "a typical
prediction for this vehicle" without the caller re-deriving the
baseline every time).
"""


def typical_trip_features(vehicle):
    from ..ml.train import BASELINE_TRIP_CONDITIONS

    features = dict(BASELINE_TRIP_CONDITIONS)
    features['battery_capacity_kwh'] = vehicle.battery_capacity_kwh
    features['epa_range_km'] = vehicle.epa_range_km
    features['vehicle_weight_kg'] = vehicle.vehicle_weight_kg
    # temperature_c intentionally left out -- callers sweeping
    # temperature (e.g. generate_efficiency_curve) set it per-point.
    return features
