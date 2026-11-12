"""Tests for app/services/battery_intelligence.py's pure functions."""
from conftest import load_app_module

bi = load_app_module('app.services.battery_intelligence')


def test_soh_at_zero_years_is_100():
    assert bi.estimate_soh_from_age(0) == 100.0


def test_soh_declines_at_cited_rate():
    # 5 years at the default 2.3%/yr Geotab-cited rate -> 88.5%
    assert bi.estimate_soh_from_age(5) == 88.5


def test_soh_floored_at_zero_not_negative():
    assert bi.estimate_soh_from_age(60) == 0.0


def test_soh_none_for_none_age():
    assert bi.estimate_soh_from_age(None) is None


def test_soh_none_for_negative_age():
    assert bi.estimate_soh_from_age(-1) is None


def test_aging_classified_typical_at_cited_rate():
    result = bi.classify_aging_rate(2.3)
    assert result['classification'] == 'typical'
    assert result['ratio_to_typical'] == 1.0


def test_aging_classified_faster_than_typical():
    result = bi.classify_aging_rate(4.0)
    assert result['classification'] == 'faster_than_typical'


def test_aging_classified_slower_than_typical():
    result = bi.classify_aging_rate(1.0)
    assert result['classification'] == 'slower_than_typical'


def test_aging_none_for_none_input():
    assert bi.classify_aging_rate(None) is None


def test_years_to_eol_basic_projection():
    # 90% now, declining 2.3%/yr, EOL at 70% -> (90-70)/2.3 = 8.7 years
    assert bi.estimate_years_to_eol(90, 2.3) == 8.7


def test_years_to_eol_already_at_or_below_threshold():
    assert bi.estimate_years_to_eol(65, 2.3) == 0.0


def test_years_to_eol_none_for_zero_decline():
    # A zero or negative decline rate can't be projected forward
    # meaningfully -- must return None, not divide by zero.
    assert bi.estimate_years_to_eol(90, 0) is None
    assert bi.estimate_years_to_eol(90, -1) is None


def test_years_to_eol_none_for_missing_inputs():
    assert bi.estimate_years_to_eol(None, 2.3) is None
    assert bi.estimate_years_to_eol(90, None) is None


def test_cold_start_full_penalty_at_extreme_cold_short_trip():
    # -20C is at the "reaches 1.0 severity" floor, ~0 distance -> full 2x
    assert bi.cold_start_energy_multiplier(0.1, -20) == 2.0


def test_cold_start_fades_to_none_by_25km():
    assert bi.cold_start_energy_multiplier(25, -20) == 1.0


def test_cold_start_none_above_10c():
    assert bi.cold_start_energy_multiplier(5, 10) == 1.0
    assert bi.cold_start_energy_multiplier(5, 20) == 1.0


def test_cold_start_none_for_zero_or_negative_distance():
    assert bi.cold_start_energy_multiplier(0, -20) == 1.0
    assert bi.cold_start_energy_multiplier(-5, -20) == 1.0


def test_cold_start_none_for_none_inputs():
    assert bi.cold_start_energy_multiplier(5, None) == 1.0
    assert bi.cold_start_energy_multiplier(None, -20) == 1.0


def test_cold_start_milder_cold_gives_smaller_penalty_than_extreme_cold():
    mild = bi.cold_start_energy_multiplier(5, -5)
    extreme = bi.cold_start_energy_multiplier(5, -20)
    assert 1.0 < mild < extreme
