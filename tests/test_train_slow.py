"""End-to-end tests that actually train real models -- slower than the
rest of the suite (real sklearn fit calls), so kept in their own file.
Run these when you have a minute to spare, not on every save.

Uses a temp directory for saved_models (via monkeypatching
train.get_models_root) so running this suite never clobbers a real
trained model version sitting in the actual saved_models/ directory.
"""
import os
import shutil
import tempfile
from conftest import load_app_module

train = load_app_module('app.ml.train')
predict = load_app_module('app.ml.predict')


def _with_temp_models_dir(test_fn):
    """Redirect get_models_root() to an isolated temp dir for the
    duration of one test, then restore it -- avoids polluting (or being
    polluted by) any real saved_models/ directory."""
    temp_dir = tempfile.mkdtemp()
    original = train.get_models_root
    train.get_models_root = lambda: temp_dir
    predict._loaded_models.clear()
    try:
        test_fn(temp_dir)
    finally:
        train.get_models_root = original
        shutil.rmtree(temp_dir, ignore_errors=True)
        predict._loaded_models.clear()


def test_train_all_models_produces_expected_metrics_shape():
    def _run(temp_dir):
        meta = train.train_all_models(n_samples=1000)
        assert meta['version'] == 1
        assert 'linear_regression' in meta['metrics']
        assert 'random_forest' in meta['metrics']
        for model_metrics in meta['metrics'].values():
            assert 'cross_validation' in model_metrics
            assert 'validation_set' in model_metrics
            assert 'held_out_test_set' in model_metrics
        assert meta['real_world_calibration']['status'] == 'ok'
    _with_temp_models_dir(_run)


def test_predict_end_to_end_after_training():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        features = {
            'temperature_c': -15, 'humidity': 70, 'wind_speed_kmh': 20, 'precipitation': 'snow',
            'battery_percentage': 80, 'vehicle_speed_kmh': 90, 'hvac_usage': True, 'terrain_type': 'hilly',
            'battery_age_years': 2, 'battery_capacity_kwh': 75, 'epa_range_km': 400, 'vehicle_weight_kg': 1900,
        }
        result = predict.get_prediction(features)
        assert 0 <= result['range_degradation_pct'] <= 65
        assert 0 <= result['confidence'] <= 1
        assert result['predicted_range_km'] >= 0
    _with_temp_models_dir(_run)


def test_predict_does_not_retrain_on_every_call():
    """Regression test for the real bug found during Phase 4/ML-4
    testing (see docs/PROJECT_WORKFLOW.md): load_model() used to
    retrain on every call when an optional model (xgboost) was
    missing, silently writing a new version directory each time.
    """
    def _run(temp_dir):
        features = {
            'temperature_c': -10, 'humidity': 60, 'wind_speed_kmh': 15, 'precipitation': 'none',
            'battery_percentage': 80, 'vehicle_speed_kmh': 70, 'hvac_usage': True, 'terrain_type': 'flat',
            'battery_age_years': 2, 'battery_capacity_kwh': 75, 'epa_range_km': 400, 'vehicle_weight_kg': 1900,
        }
        predict.get_prediction(features)  # triggers the one legitimate auto-train
        versions_after_first_call = len(train.list_versions())
        for _ in range(5):
            predict.get_prediction(features)
        versions_after_more_calls = len(train.list_versions())
        assert versions_after_first_call == 1
        assert versions_after_more_calls == 1, (
            f"Expected exactly 1 version after 6 total prediction calls, "
            f"got {versions_after_more_calls} -- the runaway-retraining bug may have regressed"
        )
    _with_temp_models_dir(_run)


def test_rollback_produces_identical_prediction_to_original_version():
    def _run(temp_dir):
        features = {
            'temperature_c': -10, 'humidity': 60, 'wind_speed_kmh': 15, 'precipitation': 'none',
            'battery_percentage': 80, 'vehicle_speed_kmh': 70, 'hvac_usage': True, 'terrain_type': 'flat',
            'battery_age_years': 2, 'battery_capacity_kwh': 75, 'epa_range_km': 400, 'vehicle_weight_kg': 1900,
        }
        train.train_all_models(n_samples=1000)  # v1
        result_v1 = predict.get_prediction(features)

        df2 = train.generate_synthetic_dataset(n_samples=1000, seed=999)
        train.train_all_models(df=df2, n_samples=1000)  # v2
        predict.clear_model_cache()
        result_v2 = predict.get_prediction(features)

        train.set_active_version(1)
        predict.clear_model_cache()
        result_after_rollback = predict.get_prediction(features)

        assert abs(result_after_rollback['range_degradation_pct'] - result_v1['range_degradation_pct']) < 0.01
        # Not a strict requirement that v1 != v2, but it's the whole
        # point of training on different data -- assert it to catch a
        # test setup bug (e.g. accidentally training the same data twice).
        assert result_v1['range_degradation_pct'] != result_v2['range_degradation_pct']
    _with_temp_models_dir(_run)


def test_train_all_models_includes_new_model_families():
    """Phase 2 ML feature expansion: LightGBM, CatBoost, a neural
    network, and a stacking ensemble all actually train and produce
    metrics -- not just present in the registry (see
    test_automl_registry.py for that structural check)."""
    def _run(temp_dir):
        meta = train.train_all_models(n_samples=1000)
        for name in ('neural_network', 'stacking_ensemble'):
            assert name in meta['metrics'], f"{name} missing from metrics -- did it fail to train? errors: {meta.get('training_errors')}"
        if train.HAS_LIGHTGBM:
            assert 'lightgbm' in meta['metrics']
        if train.HAS_CATBOOST:
            assert 'catboost' in meta['metrics']
        assert meta['training_errors'] == {}
    _with_temp_models_dir(_run)


def test_train_all_models_records_feature_selection_and_drift_baseline():
    def _run(temp_dir):
        meta = train.train_all_models(n_samples=1000)
        fs = meta['feature_selection']
        assert fs is not None
        assert len(fs['selected_features']) > 0
        assert 'physics_baseline_degradation' in fs['selected_features']

        baseline = meta['feature_distribution_baseline']
        assert 'temperature_c' in baseline
        assert 'wind_chill_index' in baseline  # engineered feature included too
    _with_temp_models_dir(_run)


def test_recommended_model_is_the_lowest_test_mae_model():
    def _run(temp_dir):
        meta = train.train_all_models(n_samples=1000)
        best_name = meta['recommended_model']
        best_mae = meta['metrics'][best_name]['held_out_test_set']['mae']
        for name, m in meta['metrics'].items():
            assert m['held_out_test_set']['mae'] >= best_mae - 1e-9
    _with_temp_models_dir(_run)


def test_run_automl_tunes_and_records_best_params():
    """AutoML: hyperparameter tuning actually runs (small n_iter/cv for
    test speed) and records per-model best params/search CV MAE for
    every tunable model family."""
    def _run(temp_dir):
        meta = train.run_automl(n_samples=800, tuning_n_iter=2, tuning_cv=2)
        assert meta['hyperparameter_tuning_used'] is True
        assert meta['automl_run'] is True
        rf_report = meta['metrics']['random_forest']['hyperparameter_tuning']
        assert rf_report is not None
        assert 'best_params' in rf_report
        assert 'search_cv_mae' in rf_report
        # linear_regression has no param_distributions -- should not be tuned
        assert meta['metrics']['linear_regression']['hyperparameter_tuning'] is None
    _with_temp_models_dir(_run)


def test_predict_confidence_excludes_stacking_ensemble_from_its_own_score():
    """The stacking ensemble is built FROM the other base models, so
    folding its own prediction into the ensemble-agreement confidence
    score would be circular. Selecting it as model_name should still
    produce a valid confidence score computed from the independent
    base models only."""
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        features = {
            'temperature_c': -15, 'humidity': 70, 'wind_speed_kmh': 20, 'precipitation': 'snow',
            'battery_percentage': 80, 'vehicle_speed_kmh': 90, 'hvac_usage': True, 'terrain_type': 'hilly',
            'battery_age_years': 2, 'battery_capacity_kwh': 75, 'epa_range_km': 400, 'vehicle_weight_kg': 1900,
        }
        result = predict.get_prediction(features, model_name='stacking_ensemble')
        assert 0 <= result['range_degradation_pct'] <= 65
        assert 0 <= result['confidence'] <= 1
    _with_temp_models_dir(_run)
