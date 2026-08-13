"""
FEAT-2: real charging station data via Open Charge Map
(https://openchargemap.org) -- a free, community-maintained global
database of EV charging locations. Same shape as the other geo
integrations (services/geo.py): a thin, documented wrapper around one
provider's API, written against their documented response shape but
not executed against the live internet in the sandbox this was built
in (see docs/PROJECT_WORKFLOW.md).

Works entirely keyless for light usage. Setting OCM_API_KEY (free,
register at https://openchargemap.org/site/develop/api) raises the
rate limit and is recommended for anything beyond casual local use --
same "works without a key, better with one" pattern as OpenWeatherMap.
"""
import requests

OCM_API_URL = "https://api.openchargemap.io/v3/poi/"


def find_charging_stations(lat, lon, distance_km=25, max_results=15, api_key=None, timeout=15):
    """Find real charging stations near a point. Returns a list of
    simplified station dicts, or None on failure (network error, bad
    response shape, etc. -- callers should treat None as "couldn't
    fetch," not "zero stations found," which is a real and different
    outcome (an empty list).
    """
    params = {
        'output': 'json',
        'latitude': lat,
        'longitude': lon,
        'distance': distance_km,
        'distanceunit': 'km',
        'maxresults': max_results,
        'compact': 'true',
        'verbose': 'false',
    }
    if api_key:
        params['key'] = api_key

    try:
        resp = requests.get(OCM_API_URL, params=params, timeout=timeout)
        resp.raise_for_status()
        raw_stations = resp.json()
        return [_simplify_station(s) for s in raw_stations if _simplify_station(s) is not None]
    except Exception as e:
        print(f"[WARN] find_charging_stations failed: {e}")
        return None


def _simplify_station(station):
    """Open Charge Map's raw response is deeply nested and has a lot of
    fields this app doesn't need. Flatten to what the UI actually shows,
    and skip entries missing basic location/address info rather than
    passing through a station a user can't actually navigate to.
    """
    info = station.get('AddressInfo')
    if not info or info.get('Latitude') is None:
        return None

    connections = station.get('Connections') or []
    connector_types = sorted(set(
        c.get('ConnectionType', {}).get('Title', 'Unknown')
        for c in connections if c.get('ConnectionType')
    ))
    max_power_kw = max(
        (c.get('PowerKW') for c in connections if c.get('PowerKW')),
        default=None,
    )
    total_points = sum(c.get('Quantity', 1) or 1 for c in connections) or len(connections)

    operator = station.get('OperatorInfo', {}).get('Title') if station.get('OperatorInfo') else None
    usage_cost = station.get('UsageCost')

    return {
        'id': station.get('ID'),
        'name': info.get('Title', 'Unnamed Station'),
        'address': ', '.join(filter(None, [
            info.get('AddressLine1'), info.get('Town'), info.get('StateOrProvince'), info.get('Postcode')
        ])),
        'latitude': info.get('Latitude'),
        'longitude': info.get('Longitude'),
        'distance_km': round(info.get('Distance', 0), 1) if info.get('Distance') is not None else None,
        'operator': operator,
        'num_points': total_points,
        'connector_types': connector_types,
        'max_power_kw': max_power_kw,
        'usage_cost': usage_cost,
        'status': (station.get('StatusType') or {}).get('Title', 'Unknown'),
    }
