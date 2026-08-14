"""Explainable AI (Phase: Explainable AI expansion).

Builds on top of predict.py's shared feature-building path
(_build_feature_row -- see that function's own docstring for why
reusing it, rather than re-encoding features by hand, matters) and
xai.py's existing rule-based + basic SHAP explanation. This module adds:

  - LIME Explanations (model-agnostic -- works for every model type,
    including the neural network / stacking ensemble SHAP's
    TreeExplainer can't handle)
  - Counterfactual Explanations ("what if you turned off the heater /
    drove slower" -- direct re-prediction under a changed scenario,
    not a formal optimization-based counterfactual search)
  - Partial Dependence Plots + ICE plots (how the prediction changes
    as ONE feature varies, holding the rest of a scenario fixed)
  - SHAP Waterfall + Force Plot data (per-feature contributions from
    the model's base value to this specific prediction)
  - A Global Explanation Dashboard (SHAP importance aggregated across
    many synthetic scenarios, not just one prediction)
  - A richer Prediction Confidence breakdown

SHAP model support is deliberately limited to tree-based models (via
shap.TreeExplainer) and linear regression (via shap.LinearExplainer) --
the neural network (an sklearn Pipeline) and the stacking ensemble
don't have a fast, exact SHAP algorithm available; the only way to
explain them with SHAP would be shap.KernelExplainer, which is a
model-agnostic but VERY slow sampling-based approximation (thousands of
model evaluations per single explanation) -- not something to run
inside a request/response cycle. LIME is offered specifically to fill
that gap: it IS model-agnostic and fast enough for interactive use
(bounded num_samples, see lime_explanation() below), so every model
type gets at least one local explanation method available.
"""
import numpy as np
import pandas as pd

from .predict import load_model, FEATURE_COLS, _build_feature_row, ENSEMBLE_MODEL_NAMES, _ensemble_confidence
from .train import RAW_FEATURE_COLS, generate_synthetic_dataset
from . import feature_engineering as fe
from .physics import physics_baseline_degradation_pct

# Degradation predictions are clamped to this range everywhere in this
# app (see predict.py's get_prediction) -- applied here too so PDP/ICE/
# counterfactual curves can't show an out-of-range value get_prediction
# itself would never actually return.
_MIN_DEGRADATION, _MAX_DEGRADATION = 0, 65

CATEGORICAL_LABELS = {
    'precipitation': {0: 'none', 1: 'rain', 2: 'snow'},
    'terrain_type': {0: 'flat', 1: 'hilly', 2: 'mountainous'},
    'hvac_usage': {0: 'off', 1: 'on'},
}

FEATURE_DISPLAY_NAMES = {
    'temperature_c': 'Temperature (C)', 'humidity': 'Humidity (%)',
    'wind_speed_kmh': 'Wind Speed (km/h)', 'precipitation': 'Precipitation',
    'battery_percentage': 'Battery Level (%)', 'vehicle_speed_kmh': 'Vehicle Speed (km/h)',
    'hvac_usage': 'Cabin Heater', 'terrain_type': 'Terrain', 'battery_age_years': 'Battery Age (years)',
    'battery_capacity_kwh': 'Battery Capacity (kWh)', 'epa_range_km': 'EPA Range (km)',
    'vehicle_weight_kg': 'Vehicle Weight (kg)', 'physics_baseline_degradation': 'Physics Baseline',
    'wind_chill_index': 'Wind Chill Index', 'hvac_cold_interaction': 'Heater x Cold Interaction',
    'speed_squared_norm': 'Speed^2 (drag proxy)', 'is_freezing': 'Below Freezing',
}

# Which raw inputs are meaningful to vary independently for a PDP/ICE
# plot. Excludes physics_baseline_degradation and every engineered
# feature (feature_engineering.ENGINEERED_FEATURE_COLS) -- those are
# DERIVED from the raw inputs (see that module's docstring), so
# "holding everything else fixed while varying wind_chill_index
# directly" would be physically incoherent; _rebuild_row() below always
# recomputes them from whichever raw feature was actually varied.
PDP_SELECTABLE_FEATURES = [c for c in RAW_FEATURE_COLS if c != 'physics_baseline_degradation']


def _predict_degradation(model, features):
    """Direct model.predict() for one scenario, clamped the same way
    predict.get_prediction() clamps its headline number. Used
    everywhere in this module instead of calling get_prediction()
    directly, since get_prediction() also loads and runs every
    ensemble member to compute a confidence score -- unnecessary
    overhead when PDP/ICE/counterfactuals need dozens of predictions
    from ONE model as fast as possible.
    """
    _, X = _build_feature_row(features)
    pred = float(model.predict(X)[0])
    return float(np.clip(pred, _MIN_DEGRADATION, _MAX_DEGRADATION))


def _rebuild_row(features, override_feature, override_value):
    """Apply ONE override on top of a features dict and re-derive every
    value that logically depends on it (physics_baseline_degradation
    depends on temperature_c; every engineered feature depends on
    several raw inputs) -- see feature_engineering.py's docstring for
    why recomputing these, rather than leaving stale values in place,
    matters for correctness. Returns a new features dict ready for
    _predict_degradation()/get_prediction().
    """
    updated = dict(features)
    updated[override_feature] = override_value
    return updated


def _feature_grid(feature_name, current_value, n_points=12):
    """Value grid for a PDP/ICE plot's x-axis. Weather/driving features
    get fixed, documented absolute ranges (matching the physically
    plausible range train.py's synthetic dataset generator itself
    samples from); vehicle-spec features (battery capacity, EPA range,
    weight) instead get a +/-30% window around the CURRENT vehicle's
    own value, since there's no single sensible absolute range across
    every EV this app might model.
    """
    categorical_grids = {
        'precipitation': [0, 1, 2],
        'terrain_type': [0, 1, 2],
        'hvac_usage': [0, 1],
    }
    if feature_name in categorical_grids:
        return categorical_grids[feature_name]

    absolute_ranges = {
        'temperature_c': (-30, 40),
        'humidity': (0, 100),
        'wind_speed_kmh': (0, 80),
        'battery_percentage': (5, 100),
        'vehicle_speed_kmh': (10, 150),
        'battery_age_years': (0, 15),
    }
    if feature_name in absolute_ranges:
        lo, hi = absolute_ranges[feature_name]
        return [round(v, 1) for v in np.linspace(lo, hi, n_points)]

    # Vehicle-spec fallback: relative window around the current value.
    base = current_value if current_value else 1.0
    lo, hi = base * 0.7, base * 1.3
    return [round(v, 1) for v in np.linspace(lo, hi, n_points)]


# ─────────────────────────── LIME ───────────────────────────

_LIME_BACKGROUND = None


def _get_lime_background(n_samples=500):
    """A small synthetic sample LIME uses to learn each feature's
    plausible distribution (needed to generate realistic local
    perturbations around an instance) -- built once per process and
    cached, since it's the same for every LIME call regardless of
    which specific prediction is being explained.
    """
    global _LIME_BACKGROUND
    if _LIME_BACKGROUND is None:
        df = generate_synthetic_dataset(n_samples=n_samples)
        _LIME_BACKGROUND = df[FEATURE_COLS].to_numpy(dtype=float)
    return _LIME_BACKGROUND


def lime_explanation(features, model_name='random_forest', num_features=8, num_samples=1000):
    """LIME Explanations: a local, model-agnostic explanation of one
    prediction, fitting a simple interpretable model (weighted linear
    regression, LIME's default) to the target model's behavior in the
    immediate neighborhood of this specific input.

    `num_samples` is capped well below LIME's default (5005) so this
    stays fast enough for an interactive request -- fewer perturbation
    samples means a slightly noisier local approximation, an accepted
    trade-off for API-call latency.
    """
    try:
        import lime.lime_tabular
    except ImportError:
        return {'available': False, 'reason': "The 'lime' package is not installed."}

    model = load_model(model_name)
    if model is None:
        return {'available': False, 'reason': f"Model '{model_name}' is not available."}

    _, X = _build_feature_row(features)
    background = _get_lime_background()

    categorical_feature_indices = [FEATURE_COLS.index(c) for c in ('precipitation', 'terrain_type', 'hvac_usage', 'is_freezing') if c in FEATURE_COLS]

    explainer = lime.lime_tabular.LimeTabularExplainer(
        background, feature_names=FEATURE_COLS, mode='regression',
        categorical_features=categorical_feature_indices, discretize_continuous=True,
        random_state=42,
    )
    exp = explainer.explain_instance(
        X.to_numpy(dtype=float)[0], model.predict, num_features=num_features, num_samples=num_samples,
    )

    return {
        'available': True,
        'model_name': model_name,
        'local_prediction': round(float(exp.local_pred[0]), 2) if exp.local_pred is not None else None,
        'model_prediction': round(float(exp.predicted_value), 2),
        'intercept': round(float(exp.intercept[1]), 3) if isinstance(exp.intercept, dict) else round(float(exp.intercept), 3),
        'explanations': [
            {'condition': condition, 'weight': round(weight, 4)}
            for condition, weight in exp.as_list()
        ],
        'note': f"Local linear approximation fit around this specific input using {num_samples} perturbation samples.",
    }


# ─────────────────────── Counterfactual ───────────────────────

def _cf_toggle_heater(features):
    if not features.get('hvac_usage', True):
        return None  # already off -- nothing to toggle
    return {**features, 'hvac_usage': False}


def _cf_reduce_speed(features):
    speed = features.get('vehicle_speed_kmh', 60)
    if speed <= 50:
        return None  # already driving slowly -- little room for this scenario
    return {**features, 'vehicle_speed_kmh': round(max(50, speed * 0.75), 1)}


def _cf_avoid_hills(features):
    if features.get('terrain_type', 'flat') == 'flat':
        return None
    return {**features, 'terrain_type': 'flat'}


def _cf_warm_up_battery(features):
    # Not literally "warm up the battery" as a driver action -- framed
    # as "if this trip happened on a milder day instead" to show how
    # much of the degradation is temperature-driven versus behavioral.
    temp = features.get('temperature_c', 20)
    if temp >= 10:
        return None
    return {**features, 'temperature_c': round(temp + 15, 1)}


COUNTERFACTUAL_SCENARIOS = [
    ('turn_off_heater', 'Turn off the cabin heater', _cf_toggle_heater),
    ('drive_slower', 'Drive about 25% slower', _cf_reduce_speed),
    ('avoid_hilly_terrain', 'Take a flatter route', _cf_avoid_hills),
    ('warmer_day', 'If it were 15C warmer', _cf_warm_up_battery),
]


def counterfactual_explanations(features, model_name='random_forest'):
    """Counterfactual Explanations: for each of a small set of concrete,
    ACTIONABLE (or at least interpretable) scenarios, re-run the model
    and show how much the predicted degradation would change. This is
    direct re-prediction under a hand-picked alternative scenario, not
    a formal counterfactual-search algorithm (e.g. DiCE) that solves
    for the minimal feature change achieving a target outcome -- a
    much heavier dependency for a handful of genuinely useful,
    explainable scenarios that don't need one.
    """
    model = load_model(model_name)
    if model is None:
        return {'available': False, 'reason': f"Model '{model_name}' is not available."}

    baseline_degradation = _predict_degradation(model, features)
    scenarios = []
    for key, description, transform in COUNTERFACTUAL_SCENARIOS:
        alt_features = transform(features)
        if alt_features is None:
            continue
        alt_degradation = _predict_degradation(model, alt_features)
        delta = round(alt_degradation - baseline_degradation, 2)
        scenarios.append({
            'scenario': key,
            'description': description,
            'baseline_degradation_pct': round(baseline_degradation, 1),
            'counterfactual_degradation_pct': round(alt_degradation, 1),
            'delta_pct': delta,
            'improves_range': delta < 0,
        })

    scenarios.sort(key=lambda s: s['delta_pct'])
    return {
        'available': True,
        'model_name': model_name,
        'baseline_degradation_pct': round(baseline_degradation, 1),
        'scenarios': scenarios,
    }


# ───────────────────────── PDP + ICE ─────────────────────────

# Fixed, documented reference scenarios for ICE lines (see PDP/ICE
# docstring below for why these are hand-picked rather than random
# synthetic samples). Each is a partial override merged onto the
# CURRENT request's own features -- so archetypes vary weather/driving
# conditions, never the vehicle itself.
ICE_ARCHETYPES = [
    ('this_scenario', 'This scenario', {}),
    ('mild_day', 'Mild day, heater off', {'temperature_c': 15, 'hvac_usage': False, 'wind_speed_kmh': 5, 'precipitation': 'none'}),
    ('harsh_winter', 'Harsh winter storm', {'temperature_c': -25, 'hvac_usage': True, 'wind_speed_kmh': 40, 'precipitation': 'snow'}),
    ('highway_commute', 'Highway commute', {'vehicle_speed_kmh': 110, 'terrain_type': 'flat'}),
    ('mountain_drive', 'Mountain drive', {'terrain_type': 'mountainous', 'vehicle_speed_kmh': 70}),
]


def pdp_ice(features, feature_name, model_name='random_forest', n_points=12):
    """Partial Dependence Plot + ICE Plot in one call -- a PDP is just
    the average of many ICE curves, so computing them together avoids
    running the same grid twice.

    ICE lines use a small set of hand-picked, DOCUMENTED reference
    scenarios (ICE_ARCHETYPES) rather than random rows from the
    training set, so every line on the plot is individually
    interpretable ("mountain drive", "harsh winter storm") instead of
    an opaque "sample #47".
    """
    if feature_name not in PDP_SELECTABLE_FEATURES:
        return {'available': False, 'reason': f"'{feature_name}' is not a PDP-selectable feature.",
                'selectable_features': PDP_SELECTABLE_FEATURES}

    model = load_model(model_name)
    if model is None:
        return {'available': False, 'reason': f"Model '{model_name}' is not available."}

    _, X = _build_feature_row(features)
    current_processed_value = X.iloc[0][feature_name] if feature_name in X.columns else features.get(feature_name)
    grid = _feature_grid(feature_name, current_processed_value, n_points)

    ice_curves = []
    for key, label, overrides in ICE_ARCHETYPES:
        scenario_base = {**features, **overrides}
        curve = []
        for grid_value in grid:
            scenario = _rebuild_row(scenario_base, feature_name, grid_value)
            pred = _predict_degradation(model, scenario)
            curve.append({'value': grid_value, 'degradation_pct': round(pred, 2)})
        ice_curves.append({'key': key, 'label': label, 'is_current_scenario': key == 'this_scenario', 'curve': curve})

    pdp_curve = [
        {'value': grid[i], 'degradation_pct': round(float(np.mean([c['curve'][i]['degradation_pct'] for c in ice_curves])), 2)}
        for i in range(len(grid))
    ]

    return {
        'available': True,
        'model_name': model_name,
        'feature': feature_name,
        'feature_display_name': FEATURE_DISPLAY_NAMES.get(feature_name, feature_name),
        'categorical_labels': CATEGORICAL_LABELS.get(feature_name),
        'pdp': pdp_curve,
        'ice_curves': ice_curves,
    }


# ─────────────────────────── SHAP ───────────────────────────

def _shap_explainer_for(model, background=None):
    """Pick the right (fast, exact) SHAP algorithm for a model type, or
    None if this model isn't one of the supported types (see module
    docstring for why the neural network / stacking ensemble aren't
    covered)."""
    import shap
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

    if isinstance(model, LinearRegression):
        return shap.LinearExplainer(model, background)

    tree_types = [RandomForestRegressor, GradientBoostingRegressor]
    try:
        from xgboost import XGBRegressor
        tree_types.append(XGBRegressor)
    except ImportError:
        pass
    try:
        from lightgbm import LGBMRegressor
        tree_types.append(LGBMRegressor)
    except ImportError:
        pass
    try:
        from catboost import CatBoostRegressor
        tree_types.append(CatBoostRegressor)
    except ImportError:
        pass

    if isinstance(model, tuple(tree_types)):
        return shap.TreeExplainer(model)
    return None


def _compute_shap_values(features, model_name):
    try:
        import shap  # noqa: F401 -- import check only, used via _shap_explainer_for
    except ImportError:
        return None, None, None, 'shap_not_installed'

    model = load_model(model_name)
    if model is None:
        return None, None, None, 'model_not_available'

    _, X = _build_feature_row(features)
    background = _get_lime_background()  # reuse the same cached synthetic sample as LIME's background
    explainer = _shap_explainer_for(model, background)
    if explainer is None:
        return None, None, None, 'unsupported_model_type'

    shap_values = explainer.shap_values(X)
    values = np.array(shap_values[0] if isinstance(shap_values, list) else shap_values[0])
    base_value = explainer.expected_value
    if isinstance(base_value, (list, np.ndarray)):
        base_value = float(np.ravel(base_value)[0])
    return values, float(base_value), X, None


_UNSUPPORTED_SHAP_REASON = {
    'shap_not_installed': "The 'shap' package is not installed.",
    'model_not_available': 'Model is not available.',
    'unsupported_model_type': "SHAP isn't available for this model type here (see explainability.py's module "
                               "docstring) -- try the LIME explanation instead, which works for every model.",
}


def shap_waterfall(features, model_name='random_forest'):
    """SHAP Waterfall Plot data: every feature's contribution, in
    order from largest to smallest absolute impact, as a running
    cumulative total from the model's base value to this prediction.
    """
    values, base_value, X, error = _compute_shap_values(features, model_name)
    if error:
        return {'available': False, 'reason': _UNSUPPORTED_SHAP_REASON[error]}

    order = np.argsort(-np.abs(values))
    steps = []
    running = base_value
    for idx in order:
        feature = FEATURE_COLS[idx]
        contribution = float(values[idx])
        running += contribution
        steps.append({
            'feature': feature,
            'display_name': FEATURE_DISPLAY_NAMES.get(feature, feature),
            'value': round(float(X.iloc[0][feature]), 2),
            'shap_value': round(contribution, 3),
            'cumulative': round(running, 2),
        })

    return {
        'available': True,
        'model_name': model_name,
        'base_value': round(base_value, 2),
        'prediction': round(running, 2),
        'steps': steps,
    }


def shap_force(features, model_name='random_forest'):
    """SHAP Force Plot data: the same per-feature contributions as the
    waterfall, regrouped into the two forces pushing the prediction
    away from the base value -- positive (pushing degradation up) and
    negative (pushing it down) -- which is the framing a force plot
    visualizes (opposing arrows converging on the final value).
    """
    values, base_value, X, error = _compute_shap_values(features, model_name)
    if error:
        return {'available': False, 'reason': _UNSUPPORTED_SHAP_REASON[error]}

    positive, negative = [], []
    for idx, contribution in enumerate(values):
        feature = FEATURE_COLS[idx]
        entry = {
            'feature': feature,
            'display_name': FEATURE_DISPLAY_NAMES.get(feature, feature),
            'value': round(float(X.iloc[0][feature]), 2),
            'shap_value': round(float(contribution), 3),
        }
        (positive if contribution >= 0 else negative).append(entry)

    positive.sort(key=lambda e: -e['shap_value'])
    negative.sort(key=lambda e: e['shap_value'])
    prediction = base_value + float(np.sum(values))

    return {
        'available': True,
        'model_name': model_name,
        'base_value': round(base_value, 2),
        'prediction': round(prediction, 2),
        'positive_forces': positive,
        'negative_forces': negative,
    }


def global_shap_summary(model_name='random_forest', n_samples=150):
    """Global Explanation Dashboard: SHAP importance aggregated across
    many synthetic scenarios (not just one prediction) -- mean absolute
    SHAP value per feature is the standard "global feature importance"
    reading of a set of local SHAP values, plus the min/max range each
    feature's contribution swung across the sample so a feature that's
    usually mild but occasionally huge (e.g. temperature_c) is
    distinguishable from one that's consistently moderate.
    """
    try:
        import shap
    except ImportError:
        return {'available': False, 'reason': "The 'shap' package is not installed."}

    model = load_model(model_name)
    if model is None:
        return {'available': False, 'reason': f"Model '{model_name}' is not available."}

    df = generate_synthetic_dataset(n_samples=n_samples)
    X = df[FEATURE_COLS]
    background = _get_lime_background()
    explainer = _shap_explainer_for(model, background)
    if explainer is None:
        return {'available': False, 'reason': _UNSUPPORTED_SHAP_REASON['unsupported_model_type']}

    shap_values = explainer.shap_values(X)
    values = np.array(shap_values)

    mean_abs = np.abs(values).mean(axis=0)
    ranked_idx = np.argsort(-mean_abs)

    global_importance = [
        {
            'feature': FEATURE_COLS[i],
            'display_name': FEATURE_DISPLAY_NAMES.get(FEATURE_COLS[i], FEATURE_COLS[i]),
            'mean_abs_shap': round(float(mean_abs[i]), 4),
            'min_shap': round(float(values[:, i].min()), 3),
            'max_shap': round(float(values[:, i].max()), 3),
        }
        for i in ranked_idx
    ]

    return {
        'available': True,
        'model_name': model_name,
        'n_samples': n_samples,
        'global_importance': global_importance,
    }


# ─────────────────────── Confidence ───────────────────────

def confidence_breakdown(features, model_name='random_forest'):
    """Prediction Confidence, explained rather than just reported: the
    same ensemble-agreement score predict.get_prediction() computes,
    plus the individual per-model predictions it's built from and a
    plain-language interpretation of the spread.
    """
    model = load_model(model_name)
    if model is None:
        return {'available': False, 'reason': f"Model '{model_name}' is not available."}

    predictions = {}
    for name in ENSEMBLE_MODEL_NAMES:
        m = load_model(name)
        if m is None:
            continue
        predictions[name] = round(_predict_degradation(m, features), 2)

    values = list(predictions.values())
    confidence = _ensemble_confidence(values)
    spread = round(float(np.std(values)), 2) if len(values) > 1 else None

    if confidence >= 0.85:
        interpretation = 'High confidence -- the models strongly agree on this prediction.'
    elif confidence >= 0.6:
        interpretation = 'Moderate confidence -- the models mostly agree, with some spread.'
    else:
        interpretation = 'Lower confidence -- the models disagree meaningfully for this input, likely an unusual combination of conditions.'

    return {
        'available': True,
        'confidence': confidence,
        'interpretation': interpretation,
        'individual_predictions': predictions,
        'spread_std_dev_pct': spread,
        'n_models': len(predictions),
    }
