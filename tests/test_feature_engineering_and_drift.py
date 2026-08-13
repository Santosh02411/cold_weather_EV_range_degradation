"""Tests for app/ml/feature_engineering.py and app/ml/drift.py -- pure
math, no Flask/DB, no real model training (fast, always-run subset;
see test_train_slow.py for the end-to-end training tests these two
new model registry additions also get exercised by).
"""
import numpy as np
import pandas as pd
from conftest import load_app_module

fe = load_app_module('app.ml.feature_engineering')
drift = load_app_module('app.ml.drift')


# --- feature_engineering.py ---

def _sample_df():
    return pd.DataFrame({
        'temperature_c': [-20.0, 5.0, 25.0],
        'wind_speed_kmh': [40.0, 10.0, 0.0],
        'hvac_usage': [1, 1, 0],
        'vehicle_speed_kmh': [120.0, 60.0, 60.0],
    })


def test_engineer_features_adds_all_expected_columns():
    df = fe.engineer_features(_sample_df())
    for col in fe.ENGINEERED_FEATURE_COLS:
        assert col in df.columns


def test_engineer_features_does_not_mutate_input():
    original = _sample_df()
    before = original.copy()
    fe.engineer_features(original)
    pd.testing.assert_frame_equal(original, before)


def test_is_freezing_flag_matches_temperature():
    df = fe.engineer_features(_sample_df())
    assert list(df['is_freezing']) == [1.0, 0.0, 0.0]


def test_wind_chill_index_colder_with_more_wind():
    calm = fe.engineer_feature_row({'temperature_c': -10, 'wind_speed_kmh': 0, 'hvac_usage': 0, 'vehicle_speed_kmh': 60})
    windy = fe.engineer_feature_row({'temperature_c': -10, 'wind_speed_kmh': 50, 'hvac_usage': 0, 'vehicle_speed_kmh': 60})
    assert windy['wind_chill_index'] < calm['wind_chill_index']


def test_hvac_cold_interaction_zero_when_hvac_off_or_warm():
    off = fe.engineer_feature_row({'temperature_c': -10, 'wind_speed_kmh': 10, 'hvac_usage': 0, 'vehicle_speed_kmh': 60})
    warm = fe.engineer_feature_row({'temperature_c': 20, 'wind_speed_kmh': 10, 'hvac_usage': 1, 'vehicle_speed_kmh': 60})
    assert off['hvac_cold_interaction'] == 0
    assert warm['hvac_cold_interaction'] == 0


def test_hvac_cold_interaction_positive_when_hvac_on_and_cold():
    row = fe.engineer_feature_row({'temperature_c': -10, 'wind_speed_kmh': 10, 'hvac_usage': 1, 'vehicle_speed_kmh': 60})
    assert row['hvac_cold_interaction'] > 0


def test_engineer_feature_row_preserves_original_keys():
    row = fe.engineer_feature_row({'temperature_c': 5, 'wind_speed_kmh': 10, 'hvac_usage': 1,
                                    'vehicle_speed_kmh': 60, 'battery_percentage': 80})
    assert row['battery_percentage'] == 80
    assert row['temperature_c'] == 5


def test_engineer_feature_row_and_engineer_features_agree():
    """The single-row path (predict.py) and the DataFrame path
    (train.py) MUST compute identical values for the same input --
    that's the whole point of sharing one function (see module
    docstring)."""
    raw = {'temperature_c': -15.0, 'wind_speed_kmh': 25.0, 'hvac_usage': 1, 'vehicle_speed_kmh': 90.0}
    row_result = fe.engineer_feature_row(raw)
    df_result = fe.engineer_features(pd.DataFrame([raw])).iloc[0]
    for col in fe.ENGINEERED_FEATURE_COLS:
        assert abs(row_result[col] - df_result[col]) < 1e-9


def test_select_features_always_keeps_always_keep_list():
    importance = {'a': 0.5, 'b': 0.3, 'physics_baseline_degradation': 0.01, 'c': 0.19}
    report = fe.select_features(importance, cumulative_threshold=0.5)
    assert 'physics_baseline_degradation' in report['selected_features']


def test_select_features_ranks_highest_importance_first():
    importance = {'a': 0.1, 'b': 0.7, 'c': 0.2}
    report = fe.select_features(importance)
    assert report['ranked'][0]['feature'] == 'b'


def test_select_features_empty_importance_returns_safe_default():
    report = fe.select_features({})
    assert report['ranked'] == []
    assert report['cumulative_importance_covered'] == 0.0


# --- drift.py ---

def test_psi_is_zero_for_identical_distributions():
    props = [0.1, 0.2, 0.3, 0.4]
    assert drift.psi(props, props) == 0.0


def test_psi_increases_with_distribution_shift():
    baseline = [0.25, 0.25, 0.25, 0.25]
    slight_shift = [0.2, 0.3, 0.25, 0.25]
    big_shift = [0.7, 0.1, 0.1, 0.1]
    psi_slight = drift.psi(baseline, slight_shift)
    psi_big = drift.psi(baseline, big_shift)
    assert psi_slight > 0
    assert psi_big > psi_slight


def test_compute_baseline_distribution_covers_requested_columns():
    df = pd.DataFrame({
        'temperature_c': np.random.default_rng(1).uniform(-30, 40, 500),
        'flag_col': [1] * 500,  # degenerate/constant column
    })
    baseline = drift.compute_baseline_distribution(df, ['temperature_c', 'flag_col'])
    assert 'temperature_c' in baseline
    assert baseline['temperature_c']['degenerate'] is False
    assert baseline['flag_col']['degenerate'] is True


def test_compute_drift_report_no_drift_for_same_distribution():
    rng = np.random.default_rng(7)
    values = rng.uniform(-30, 40, 2000)
    df = pd.DataFrame({'temperature_c': values})
    baseline = drift.compute_baseline_distribution(df, ['temperature_c'])
    same_dist_df = pd.DataFrame({'temperature_c': rng.uniform(-30, 40, 500)})
    report = drift.compute_drift_report(baseline, same_dist_df, ['temperature_c'])
    assert report['status'] == 'ok'
    assert report['overall_severity'] == 'none'


def test_compute_drift_report_detects_significant_shift():
    rng = np.random.default_rng(7)
    training_values = rng.uniform(-30, 40, 2000)
    df = pd.DataFrame({'temperature_c': training_values})
    baseline = drift.compute_baseline_distribution(df, ['temperature_c'])
    # Recent predictions are all bitterly cold -- a real distribution
    # shift versus the (roughly uniform -30..40) training data.
    shifted_df = pd.DataFrame({'temperature_c': rng.uniform(-30, -25, 500)})
    report = drift.compute_drift_report(baseline, shifted_df, ['temperature_c'])
    assert report['status'] == 'ok'
    assert report['overall_severity'] == 'significant'
    assert report['worst_feature'] == 'temperature_c'


def test_compute_drift_report_insufficient_data_status():
    baseline = {'temperature_c': {'bin_edges': [0, 1, 2], 'bin_proportions': [0.5, 0.5], 'degenerate': False}}
    empty_df = pd.DataFrame({'temperature_c': []})
    report = drift.compute_drift_report(baseline, empty_df, ['temperature_c'])
    assert report['status'] == 'insufficient_data'
