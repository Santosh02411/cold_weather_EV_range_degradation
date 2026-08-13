"""Tests for app/ml/physics.py -- the real-world-calibrated temperature
baseline curve (Phase 1). See docs/PROJECT_WORKFLOW.md for the two real
bugs this module's development surfaced (non-monotonic curve from
duplicate/conflicting anchor points); these tests encode the fixes as
regression tests so they can't silently regress.
"""
from conftest import load_app_module

physics = load_app_module('app.ml.physics')


def test_degradation_is_monotonic_non_increasing_with_temperature():
    """The core property the Phase 1 isotonic-regression fix exists for:
    colder must never show LESS degradation than a warmer point below
    the sweet spot. This is exactly the bug that shipped twice during
    Phase 1 development before the isotonic-regression fix (see
    PROJECT_WORKFLOW.md Bug #1/#2) -- regression-tested here so it can't
    come back silently.
    """
    temps = list(range(-30, 25, 1))
    degradations = [physics.physics_baseline_degradation_pct(t) for t in temps]
    for i in range(1, len(degradations)):
        assert degradations[i] <= degradations[i - 1] + 1e-9, (
            f"Non-monotonic: {degradations[i]}% at {temps[i]}C is worse than "
            f"{degradations[i-1]}% at {temps[i-1]}C"
        )


def test_degradation_floored_at_zero_above_sweet_spot():
    for t in (25, 30, 35, 40):
        assert physics.physics_baseline_degradation_pct(t) == 0.0


def test_degradation_capped_at_65():
    # Extreme cold beyond any real anchor point still returns a sane,
    # capped value rather than extrapolating to something absurd.
    assert physics.physics_baseline_degradation_pct(-60) <= 65.0


def test_extreme_cold_shows_real_degradation():
    # Sanity floor: -20C should show substantial (not negligible)
    # degradation, consistent with the real published anchors this
    # curve is fit to (Geotab's -15C anchor alone implies ~46%).
    assert physics.physics_baseline_degradation_pct(-20) > 30


def test_batch_matches_scalar():
    import numpy as np
    temps = np.array([-20, -10, 0, 10, 25])
    batch_result = physics.physics_baseline_batch(temps)
    scalar_result = [physics.physics_baseline_degradation_pct(t) for t in temps]
    for b, s in zip(batch_result, scalar_result):
        assert abs(b - s) < 1e-6


def test_calibration_anchors_are_real_and_cited():
    # Not a numeric check -- just confirms the anchor-loading path
    # actually pulled real rows from the calibration CSV, not only the
    # hardcoded fallback constants (which would silently mask the CSV
    # going missing or malformed).
    anchors = physics.calibration_anchors()
    assert len(anchors) >= 5
    temps = [a[0] for a in anchors]
    assert min(temps) < -20 and max(temps) > 15
