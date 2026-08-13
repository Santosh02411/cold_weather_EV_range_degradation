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

Phase 2 additions (ML feature expansion):
  - Model registry (see automl.py) now also includes LightGBM,
    CatBoost, an MLPRegressor neural network, and a StackingRegressor
    ensemble, alongside the original linear/RF/GB/XGBoost set -- every
    optional package follows the same "absent package -> silently
    excluded, not a crash" convention already established for xgboost.
  - Feature engineering (see feature_engineering.py): a handful of
    physically-motivated interaction features (wind chill, HVAC-cold
    interaction, speed^2, is-freezing) are computed by the SAME
    function for both training and prediction, so the two can't drift
    apart the way physics_baseline_degradation almost did (see this
    file's Phase 1 notes above).
  - Optional per-model hyperparameter tuning (RandomizedSearchCV) via
    `use_hyperparameter_tuning=True`. `run_automl()` is a thin,
    self-documenting wrapper for "turn tuning on and train everything".
  - Feature selection is reported (not silently applied) -- see
    feature_engineering.select_features(): a cumulative-importance
    ranking is stored in metadata so the admin dashboard can show which
    inputs are pulling weight, without a threshold silently shrinking
    what predict.py expects to receive.
  - A per-feature distribution baseline (quantile bins) is stored in
    metadata for data-drift detection (see drift.py) -- this is what
    services/drift_monitor.py compares live prediction inputs against.
"""
import os
import json
import joblib
import csv
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

try:
    from . import automl as automl_mod
    from . import feature_engineering as fe
    from . import drift as drift_mod
    from .physics import physics_baseline_batch, calibration_anchors
except ImportError:  # allows running this file standalone via `python train.py`
    import automl as automl_mod
    import feature_engineering as fe
    import drift as drift_mod
    from physics import physics_baseline_batch, calibration_anchors

HAS_XGBOOST = automl_mod.HAS_XGBOOST
HAS_LIGHTGBM = automl_mod.HAS_LIGHTGBM
HAS_CATBOOST = automl_mod.HAS_CATBOOST


CALIBRATION_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', '..',
    'data', 'real_world_calibration', 'temperature_range_benchmarks.csv'
)

RAW_FEATURE_COLS = [
    'temperature_c', 'humidity', 'wind_speed_kmh', 'precipitation',
    'battery_percentage', 'vehicle_speed_kmh', 'hvac_usage',
    'terrain_type', 'battery_age_years', 'battery_capacity_kwh',
    'epa_range_km', 'vehicle_weight_kg', 'physics_baseline_degradation',
]

# Raw inputs + engineered interaction features (feature_engineering.py).
# Every model trains and predicts on this full set -- see that module's
# docstring for why engineering the features is a shared function
# rather than duplicated logic in train.py and predict.py.
FEATURE_COLS = RAW_FEATURE_COLS + fe.ENGINEERED_FEATURE_COLS


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

    df = fe.engineer_features(df)
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


REQUIRED_MODEL_FILES = ['linear_regression.pkl', 'random_forest.pkl', 'gradient_boosting.pkl']


def list_versions():
    """ML-4: list every trained version with its key metrics, newest
    first, plus which one is currently active. Reads each version's own
    metadata.json rather than assuming the flat saved_models/ copy
    reflects any particular version -- the two can legitimately differ
    now that set_active_version() can point 'active' at an older run
    without retraining.
    """
    models_root = get_models_root()
    active = get_active_version_info()
    versions = []
    for entry in sorted(os.listdir(models_root), reverse=True):
        version_dir = os.path.join(models_root, entry)
        meta_path = os.path.join(version_dir, 'metadata.json')
        if not (entry.startswith('v') and '_' in entry and os.path.isdir(version_dir) and os.path.exists(meta_path)):
            continue
        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except Exception:
            continue
        best_model = min(
            meta.get('metrics', {}).items(),
            key=lambda kv: kv[1].get('held_out_test_set', {}).get('mae', float('inf')),
            default=(None, {}),
        )
        cal = meta.get('real_world_calibration', {})
        versions.append({
            'version': meta.get('version'),
            'version_dir': entry,
            'trained_at_utc': meta.get('trained_at_utc'),
            'models_included': meta.get('models_included', []),
            'best_model': best_model[0],
            'best_model_test_mae': best_model[1].get('held_out_test_set', {}).get('mae'),
            'real_world_calibration_mae_pp': cal.get('mae_vs_real_world_benchmarks_pct'),
            'is_active': active is not None and entry == active.get('active_dir'),
        })
    return versions


def get_active_version_info():
    """Read current_version.json. Returns None if it doesn't exist yet
    (e.g. a fresh clone before the first training run)."""
    models_root = get_models_root()
    path = os.path.join(models_root, 'current_version.json')
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def get_active_model_dir():
    """ML-4: where predict.py should actually load models from. Prefers
    the versioned directory current_version.json points at (so a
    rollback via set_active_version() takes effect immediately without
    retraining or copying files); falls back to the flat saved_models/
    layout if no version pointer exists yet, for compatibility with any
    older install that predates versioning.
    """
    models_root = get_models_root()
    active = get_active_version_info()
    if active:
        version_dir = os.path.join(models_root, active.get('active_dir', ''))
        if os.path.isdir(version_dir) and all(
            os.path.exists(os.path.join(version_dir, f)) for f in REQUIRED_MODEL_FILES
        ):
            return version_dir
    return models_root


def set_active_version(version_num):
    """ML-4: instant rollback (or roll-forward) -- point
    current_version.json at an already-trained version. No retraining,
    no file copying; get_active_model_dir() picks it up on the next
    prediction. Returns the activated version's metadata dict.
    Raises ValueError if the requested version doesn't exist or is
    missing required model files (e.g. was trained without xgboost and
    you're asking to activate it as if it had every model -- validated
    against REQUIRED_MODEL_FILES, the models every version is guaranteed
    to include, rather than the optional xgboost one).
    """
    models_root = get_models_root()
    target_dir = None
    for entry in os.listdir(models_root):
        if entry.startswith(f'v{version_num}_'):
            target_dir = entry
            break
    if not target_dir:
        raise ValueError(f'No trained version v{version_num} found in {models_root}')

    version_path = os.path.join(models_root, target_dir)
    missing = [f for f in REQUIRED_MODEL_FILES if not os.path.exists(os.path.join(version_path, f))]
    if missing:
        raise ValueError(f'Version v{version_num} is missing required model file(s): {missing}')

    with open(os.path.join(models_root, 'current_version.json'), 'w') as f:
        json.dump({'active_version': version_num, 'active_dir': target_dir}, f, indent=2)

    meta_path = os.path.join(version_path, 'metadata.json')
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            return json.load(f)
    return {'version': version_num, 'version_dir': target_dir}


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
        sample = fe.engineer_feature_row(sample)
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


def _extract_feature_importance(model):
    """Best-effort feature importance extraction across every model
    type this project trains. Pipelines (the neural network) and the
    stacking ensemble don't expose a simple per-input-feature
    importance the same way a single tree/linear model does, so they
    report an empty dict rather than a misleading one -- their
    contribution shows up in the model-comparison metrics instead.
    """
    if isinstance(model, Pipeline) or isinstance(model, automl_mod.StackingRegressor):
        return {}
    if hasattr(model, 'feature_importances_'):
        return dict(zip(FEATURE_COLS, model.feature_importances_.tolist()))
    if hasattr(model, 'coef_'):
        return dict(zip(FEATURE_COLS, np.abs(np.ravel(model.coef_)).tolist()))
    return {}


def train_all_models(df=None, n_samples=8000, extra_metadata=None,
                      use_hyperparameter_tuning=False, tuning_n_iter=8, tuning_cv=3,
                      include_ensemble=True):
    """Train all ML models, evaluate on a real train/val/test split with
    cross-validation, validate against real-world benchmarks, and save
    a new versioned model bundle. Returns the results dict that also
    gets written to disk.

    `extra_metadata`: optional dict merged into the saved metadata.json
    BEFORE it's written to disk (e.g. services/recalibration.py records
    how much real user-reported data was blended into this training
    run here) -- added specifically so that information doesn't only
    exist in the in-memory return value and silently vanish once the
    caller's local variable goes out of scope. A training run's
    provenance should be recoverable from disk alone.

    `use_hyperparameter_tuning`: when True, every tunable model family
    runs a small RandomizedSearchCV (see automl.py) before its final
    fit, and the search's best params/CV MAE are recorded per model.
    Off by default so a plain retrain stays fast -- see run_automl()
    below for the "on" entry point.

    A single model family failing to fit (a real risk once optional
    packages like catboost/lightgbm and a gradient-based neural network
    are in the mix) is caught and skipped rather than aborting the
    whole training run -- reported under metadata['training_errors']
    -- since Live Model Retraining depends on a bad/unavailable model
    never being able to take down every other model's retrain.
    """
    if df is None:
        df = generate_synthetic_dataset(n_samples)

    X = df[FEATURE_COLS]
    y = df['range_degradation_pct']

    # 70 / 15 / 15 train / validation / test split
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.50, random_state=42)

    registry = automl_mod.build_model_registry(include_ensemble=include_ensemble)

    results = {}
    trained_models = {}
    training_errors = {}
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    for name, spec in registry.items():
        try:
            model = spec['estimator']
            tuning_report = None

            if use_hyperparameter_tuning and spec['param_distributions']:
                model, best_params, best_cv_mae = automl_mod.tune_hyperparameters(
                    model, spec['param_distributions'], X_train, y_train,
                    n_iter=tuning_n_iter, cv=tuning_cv,
                )
                tuning_report = {'best_params': _jsonable(best_params), 'search_cv_mae': round(best_cv_mae, 4)}

            # 5-fold cross-validation on the training split, using
            # whichever hyperparameters this model ended up with
            # (tuned or default) -- kept as a separate, standard-shaped
            # CV pass on top of any tuning search so every model's
            # cross-validation numbers are directly comparable on the
            # admin dashboard regardless of whether tuning ran.
            cv_scores = cross_val_score(model, X_train, y_train, cv=kf, scoring='neg_mean_absolute_error')
            cv_mae_mean = float(-cv_scores.mean())
            cv_mae_std = float(cv_scores.std())

            model.fit(X_train, y_train)
            trained_models[name] = model

            val_pred = model.predict(X_val)
            test_pred = model.predict(X_test)
            importance = _extract_feature_importance(model)

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
                'hyperparameter_tuning': tuning_report,
            }
        except Exception as e:
            # Don't let one flaky model family (e.g. a neural net that
            # fails to converge on a pathological resample, or an
            # optional package with a version mismatch) take down the
            # entire training run -- report it and move on.
            training_errors[name] = str(e)

    # Real-world calibration check against the neutral "typical commute"
    # baseline (see BASELINE_TRIP_CONDITIONS).
    calibration_report = run_calibration_check(trained_models)

    # Feature selection report (diagnostic only -- see
    # feature_engineering.select_features()'s docstring for why this
    # doesn't change which columns the models actually train on).
    # Random forest's importances are used as the ranking source since
    # they're available for every training run (never an empty dict).
    feature_selection_report = None
    if 'random_forest' in results and results['random_forest']['feature_importance']:
        feature_selection_report = fe.select_features(results['random_forest']['feature_importance'])

    # Data-drift baseline: the reference distribution predict-time
    # inputs get compared against later (see drift.py / services/drift_monitor.py).
    feature_distribution_baseline = drift_mod.compute_baseline_distribution(X_train, FEATURE_COLS)

    # Best model by held-out test MAE -- the same ranking list_versions()
    # computes per-version, stored here too so a single training run's
    # own return value/metadata.json is self-sufficient without having
    # to re-derive it from list_versions().
    recommended_model = None
    if results:
        recommended_model = min(
            results.items(), key=lambda kv: kv[1]['held_out_test_set']['mae']
        )[0]

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
        'raw_feature_columns': RAW_FEATURE_COLS,
        'engineered_feature_columns': fe.ENGINEERED_FEATURE_COLS,
        'models_included': list(trained_models.keys()),
        'has_xgboost': HAS_XGBOOST,
        'has_lightgbm': HAS_LIGHTGBM,
        'has_catboost': HAS_CATBOOST,
        'hyperparameter_tuning_used': use_hyperparameter_tuning,
        'recommended_model': recommended_model,
        'metrics': results,
        'training_errors': training_errors,
        'real_world_calibration': calibration_report,
        'physics_baseline_anchors': calibration_anchors(),
        'feature_selection': feature_selection_report,
        'feature_distribution_baseline': feature_distribution_baseline,
    }
    if extra_metadata:
        metadata.update(extra_metadata)
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


def _jsonable(d):
    """Best-effort conversion of a hyperparameter dict (which may
    contain numpy scalars or tuples, e.g. MLPRegressor's
    hidden_layer_sizes) into something json.dump can serialize as-is.
    """
    out = {}
    for k, v in d.items():
        if isinstance(v, tuple):
            out[k] = list(v)
        elif isinstance(v, (np.integer, np.floating)):
            out[k] = v.item()
        else:
            out[k] = v
    return out


def run_automl(df=None, n_samples=8000, tuning_n_iter=8, tuning_cv=3, extra_metadata=None):
    """AutoML: automatically hyperparameter-tune every tunable model
    family and select the best performer by held-out test MAE. A thin,
    self-documenting wrapper around
    train_all_models(use_hyperparameter_tuning=True) -- kept as its
    own entry point so callers (the admin AutoML button) don't need to
    know which flag combination "AutoML" maps to.
    """
    meta = dict(extra_metadata) if extra_metadata else {}
    meta['automl_run'] = True
    return train_all_models(
        df=df, n_samples=n_samples, extra_metadata=meta,
        use_hyperparameter_tuning=True, tuning_n_iter=tuning_n_iter, tuning_cv=tuning_cv,
    )


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
