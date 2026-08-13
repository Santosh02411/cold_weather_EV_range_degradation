"""Charger Type Detection.

Open Charge Map's connector names are freeform strings from many
different station operators/networks ("CCS (Type 2)", "CCS1", "Combo
1", "Tesla (Standard)", "Type 2 (Socket Only)", ...) -- this module
normalizes them into a small set of canonical connector families and
checks them against a vehicle's own `charging_type` (also freeform,
see models/ev_vehicle.py) so a trip-planning UI can flag which nearby
stations a specific vehicle can actually plug into.
"""

# canonical family -> substrings that indicate it, checked against a
# lowercased connector/vehicle string. Order matters -- more specific
# patterns (nacs/tesla) are checked before generic ones.
_FAMILY_PATTERNS = [
    ('nacs', ['nacs', 'tesla']),
    ('ccs', ['ccs', 'combo']),
    ('chademo', ['chademo']),
    ('type2', ['type 2', 'type2', 'mennekes', 'j1772', 'type 1']),
]


def normalize_connector(name):
    """Map a freeform connector/charging-type string to a canonical
    family ('ccs', 'chademo', 'nacs', 'type2'), or None if it doesn't
    match anything recognized (kept as None rather than an 'unknown'
    bucket so callers can decide how to treat genuinely unrecognized
    strings -- a Charger Type Detection false negative is safer than a
    false positive here, since this drives whether a user is told a
    station will actually work for their car).
    """
    if not name:
        return None
    lowered = name.lower()
    for family, patterns in _FAMILY_PATTERNS:
        if any(p in lowered for p in patterns):
            return family
    return None


def is_compatible(vehicle_charging_type, station_connector_types):
    """Charger Type Detection: does at least one of a station's
    connector types match the vehicle's own charging type? Returns
    None (unknown, not incompatible) rather than False when either side
    can't be normalized -- an unrecognized connector string is NOT the
    same claim as "this definitely won't work."
    """
    vehicle_family = normalize_connector(vehicle_charging_type)
    if vehicle_family is None:
        return None
    station_families = {normalize_connector(c) for c in (station_connector_types or [])}
    station_families.discard(None)
    if not station_families:
        return None
    return vehicle_family in station_families


def annotate_compatibility(vehicle_charging_type, stations):
    """Add a 'compatible' field (True/False/None) to each station dict
    from services/charging_stations.py's find_charging_stations()."""
    for station in stations:
        station['compatible'] = is_compatible(vehicle_charging_type, station.get('connector_types'))
    return stations
