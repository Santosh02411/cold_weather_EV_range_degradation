"""ML Prediction Engine"""
import os, joblib
import numpy as np
from .train import FEATURE_COLS, get_models_dir, train_all_models

_loaded_models = {}


def _encode_precipitation(val):
    mapping = {'none': 0, 'rain': 1, 'snow': 2}
    return mapping.get(str(val).lower(), 0)

def _encode_terrain(val):
    mapping = {'flat': 0, 'hilly': 1, 'mountainous': 2}
    return mapping.get(str(val).lower(), 0)


def load_model(model_name):
    if model_name in _loaded_models:
        return _loaded_models[model_name]

    models_dir = get_models_dir()
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
    models_dir = get_models_dir()
    available = []
    for name in ['linear_regression', 'random_forest', 'xgboost', 'gradient_boosting']:
        path = os.path.join(models_dir, f'{name}.pkl')
        available.append({
            'name': name,
            'display_name': name.replace('_', ' ').title(),
            'available': os.path.exists(path),
        })
    return available


def get_prediction(features, model_name='random_forest'):
    """Get range degradation prediction"""
    # Encode categorical features
    processed = features.copy()
    if isinstance(processed.get('precipitation'), str):
        processed['precipitation'] = _encode_precipitation(processed['precipitation'])
    if isinstance(processed.get('hvac_usage'), bool):
        processed['hvac_usage'] = 1 if processed['hvac_usage'] else 0
    if isinstance(processed.get('terrain_type'), str):
        processed['terrain_type'] = _encode_terrain(processed['terrain_type'])

    # Build feature vector
    X = np.array([[processed.get(col, 0) for col in FEATURE_COLS]])

    model = load_model(model_name)
    if model is None:
        # Fallback physics-based prediction
        return _physics_prediction(features)

    try:
        degradation = float(model.predict(X)[0])
    except Exception as e:
        print(f"[ERROR] ML Prediction failed: {e}. Falling back to physics model.")
        return _physics_prediction(features)

    degradation = max(0, min(65, degradation))

    epa_range = features.get('epa_range_km', 400)
    battery_pct = features.get('battery_percentage', 100)
    predicted_range = epa_range * (1 - degradation / 100) * (battery_pct / 100)

    # Energy consumption
    capacity = features.get('battery_capacity_kwh', 75)
    base_consumption = (capacity / epa_range) * 1000  # Wh/km
    actual_consumption = base_consumption * (1 + degradation / 100)

    # Charging slowdown
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
        'confidence': 0.85,
        'model_used': model_name,
    }


def _physics_prediction(features):
    """Fallback physics-based prediction when no ML model available"""
    temp = features.get('temperature_c', 20)
    hvac = features.get('hvac_usage', True)

    if temp < -20:
        deg = 40
    elif temp < -10:
        deg = 28
    elif temp < 0:
        deg = 18
    elif temp < 10:
        deg = 10
    elif temp <= 25:
        deg = 2
    else:
        deg = 5

    if hvac and temp < 10:
        deg += 8

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
        'confidence': 0.6,
        'model_used': 'physics_fallback',
    }
