"""Fastest Charger Recommendation + Cheapest Charger Recommendation.

Ties together every other Charging Management piece --
charger_matching.py (compatibility), charging_time.py (speed, capped by
each station's own max power), charging_cost.py (price), and
charging_availability.py (a real wait, not just a hypothetical one) --
into one ranked list of real nearby stations for a specific vehicle and
charging need.
"""
from .charger_matching import is_compatible
from .charging_time import predict_charging_time
from .charging_cost import estimate_charging_cost
from .charging_availability import estimate_queue_time


def evaluate_stations(vehicle, stations, current_pct, target_pct, temperature_c,
                       fast_charging=True, departure_time=None, home_rate_usd_per_kwh=None):
    """Annotate every station with predicted charging time (capped by
    that station's own max_power_kw), estimated cost, compatibility,
    and an availability/queue estimate. Returns the same list with
    those fields added -- ranking/filtering is left to the two
    recommend_* functions below so callers needing just the raw
    annotated list (e.g. the stations table in the UI) can use this
    directly too.
    """
    for station in stations:
        charging = predict_charging_time(
            vehicle, temperature_c, current_pct, target_pct, fast_charging,
            station_max_power_kw=station.get('max_power_kw'),
        )
        cost = estimate_charging_cost(
            charging['energy_needed_kwh'], fast_charging=fast_charging,
            usage_cost_text=station.get('usage_cost'),
        )
        queue = estimate_queue_time(station, departure_time)

        station['compatible'] = is_compatible(vehicle.charging_type, station.get('connector_types'))
        station['charging_estimate'] = charging
        station['cost_estimate'] = cost
        station['availability'] = queue
        # A simple, transparent "total time" a driver actually
        # experiences: predicted queue wait (0 if likely available)
        # plus predicted charging time -- this is what fastest-charger
        # ranking should optimize, not charging time alone.
        wait = queue.get('expected_wait_minutes') or 0
        station['total_time_estimate_minutes'] = round(charging['charging_time_minutes'] + wait, 1)
    return stations


def recommend_fastest(vehicle, stations, current_pct, target_pct, temperature_c,
                       fast_charging=True, departure_time=None, only_compatible=True):
    """Fastest Charger Recommendation: rank already-evaluated (or
    raw, evaluated here) stations by total time (queue wait +
    charging), compatible ones only by default.
    """
    evaluated = evaluate_stations(vehicle, stations, current_pct, target_pct, temperature_c,
                                   fast_charging, departure_time)
    candidates = [s for s in evaluated if not only_compatible or s['compatible'] is not False]
    candidates.sort(key=lambda s: s['total_time_estimate_minutes'])
    return candidates


def recommend_cheapest(vehicle, stations, current_pct, target_pct, temperature_c,
                        fast_charging=True, departure_time=None, only_compatible=True,
                        home_rate_usd_per_kwh=None):
    """Cheapest Charger Recommendation: rank already-evaluated (or raw,
    evaluated here) stations by estimated total cost, compatible ones
    only by default.
    """
    evaluated = evaluate_stations(vehicle, stations, current_pct, target_pct, temperature_c,
                                   fast_charging, departure_time, home_rate_usd_per_kwh)
    candidates = [s for s in evaluated if not only_compatible or s['compatible'] is not False]
    candidates.sort(key=lambda s: s['cost_estimate']['estimated_cost_usd'])
    return candidates
