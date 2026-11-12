"""Fast, pure-logic tests for the Trip Planning phase's non-network,
non-DB services: route_optimization.py, traffic.py, energy_model.py.
Network-dependent pieces (geo.py's providers, destination_recommender,
route_planning's leg orchestration) are covered separately -- see
test_route_planning_integration.py -- following the same
written-but-not-executed-against-the-live-internet convention
services/geo.py's own docstring already establishes for this sandbox.
"""
from conftest import load_app_module

route_optimization = load_app_module('app.services.route_optimization')
traffic = load_app_module('app.services.traffic')
energy_model = load_app_module('app.services.energy_model')


# --- route_optimization.py ---

def test_estimate_route_energy_kwh_scales_with_distance():
    short = route_optimization.estimate_route_energy_kwh(100, 0, 170)
    long = route_optimization.estimate_route_energy_kwh(200, 0, 170)
    assert long > short
    assert short == 17.0


def test_estimate_route_energy_kwh_penalizes_elevation_gain():
    flat = route_optimization.estimate_route_energy_kwh(100, 0, 170)
    hilly = route_optimization.estimate_route_energy_kwh(100, 1000, 170)
    assert hilly > flat


def test_optimize_routes_flags_fastest_and_most_efficient():
    routes = [
        {'distance_km': 100, 'duration_min': 60, 'provider': 'osrm'},
        {'distance_km': 130, 'duration_min': 55, 'provider': 'osrm'},
    ]
    result = route_optimization.optimize_routes(routes, base_wh_per_km=170)
    fastest = next(r for r in result if r['is_fastest'])
    most_efficient = next(r for r in result if r['is_most_efficient'])
    assert fastest['duration_min'] == 55
    assert most_efficient['distance_km'] == 100


def test_optimize_routes_empty_input():
    assert route_optimization.optimize_routes([], base_wh_per_km=170) == []


def test_optimize_routes_uses_elevation_when_provided():
    routes = [
        {'distance_km': 100, 'duration_min': 60},
        {'distance_km': 100, 'duration_min': 60},
    ]
    result = route_optimization.optimize_routes(routes, base_wh_per_km=170, elevation_gains=[0, 2000])
    low_gain = next(r for r in result if r['elevation_gain_m'] == 0)
    high_gain = next(r for r in result if r['elevation_gain_m'] == 2000)
    assert low_gain['estimated_energy_kwh'] < high_gain['estimated_energy_kwh']
    assert low_gain['is_most_efficient'] is True


# --- traffic.py ---

def test_estimate_traffic_factor_rush_hour_is_heavy():
    from datetime import datetime
    dt = datetime(2026, 1, 5, 8, 0)  # 8am, weekday-agnostic (heuristic doesn't check day of week)
    factor = traffic.estimate_traffic_factor(departure_time=dt, is_urban=True)
    assert factor['congestion_level'] == 'heavy'
    assert factor['duration_multiplier'] > 1.0


def test_estimate_traffic_factor_offpeak_is_light():
    from datetime import datetime
    dt = datetime(2026, 1, 5, 2, 0)  # 2am
    factor = traffic.estimate_traffic_factor(departure_time=dt, is_urban=True)
    assert factor['congestion_level'] == 'light'
    assert factor['duration_multiplier'] == 1.0


def test_estimate_traffic_factor_rural_ignores_rush_hour():
    from datetime import datetime
    dt = datetime(2026, 1, 5, 8, 0)
    factor = traffic.estimate_traffic_factor(departure_time=dt, is_urban=False)
    assert factor['duration_multiplier'] == 1.0


def test_apply_traffic_prefers_real_google_data_over_heuristic():
    route = {'duration_in_traffic_min': 90}
    result = traffic.apply_traffic(60, route=route)
    assert result['source'] == 'google_directions'
    assert result['adjusted_duration_min'] == 90


def test_apply_traffic_falls_back_to_heuristic_without_google_data():
    from datetime import datetime
    result = traffic.apply_traffic(60, route=None, departure_time=datetime(2026, 1, 5, 8, 0))
    assert result['source'] == 'heuristic'
    assert result['adjusted_duration_min'] > 60


def test_traffic_adjusted_speed_decreases_under_congestion():
    normal = traffic.traffic_adjusted_speed_kmh(100, 1.0)
    congested = traffic.traffic_adjusted_speed_kmh(100, 1.5)
    assert congested < normal


# --- energy_model.py ---

def test_energy_consumption_lowest_near_efficient_speed():
    at_sweet_spot = energy_model.energy_consumption_by_speed(170, energy_model.EFFICIENT_SPEED_KMH)
    slow = energy_model.energy_consumption_by_speed(170, 10)
    fast = energy_model.energy_consumption_by_speed(170, 130)
    assert at_sweet_spot < slow
    assert at_sweet_spot < fast


def test_energy_consumption_increases_with_high_speed():
    moderate = energy_model.energy_consumption_by_speed(170, 90)
    fast = energy_model.energy_consumption_by_speed(170, 130)
    assert fast > moderate


def test_energy_curve_returns_expected_shape():
    curve = energy_model.energy_curve(170)
    assert len(curve) > 0
    assert all('speed_kmh' in pt and 'wh_per_km' in pt for pt in curve)


def test_energy_curve_custom_speed_range():
    curve = energy_model.energy_curve(170, speed_range=[30, 60, 90])
    assert [pt['speed_kmh'] for pt in curve] == [30, 60, 90]
