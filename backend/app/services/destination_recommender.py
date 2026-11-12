"""Destination Recommendation.

Given a current location and a SAFE driving radius (already accounting
for cold-weather range degradation -- see route_planning.py's
safe_range_km(), which callers should pass in rather than the vehicle's
raw EPA range), suggest real nearby destinations the vehicle can
actually reach and return from.

Uses the Overpass API (https://overpass-api.de), the free/keyless
query interface over OpenStreetMap's POI data -- same "free provider,
documented usage constraints, written but not executed against the
live internet in this sandbox" pattern as services/geo.py and
services/charging_stations.py (see geo.py's module docstring for the
verification caveat, which applies here identically).

Charging stations are deliberately NOT served from here even though
Overpass could return them -- services/charging_stations.py's Open
Charge Map integration is a purpose-built, richer data source for that
one category (connector types, live status, power ratings) and is
still the right tool for "find me a charger."  This module is for
everything else someone might want to drive an EV to.
"""
import requests

from .geo import haversine_km

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

_HEADERS = {
    'User-Agent': 'ColdWeatherEVRangeDegradation/1.0 (educational project)'
}

# category -> Overpass tag filter. Kept small and curated rather than
# exposing raw OSM tags to callers -- these are the categories a trip-
# planning UI realistically offers as buttons.
CATEGORY_TAGS = {
    'tourism': 'tourism=attraction',
    'nature': 'leisure=park',
    'restaurant': 'amenity=restaurant',
    'cafe': 'amenity=cafe',
    'lodging': 'tourism=hotel',
}


def recommend_destinations(lat, lon, safe_range_km, category='tourism', max_results=10, timeout=20):
    """Find real POIs of `category` within `safe_range_km` of (lat,
    lon), sorted nearest-first. Returns a list of dicts, or None on a
    genuine fetch failure (distinct from an empty list, which means
    "fetched fine, nothing found" -- same None-vs-empty-list contract
    services/charging_stations.py already uses).
    """
    tag_filter = CATEGORY_TAGS.get(category, CATEGORY_TAGS['tourism'])
    radius_m = int(safe_range_km * 1000)

    # Overpass QL: find nodes/ways with the given tag within radius_m
    # meters of the point. `out center` collapses ways to a
    # representative point so every result has a single lat/lon.
    query = f"""
    [out:json][timeout:{timeout}];
    (
      node[{tag_filter}](around:{radius_m},{lat},{lon});
      way[{tag_filter}](around:{radius_m},{lat},{lon});
    );
    out center {max_results * 3};
    """

    try:
        resp = requests.post(OVERPASS_URL, data={'data': query}, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[WARN] recommend_destinations failed: {e}")
        return None

    results = []
    for element in data.get('elements', []):
        poi_lat = element.get('lat') or (element.get('center') or {}).get('lat')
        poi_lon = element.get('lon') or (element.get('center') or {}).get('lon')
        name = (element.get('tags') or {}).get('name')
        if poi_lat is None or poi_lon is None or not name:
            continue
        distance_km = round(haversine_km(lat, lon, poi_lat, poi_lon), 1)
        results.append({
            'name': name,
            'category': category,
            'latitude': poi_lat,
            'longitude': poi_lon,
            'distance_km': distance_km,
            'round_trip_distance_km': round(distance_km * 2, 1),
        })

    results.sort(key=lambda r: r['distance_km'])
    return results[:max_results]
