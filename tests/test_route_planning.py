"""Tests for services/route_planning.py's multi-stop / round-trip
orchestration and charging-stop insertion logic. Every network call
(geocoding, routing, elevation) and the ML prediction call are mocked
-- this project's real geo/ML calls are exercised elsewhere (see
test_geo.py-style pure-logic tests and test_train_slow.py); this file
is purely about whether plan_multi_stop_trip() assembles those pieces
and does its battery/charging bookkeeping correctly.
"""
from types import SimpleNamespace
from unittest.mock import patch
from conftest import load_app_module

route_planning = load_app_module('app.services.route_planning')


def _vehicle(battery_capacity_kwh=75, epa_range_km=400, vehicle_weight_kg=1900, max_charging_power_kw=150):
    return SimpleNamespace(
        battery_capacity_kwh=battery_capacity_kwh, epa_range_km=epa_range_km,
        vehicle_weight_kg=vehicle_weight_kg, max_charging_power_kw=max_charging_power_kw,
    )


def _fake_geocode(place_name, provider_config=None):
    # Deterministic fake coordinates keyed off the place name so
    # different stops get different (fake) lat/lon.
    coords = {
        'CityA': (40.0, -74.0), 'CityB': (41.0, -75.0), 'CityC': (42.0, -76.0),
    }
    lat, lon = coords.get(place_name, (0.0, 0.0))
    return lat, lon, place_name


def _fake_route(*args, **kwargs):
    return {'distance_km': 100.0, 'duration_min': 60.0, 'coordinates': [(0, 0), (1, 1)], 'provider': 'osrm'}


def _fake_prediction_low_consumption(features, model_name):
    # A low, fixed Wh/km so a single 100km leg uses a small,
    # predictable slice of a 75kWh battery -- keeps the arithmetic easy
    # to assert on.
    return {
        'range_degradation_pct': 10.0,
        'predicted_range_km': 350.0,
        'energy_consumption_wh_km': 150.0,  # 100km * 150Wh/km = 15kWh = 20% of a 75kWh battery
        'confidence': 0.9,
    }


def _patched():
    """Context manager stack for the common mock set every test here needs."""
    return (
        patch.object(route_planning.geo, 'geocode_place', side_effect=_fake_geocode),
        patch.object(route_planning.geo, 'get_route', side_effect=_fake_route),
        patch.object(route_planning.geo, 'get_elevation_profile', return_value=None),
        patch.object(route_planning, 'get_prediction', side_effect=_fake_prediction_low_consumption),
    )


def test_requires_at_least_two_stops():
    result = route_planning.plan_multi_stop_trip(_vehicle(), ['OnlyOne'])
    assert 'error' in result


def test_geocode_failure_returns_error():
    with patch.object(route_planning.geo, 'geocode_place', return_value=(None, None, None)):
        result = route_planning.plan_multi_stop_trip(_vehicle(), ['Nowhere', 'AlsoNowhere'])
    assert 'error' in result


def test_simple_two_stop_trip_no_charging_needed():
    p1, p2, p3, p4 = _patched()
    with p1, p2, p3, p4:
        result = route_planning.plan_multi_stop_trip(_vehicle(), ['CityA', 'CityB'], start_battery_pct=100)
    assert 'error' not in result
    assert len(result['legs']) == 1
    assert result['num_charging_stops'] == 0
    assert result['total_distance_km'] == 100.0
    assert result['feasible'] is True
    # 20% battery used, starting at 100% -> 80% remaining, well above margin
    assert result['final_battery_pct'] == 80.0


def test_multi_stop_trip_inserts_charging_when_needed():
    p1, p2, p3, p4 = _patched()
    with p1, p2, p3, p4:
        # Start low enough that leg 2 would dip below the safety margin
        # without a charging stop (each leg uses 20%; starting at 30%
        # means after leg 1 -> 10%, which is below SAFETY_MARGIN_PCT=15
        # even before leg 2 starts).
        result = route_planning.plan_multi_stop_trip(
            _vehicle(), ['CityA', 'CityB', 'CityC'], start_battery_pct=30,
        )
    assert 'error' not in result
    assert len(result['legs']) == 2
    assert result['num_charging_stops'] >= 1
    assert result['total_charging_time_min'] > 0
    assert result['feasible'] is True


def test_round_trip_appends_return_leg():
    p1, p2, p3, p4 = _patched()
    with p1, p2, p3, p4:
        result = route_planning.plan_multi_stop_trip(
            _vehicle(), ['CityA', 'CityB'], round_trip=True, start_battery_pct=100,
        )
    assert 'error' not in result
    assert result['round_trip'] is True
    assert len(result['legs']) == 2  # CityA->CityB, CityB->CityA
    assert result['stops'][0] == result['stops'][-1] == 'CityA'


def test_infeasible_trip_flagged_when_leg_exceeds_full_battery():
    def huge_consumption(features, model_name):
        return {'range_degradation_pct': 10.0, 'predicted_range_km': 350.0,
                'energy_consumption_wh_km': 900.0, 'confidence': 0.9}  # 100km * 900Wh/km = 90kWh > 75kWh capacity

    p1, p2, p3, _ = _patched()
    with p1, p2, p3, patch.object(route_planning, 'get_prediction', side_effect=huge_consumption):
        result = route_planning.plan_multi_stop_trip(_vehicle(), ['CityA', 'CityB'], start_battery_pct=100)
    assert 'error' not in result
    assert result['feasible'] is False


def test_safe_range_km_applies_margin():
    assert route_planning.safe_range_km(400, safety_margin_pct=15) == 340.0
    assert route_planning.safe_range_km(400, safety_margin_pct=0) == 400.0


def test_eta_includes_both_driving_and_charging_time():
    p1, p2, p3, p4 = _patched()
    with p1, p2, p3, p4:
        result = route_planning.plan_multi_stop_trip(
            _vehicle(), ['CityA', 'CityB', 'CityC'], start_battery_pct=30,
        )
    assert result['total_eta_min'] == round(result['total_driving_duration_min'] + result['total_charging_time_min'], 1)
