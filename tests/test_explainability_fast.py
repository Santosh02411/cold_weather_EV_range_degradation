"""Fast tests for the pure-logic pieces of ml/explainability.py that
don't need a trained model on disk -- grid generation, feature
selection lists, and scenario-applicability logic. Everything that
actually loads/runs a model is in test_explainability_slow.py instead.
"""
from conftest import load_app_module

explainability = load_app_module('app.ml.explainability')


def test_pdp_selectable_features_excludes_engineered_and_physics_baseline():
    assert 'physics_baseline_degradation' not in explainability.PDP_SELECTABLE_FEATURES
    assert 'wind_chill_index' not in explainability.PDP_SELECTABLE_FEATURES
    assert 'temperature_c' in explainability.PDP_SELECTABLE_FEATURES
    assert 'vehicle_speed_kmh' in explainability.PDP_SELECTABLE_FEATURES


def test_feature_display_names_cover_every_feature_col():
    for col in explainability.FEATURE_COLS:
        assert col in explainability.FEATURE_DISPLAY_NAMES, f"Missing display name for {col}"


def test_feature_grid_categorical():
    assert explainability._feature_grid('hvac_usage', 1) == [0, 1]
    assert explainability._feature_grid('terrain_type', 0) == [0, 1, 2]
    assert explainability._feature_grid('precipitation', 0) == [0, 1, 2]


def test_feature_grid_absolute_range():
    grid = explainability._feature_grid('temperature_c', -5, n_points=5)
    assert len(grid) == 5
    assert min(grid) == -30
    assert max(grid) == 40


def test_feature_grid_relative_range_for_vehicle_specs():
    grid = explainability._feature_grid('battery_capacity_kwh', 100, n_points=5)
    assert min(grid) == 70.0
    assert max(grid) == 130.0


def test_rebuild_row_overrides_single_feature():
    base = {'temperature_c': 10, 'vehicle_speed_kmh': 60}
    updated = explainability._rebuild_row(base, 'temperature_c', -20)
    assert updated['temperature_c'] == -20
    assert updated['vehicle_speed_kmh'] == 60
    assert base['temperature_c'] == 10  # original untouched


def test_counterfactual_heater_toggle_none_when_already_off():
    assert explainability._cf_toggle_heater({'hvac_usage': False}) is None
    result = explainability._cf_toggle_heater({'hvac_usage': True})
    assert result['hvac_usage'] is False


def test_counterfactual_reduce_speed_none_when_already_slow():
    assert explainability._cf_reduce_speed({'vehicle_speed_kmh': 40}) is None
    result = explainability._cf_reduce_speed({'vehicle_speed_kmh': 100})
    assert result['vehicle_speed_kmh'] < 100


def test_counterfactual_avoid_hills_none_when_already_flat():
    assert explainability._cf_avoid_hills({'terrain_type': 'flat'}) is None
    result = explainability._cf_avoid_hills({'terrain_type': 'mountainous'})
    assert result['terrain_type'] == 'flat'


def test_counterfactual_warmer_day_none_when_already_warm():
    assert explainability._cf_warm_up_battery({'temperature_c': 20}) is None
    result = explainability._cf_warm_up_battery({'temperature_c': -10})
    assert result['temperature_c'] == 5


def test_ice_archetypes_include_current_scenario_marker():
    keys = [key for key, _, _ in explainability.ICE_ARCHETYPES]
    assert 'this_scenario' in keys
    this_scenario = next(overrides for key, _, overrides in explainability.ICE_ARCHETYPES if key == 'this_scenario')
    assert this_scenario == {}


def test_unsupported_shap_reason_covers_every_error_code():
    # every error code _compute_shap_values can return must have a
    # human-readable reason registered, or an endpoint would silently
    # return a KeyError instead of a clean 'unavailable' response.
    for code in ('shap_not_installed', 'model_not_available', 'unsupported_model_type'):
        assert code in explainability._UNSUPPORTED_SHAP_REASON
