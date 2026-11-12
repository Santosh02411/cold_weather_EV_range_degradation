"""Tests for app/ml/train.py -- synthetic dataset generation and the
real-world calibration check (Phase 1). Does NOT test train_all_models()
end-to-end here (that trains real models and takes real time) -- this
file is the fast, always-run subset. See test_train_slow.py for the
full training pipeline test.
"""
import tempfile
from conftest import load_app_module

train = load_app_module('app.ml.train')


def test_generate_synthetic_dataset_shape():
    df = train.generate_synthetic_dataset(n_samples=500, seed=1)
    assert len(df) == 500
    for col in train.FEATURE_COLS:
        assert col in df.columns
    assert 'range_degradation_pct' in df.columns


def test_generate_synthetic_dataset_degradation_bounds():
    df = train.generate_synthetic_dataset(n_samples=2000, seed=1)
    assert df['range_degradation_pct'].min() >= 0
    assert df['range_degradation_pct'].max() <= 65


def test_generate_synthetic_dataset_is_reproducible_with_same_seed():
    df1 = train.generate_synthetic_dataset(n_samples=200, seed=42)
    df2 = train.generate_synthetic_dataset(n_samples=200, seed=42)
    assert (df1['range_degradation_pct'] == df2['range_degradation_pct']).all()


def test_generate_synthetic_dataset_different_seeds_differ():
    df1 = train.generate_synthetic_dataset(n_samples=200, seed=1)
    df2 = train.generate_synthetic_dataset(n_samples=200, seed=2)
    assert not (df1['range_degradation_pct'] == df2['range_degradation_pct']).all()


def test_colder_temperature_means_more_degradation_on_average():
    """Coarse sanity check on the dataset's core relationship: bucket by
    temperature, confirm average degradation gets worse as it gets
    colder. Not a precise numeric check (physics.py's tests own that) --
    just confirms train.py's additive effects didn't accidentally
    invert the relationship.
    """
    df = train.generate_synthetic_dataset(n_samples=5000, seed=1)
    cold = df[df['temperature_c'] < -15]['range_degradation_pct'].mean()
    mild = df[(df['temperature_c'] > 10) & (df['temperature_c'] < 20)]['range_degradation_pct'].mean()
    assert cold > mild


def test_baseline_trip_conditions_has_all_required_keys():
    fe = load_app_module('app.ml.feature_engineering')
    skip = {'temperature_c', 'physics_baseline_degradation'} | set(fe.ENGINEERED_FEATURE_COLS)
    for col in train.FEATURE_COLS:
        if col in skip:
            continue  # set per-row (physics baseline) or computed (engineered features)
        assert col in train.BASELINE_TRIP_CONDITIONS, f"Missing {col} in BASELINE_TRIP_CONDITIONS"


def test_next_version_starts_at_one_for_empty_dir():
    empty_dir = tempfile.mkdtemp()
    assert train._next_version(empty_dir) == 1


def test_next_version_increments_past_existing():
    import os
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'v1_20260101T000000Z'))
    os.makedirs(os.path.join(d, 'v3_20260102T000000Z'))
    assert train._next_version(d) == 4
