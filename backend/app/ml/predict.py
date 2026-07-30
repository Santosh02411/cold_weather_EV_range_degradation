"""ML Prediction Engine (v2 - Phase 1)

Two behavioural changes from v1:
  1. `physics_baseline_degradation` is computed for every request and fed
     in as a feature, matching how the models were trained (see train.py).
     Forgetting this step is a real bug that was hit while wiring this up
     - see docs/PROJECT_WORKFLOW.md - because the old FEATURE_COLS list
     silently changed shape and joblib's model.predict() doesn't
     complain about a missing/extra column by name, it just misaligns
     positionally, which is a much scarier failure mode.
  2. `confidence` is no longer a hardcoded 0.85. It's derived from how
     much the loaded models agree with each other for this specific
     input - low agreement (e.g. a very unusual combination of extreme
     cold + high speed + mountainous terrain) now genuinely produces a
     lower confidence score.
"""
import os
import joblib
import numpy as np
import pandas as pd

from .train import FEATURE_COLS, get_models_root, train_all_models
from .physics import physics_baseline_degradation_pct

_loaded_models = {}

# Kept as an alias since other modules (or notebooks/scripts) may still
# import the old name.
get_models_dir = get_models_root

ENSEMBLE_MODEL_NAMES = ['linear_regression', 'random_forest', 'gradient_boosting', 'xgboost']


def _encode_precipitation(val):
    mapping = {'none': 0, 'rain': 1, 'snow': 2}
    return mapping.get(str(val).lower(), 0)


def _encode_terrain(val):
    mapping = {'flat': 0, 'hilly': 1, 'mountainous': 2}
    return mapping.get(str(val).lower(), 0)


def load_model(model_name):
    if model_name in _loaded_models:
        return _loaded_models[model_name]

    models_dir = get_models_root()
    path = os.path.join(models_dir, f'{model_name}.pkl')

    if not os.path.exists(path):
        # Train models if not yet trained
        train_all_models()

    if os.path.exists(path):
        model = joblib.load(path)
        _loaded_models[model_name] = model
        return model
    return None


def get_available_models():
    models_dir = get_models_root()
    available = []
    for name in ['linear_regression', 'random_forest', 'xgboost', 'gradient_boosting']:
        path = os.path.join(models_dir, f'{name}.pkl')
        available.append({
            'name': name,
            'display_name': name.replace('_', ' ').title(),
            'available': os.path.exists(path),
        })
    return available


def _build_feature_row(features):
    """Encode categorical fields and attach the physics baseline feature.
    Returns (processed_dict, numpy row) so callers can reuse the dict.
    """
    processed = features.copy()
    if isinstance(processed.get('precipitation'), str):
        processed['precipitation'] = _encode_precipitation(processed['precipitation'])
    if isinstance(processed.get('hvac_usage'), bool):
        processed['hvac_usage'] = 1 if processed['hvac_usage'] else 0
    if isinstance(processed.get('terrain_type'), str):
        processed['terrain_type'] = _encode_terrain(processed['terrain_type'])

    temp = processed.get('temperature_c', 20)
    processed['physics_baseline_degradation'] = physics_baseline_degradation_pct(temp)

    # Built as a DataFrame with the exact training column names/order --
    # a raw numpy array here previously triggered a scikit-learn
    # "X does not have valid feature names" warning on every single
    # prediction, since the models were fit on a named DataFrame.
    # Harmless in this sklearn version, but worth fixing properly rather
    # than living with warning-per-request noise in production logs.
    row = {col: processed.get(col, 0) for col in FEATURE_COLS}
    X = pd.DataFrame([row], columns=FEATURE_COLS)
    return processed, X


def _ensemble_confidence(predictions):
    """Turn model disagreement into a 0-1 confidence score.

    predictions: list of raw degradation-pct predictions from each
    available model for the SAME input. Low spread -> high confidence.
    The scale (12 percentage points of spread -> ~0 confidence) is a
    judgment call, not derived from a formal statistical model - it's
    calibrated so that typical everyday inputs (where models usually
    agree within 1-3 points) land around 0.85-0.97, and genuinely
    unusual inputs (where models can disagree by 10+ points) drop
    below 0.5. It replaces the old hardcoded confidence=0.85 constant.
    """
    if len(predictions) < 2:
        return 0.6  # only one model available - can't measure agreement
    spread = float(np.std(predictions))
    confidence = 1.0 - (spread / 12.0)
    return round(float(np.clip(confidence, 0.15, 0.98)), 2)


def get_prediction(features, model_name='random_forest'):
    """Get range degradation prediction, plus an ensemble-agreement
    confidence score computed across every currently available model."""
    processed, X = _build_feature_row(features)

    model = load_model(model_name)
    if model is None:
        return _physics_prediction(features)

    all_predictions = {}
    for name in ENSEMBLE_MODEL_NAMES:
        m = load_model(name)
        if m is None:
            continue
        try:
            all_predictions[name] = float(m.predict(X)[0])
        except Exception as e:
            print(f"[WARN] Ensemble member '{name}' failed to predict: {e}")

    if model_name not in all_predictions:
        try:
            all_predictions[model_name] = float(model.predict(X)[0])
        except Exception as e:
            print(f"[ERROR] ML Prediction failed: {e}. Falling back to physics model.")
            return _physics_prediction(features)

    degradation = all_predictions[model_name]
    degradation = max(0, min(65, degradation))
    confidence = _ensemble_confidence(list(all_predictions.values()))

    epa_range = features.get('epa_range_km', 400)
    battery_pct = features.get('battery_percentage', 100)
    predicted_range = epa_range * (1 - degradation / 100) * (battery_pct / 100)

    # Energy consumption
    capacity = features.get('battery_capacity_kwh', 75)
    base_consumption = (capacity / epa_range) * 1000  # Wh/km
    actual_consumption = base_consumption * (1 + degradation / 100)

    # Charging slowdown: still an engineering estimate, not fit to a
    # real charging-curve dataset yet. Flagged for Phase 2 (see
    # docs/FEATURE_TICKET_LIST.md) once INL's cold-weather charging
    # time data or a real fast-charger telemetry source is wired in.
    temp = features.get('temperature_c', 20)
    if temp < -20:
        charging_slow = 60
    elif temp < -10:
        charging_slow = 45
    elif temp < 0:
        charging_slow = 30
    elif temp < 10:
        charging_slow = 15
    else:
        charging_slow = 0

    return {
        'range_degradation_pct': round(degradation, 1),
        'predicted_range_km': round(predicted_range, 1),
        'energy_consumption_wh_km': round(actual_consumption, 1),
        'charging_slowdown_pct': round(charging_slow, 1),
        'confidence': confidence,
        'confidence_note': f"based on agreement across {len(all_predictions)} models",
        'model_used': model_name,
        'models_in_ensemble': list(all_predictions.keys()),
        'physics_baseline_degradation_pct': round(processed['physics_baseline_degradation'], 1),
    }


def _physics_prediction(features):
    """Fallback physics-based prediction when no ML model is available,
    e.g. on a fresh clone before `python train.py` has been run. Now
    uses the same real-world-calibrated curve as training, instead of
    a second, separate set of hardcoded thresholds (v1 had two
    different guesses for the same relationship - a real inconsistency
    that surfaced while writing this doc)."""
    temp = features.get('temperature_c', 20)
    hvac = features.get('hvac_usage', True)

    deg = physics_baseline_degradation_pct(temp)
    if hvac and temp < 10:
        deg += 8

    deg = max(0, min(65, deg))

    epa_range = features.get('epa_range_km', 400)
    battery_pct = features.get('battery_percentage', 100)
    predicted_range = epa_range * (1 - deg / 100) * (battery_pct / 100)
    capacity = features.get('battery_capacity_kwh', 75)
    consumption = (capacity / epa_range) * 1000 * (1 + deg / 100)

    return {
        'range_degradation_pct': round(deg, 1),
        'predicted_range_km': round(predicted_range, 1),
        'energy_consumption_wh_km': round(consumption, 1),
        'charging_slowdown_pct': max(0, round((10 - temp) * 3, 1)) if temp < 10 else 0,
        'confidence': 0.4,
        'confidence_note': 'physics-only fallback, no trained model available',
        'model_used': 'physics_fallback',
        'models_in_ensemble': [],
        'physics_baseline_degradation_pct': round(deg, 1),
    }
