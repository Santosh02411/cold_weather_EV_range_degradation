"""End-to-end tests for ml/explainability.py -- these need real trained
models on disk (LIME/SHAP/PDP/confidence all load and run actual
sklearn models), so they're slow like test_train_slow.py and use the
exact same temp-models-dir isolation pattern from that file.
"""
import shutil
import tempfile
from conftest import load_app_module

train = load_app_module('app.ml.train')
predict = load_app_module('app.ml.predict')
explainability = load_app_module('app.ml.explainability')


def _with_temp_models_dir(test_fn):
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


SAMPLE_FEATURES = {
    'temperature_c': -15, 'humidity': 70, 'wind_speed_kmh': 20, 'precipitation': 'snow',
    'battery_percentage': 60, 'vehicle_speed_kmh': 90, 'hvac_usage': True, 'terrain_type': 'hilly',
    'battery_age_years': 3, 'battery_capacity_kwh': 75, 'epa_range_km': 400, 'vehicle_weight_kg': 1900,
}


def test_lime_explanation_returns_local_explanation():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        result = explainability.lime_explanation(SAMPLE_FEATURES, model_name='random_forest', num_samples=300)
        assert result['available'] is True
        assert len(result['explanations']) > 0
        assert all('condition' in e and 'weight' in e for e in result['explanations'])
    _with_temp_models_dir(_run)


def test_lime_works_for_neural_network_which_shap_cannot_explain():
    """The whole point of offering LIME alongside SHAP -- it should
    work for model types shap.TreeExplainer/LinearExplainer can't."""
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        result = explainability.lime_explanation(SAMPLE_FEATURES, model_name='neural_network', num_samples=300)
        assert result['available'] is True
    _with_temp_models_dir(_run)


def test_counterfactual_explanations_shape():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        result = explainability.counterfactual_explanations(SAMPLE_FEATURES, model_name='random_forest')
        assert result['available'] is True
        assert len(result['scenarios']) > 0
        for s in result['scenarios']:
            assert 'delta_pct' in s
            assert 'improves_range' in s
    _with_temp_models_dir(_run)


def test_counterfactual_heater_off_scenario_reduces_or_maintains_degradation():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        result = explainability.counterfactual_explanations(SAMPLE_FEATURES, model_name='random_forest')
        heater_scenario = next((s for s in result['scenarios'] if s['scenario'] == 'turn_off_heater'), None)
        assert heater_scenario is not None
        # Turning off the heater should never make cold-weather degradation WORSE.
        assert heater_scenario['delta_pct'] <= 0.5  # small tolerance for model noise
    _with_temp_models_dir(_run)


def test_counterfactual_skips_inapplicable_scenarios():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        mild_flat_slow = {**SAMPLE_FEATURES, 'hvac_usage': False, 'terrain_type': 'flat', 'vehicle_speed_kmh': 40}
        result = explainability.counterfactual_explanations(mild_flat_slow, model_name='random_forest')
        scenario_keys = {s['scenario'] for s in result['scenarios']}
        assert 'turn_off_heater' not in scenario_keys  # already off
        assert 'avoid_hilly_terrain' not in scenario_keys  # already flat
        assert 'drive_slower' not in scenario_keys  # already slow
    _with_temp_models_dir(_run)


def test_pdp_ice_returns_curves_for_selectable_feature():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        result = explainability.pdp_ice(SAMPLE_FEATURES, 'temperature_c', model_name='random_forest', n_points=6)
        assert result['available'] is True
        assert len(result['pdp']) == 6
        assert len(result['ice_curves']) == len(explainability.ICE_ARCHETYPES)
        assert any(c['is_current_scenario'] for c in result['ice_curves'])
    _with_temp_models_dir(_run)


def test_pdp_ice_rejects_non_selectable_feature():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        result = explainability.pdp_ice(SAMPLE_FEATURES, 'wind_chill_index', model_name='random_forest')
        assert result['available'] is False
        assert 'selectable_features' in result
    _with_temp_models_dir(_run)


def test_pdp_colder_temperature_increases_degradation():
    """Sanity check on PDP correctness: colder temperature grid points
    should predict higher (or equal) degradation than warmer ones,
    since that's the core physical relationship this whole app models."""
    def _run(temp_dir):
        train.train_all_models(n_samples=1500)
        result = explainability.pdp_ice(SAMPLE_FEATURES, 'temperature_c', model_name='random_forest', n_points=10)
        pdp = sorted(result['pdp'], key=lambda p: p['value'])
        coldest_degradation = pdp[0]['degradation_pct']
        warmest_degradation = pdp[-1]['degradation_pct']
        assert coldest_degradation > warmest_degradation
    _with_temp_models_dir(_run)


def test_shap_waterfall_tree_model():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        result = explainability.shap_waterfall(SAMPLE_FEATURES, model_name='random_forest')
        assert result['available'] is True
        assert len(result['steps']) == len(explainability.FEATURE_COLS)
        # cumulative should end at (approximately) the reported prediction
        assert abs(result['steps'][-1]['cumulative'] - result['prediction']) < 0.5
    _with_temp_models_dir(_run)


def test_shap_waterfall_unsupported_model_returns_reason():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        result = explainability.shap_waterfall(SAMPLE_FEATURES, model_name='neural_network')
        assert result['available'] is False
        assert 'reason' in result
    _with_temp_models_dir(_run)


def test_shap_force_splits_positive_and_negative():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        result = explainability.shap_force(SAMPLE_FEATURES, model_name='random_forest')
        assert result['available'] is True
        assert isinstance(result['positive_forces'], list)
        assert isinstance(result['negative_forces'], list)
        total_features = len(result['positive_forces']) + len(result['negative_forces'])
        assert total_features == len(explainability.FEATURE_COLS)
    _with_temp_models_dir(_run)


def test_global_shap_summary_ranks_features():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        result = explainability.global_shap_summary(model_name='random_forest', n_samples=50)
        assert result['available'] is True
        assert len(result['global_importance']) == len(explainability.FEATURE_COLS)
        importances = [f['mean_abs_shap'] for f in result['global_importance']]
        assert importances == sorted(importances, reverse=True)
    _with_temp_models_dir(_run)


def test_confidence_breakdown_shape():
    def _run(temp_dir):
        train.train_all_models(n_samples=1000)
        result = explainability.confidence_breakdown(SAMPLE_FEATURES, model_name='random_forest')
        assert result['available'] is True
        assert 0 <= result['confidence'] <= 1
        assert result['n_models'] > 1
        assert 'interpretation' in result
    _with_temp_models_dir(_run)
