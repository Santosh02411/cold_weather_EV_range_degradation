"""Fast, pure-logic tests for the Charging Management phase's non-DB
services: charger_matching, charging_cost, charging_availability,
home_charging, charger_recommendation, and the station_max_power_kw
cap added to charging_time.predict_charging_time. All network-free
(charging_stations.py's real OCM call is exercised only where already
covered, not here) -- same convention as
test_trip_planning_services.py.
"""
from types import SimpleNamespace
from datetime import datetime
from conftest import load_app_module

charger_matching = load_app_module('app.services.charger_matching')
charging_cost = load_app_module('app.services.charging_cost')
charging_availability = load_app_module('app.services.charging_availability')
charging_time = load_app_module('app.services.charging_time')
home_charging = load_app_module('app.services.home_charging')
charger_recommendation = load_app_module('app.services.charger_recommendation')


def _vehicle(charging_type='CCS', battery_capacity_kwh=75, max_charging_power_kw=150):
    return SimpleNamespace(charging_type=charging_type, battery_capacity_kwh=battery_capacity_kwh,
                            max_charging_power_kw=max_charging_power_kw)


# --- charger_matching.py ---

def test_normalize_connector_recognizes_families():
    assert charger_matching.normalize_connector('CCS (Type 2)') == 'ccs'
    assert charger_matching.normalize_connector('CHAdeMO') == 'chademo'
    assert charger_matching.normalize_connector('Tesla (Standard)') == 'nacs'
    assert charger_matching.normalize_connector('Type 2 (Socket Only)') == 'type2'
    assert charger_matching.normalize_connector('Some Weird Unknown Thing') is None
    assert charger_matching.normalize_connector(None) is None


def test_is_compatible_true_when_matching_family_present():
    assert charger_matching.is_compatible('CCS', ['Type 2', 'CCS (Type 2)']) is True


def test_is_compatible_false_when_no_matching_family():
    assert charger_matching.is_compatible('CHAdeMO', ['CCS (Type 2)', 'Type 2']) is False


def test_is_compatible_none_when_vehicle_type_unrecognized():
    assert charger_matching.is_compatible('Some Proprietary Thing', ['CCS']) is None


def test_is_compatible_none_when_station_has_no_recognized_connectors():
    assert charger_matching.is_compatible('CCS', []) is None
    assert charger_matching.is_compatible('CCS', ['Unknown Connector']) is None


def test_annotate_compatibility_adds_field_to_every_station():
    stations = [{'connector_types': ['CCS']}, {'connector_types': ['CHAdeMO']}]
    charger_matching.annotate_compatibility('CCS', stations)
    assert stations[0]['compatible'] is True
    assert stations[1]['compatible'] is False


# --- charging_cost.py ---

def test_parse_price_per_kwh_extracts_dollar_rate():
    assert charging_cost.parse_price_per_kwh('$0.35/kWh') == 0.35


def test_parse_price_per_kwh_extracts_worded_rate():
    assert charging_cost.parse_price_per_kwh('0.42 USD per kWh') == 0.42


def test_parse_price_per_kwh_recognizes_free():
    assert charging_cost.parse_price_per_kwh('Free to use') == 0.0


def test_parse_price_per_kwh_returns_none_for_unparseable():
    assert charging_cost.parse_price_per_kwh('Membership required') is None
    assert charging_cost.parse_price_per_kwh(None) is None


def test_estimate_charging_cost_uses_station_listed_rate_when_available():
    result = charging_cost.estimate_charging_cost(50, fast_charging=True, usage_cost_text='$0.30/kWh')
    assert result['source'] == 'station_listed'
    assert result['estimated_cost_usd'] == 15.0


def test_estimate_charging_cost_falls_back_to_default():
    result = charging_cost.estimate_charging_cost(50, fast_charging=True, usage_cost_text=None)
    assert result['source'] == 'default_estimate'
    assert result['price_per_kwh_usd'] == charging_cost.DEFAULT_RATES_USD_PER_KWH['dc_fast']


def test_estimate_charging_cost_custom_rate_wins():
    result = charging_cost.estimate_charging_cost(50, usage_cost_text='$0.30/kWh', custom_rate=0.10)
    assert result['source'] == 'custom_rate'
    assert result['estimated_cost_usd'] == 5.0


# --- charging_availability.py ---

def test_estimate_availability_down_station_is_zero():
    station = {'status': 'Faulted', 'num_points': 4}
    result = charging_availability.estimate_availability(station)
    assert result['available_probability_pct'] == 0


def test_estimate_availability_off_peak_higher_than_peak():
    station = {'status': 'Operational', 'num_points': 2}
    off_peak = charging_availability.estimate_availability(station, departure_time=datetime(2026, 1, 5, 2, 0))
    peak = charging_availability.estimate_availability(station, departure_time=datetime(2026, 1, 5, 8, 0))
    assert off_peak['available_probability_pct'] > peak['available_probability_pct']


def test_estimate_availability_more_points_increases_probability():
    few = charging_availability.estimate_availability({'status': 'Operational', 'num_points': 1}, datetime(2026, 1, 5, 8, 0))
    many = charging_availability.estimate_availability({'status': 'Operational', 'num_points': 8}, datetime(2026, 1, 5, 8, 0))
    assert many['available_probability_pct'] > few['available_probability_pct']


def test_estimate_queue_time_zero_when_likely_available():
    station = {'status': 'Operational', 'num_points': 6}
    result = charging_availability.estimate_queue_time(station, datetime(2026, 1, 5, 2, 0))
    assert result['expected_wait_minutes'] == 0


def test_estimate_queue_time_none_when_station_down():
    station = {'status': 'Faulted', 'num_points': 6}
    result = charging_availability.estimate_queue_time(station)
    assert result['expected_wait_minutes'] is None


# --- charging_time.py station_max_power_kw cap ---

def test_station_max_power_caps_charging_speed():
    vehicle = _vehicle(max_charging_power_kw=250)
    uncapped = charging_time.predict_charging_time(vehicle, 20, 0, 100, True)
    capped = charging_time.predict_charging_time(vehicle, 20, 0, 100, True, station_max_power_kw=20)
    assert capped['effective_power_kw'] <= 20
    assert capped['charging_time_minutes'] > uncapped['charging_time_minutes']


def test_predict_charging_time_backward_compatible_without_station_cap():
    vehicle = _vehicle()
    result = charging_time.predict_charging_time(vehicle, 20, 0, 100, True)
    assert result['charging_time_minutes'] == 100.0


# --- home_charging.py ---

def test_home_recommended_when_it_fits_the_window():
    vehicle = _vehicle(battery_capacity_kwh=75)
    result = home_charging.recommend_home_vs_public(vehicle, 20, 80, temperature_c=20, hours_available_at_home=10)
    assert result['recommendation'] == 'home'
    assert result['home']['fits_in_available_window'] is True


def test_public_recommended_when_home_window_too_short():
    vehicle = _vehicle(battery_capacity_kwh=75)
    result = home_charging.recommend_home_vs_public(vehicle, 20, 80, temperature_c=-15, hours_available_at_home=0.5)
    assert result['recommendation'] == 'public_fast'


def test_home_charging_is_cheaper_than_public_by_default_rates():
    vehicle = _vehicle(battery_capacity_kwh=75)
    result = home_charging.recommend_home_vs_public(vehicle, 20, 80, temperature_c=20, hours_available_at_home=10)
    assert result['estimated_savings_charging_at_home_usd'] > 0


# --- charger_recommendation.py ---

def _sample_stations():
    return [
        {'name': 'Fast Expensive', 'connector_types': ['CCS'], 'max_power_kw': 150,
         'status': 'Operational', 'num_points': 1, 'usage_cost': '$0.50/kWh'},
        {'name': 'Slow Cheap', 'connector_types': ['CCS'], 'max_power_kw': 25,
         'status': 'Operational', 'num_points': 6, 'usage_cost': '$0.15/kWh'},
        {'name': 'Incompatible', 'connector_types': ['CHAdeMO'], 'max_power_kw': 100,
         'status': 'Operational', 'num_points': 4, 'usage_cost': '$0.20/kWh'},
    ]


def test_recommend_fastest_excludes_incompatible_by_default():
    vehicle = _vehicle(charging_type='CCS')
    ranked = charger_recommendation.recommend_fastest(vehicle, _sample_stations(), 20, 80, 20,
                                                        departure_time=datetime(2026, 1, 5, 2, 0))
    names = [s['name'] for s in ranked]
    assert 'Incompatible' not in names
    assert names[0] == 'Fast Expensive'  # fastest despite being pricier


def test_recommend_cheapest_ranks_by_cost():
    vehicle = _vehicle(charging_type='CCS')
    ranked = charger_recommendation.recommend_cheapest(vehicle, _sample_stations(), 20, 80, 20,
                                                         departure_time=datetime(2026, 1, 5, 2, 0))
    assert ranked[0]['name'] == 'Slow Cheap'


def test_recommend_fastest_can_include_incompatible_when_asked():
    vehicle = _vehicle(charging_type='CCS')
    ranked = charger_recommendation.recommend_fastest(vehicle, _sample_stations(), 20, 80, 20,
                                                        only_compatible=False)
    assert len(ranked) == 3
