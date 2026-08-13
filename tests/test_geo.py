"""Tests for the pure (no-network) logic in app/services/geo.py: terrain
classification from elevation (RT-1/Phase 2) and waypoint selection
(RT-6/Phase 4). Does NOT test geocode_place/get_route/get_elevation_profile
here -- those make real HTTP calls and were never executable in this
project's build sandbox (see docs/PROJECT_WORKFLOW.md); testing them
needs a real network connection and belongs in a separate,
explicitly-network-dependent test file, not this fast/offline suite.
"""
from conftest import load_app_module

geo = load_app_module('app.services.geo')


def test_flat_terrain_classified_correctly():
    flat = [100, 101, 99, 102, 100, 103, 101]
    terrain, gain = geo.classify_terrain_from_elevations(flat)
    assert terrain == 'flat'


def test_mountainous_terrain_classified_correctly():
    import random
    random.seed(1)
    mtn = [100]
    for _ in range(50):
        mtn.append(mtn[-1] + random.uniform(-5, 40))
    terrain, gain = geo.classify_terrain_from_elevations(mtn)
    assert terrain == 'mountainous'


def test_empty_elevations_defaults_to_flat_no_crash():
    terrain, gain = geo.classify_terrain_from_elevations([])
    assert terrain == 'flat'
    assert gain == 0.0


def test_single_point_elevations_no_crash():
    # Regression guard: span_points could be 0 here, which would raise
    # ZeroDivisionError with a naive implementation.
    terrain, gain = geo.classify_terrain_from_elevations([100])
    assert terrain == 'flat'


def test_select_route_waypoints_short_route_returns_endpoints_only():
    short = [(40.0, -74.0), (40.01, -74.0), (40.02, -74.0)]
    waypoints = geo.select_route_waypoints(short, interval_km=150)
    assert waypoints == [short[0], short[-1]]


def test_select_route_waypoints_respects_max_waypoints_cap():
    coords = [(40.0 + i * 0.05, -74.0) for i in range(500)]  # long route
    waypoints = geo.select_route_waypoints(coords, interval_km=10, max_waypoints=4)
    assert len(waypoints) <= 4


def test_select_route_waypoints_includes_origin_and_destination():
    coords = [(40.0 + i * 0.02, -74.0) for i in range(200)]
    waypoints = geo.select_route_waypoints(coords, interval_km=150, max_waypoints=6)
    assert waypoints[0] == coords[0]
    assert waypoints[-1] == coords[-1]


def test_select_route_waypoints_empty_input_no_crash():
    assert geo.select_route_waypoints([], interval_km=150) == []


def test_haversine_zero_distance_for_same_point():
    assert geo._haversine_km(40.0, -74.0, 40.0, -74.0) < 1e-9


def test_haversine_known_distance_nyc_to_boston():
    # NYC to Boston is approximately 300km -- loose bounds since this
    # is a sanity check on the formula, not a precision test.
    dist = geo._haversine_km(40.7128, -74.0060, 42.3601, -71.0589)
    assert 290 < dist < 310
