"""Traffic-aware Prediction.

Two tiers, same "real data when available, honest documented heuristic
otherwise" pattern the rest of services/ already uses (see geo.py's
module docstring):

1. REAL traffic: when routing goes through Google's Directions API
   with a departure_time (see geo.py's _get_route_google), Google
   returns `duration_in_traffic_min` directly -- this module doesn't
   need to estimate anything, it just needs to prefer that number when
   present (see route_planning.py, which calls apply_traffic()).

2. HEURISTIC fallback (every other provider, or no departure_time):
   a simple time-of-day rush-hour model. This is NOT live traffic data
   -- it's a documented estimate based on typical urban commute
   patterns, used only when nothing better is available, and always
   labeled as a heuristic in the response (never presented as measured
   like the Google branch is).
"""
from datetime import datetime

# Rush-hour windows (local time, 24h) and their congestion multiplier
# applied to free-flow drive time. Values are a common rule-of-thumb
# range for urban commute slowdown (roughly 20-40% longer during peak,
# per widely-cited traffic studies) -- not derived from this app's own
# data, since it has none.
_RUSH_HOUR_WINDOWS = [
    (7, 9, 1.35),    # morning rush
    (16, 19, 1.40),  # evening rush (slightly worse -- typically the heavier of the two)
]
_MODERATE_WINDOWS = [
    (6, 7, 1.10),
    (9, 10, 1.10),
    (12, 14, 1.10),  # lunchtime bump
    (19, 21, 1.10),
]


def _congestion_multiplier_for_hour(hour, is_urban):
    if not is_urban:
        # Rush-hour effects are a predominantly urban/suburban commute
        # pattern -- a rural or highway-only route doesn't get the same
        # multiplier just because of the clock.
        return 1.0, 'light'
    for start, end, mult in _RUSH_HOUR_WINDOWS:
        if start <= hour < end:
            return mult, 'heavy'
    for start, end, mult in _MODERATE_WINDOWS:
        if start <= hour < end:
            return mult, 'moderate'
    return 1.0, 'light'


def estimate_traffic_factor(departure_time=None, is_urban=True):
    """Heuristic time-of-day congestion estimate. `departure_time` is a
    naive local datetime (defaults to now) -- this app has no timezone
    data per route, so this is inherently an approximation, documented
    as such in the returned dict.
    """
    dt = departure_time or datetime.now()
    multiplier, level = _congestion_multiplier_for_hour(dt.hour, is_urban)
    return {
        'source': 'heuristic',
        'congestion_level': level,
        'duration_multiplier': multiplier,
        'note': 'Time-of-day estimate, not live traffic data. Configure GOOGLE_MAPS_API_KEY + '
                "ROUTING_PROVIDER='google' for real traffic-aware duration.",
    }


def apply_traffic(base_duration_min, route=None, departure_time=None, is_urban=True):
    """Single entry point route_planning.py/trip.py call: prefer REAL
    traffic (Google's duration_in_traffic_min, if `route` carries it)
    over the heuristic estimate.
    """
    if route and route.get('duration_in_traffic_min') is not None:
        traffic_duration = route['duration_in_traffic_min']
        return {
            'source': 'google_directions',
            'congestion_level': _label_from_ratio(traffic_duration / base_duration_min) if base_duration_min else 'unknown',
            'duration_multiplier': round(traffic_duration / base_duration_min, 2) if base_duration_min else None,
            'adjusted_duration_min': traffic_duration,
            'note': 'Real traffic-aware duration from Google Directions API.',
        }

    factor = estimate_traffic_factor(departure_time, is_urban)
    factor['adjusted_duration_min'] = round(base_duration_min * factor['duration_multiplier'], 1)
    return factor


def _label_from_ratio(ratio):
    if ratio >= 1.3:
        return 'heavy'
    if ratio >= 1.1:
        return 'moderate'
    return 'light'


def traffic_adjusted_speed_kmh(free_flow_speed_kmh, duration_multiplier):
    """Stop-and-go traffic doesn't just take longer -- it's also less
    energy-efficient per km (more braking/re-accelerating) than the
    same distance at a steady speed. Used to adjust the effective
    average speed fed into the range-prediction model's
    vehicle_speed_kmh feature, rather than only affecting ETA.
    """
    if duration_multiplier <= 1.0:
        return free_flow_speed_kmh
    return round(free_flow_speed_kmh / duration_multiplier, 1)
