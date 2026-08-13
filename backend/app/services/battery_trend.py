"""FEAT-1: turn a series of (date, SOH%) readings into a real trend --
estimated degradation rate per year, plus a naive projection. Kept as
plain functions operating on simple tuples (not ORM objects) so this
can be tested without a database, same pattern as
services/recalibration.py's degradation math.
"""
import numpy as np
from datetime import datetime, timedelta


def compute_trend(records):
    """`records`: list of (recorded_at: datetime, soh_pct: float),
    any order. Returns None if fewer than 2 records (can't fit a trend
    to a single point), otherwise a dict with the fitted slope
    (%/year), a simple linear projection for 1/3/5 years from the most
    recent record, and the raw data sorted chronologically for charting.
    """
    if len(records) < 2:
        return None

    sorted_records = sorted(records, key=lambda r: r[0])
    first_date = sorted_records[0][0]
    days = np.array([(r[0] - first_date).days for r in sorted_records], dtype=float)
    soh = np.array([r[1] for r in sorted_records], dtype=float)

    # Simple linear fit -- deliberately not a more complex degradation
    # curve (e.g. sqrt-of-time, which is more physically realistic for
    # calendar aging over long horizons): with typically few, irregularly
    # spaced, user-entered readings, a linear fit is the honest choice --
    # it doesn't pretend to model a curve shape that a handful of noisy
    # points can't actually distinguish from a straight line.
    slope_per_day, intercept = np.polyfit(days, soh, 1)
    slope_per_year = slope_per_day * 365.25

    latest_date, latest_soh = sorted_records[-1]
    projections = {}
    for years in (1, 3, 5):
        projected = latest_soh + slope_per_year * years
        projections[f'{years}_year'] = round(float(np.clip(projected, 0, 100)), 1)

    return {
        'slope_pct_per_year': round(float(slope_per_year), 2),
        'latest_soh_pct': latest_soh,
        'latest_recorded_at': latest_date.isoformat(),
        'num_records': len(records),
        'projections': projections,
        'data_points': [
            {'recorded_at': r[0].isoformat(), 'soh_pct': r[1]} for r in sorted_records
        ],
    }
