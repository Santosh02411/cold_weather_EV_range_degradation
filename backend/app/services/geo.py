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

IMPORTANT — these calls were written against each provider's documented
request/response format but could NOT be executed against the live
internet in the sandbox this was built in (no outbound network access
there). See docs/PROJECT_WORKFLOW.md for exactly what was and wasn't
verified. Test these against the real APIs before relying on them.
"""
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_ROUTE_URL = "http://router.project-osrm.org/route/v1/driving"
OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"

_HEADERS = {
    # Nominatim's usage policy requires a real, descriptive User-Agent
    # identifying the application - an empty/default one can get
    # requests silently blocked.
    'User-Agent': 'ColdWeatherEVRangeDegradation/1.0 (educational project)'
}


def geocode_place(place_name, timeout=10):
    """Resolve a place name (city, address) to (lat, lon) via Nominatim.
    Returns (lat, lon, display_name) or (None, None, None) on failure.
    """
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


def get_route(origin_lat, origin_lon, dest_lat, dest_lon, timeout=15):
    """Fetch a driving route from OSRM. Returns a dict with
    distance_km, duration_min, and a list of (lat, lon) coordinates
    along the route (used for elevation sampling), or None on failure.
    """
    coords = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    url = f"{OSRM_ROUTE_URL}/{coords}"
    try:
        resp = requests.get(
            url,
            params={'overview': 'full', 'geometries': 'geojson'},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get('code') != 'Ok' or not data.get('routes'):
            return None
        route = data['routes'][0]
        # GeoJSON coordinates are [lon, lat] pairs
        raw_coords = route['geometry']['coordinates']
        return {
            'distance_km': round(route['distance'] / 1000, 1),
            'duration_min': round(route['duration'] / 60, 1),
            'coordinates': [(c[1], c[0]) for c in raw_coords],
        }
    except Exception as e:
        print(f"[WARN] get_route failed: {e}")
        return None


def _sample_coordinates(coords, max_points=25):
    """Elevation APIs charge per point; a route can have hundreds of
    shape points. Evenly sample down to max_points so terrain
    classification stays representative without spamming the API."""
    if len(coords) <= max_points:
        return coords
    step = len(coords) / max_points
    return [coords[int(i * step)] for i in range(max_points)]


def get_elevation_profile(coordinates, timeout=15):
    """Batch elevation lookup via Open-Elevation. `coordinates` is a
    list of (lat, lon) tuples. Returns a list of elevation values in
    meters (same order), or None on failure."""
    if not coordinates:
        return None
    sampled = _sample_coordinates(coordinates)
    payload = {'locations': [{'latitude': lat, 'longitude': lon} for lat, lon in sampled]}
    try:
        resp = requests.post(OPEN_ELEVATION_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return [pt['elevation'] for pt in data.get('results', [])]
    except Exception as e:
        print(f"[WARN] get_elevation_profile failed: {e}")
        return None


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
