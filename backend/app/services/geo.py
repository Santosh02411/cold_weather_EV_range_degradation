"""
Geo services for Phase 2 (RT-1 / RT-2): real route + elevation lookups to
replace the manual flat/hilly/mountainous dropdown with an actual terrain
classification, and to support route-based (not just single-point)
predictions.

All three providers below are free and require no API key, which is why
they were chosen for a project without a paid geo budget. Each has real
usage constraints, documented inline and in
docs/TECHNICAL_ARCHITECTURE.md, because using a free public demo server
in production without knowing its limits is exactly the kind of
unverified-but-looks-solid gap this project is trying to get away from:

- Nominatim (OpenStreetMap) — geocoding. Usage policy requires a
  descriptive User-Agent and caps at ~1 request/second for the public
  instance. Fine for this app's request-driven (not bulk) usage pattern.
  https://operations.osmfoundation.org/policies/nominatim/
- OSRM demo server — routing. The public router.project-osrm.org
  instance is explicitly for "light usage" / evaluation, not production
  traffic. Fine for demoing route-based prediction; a real deployment
  should self-host OSRM or switch to a paid provider (see
  FEATURE_TICKET_LIST.md, ticket RT-4).
- Open-Elevation — elevation lookups. Free public API, no key, but can
  be slow/rate-limited under load; batched into a single POST per route
  rather than one request per point to stay well under any reasonable
  limit.

Trip Planning phase adds Google Maps as an OPTIONAL fourth provider,
covering geocoding, routing (with real traffic-aware duration), and
elevation -- gated behind GOOGLE_MAPS_API_KEY, same opt-in pattern
ROUTING_PROVIDER='ors' already established. Google's APIs are paid
beyond a free monthly credit, which is exactly why they're optional
rather than the default: this project has no paid geo budget (see
above), but a deployment that DOES have a Google Maps budget gets
noticeably better data (real traffic, more complete road network,
higher rate limits) by setting the key and provider.

IMPORTANT — these calls were written against each provider's documented
request/response format but could NOT be executed against the live
internet in the sandbox this was built in (no outbound network access
there). See docs/PROJECT_WORKFLOW.md for exactly what was and wasn't
verified. Test these against the real APIs before relying on them.
"""
import requests
import numpy as np

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_DEMO_URL = "http://router.project-osrm.org"
ORS_ROUTE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"
OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"

GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
GOOGLE_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
GOOGLE_ELEVATION_URL = "https://maps.googleapis.com/maps/api/elevation/json"

_HEADERS = {
    # Nominatim's usage policy requires a real, descriptive User-Agent
    # identifying the application - an empty/default one can get
    # requests silently blocked.
    'User-Agent': 'ColdWeatherEVRangeDegradation/1.0 (educational project)'
}


def geocode_place(place_name, timeout=10, provider_config=None):
    """Resolve a place name (city, address) to (lat, lon). Uses Google's
    Geocoding API when `provider_config` sets GEOCODE_PROVIDER='google'
    AND a GOOGLE_MAPS_API_KEY is present; Nominatim (the original,
    keyless default) otherwise -- `provider_config` defaults to None so
    every existing caller that doesn't pass it keeps the exact original
    behavior. Returns (lat, lon, display_name) or (None, None, None) on
    failure.
    """
    provider_config = provider_config or {}
    api_key = provider_config.get('GOOGLE_MAPS_API_KEY')
    if provider_config.get('GEOCODE_PROVIDER') == 'google' and api_key:
        result = _geocode_google(place_name, api_key, timeout)
        if result[0] is not None:
            return result
        # Fall through to Nominatim rather than failing outright -- a
        # transient Google error shouldn't take down geocoding entirely
        # when a free fallback is available.
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={'q': place_name, 'format': 'json', 'limit': 1},
            headers=_HEADERS,
            timeout=timeout,
        )
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None, None, None
        top = results[0]
        return float(top['lat']), float(top['lon']), top.get('display_name', place_name)
    except Exception as e:
        print(f"[WARN] geocode_place('{place_name}') failed: {e}")
        return None, None, None


def _geocode_google(place_name, api_key, timeout):
    try:
        resp = requests.get(
            GOOGLE_GEOCODE_URL,
            params={'address': place_name, 'key': api_key},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') != 'OK' or not data.get('results'):
            return None, None, None
        top = data['results'][0]
        loc = top['geometry']['location']
        return float(loc['lat']), float(loc['lng']), top.get('formatted_address', place_name)
    except Exception as e:
        print(f"[WARN] _geocode_google('{place_name}') failed: {e}")
        return None, None, None


def get_route(origin_lat, origin_lon, dest_lat, dest_lon, provider_config=None, timeout=15, departure_time=None):
    """Fetch a driving route. Returns a dict with distance_km,
    duration_min, and a list of (lat, lon) coordinates along the route
    (used for elevation sampling), or None on failure.

    `provider_config` (a dict, typically Flask's app.config) controls
    which provider is used -- RT-4: this used to be hardcoded to OSRM's
    public demo server, which its own usage policy describes as "light
    usage / evaluation only," not something to point real traffic at.
      - ROUTING_PROVIDER='osrm' (default) + OSRM_BASE_URL: point at a
        self-hosted OSRM instance (see docs/TECHNICAL_ARCHITECTURE.md §5
        for a docker-compose starting point) or leave OSRM_BASE_URL
        unset to keep using the public demo server for local dev/testing.
      - ROUTING_PROVIDER='ors' + ORS_API_KEY: use OpenRouteService's free
        tier (2,000 requests/day as of their published free plan)
        instead of OSRM entirely.
      - ROUTING_PROVIDER='google' + GOOGLE_MAPS_API_KEY: use Google's
        Directions API. The only provider here that can return REAL
        traffic-aware duration -- pass `departure_time='now'` (or a unix
        timestamp) to get `duration_in_traffic_min` back in the result
        (see services/traffic.py, which uses this when available and
        falls back to a time-of-day heuristic otherwise).
    """
    provider_config = provider_config or {}
    provider = provider_config.get('ROUTING_PROVIDER', 'osrm')

    if provider == 'google' and provider_config.get('GOOGLE_MAPS_API_KEY'):
        return _get_route_google(origin_lat, origin_lon, dest_lat, dest_lon,
                                  provider_config['GOOGLE_MAPS_API_KEY'], timeout, departure_time)
    if provider == 'ors' and provider_config.get('ORS_API_KEY'):
        return _get_route_ors(origin_lat, origin_lon, dest_lat, dest_lon,
                               provider_config['ORS_API_KEY'], timeout)
    return _get_route_osrm(origin_lat, origin_lon, dest_lat, dest_lon,
                            provider_config.get('OSRM_BASE_URL', OSRM_DEMO_URL), timeout)


def get_route_alternatives(origin_lat, origin_lon, dest_lat, dest_lon, provider_config=None, timeout=15, max_alternatives=3):
    """Route Optimization: fetch up to `max_alternatives` distinct
    driving routes between two points, instead of just the single
    fastest one get_route() returns. Only OSRM (self-hosted or the
    public demo server) supports this directly via `alternatives=true`;
    ORS and Google both return a single best route through this app's
    simpler request shape, so for those providers this returns a
    one-route list -- callers (see services/route_optimization.py)
    should handle "only one option" as a normal, valid outcome rather
    than an error.
    """
    provider_config = provider_config or {}
    provider = provider_config.get('ROUTING_PROVIDER', 'osrm')

    if provider == 'osrm':
        routes = _get_route_osrm(origin_lat, origin_lon, dest_lat, dest_lon,
                                  provider_config.get('OSRM_BASE_URL', OSRM_DEMO_URL), timeout,
                                  alternatives=True, max_alternatives=max_alternatives)
        if routes:
            return routes
    single = get_route(origin_lat, origin_lon, dest_lat, dest_lon, provider_config, timeout)
    return [single] if single else []


def _get_route_osrm(origin_lat, origin_lon, dest_lat, dest_lon, base_url, timeout, alternatives=False, max_alternatives=3):
    coords = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    url = f"{base_url.rstrip('/')}/route/v1/driving/{coords}"
    try:
        resp = requests.get(
            url,
            params={'overview': 'full', 'geometries': 'geojson', 'alternatives': 'true' if alternatives else 'false'},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get('code') != 'Ok' or not data.get('routes'):
            return None
        routes_out = []
        for route in data['routes'][:max_alternatives if alternatives else 1]:
            # GeoJSON coordinates are [lon, lat] pairs
            raw_coords = route['geometry']['coordinates']
            routes_out.append({
                'distance_km': round(route['distance'] / 1000, 1),
                'duration_min': round(route['duration'] / 60, 1),
                'coordinates': [(c[1], c[0]) for c in raw_coords],
                'provider': 'osrm',
            })
        return routes_out if alternatives else routes_out[0]
    except Exception as e:
        print(f"[WARN] get_route (OSRM, {base_url}) failed: {e}")
        return None


def _get_route_ors(origin_lat, origin_lon, dest_lat, dest_lon, api_key, timeout):
    try:
        resp = requests.get(
            ORS_ROUTE_URL,
            params={
                'api_key': api_key,
                'start': f'{origin_lon},{origin_lat}',
                'end': f'{dest_lon},{dest_lat}',
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        features = data.get('features', [])
        if not features:
            return None
        feature = features[0]
        props = feature['properties']['summary']
        raw_coords = feature['geometry']['coordinates']  # [lon, lat] pairs
        return {
            'distance_km': round(props['distance'] / 1000, 1),
            'duration_min': round(props['duration'] / 60, 1),
            'coordinates': [(c[1], c[0]) for c in raw_coords],
            'provider': 'ors',
        }
    except Exception as e:
        print(f"[WARN] get_route (OpenRouteService) failed: {e}")
        return None


def _get_route_google(origin_lat, origin_lon, dest_lat, dest_lon, api_key, timeout, departure_time=None):
    """Google Directions API. When `departure_time` is given ('now' or a
    unix timestamp), Google also returns `duration_in_traffic` -- REAL
    traffic-aware duration, not a heuristic -- surfaced here as
    `duration_in_traffic_min` when present (see services/traffic.py).
    """
    params = {
        'origin': f'{origin_lat},{origin_lon}',
        'destination': f'{dest_lat},{dest_lon}',
        'mode': 'driving',
        'key': api_key,
    }
    if departure_time is not None:
        params['departure_time'] = departure_time
        params['traffic_model'] = 'best_guess'
    try:
        resp = requests.get(GOOGLE_DIRECTIONS_URL, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') != 'OK' or not data.get('routes'):
            return None
        route = data['routes'][0]
        leg = route['legs'][0]
        coordinates = [(step['start_location']['lat'], step['start_location']['lng']) for step in leg['steps']]
        end_step = leg['steps'][-1]
        coordinates.append((end_step['end_location']['lat'], end_step['end_location']['lng']))

        result = {
            'distance_km': round(leg['distance']['value'] / 1000, 1),
            'duration_min': round(leg['duration']['value'] / 60, 1),
            'coordinates': coordinates,
            'provider': 'google',
        }
        if 'duration_in_traffic' in leg:
            result['duration_in_traffic_min'] = round(leg['duration_in_traffic']['value'] / 60, 1)
        return result
    except Exception as e:
        print(f"[WARN] get_route (Google Directions) failed: {e}")
        return None


def _sample_coordinates(coords, max_points=25):
    """Elevation APIs charge per point; a route can have hundreds of
    shape points. Evenly sample down to max_points so terrain
    classification stays representative without spamming the API."""
    if len(coords) <= max_points:
        return coords
    step = len(coords) / max_points
    return [coords[int(i * step)] for i in range(max_points)]


def get_elevation_profile(coordinates, timeout=15, provider_config=None):
    """Batch elevation lookup. `coordinates` is a list of (lat, lon)
    tuples. Returns a list of elevation values in meters (same order),
    or None on failure. Uses Google's Elevation API when
    `provider_config` sets ELEVATION_PROVIDER='google' AND a
    GOOGLE_MAPS_API_KEY is present; Open-Elevation (keyless default)
    otherwise.
    """
    if not coordinates:
        return None
    sampled = _sample_coordinates(coordinates)

    provider_config = provider_config or {}
    api_key = provider_config.get('GOOGLE_MAPS_API_KEY')
    if provider_config.get('ELEVATION_PROVIDER') == 'google' and api_key:
        result = _get_elevation_google(sampled, api_key, timeout)
        if result is not None:
            return result
        # Fall through to Open-Elevation on a transient Google failure.

    payload = {'locations': [{'latitude': lat, 'longitude': lon} for lat, lon in sampled]}
    try:
        resp = requests.post(OPEN_ELEVATION_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return [pt['elevation'] for pt in data.get('results', [])]
    except Exception as e:
        print(f"[WARN] get_elevation_profile failed: {e}")
        return None


def _get_elevation_google(sampled_coordinates, api_key, timeout):
    locations = '|'.join(f'{lat},{lon}' for lat, lon in sampled_coordinates)
    try:
        resp = requests.get(
            GOOGLE_ELEVATION_URL,
            params={'locations': locations, 'key': api_key},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') != 'OK':
            return None
        return [pt['elevation'] for pt in data.get('results', [])]
    except Exception as e:
        print(f"[WARN] _get_elevation_google failed: {e}")
        return None


def _haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in km."""
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlambda / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(a))


# Public alias -- other services (destination_recommender.py) reuse this
# same great-circle distance calc rather than re-implementing it.
haversine_km = _haversine_km


def select_route_waypoints(coordinates, interval_km=150, max_waypoints=6):
    """RT-6: pick evenly-spaced waypoints along a route's coordinate
    list for weather sampling, instead of only ever sampling the two
    endpoints (Phase 3's 2-point approach). Walks the route's actual
    path length (not straight-line distance) and drops a waypoint every
    `interval_km`, capped at `max_waypoints` -- capped because each
    waypoint is a real extra weather-API call (see config.py's
    WEATHER_MULTI_WAYPOINT_ENABLED docstring for the cost tradeoff this
    is gated behind). Always includes the origin and destination.
    """
    if not coordinates or len(coordinates) < 2:
        return coordinates

    cumulative = [0.0]
    for i in range(1, len(coordinates)):
        lat1, lon1 = coordinates[i - 1]
        lat2, lon2 = coordinates[i]
        cumulative.append(cumulative[-1] + _haversine_km(lat1, lon1, lat2, lon2))
    total_km = cumulative[-1]

    if total_km <= interval_km:
        return [coordinates[0], coordinates[-1]]

    n_waypoints = min(max_waypoints, int(total_km // interval_km) + 1)
    target_distances = np.linspace(0, total_km, n_waypoints)

    waypoints = []
    for target in target_distances:
        idx = int(np.searchsorted(cumulative, target))
        idx = min(idx, len(coordinates) - 1)
        waypoints.append(coordinates[idx])
    return waypoints


def classify_terrain_from_elevations(elevations):
    """Turn a real elevation profile into the terrain_type category the
    prediction model expects ('flat' / 'hilly' / 'mountainous'),
    replacing the user's manual guess with an actual measurement.

    Classification is based on cumulative elevation gain per 100km of
    route (a standard cycling/driving climbing-intensity metric),
    thresholds chosen conservatively (documented, not derived from a
    formal study, since this maps a real measurement onto this
    project's existing 3-bucket categorical feature rather than
    replacing it with a continuous one):
      < 150 m of gain per 100km   -> flat
      150-500 m of gain per 100km -> hilly
      > 500 m of gain per 100km   -> mountainous
    """
    if not elevations or len(elevations) < 2:
        return 'flat', 0.0

    gain = sum(max(0, elevations[i] - elevations[i - 1]) for i in range(1, len(elevations)))
    span_points = len(elevations) - 1
    # Normalize gain to a "per 100 sampled segments" basis so the
    # threshold isn't sensitive to how many points were sampled.
    normalized_gain = (gain / span_points) * 100 if span_points else 0

    if normalized_gain < 150:
        return 'flat', round(gain, 1)
    elif normalized_gain < 500:
        return 'hilly', round(gain, 1)
    else:
        return 'mountainous', round(gain, 1)


def elevation_profile_stats(elevations):
    """Route Elevation Analysis: turn a raw elevation sample list into
    the summary stats a trip-planning UI actually wants to show (a
    mini elevation chart's axis range, total climbing/descending,
    highest/lowest points) -- classify_terrain_from_elevations() above
    only returns the single terrain bucket + gain the ML model needs;
    this is the fuller picture for a human looking at the route.
    """
    if not elevations or len(elevations) < 2:
        return None

    gain = sum(max(0, elevations[i] - elevations[i - 1]) for i in range(1, len(elevations)))
    loss = sum(max(0, elevations[i - 1] - elevations[i]) for i in range(1, len(elevations)))

    return {
        'min_elevation_m': round(min(elevations), 1),
        'max_elevation_m': round(max(elevations), 1),
        'total_ascent_m': round(gain, 1),
        'total_descent_m': round(loss, 1),
        'net_elevation_change_m': round(elevations[-1] - elevations[0], 1),
        'sample_points': len(elevations),
        'profile': [round(e, 1) for e in elevations],
    }
