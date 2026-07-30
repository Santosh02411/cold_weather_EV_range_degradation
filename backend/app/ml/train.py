"""
ML Training Pipeline for Cold Weather EV Range Degradation (v2 - Phase 1)

Changes from v1 (see /docs/PROJECT_WORKFLOW.md for the full story):
  - Training data's temperature -> degradation relationship is generated
    from physics.py's isotonic curve, which is itself fit to real,
    cited, published cold-weather EV studies (Geotab, Recurrent Auto,
    AAA, DOE) instead of arbitrary hand-picked thresholds.
  - The physics baseline is exposed to every model as an explicit input
    feature ('physics_baseline_degradation'), so the ML models learn to
    CORRECT the physics estimate using the other operating conditions,
    rather than learn the temperature relationship from a blank slate.
  - Real train/validation/test split (70/15/15) plus k-fold cross-
    validation on the training set, reported per model.
  - A calibration check that scores the trained ensemble against the
    real-world benchmark table directly (not just against synthetic
    held-out data), so accuracy claims can be traced to real sources.
  - Ensemble-variance-based confidence (see predict.py) replaces the
    old hardcoded confidence=0.85.
  - Model versioning: every training run is written to its own
    saved_models/v<N>_<timestamp>/ directory with metadata, and
    saved_models/current_version.json points at the active version.
"""
import os
import json
import joblib
import csv
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from .physics import physics_baseline_batch, calibration_anchors
except ImportError:  # allows running this file standalone via `python train.py`
    from physics import physics_baseline_batch, calibration_anchors


CALIBRATION_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', '..',
    'data', 'real_world_calibration', 'temperature_range_benchmarks.csv'
)

FEATURE_COLS = [
    'temperature_c', 'humidity', 'wind_speed_kmh', 'precipitation',
    'battery_percentage', 'vehicle_speed_kmh', 'hvac_usage',
    'terrain_type', 'battery_age_years', 'battery_capacity_kwh',
    'epa_range_km', 'vehicle_weight_kg', 'physics_baseline_degradation',
]


def generate_synthetic_dataset(n_samples=8000, seed=42):
    """Generate training data whose temperature -> degradation
    relationship is grounded in physics.py's real-world-calibrated
    curve, with additional operating-condition effects layered on top.

    These additional effects (HVAC, wind, terrain, battery age, speed,
    precipitation, vehicle weight) are still engineering estimates --
    row-level, single-vehicle telemetry linking every one of these
    variables simultaneously to measured degradation is not available
    as a public dataset (see docs/TECHNICAL_ARCHITECTURE.md for what
    was checked and why). Keeping the temperature relationship
    grounded in cited real data, while being explicit that the rest
    is engineering-estimated, is the honest middle ground for a
    project without access to proprietary fleet telemetry.
    """
    rng = np.random.default_rng(seed)

    temperatures = rng.uniform(-30, 40, n_samples)
    humidity = rng.uniform(20, 100, n_samples)
    wind_speed = rng.uniform(0, 80, n_samples)
    precipitation_codes = rng.choice([0, 1, 2], n_samples, p=[0.6, 0.25, 0.15])
    battery_pct = rng.uniform(10, 100, n_samples)
    vehicle_speed = rng.uniform(20, 140, n_samples)
    hvac_usage = rng.choice([0, 1], n_samples, p=[0.3, 0.7])
    terrain_codes = rng.choice([0, 1, 2], n_samples, p=[0.5, 0.35, 0.15])
    battery_age = rng.uniform(0, 10, n_samples)
    battery_capacity = rng.choice([40, 58, 60, 72, 75, 77, 82, 85, 100], n_samples)
    epa_range = battery_capacity * rng.uniform(4.5, 6.5, n_samples)
    vehicle_weight = rng.uniform(1500, 2800, n_samples)

    # Real-world-calibrated temperature baseline (see physics.py)
    physics_baseline = physics_baseline_batch(temperatures)
    degradation = physics_baseline.copy()
    degradation += rng.normal(0, 2.0, n_samples)  # measurement/model noise

    # HVAC effect: bigger below 10C, matching AAA's finding that active
    # cabin heating adds up to ~40% loss on top of temperature alone.
    degradation += hvac_usage * np.where(temperatures < 10, 8, 3) * rng.uniform(0.8, 1.2, n_samples)
    # Wind resistance
    degradation += (wind_speed / 80) * 5 * rng.uniform(0.8, 1.2, n_samples)
    # High-speed aerodynamic drag effect
    degradation += np.where(vehicle_speed > 100, (vehicle_speed - 100) * 0.15, 0)
    # Terrain
    degradation += terrain_codes * 4
    # Battery age / calendar degradation (Geotab: ~2.3%/yr storage capacity loss)
    degradation += battery_age * 1.2
    # Precipitation (rolling resistance, wipers, defrost load)
    degradation += precipitation_codes * 2
    # Heavier vehicles draw more energy per km
    degradation += (vehicle_weight - 1800) / 1000 * 3

    degradation = np.clip(degradation, 0, 65)

    df = pd.DataFrame({
        'temperature_c': temperatures,
        'humidity': humidity,
        'wind_speed_kmh': wind_speed,
        'precipitation': precipitation_codes,
        'battery_percentage': battery_pct,
        'vehicle_speed_kmh': vehicle_speed,
        'hvac_usage': hvac_usage,
        'terrain_type': terrain_codes,
        'battery_age_years': battery_age,
        'battery_capacity_kwh': battery_capacity,
        'epa_range_km': epa_range,
        'vehicle_weight_kg': vehicle_weight,
        'physics_baseline_degradation': physics_baseline,
        'range_degradation_pct': np.round(degradation, 2),
    })

    return df


def get_models_root():
    base = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(base, 'saved_models')
    os.makedirs(root, exist_ok=True)
    return root


def _next_version(models_root):
    existing = [d for d in os.listdir(models_root) if d.startswith('v') and '_' in d]
    nums = []
    for d in existing:
        try:
            nums.append(int(d.split('_')[0][1:]))
        except ValueError:
            continue
    return (max(nums) + 1) if nums else 1


# Neutral "typical trip" backdrop used ONLY for the real-world calibration
# check. Using raw training-set medians here initially (v1 bug, see
# docs/PROJECT_WORKFLOW.md) skewed worst-case -- e.g. the median battery
# age and terrain pulled from a uniformly-sampled synthetic distribution
# don't represent the "average commute" the field studies were measuring,
# so predictions came out ~17-20 percentage points high across the board
# even at temperatures where the physics baseline itself was 0. The
# benchmarks describe ordinary daily driving (new-ish battery, mostly
# flat commuting, normal ambient wind, moderate speed), so that's what
# this baseline represents -- not a stress-test scenario.
BASELINE_TRIP_CONDITIONS = {
    'humidity': 60.0,
    'wind_speed_kmh': 12.0,
    'precipitation': 0,
    'battery_percentage': 70.0,
    'vehicle_speed_kmh': 60.0,
    'hvac_usage': 1,
    'terrain_type': 0,
    'battery_age_years': 1.0,
    'battery_capacity_kwh': 75.0,
    'epa_range_km': 75.0 * 5.4,
    'vehicle_weight_kg': 1900.0,
}


def run_calibration_check(models, feature_medians=None):
    """Score the trained models directly against the real published
    benchmark table (not synthetic data), holding every non-temperature
    feature at a neutral 'typical commute' baseline so the comparison
    isolates the temperature effect the benchmarks actually measured.
    `feature_medians` is accepted for backwards compatibility but no
    longer used as the backdrop -- see BASELINE_TRIP_CONDITIONS above.
    """
    if not os.path.exists(CALIBRATION_CSV):
        return {'status': 'skipped', 'reason': 'calibration CSV not found'}

    rows = []
    with open(CALIBRATION_CSV, newline='') as f:
        for row in csv.DictReader(f):
            rows.append(row)

    checks = []
    for row in rows:
        temp_c = float(row['temperature_c'])
        real_degradation = 100.0 - float(row['pct_of_rated_range_retained'])
        real_degradation = max(0.0, real_degradation)

        sample = dict(BASELINE_TRIP_CONDITIONS)
        sample['temperature_c'] = temp_c
        sample['physics_baseline_degradation'] = float(physics_baseline_batch(np.array([temp_c]))[0])
        X = pd.DataFrame([sample])[FEATURE_COLS]

        preds = {name: float(model.predict(X)[0]) for name, model in models.items()}
        ensemble_pred = float(np.mean(list(preds.values())))

        checks.append({
            'source': row['source'],
            'temperature_c': temp_c,
            'condition': row['condition'],
            'real_world_degradation_pct': round(real_degradation, 1),
            'model_ensemble_prediction_pct': round(ensemble_pred, 1),
            'abs_error_pct': round(abs(ensemble_pred - real_degradation), 1),
        })

    mae_vs_real = float(np.mean([c['abs_error_pct'] for c in checks]))
    return {
        'status': 'ok',
        'num_benchmark_points': len(checks),
        'mae_vs_real_world_benchmarks_pct': round(mae_vs_real, 2),
        'details': checks,
    }


def train_all_models(df=None, n_samples=8000):
    """Train all ML models, evaluate on a real train/val/test split with
    cross-validation, validate against real-world benchmarks, and save
    a new versioned model bundle. Returns the results dict that also
    gets written to disk."""
    if df is None:
        df = generate_synthetic_dataset(n_samples)

    X = df[FEATURE_COLS]
    y = df['range_degradation_pct']

    # 70 / 15 / 15 train / validation / test split
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.50, random_state=42)

    model_defs = {
        'linear_regression': LinearRegression(),
        'random_forest': RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1),
        'gradient_boosting': GradientBoostingRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42),
    }
    if HAS_XGBOOST:
        model_defs['xgboost'] = XGBRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42)

    results = {}
    trained_models = {}
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    for name, model in model_defs.items():
        # 5-fold cross-validation on the training split
        cv_scores = cross_val_score(model, X_train, y_train, cv=kf, scoring='neg_mean_absolute_error')
        cv_mae_mean = float(-cv_scores.mean())
        cv_mae_std = float(cv_scores.std())

        model.fit(X_train, y_train)
        trained_models[name] = model

        val_pred = model.predict(X_val)
        test_pred = model.predict(X_test)

        if hasattr(model, 'feature_importances_'):
            importance = dict(zip(FEATURE_COLS, model.feature_importances_.tolist()))
        elif hasattr(model, 'coef_'):
            importance = dict(zip(FEATURE_COLS, np.abs(model.coef_).tolist()))
        else:
            importance = {}

        results[name] = {
            'cross_validation': {
                'folds': 5,
                'mae_mean': round(cv_mae_mean, 4),
                'mae_std': round(cv_mae_std, 4),
            },
            'validation_set': {
                'mae': round(mean_absolute_error(y_val, val_pred), 4),
                'rmse': round(float(np.sqrt(mean_squared_error(y_val, val_pred))), 4),
                'r2_score': round(r2_score(y_val, val_pred), 4),
            },
            'held_out_test_set': {
                'mae': round(mean_absolute_error(y_test, test_pred), 4),
                'rmse': round(float(np.sqrt(mean_squared_error(y_test, test_pred))), 4),
                'r2_score': round(r2_score(y_test, test_pred), 4),
            },
            'feature_importance': importance,
        }

    # Real-world calibration check against the neutral "typical commute"
    # baseline (see BASELINE_TRIP_CONDITIONS).
    calibration_report = run_calibration_check(trained_models)

    # --- Versioned save ---
    models_root = get_models_root()
    version_num = _next_version(models_root)
    version_dir_name = f"v{version_num}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    version_dir = os.path.join(models_root, version_dir_name)
    os.makedirs(version_dir, exist_ok=True)

    for name, model in trained_models.items():
        joblib.dump(model, os.path.join(version_dir, f'{name}.pkl'))

    metadata = {
        'version': version_num,
        'version_dir': version_dir_name,
        'trained_at_utc': datetime.now(timezone.utc).isoformat(),
        'n_samples': n_samples,
        'feature_columns': FEATURE_COLS,
        'models_included': list(trained_models.keys()),
        'has_xgboost': HAS_XGBOOST,
        'metrics': results,
        'real_world_calibration': calibration_report,
        'physics_baseline_anchors': calibration_anchors(),
    }
    with open(os.path.join(version_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)

    # Point "current_version" at this run, but keep a copy of the flat
    # *.pkl layout the rest of the app (predict.py) expects, for
    # backwards compatibility with the original single-directory layout.
    with open(os.path.join(models_root, 'current_version.json'), 'w') as f:
        json.dump({'active_version': version_num, 'active_dir': version_dir_name}, f, indent=2)

    for name, model in trained_models.items():
        joblib.dump(model, os.path.join(models_root, f'{name}.pkl'))
    with open(os.path.join(models_root, 'training_results.json'), 'w') as f:
        json.dump(metadata, f, indent=2)

    return metadata


if __name__ == '__main__':
    meta = train_all_models()
    print(f"\nTrained model version v{meta['version']} ({meta['version_dir']})")
    for name, metrics in meta['metrics'].items():
        print(f"\n{name}:")
        print(f"  CV MAE (5-fold):   {metrics['cross_validation']['mae_mean']} +/- {metrics['cross_validation']['mae_std']}")
        print(f"  Validation MAE:    {metrics['validation_set']['mae']}  R2: {metrics['validation_set']['r2_score']}")
        print(f"  Held-out Test MAE: {metrics['held_out_test_set']['mae']}  R2: {metrics['held_out_test_set']['r2_score']}")
    cal = meta['real_world_calibration']
    if cal.get('status') == 'ok':
        print(f"\nReal-world calibration MAE (vs {cal['num_benchmark_points']} published benchmarks): {cal['mae_vs_real_world_benchmarks_pct']} percentage points")
