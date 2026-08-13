"""Tests for the pure math in app/services/recalibration.py
(_degradation_from_actual). Does NOT import recalibration.py directly,
since it imports ..models.prediction/..models.ev_vehicle at module
level, which pulls in SQLAlchemy model definitions requiring
flask_sqlalchemy -- not available in this project's build sandbox (see
docs/PROJECT_WORKFLOW.md). The function is small and pure enough that
it's duplicated here verbatim as a regression test of the FORMULA
rather than the module; if this drifts out of sync with the real
function, that's a real risk of these tests silently testing the wrong
thing -- flagged here deliberately rather than hidden, and worth fixing
properly (e.g. extracting this formula into a flask-free module) if
this project's test infrastructure gets a real Flask+DB environment to
run in.
"""
import numpy as np


def _degradation_from_actual(reported_range_km, epa_range_km, battery_pct):
    """Verbatim copy of recalibration.py's _degradation_from_actual --
    see this file's module docstring for why it's duplicated rather
    than imported."""
    if not epa_range_km or not battery_pct or battery_pct <= 0:
        return None
    expected_range_at_this_charge = epa_range_km * (battery_pct / 100.0)
    if expected_range_at_this_charge <= 0:
        return None
    degradation = 100.0 * (1 - (reported_range_km / expected_range_at_this_charge))
    return float(np.clip(degradation, 0, 65))


def test_no_degradation_when_actual_matches_expected():
    assert _degradation_from_actual(400, 400, 100) == 0.0


def test_fifty_percent_degradation():
    assert _degradation_from_actual(200, 400, 100) == 50.0


def test_partial_battery_charge_accounted_for():
    # Same 200km actual, but only charged to 50% -- expected range is
    # 200km at 50%, so this should show ~0% degradation, not 50%.
    assert _degradation_from_actual(200, 400, 50) == 0.0


def test_exceeding_rated_range_clips_to_zero_not_negative():
    assert _degradation_from_actual(450, 400, 100) == 0.0


def test_zero_battery_percentage_returns_none():
    assert _degradation_from_actual(100, 400, 0) is None


def test_negative_battery_percentage_returns_none():
    assert _degradation_from_actual(100, 400, -10) is None


def test_zero_epa_range_returns_none():
    assert _degradation_from_actual(100, 0, 100) is None


def test_extreme_loss_clips_at_65_not_higher():
    assert _degradation_from_actual(10, 400, 100) == 65.0
