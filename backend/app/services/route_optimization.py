"""Route Optimization: given several candidate routes between the same
two points (see services/geo.py's get_route_alternatives()), score each
one by predicted energy cost -- not just distance/duration -- and
recommend both the fastest and the most range-efficient option.

Deliberately does NOT re-run the full ML prediction pipeline per
alternative (that would mean N model-load-and-predict calls for a
single route-optimization request, which is slow and mostly redundant
-- the alternatives differ in distance/elevation, not in weather or
vehicle state). Instead it uses a lightweight physics-based energy
estimate (base Wh/km scaled by elevation gain) purely to RANK the
alternatives relative to each other. The actual headline
degradation/range numbers a user sees still come from the real ML
prediction (via /trip/api/route-predict or /trip/api/plan) run on
WHICHEVER route they pick.
"""

# Every 100m of climbing costs roughly this fraction of extra energy
# per km of route, on top of flat-ground consumption -- consistent with
# the elevation-gain-based terrain classification geo.py's
# classify_terrain_from_elevations() already uses, just expressed as a
# continuous energy penalty here instead of a 3-bucket category.
# Documented estimate, not a measured constant (see that function's
# docstring for the same disclosure).
ELEVATION_ENERGY_PENALTY_PER_100M_PER_100KM = 0.03  # +3% energy per 100m gain per 100km


def estimate_route_energy_kwh(distance_km, elevation_gain_m, base_wh_per_km):
    """Rough energy estimate for ranking alternatives against each
    other (see module docstring for why this isn't the ML model)."""
    base_kwh = distance_km * (base_wh_per_km / 1000)
    if distance_km <= 0:
        return round(base_kwh, 2)
    gain_per_100km = (elevation_gain_m / distance_km) * 100 if elevation_gain_m else 0
    penalty_multiplier = 1 + (gain_per_100km / 100) * ELEVATION_ENERGY_PENALTY_PER_100M_PER_100KM
    return round(base_kwh * penalty_multiplier, 2)


def optimize_routes(routes, base_wh_per_km, elevation_gains=None):
    """Annotate and rank a list of route dicts (from
    geo.get_route_alternatives(), each with distance_km/duration_min)
    with an estimated energy cost, and flag which is fastest vs most
    efficient.

    `elevation_gains`: optional list (same length/order as `routes`) of
    elevation gain in meters per route, from geo.get_elevation_profile()
    + classify_terrain_from_elevations() run per alternative. When not
    provided (e.g. elevation lookups were skipped to save API calls),
    ranks by distance alone -- flagged via `elevation_data` per entry
    so the caller/UI can be honest about it rather than presenting a
    guess as a measurement.
    """
    if not routes:
        return []

    annotated = []
    for i, route in enumerate(routes):
        gain = elevation_gains[i] if elevation_gains and i < len(elevation_gains) else None
        energy_kwh = estimate_route_energy_kwh(route['distance_km'], gain or 0, base_wh_per_km)
        annotated.append({
            **route,
            'estimated_energy_kwh': energy_kwh,
            'elevation_gain_m': gain,
            'elevation_data': gain is not None,
        })

    fastest = min(annotated, key=lambda r: r['duration_min'])
    most_efficient = min(annotated, key=lambda r: r['estimated_energy_kwh'])

    for r in annotated:
        r['is_fastest'] = r is fastest
        r['is_most_efficient'] = r is most_efficient

    annotated.sort(key=lambda r: (not r['is_most_efficient'], r['duration_min']))
    return annotated
