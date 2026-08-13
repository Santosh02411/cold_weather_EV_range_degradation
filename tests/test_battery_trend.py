"""Tests for app/services/battery_trend.py (FEAT-1)."""
from datetime import datetime
from conftest import load_app_module

bt = load_app_module('app.services.battery_trend')


def test_single_record_returns_none():
    assert bt.compute_trend([(datetime(2024, 1, 1), 100.0)]) is None


def test_empty_records_returns_none():
    assert bt.compute_trend([]) is None


def test_two_records_one_year_apart_computes_expected_slope():
    result = bt.compute_trend([
        (datetime(2024, 1, 1), 100.0),
        (datetime(2025, 1, 1), 97.0),
    ])
    assert -3.1 < result['slope_pct_per_year'] < -2.9
    assert result['num_records'] == 2


def test_projection_clipped_to_valid_range():
    # Extreme slope shouldn't project below 0% or above 100%
    result = bt.compute_trend([
        (datetime(2024, 1, 1), 100.0),
        (datetime(2024, 2, 1), 50.0),
    ])
    assert 0 <= result['projections']['5_year'] <= 100


def test_records_out_of_order_are_sorted_chronologically():
    result = bt.compute_trend([
        (datetime(2025, 1, 1), 97.0),
        (datetime(2024, 1, 1), 100.0),
    ])
    assert result['data_points'][0]['soh_pct'] == 100.0
    assert result['data_points'][1]['soh_pct'] == 97.0


def test_improving_soh_gives_positive_slope():
    # Shouldn't happen in reality, but the math itself shouldn't assume
    # degradation is always negative -- confirms no hidden sign-flipping.
    result = bt.compute_trend([
        (datetime(2024, 1, 1), 90.0),
        (datetime(2025, 1, 1), 95.0),
    ])
    assert result['slope_pct_per_year'] > 0
