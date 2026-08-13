"""Multi-stop Trip Planning, Round Trip Planning, and ETA Prediction.

Orchestrates the pieces that already exist (geo.py's routing/elevation/
weather-adjacent lookups, ml/predict.py's range-degradation model,
charging_time.py's charging-time model, traffic.py's traffic
adjustment) into a single leg-by-leg plan across an arbitrary number of
stops, inserting charging stops wherever a leg's energy need would
otherwise take the battery below a safety margin.

This module is deliberately still Flask-app-context-free where
possible (no direct DB queries) -- api/trip.py is responsible for
turning the result into a saved TripPlan row. The one exception is
`safe_range_km()`, a tiny pure function with no DB/Flask dependency at
all, kept here because it's the shared definition of "safe range" used
by both trip planning (this module) and destination recommendation
(services/destination_recommender.py).
"""
from . import geo
from . import traffic as traffic_mod
from .charging_time import predict_charging_time
from ..ml.predict import get_prediction

# Never plan a leg (or destination-recommendation radius) all the way
# down to 0% battery -- always keep this much in reserve. Matches the
# kind of conservative buffer real EV nav systems build in for a
# cold-weather range estimate that already carries real uncertainty.
SAFETY_MARGIN_PCT = 15.0

# When a leg's arrival battery would dip below SAFETY_MARGIN_PCT,
# charge back up to this level before continuing -- not all the way to
# 100% (slower charging tapers hard above ~80% on most EVs, and this
# app's charging model doesn't need to model that taper if trips just
# never target above this).
CHARGE_TARGET_PCT = 80.0


def safe_range_km(predicted_range_km, safety_margin_pct=SAFETY_MARGIN_PCT):
    """The range a trip plan (or destination recommendation) should
    actually treat as usable -- the model's predicted range held back
    by the safety margin, not the raw number. Shared by
    destination_recommender.py so "how far can I go and come back" uses
    the exact same margin trip planning does.
    """
    return round(predicted_range_km * (1 - safety_margin_pct / 100), 1)


def _predict_leg(vehicle, origin_lat, origin_lon, dest_lat, dest_lon, origin_name, dest_name,
                  battery_pct, heater_usage, num_passengers, battery_age_years,
                  speed_kmh, ambient_temperature_c, provider_config, departure_time=None, consumption_multiplier=1.0):
    """Fetch a real route + run the range model for ONE leg. Weather is
    approximated at the origin only (unlike trip.py's route-predict,
    which samples both ends) -- multi-stop plans already make one
    weather call per leg via this same approximation on every leg's
    origin, so sampling both ends of every leg would double the call
    count for comparatively little extra accuracy over a short leg.
    """
    route = geo.get_route(origin_lat, origin_lon, dest_lat, dest_lon,
                           provider_config=provider_config, departure_time=departure_time)
    if route is None:
        return None

    elevations = geo.get_elevation_profile(route['coordinates'], provider_config=provider_config)
    if elevations:
        terrain_type, elevation_gain_m = geo.classify_terrain_from_elevations(elevations)
    else:
        terrain_type, elevation_gain_m = 'flat', None

    traffic_report = traffic_mod.apply_traffic(route['duration_min'], route=route, departure_time=departure_time)
    effective_speed = traffic_mod.traffic_adjusted_speed_kmh(speed_kmh, traffic_report['duration_multiplier'] or 1.0)

    # Weather is intentionally NOT re-fetched here to keep this module
    # provider-agnostic and network-call-bounded -- callers that want
    # real weather per leg should pass it in via a future extension
    # point; for now this uses a caller-supplied ambient temperature
    # (see plan_multi_stop_trip's `ambient_temperature_c` parameter),
    # same conservative "one number for the whole plan" approach
    # trip.py's manual-entry mode already offers as an alternative to
    # per-point weather sampling.
    features = {
        'temperature_c': ambient_temperature_c,
        'humidity': 60,
        'wind_speed_kmh': 15,
        'precipitation': 'none',
        'battery_percentage': battery_pct,
        'vehicle_speed_kmh': effective_speed,
        'hvac_usage': heater_usage,
        'terrain_type': terrain_type,
        'battery_age_years': battery_age_years,
        'battery_capacity_kwh': vehicle.battery_capacity_kwh,
        'epa_range_km': vehicle.epa_range_km,
        'vehicle_weight_kg': vehicle.vehicle_weight_kg + (num_passengers * 75),
    }
    result = get_prediction(features, 'random_forest')

    energy_per_km_kwh = (result['energy_consumption_wh_km'] * consumption_multiplier) / 1000
    total_energy_kwh = route['distance_km'] * energy_per_km_kwh
    battery_used_pct = (total_energy_kwh / vehicle.battery_capacity_kwh) * 100

    return {
        'origin': origin_name, 'destination': dest_name,
        'distance_km': route['distance_km'],
        'driving_duration_min': route['duration_min'],
        'traffic': traffic_report,
        'terrain_type': terrain_type,
        'elevation_gain_m': elevation_gain_m,
        'energy_kwh': round(total_energy_kwh, 2),
        'battery_used_pct': round(battery_used_pct, 1),
        'degradation_pct': result['range_degradation_pct'],
        'confidence': result.get('confidence'),
        'route_coordinates': route['coordinates'],
        'destination_lat': dest_lat, 'destination_lon': dest_lon,
    }


def plan_multi_stop_trip(vehicle, stop_names, round_trip=False, start_battery_pct=100.0,
                          heater_usage=True, num_passengers=1, battery_age_years=0.0,
                          speed_kmh=80.0, ambient_temperature_c=0.0, fast_charging=True,
                          consumption_multiplier=1.0, provider_config=None, departure_time=None):
    """Multi-stop Trip Planning + Round Trip Planning + ETA Prediction,
    all in one pass: geocode every stop, run each consecutive leg
    through the real range model, and insert a charging stop wherever a
    leg would otherwise arrive below SAFETY_MARGIN_PCT.

    `round_trip=True` appends the first stop again at the end -- the
    whole itinerary is then planned as one continuous sequence of legs,
    so a round trip's return leg gets its own real route/terrain/energy
    calculation rather than assuming it mirrors the outbound leg
    (return terrain/route CAN differ on some road networks, and even
    when it doesn't, computing it explicitly costs nothing extra and
    avoids the assumption).

    Returns a dict with per-leg detail and trip-wide totals, or an
    'error' key if a stop couldn't be geocoded/routed.
    """
    if not stop_names or len(stop_names) < 2:
        return {'error': 'At least 2 stops (origin + destination) are required.'}

    provider_config = dict(provider_config or {})
    stops = list(stop_names)
    if round_trip:
        stops = stops + [stops[0]]

    geocoded = []
    for name in stops:
        lat, lon, display = geo.geocode_place(name, provider_config=provider_config)
        if lat is None:
            return {'error': f"Could not geocode '{name}'"}
        geocoded.append({'name': name, 'display': display, 'lat': lat, 'lon': lon})

    legs = []
    battery_pct = start_battery_pct
    num_charging_stops = 0
    total_distance_km = 0.0
    total_driving_min = 0.0
    total_charging_min = 0.0
    feasible = True

    for i in range(len(geocoded) - 1):
        origin, dest = geocoded[i], geocoded[i + 1]
        leg = _predict_leg(
            vehicle, origin['lat'], origin['lon'], dest['lat'], dest['lon'],
            origin['display'] or origin['name'], dest['display'] or dest['name'],
            battery_pct, heater_usage, num_passengers, battery_age_years,
            speed_kmh, ambient_temperature_c, provider_config, departure_time, consumption_multiplier,
        )
        if leg is None:
            return {'error': f"Could not fetch a route from '{origin['name']}' to '{dest['name']}'"}

        arrival_pct = battery_pct - leg['battery_used_pct']
        charging_stop = None
        needed_start_pct = leg['battery_used_pct'] + SAFETY_MARGIN_PCT

        if battery_pct < needed_start_pct:
            # Need to charge before departing on this leg. Charge to
            # whichever is higher: the standard CHARGE_TARGET_PCT, or
            # just enough to cover this leg + margin if that's more
            # (e.g. an unusually long leg).
            charge_to = max(CHARGE_TARGET_PCT, min(100.0, needed_start_pct))
            if needed_start_pct > 100.0:
                # Even a full charge can't cover this leg with the
                # safety margin intact -- flag infeasible, but still
                # simulate charging to 100% and completing the leg
                # (arriving below margin) so the plan shows what WOULD
                # happen rather than just stopping.
                feasible = False
                charge_to = 100.0
            charging_result = predict_charging_time(vehicle, ambient_temperature_c, battery_pct, charge_to, fast_charging)
            charging_stop = {
                'at': leg['origin'],
                'charge_from_pct': round(battery_pct, 1),
                'charge_to_pct': round(charge_to, 1),
                **charging_result,
            }
            num_charging_stops += 1
            total_charging_min += charging_result['charging_time_minutes']
            battery_pct = charge_to
            arrival_pct = battery_pct - leg['battery_used_pct']

        if arrival_pct < 0:
            # Safety net -- shouldn't be reachable given the check
            # above, but never report a negative battery percentage.
            feasible = False
            arrival_pct = 0.0

        leg['charging_stop'] = charging_stop
        leg['battery_pct_at_departure'] = round(battery_pct, 1)
        leg['battery_pct_on_arrival'] = round(max(0.0, arrival_pct), 1)
        legs.append(leg)

        battery_pct = max(0.0, arrival_pct)
        total_distance_km += leg['distance_km']
        total_driving_min += leg['driving_duration_min']

    return {
        'stops': [g['display'] or g['name'] for g in geocoded],
        'round_trip': round_trip,
        'legs': legs,
        'total_distance_km': round(total_distance_km, 1),
        'total_driving_duration_min': round(total_driving_min, 1),
        'total_charging_time_min': round(total_charging_min, 1),
        'total_eta_min': round(total_driving_min + total_charging_min, 1),
        'num_charging_stops': num_charging_stops,
        'final_battery_pct': round(battery_pct, 1),
        'feasible': feasible,
    }
