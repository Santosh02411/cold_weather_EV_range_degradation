"""Tests for app/ml/automl.py's model registry shape. Deliberately does
NOT fit any models here (that's real training time, see
test_train_slow.py) -- just checks the registry is well-formed so a
bug here (e.g. a typo'd param name) is caught fast, before it'd only
otherwise surface 30+ seconds into a real training run.
"""
from conftest import load_app_module

automl = load_app_module('app.ml.automl')


def test_registry_always_includes_core_models():
    registry = automl.build_model_registry()
    for name in ('linear_regression', 'random_forest', 'gradient_boosting', 'neural_network'):
        assert name in registry
        assert registry[name]['estimator'] is not None


def test_registry_includes_stacking_ensemble_when_requested():
    registry = automl.build_model_registry(include_ensemble=True)
    assert 'stacking_ensemble' in registry


def test_registry_excludes_stacking_ensemble_when_not_requested():
    registry = automl.build_model_registry(include_ensemble=False)
    assert 'stacking_ensemble' not in registry


def test_registry_only_includes_optional_families_that_are_installed():
    registry = automl.build_model_registry()
    assert ('xgboost' in registry) == automl.HAS_XGBOOST
    assert ('lightgbm' in registry) == automl.HAS_LIGHTGBM
    assert ('catboost' in registry) == automl.HAS_CATBOOST


def test_tunable_models_have_param_distributions_and_untunable_dont():
    registry = automl.build_model_registry()
    assert registry['linear_regression']['param_distributions'] is None
    assert registry['random_forest']['param_distributions'] is not None
    assert registry['neural_network']['param_distributions'] is not None
    assert registry['stacking_ensemble']['param_distributions'] is None


def test_each_registry_entry_gives_a_fresh_unfitted_estimator_instance():
    """build_model_registry() is called on every training run --
    entries must not accidentally share mutable state (e.g. a single
    module-level estimator instance reused/refit across runs)."""
    registry_a = automl.build_model_registry()
    registry_b = automl.build_model_registry()
    assert registry_a['random_forest']['estimator'] is not registry_b['random_forest']['estimator']
