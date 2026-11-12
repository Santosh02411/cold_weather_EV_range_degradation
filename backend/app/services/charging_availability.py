"""Charger Availability + Charging Queue Prediction.

No free, broadly-available API gives real-time per-connector occupancy
across arbitrary charging networks the way OCM gives static station
data (a handful of individual network apps expose their own live
status, but not through one aggregated free API). So both of these are
DOCUMENTED HEURISTIC ESTIMATES, clearly labeled as such in every
result -- never presented as live occupancy data:

  - Charger Availability: whether the station itself is reported
    operational (real data, from OCM's StatusType) combined with a
    time-of-day demand heuristic for how likely an individual connector
    is to be free.
  - Charging Queue Prediction: an expected wait time derived from that
    same availability estimate and how many connectors the station has
    (more points -> lower expected wait for the same demand level).

Demand-by-hour follows the same shape as services/traffic.py's rush-
hour heuristic (commute-hour peaks), since EV charging demand at public
stations tracks commute patterns reasonably closely -- morning/evening
commute windows are this module's peak-demand windows too.
"""
from datetime import datetime

# hour-of-day -> relative demand level (0=quiet, 1=typical, 2=peak).
# Same rush-hour windows services/traffic.py uses, since public
# charging demand tracks commute timing.
_PEAK_HOURS = [(7, 9), (16, 19)]
_MODERATE_HOURS = [(9, 11), (12, 14), (19, 21)]

# Non-operational OCM status values that mean "don't bother" regardless
# of any demand heuristic.
_DOWN_STATUSES = {'faulted', 'not operational', 'temporarily unavailable', 'planned for future date'}


def _demand_level(hour):
    for start, end in _PEAK_HOURS:
        if start <= hour < end:
            return 2
    for start, end in _MODERATE_HOURS:
        if start <= hour < end:
            return 1
    return 0


def estimate_availability(station, departure_time=None):
    """Estimate the probability an arriving driver finds a free
    connector at `station` (a dict from
    services/charging_stations.py). Returns a dict with a 0-100
    'available_probability_pct' and a plain-language label, always
    flagged as a heuristic estimate.
    """
    status = (station.get('status') or 'unknown').lower()
    if any(down in status for down in _DOWN_STATUSES):
        return {
            'source': 'heuristic', 'available_probability_pct': 0, 'label': 'likely unavailable',
            'reason': f"Station status reported as '{station.get('status')}'.",
        }

    num_points = station.get('num_points') or 1
    dt = departure_time or datetime.now()
    demand = _demand_level(dt.hour)

    # More connectors at a station meaningfully lowers the chance ALL
    # of them are occupied at once for the same demand level -- modeled
    # here as a simple diminishing-returns curve, not a queueing-theory
    # simulation (this app has no real arrival-rate data to calibrate
    # one against).
    base_pct = {0: 85, 1: 65, 2: 40}[demand]
    points_bonus = min(15, (num_points - 1) * 5)
    probability = min(98, base_pct + points_bonus)

    label = 'likely available' if probability >= 70 else ('possibly busy' if probability >= 45 else 'likely busy')
    return {
        'source': 'heuristic', 'available_probability_pct': probability, 'label': label,
        'reason': f"Time-of-day demand estimate ({['off-peak', 'moderate', 'peak'][demand]} hours), "
                  f"{num_points} connector(s) at this station.",
    }


def estimate_queue_time(station, departure_time=None):
    """Charging Queue Prediction: expected wait (minutes) for a free
    connector, derived from estimate_availability() above. Always 0
    when availability is estimated 'likely available' -- this is not
    trying to predict exact queue lengths, just flag "you might wait a
    bit" vs "you almost certainly won't."
    """
    availability = estimate_availability(station, departure_time)
    prob = availability['available_probability_pct']

    if prob >= 70:
        expected_wait_min = 0
    elif prob >= 45:
        expected_wait_min = 10
    elif prob > 0:
        expected_wait_min = 25
    else:
        expected_wait_min = None  # station itself down -- "wait" isn't the right frame

    return {
        **availability,
        'expected_wait_minutes': expected_wait_min,
    }
