"""Feature engineering + feature selection for the range-degradation
models.

Kept dependency-free of Flask/DB (same convention as the rest of
app/ml/, see tests/conftest.py's load_app_module docstring) so it can
be imported and unit tested directly.

Two responsibilities:
  1. engineer_features() / engineer_feature_row() -- derive a small set
     of physically-motivated interaction features from the raw inputs.
     Both train.py's dataset generator and predict.py's single-row
     path call the SAME function so the two can never drift apart (a
     real bug class this project has hit before with the plain
     physics_baseline_degradation feature -- see train.py's module
     docstring).
  2. select_features() -- rank features by a trained model's importance
     and report a recommended reduced subset. This is a DIAGNOSTIC
     report only (surfaced on the admin ML dashboard so a human can see
     which inputs are pulling weight) -- it does not by itself change
     which columns the production models are trained/predicted on.
     Changing FEATURE_COLS is a deliberate, versioned decision (see
     train.py), not something a threshold should do silently, since a
     silently-shrinking feature set would desync predict.py's row
     builder from whatever the last training run happened to select.
"""
import numpy as np
import pandas as pd

# New columns this module adds on top of the raw inputs. Both train.py
# (FEATURE_COLS) and predict.py rely on this exact list/order.
ENGINEERED_FEATURE_COLS = [
    'wind_chill_index',
    'hvac_cold_interaction',
    'speed_squared_norm',
    'is_freezing',
]


def _compute(temperature_c, wind_speed_kmh, hvac_usage, vehicle_speed_kmh):
    # Simplified wind-chill proxy: colder air moving faster feels (and
    # draws heat) colder still. Not the full NWS wind-chill formula
    # (that also needs units/exponents this dataset doesn't cleanly
    # support) -- a linear proxy that captures the same direction of
    # effect for feature-engineering purposes.
    wind_chill_index = temperature_c - (wind_speed_kmh * 0.15)

    # HVAC draws disproportionately more as it gets colder (AAA: cabin
    # heating load rises sharply below ~10C) -- an explicit interaction
    # term so tree models don't have to rediscover the multiplicative
    # relationship by splitting on both features separately.
    hvac_cold_interaction = hvac_usage * np.maximum(0, 10 - temperature_c)

    # Aerodynamic drag scales with the square of speed, not speed
    # itself. Normalized by 1000 to keep it on a similar scale to the
    # other features (helps the neural network's gradient-based
    # optimizer, which is sensitive to wildly different feature
    # scales even after standardization of the raw inputs).
    speed_squared_norm = (vehicle_speed_kmh ** 2) / 1000.0

    is_freezing = (temperature_c < 0).astype(float) if hasattr(temperature_c, 'astype') else float(temperature_c < 0)

    return wind_chill_index, hvac_cold_interaction, speed_squared_norm, is_freezing


def engineer_features(df):
    """Add ENGINEERED_FEATURE_COLS to a DataFrame that already has the
    raw columns (temperature_c, wind_speed_kmh, hvac_usage,
    vehicle_speed_kmh). Returns a new DataFrame (does not mutate the
    input in place, to avoid surprising callers that still hold a
    reference to the original)."""
    out = df.copy()
    wci, hci, ssn, frz = _compute(
        out['temperature_c'].to_numpy(dtype=float),
        out['wind_speed_kmh'].to_numpy(dtype=float),
        out['hvac_usage'].to_numpy(dtype=float),
        out['vehicle_speed_kmh'].to_numpy(dtype=float),
    )
    out['wind_chill_index'] = wci
    out['hvac_cold_interaction'] = hci
    out['speed_squared_norm'] = ssn
    out['is_freezing'] = frz
    return out


def engineer_feature_row(processed):
    """Same computation as engineer_features(), for a single already-
    encoded feature dict (predict.py's per-request path). Returns a
    NEW dict with the engineered keys merged in.
    """
    temp = float(processed.get('temperature_c', 20))
    wind = float(processed.get('wind_speed_kmh', 0) or 0)
    hvac = float(processed.get('hvac_usage', 0) or 0)
    speed = float(processed.get('vehicle_speed_kmh', 0) or 0)

    wci, hci, ssn, frz = _compute(temp, wind, hvac, speed)
    result = dict(processed)
    result['wind_chill_index'] = wci
    result['hvac_cold_interaction'] = hci
    result['speed_squared_norm'] = ssn
    result['is_freezing'] = frz
    return result


def select_features(importance_dict, cumulative_threshold=0.95, always_keep=('physics_baseline_degradation',)):
    """Rank features by importance (highest first) and report the
    smallest prefix of that ranking whose importances sum to at least
    `cumulative_threshold` of the total -- a standard cumulative-
    importance feature-selection report. Features named in
    `always_keep` are always included in the selected set regardless
    of rank, since they encode domain knowledge (the physics baseline)
    rather than something a purely data-driven ranking should be able
    to drop.

    Returns a dict shaped for direct JSON display on the admin
    dashboard: ranked list + which ones are recommended + how much
    combined importance the recommended subset covers.
    """
    total = sum(importance_dict.values())
    if not importance_dict or total <= 0:
        return {'ranked': [], 'selected_features': list(always_keep), 'cumulative_importance_covered': 0.0}

    ranked = sorted(importance_dict.items(), key=lambda kv: kv[1], reverse=True)

    selected = []
    running = 0.0
    for name, score in ranked:
        if running / total >= cumulative_threshold and name not in always_keep:
            continue
        selected.append(name)
        running += score

    for feat in always_keep:
        if feat not in selected:
            selected.append(feat)

    return {
        'ranked': [{'feature': name, 'importance': round(score, 5),
                    'importance_pct': round(100 * score / total, 2)} for name, score in ranked],
        'selected_features': selected,
        'dropped_features': [name for name, _ in ranked if name not in selected],
        'cumulative_importance_covered': round(min(running / total, 1.0), 4),
        'cumulative_threshold': cumulative_threshold,
    }
