"""Explainable AI Module — SHAP-based explanations"""
import numpy as np
from .predict import load_model, FEATURE_COLS, _encode_precipitation, _encode_terrain


def get_shap_explanation(features, model_name='random_forest'):
    """Generate human-readable explanation for prediction"""
    processed = features.copy()
    if isinstance(processed.get('precipitation'), str):
        processed['precipitation'] = _encode_precipitation(processed['precipitation'])
    if isinstance(processed.get('hvac_usage'), bool):
        processed['hvac_usage'] = 1 if processed['hvac_usage'] else 0
    if isinstance(processed.get('terrain_type'), str):
        processed['terrain_type'] = _encode_terrain(processed['terrain_type'])

    # Generate rule-based explanations (works without SHAP library)
    explanations = []
    temp = features.get('temperature_c', 20)
    hvac = features.get('hvac_usage', True)
    speed = features.get('vehicle_speed_kmh', 60)
    wind = features.get('wind_speed_kmh', 10)
    age = features.get('battery_age_years', 0)
    terrain = features.get('terrain_type', 'flat')
    precip = features.get('precipitation', 'none')

    if temp < -15:
        explanations.append({
            'factor': 'Extreme Cold Temperature',
            'impact': 'high_negative',
            'detail': f'Temperature {temp}°C causes severe battery chemical slowdown',
            'contribution_pct': 35
        })
    elif temp < 0:
        explanations.append({
            'factor': 'Below Freezing Temperature',
            'impact': 'negative',
            'detail': f'Temperature {temp}°C reduces battery ion mobility',
            'contribution_pct': 20
        })
    elif temp < 10:
        explanations.append({
            'factor': 'Cool Temperature',
            'impact': 'slight_negative',
            'detail': f'Temperature {temp}°C slightly impacts efficiency',
            'contribution_pct': 8
        })

    if hvac and temp < 10:
        explanations.append({
            'factor': 'Cabin Heater Active',
            'impact': 'negative',
            'detail': 'HVAC heating draws significant battery power',
            'contribution_pct': 12
        })

    if speed > 100:
        explanations.append({
            'factor': 'High Speed Driving',
            'impact': 'negative',
            'detail': f'Speed {speed} km/h increases aerodynamic drag exponentially',
            'contribution_pct': 10
        })

    if wind > 30:
        explanations.append({
            'factor': 'Strong Wind',
            'impact': 'negative',
            'detail': f'Wind at {wind} km/h increases air resistance',
            'contribution_pct': 5
        })

    if age > 3:
        explanations.append({
            'factor': 'Battery Aging',
            'impact': 'negative',
            'detail': f'Battery is {age:.1f} years old, capacity has degraded',
            'contribution_pct': 7
        })

    if terrain == 'mountainous':
        explanations.append({
            'factor': 'Mountainous Terrain',
            'impact': 'negative',
            'detail': 'Elevation changes increase energy consumption',
            'contribution_pct': 8
        })

    if precip == 'snow':
        explanations.append({
            'factor': 'Snow Conditions',
            'impact': 'negative',
            'detail': 'Snow increases rolling resistance and reduces traction',
            'contribution_pct': 5
        })

    if not explanations:
        explanations.append({
            'factor': 'Favorable Conditions',
            'impact': 'positive',
            'detail': 'Current conditions are good for EV efficiency',
            'contribution_pct': 0
        })

    # Try SHAP if available
    feature_importance = {}
    try:
        import shap
        model = load_model(model_name)
        if model and hasattr(model, 'predict'):
            X = np.array([[processed.get(col, 0) for col in FEATURE_COLS]])
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            feature_importance = dict(zip(FEATURE_COLS, shap_values[0].tolist()))
    except Exception:
        # Use feature importance from model instead
        model = load_model(model_name)
        if model and hasattr(model, 'feature_importances_'):
            feature_importance = dict(zip(FEATURE_COLS, model.feature_importances_.tolist()))

    return {
        'explanations': explanations,
        'feature_importance': feature_importance,
        'summary': _generate_summary(explanations),
    }


def _generate_summary(explanations):
    """Generate human-readable summary"""
    negative = [e for e in explanations if 'negative' in e.get('impact', '')]
    if not negative:
        return "Conditions are favorable. Minimal range degradation expected."

    reasons = [e['factor'] for e in negative[:3]]
    if len(reasons) == 1:
        return f"Range decreased primarily because of {reasons[0]}."
    elif len(reasons) == 2:
        return f"Range decreased because of {reasons[0]} and {reasons[1]}."
    else:
        return f"Range decreased because of {', '.join(reasons[:-1])}, and {reasons[-1]}."
