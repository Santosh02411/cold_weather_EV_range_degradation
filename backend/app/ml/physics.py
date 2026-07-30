"""
Physics-informed baseline for cold-weather EV range degradation.

Unlike the original implementation (which used arbitrary hand-picked
temperature thresholds), this module derives the temperature -> degradation
curve by interpolating between real, published, cited benchmarks
(Geotab's 5.2M-trip analysis, Recurrent Auto's 30,000-vehicle winter study,
AAA's cold weather test, and DOE/INL findings). See:
/data/real_world_calibration/temperature_range_benchmarks.csv for the raw
anchor points and citations.

This baseline is intentionally simple and monotonic in temperature. The ML
models in train.py/predict.py are trained to CORRECT this baseline using
the other operating conditions (HVAC, wind, terrain, speed, battery age,
battery capacity) rather than learn the temperature relationship from
scratch, which is what "physics-informed ML" means in this project.
"""
import os
import csv
import numpy as np
from sklearn.isotonic import IsotonicRegression

_CALIBRATION_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', '..',
    'data', 'real_world_calibration', 'temperature_range_benchmarks.csv'
)

# Canonical anchor points used to build the monotonic curve: one "average,
# no explicit heat pump/resistive split" observation per temperature,
# taken directly from the CSV above. Kept as a literal fallback so the
# app still works if the CSV file is ever missing (e.g. minimal deploy).
_FALLBACK_ANCHORS_C = [-25, -15, -10, -7, 0, 10, 21.5, 30]
_FALLBACK_RETAINED_PCT = [50, 54, 75, 74, 78, 100, 115, 100]


def _load_anchor_curve():
    """Build the temperature -> % range retained curve from the real
    calibration CSV. Falls back to the literal constants above if the
    file can't be read."""
    if not os.path.exists(_CALIBRATION_CSV):
        return _FALLBACK_ANCHORS_C, _FALLBACK_RETAINED_PCT

    rows = []
    try:
        with open(_CALIBRATION_CSV, newline='') as f:
            for row in csv.DictReader(f):
                cond = row.get('condition', '')
                # Use the "average" style rows only for the canonical
                # curve; best/worst-performer and heat-pump/resistive
                # splits are informative but would distort a single
                # baseline curve, so they're excluded here.
                if 'best-performing' in cond or 'worst-performing' in cond:
                    continue
                if 'heat pump' in cond or 'resistive' in cond:
                    continue
                # AAA's rows split the SAME -7C point into "with heater"
                # and "temperature alone" variants -- both describe -7C
                # but aren't a single average, so they'd otherwise create
                # two y-values for one x and break monotonicity. Skip the
                # "no cabin heating" variant here since every other row
                # in this curve implicitly includes normal HVAC use.
                if 'temperature alone' in cond:
                    continue
                rows.append((float(row['temperature_c']), float(row['pct_of_rated_range_retained'])))
    except Exception:
        return _FALLBACK_ANCHORS_C, _FALLBACK_RETAINED_PCT

    if len(rows) < 3:
        return _FALLBACK_ANCHORS_C, _FALLBACK_RETAINED_PCT

    # Average any remaining duplicate temperatures so np.interp always
    # receives a strictly increasing x sequence (a second real bug this
    # surfaced: interpolating with duplicate/out-of-order x values
    # silently produces a non-monotonic curve instead of raising an error).
    by_temp = {}
    for t, pct in rows:
        by_temp.setdefault(t, []).append(pct)
    merged = sorted((t, sum(v) / len(v)) for t, v in by_temp.items())
    temps, pcts = zip(*merged)
    return list(temps), list(pcts)


_ANCHOR_TEMPS_C, _ANCHOR_RETAINED_PCT = _load_anchor_curve()

# Different published studies use different methodologies and disagree
# with each other at nearby temperatures (e.g. AAA's -7C lab test reads
# worse than Recurrent's -10C fleet-average). Straight-line interpolation
# through raw anchor points on data like that produces a curve where
# degradation briefly gets *better* as it gets colder, which is not
# physically meaningful. An isotonic (monotonic) regression finds the
# best-fitting curve that still only worsens as temperature drops,
# reconciling disagreeing sources instead of literally connecting them
# point to point. This only applies below the ~21.5C "sweet spot" that
# Geotab identifies; above it we don't have cold-weather-study coverage
# and treat degradation as 0, consistent with this project's cold-weather
# scope.
_SWEET_SPOT_C = 21.5

_cold_pairs = sorted(
    (t, max(0.0, 100.0 - p)) for t, p in zip(_ANCHOR_TEMPS_C, _ANCHOR_RETAINED_PCT)
    if t <= _SWEET_SPOT_C
)
_cold_temps = np.array([t for t, _ in _cold_pairs])
_cold_degradation = np.array([d for _, d in _cold_pairs])

_iso = IsotonicRegression(increasing=False, out_of_bounds='clip')
_iso.fit(_cold_temps, _cold_degradation)


def physics_baseline_degradation_pct(temperature_c):
    """Return the calibrated baseline % range degradation for a given
    ambient temperature, fit from real published benchmarks via isotonic
    regression (see module docstring for why not raw interpolation).
    Degradation is floored at 0 above the ~21.5C sweet spot; this project
    is scoped to cold-weather degradation, not heat-related loss.
    """
    if temperature_c >= _SWEET_SPOT_C:
        return 0.0
    degradation = _iso.predict([temperature_c])[0]
    return float(np.clip(degradation, 0, 65))


def physics_baseline_batch(temperature_c_array):
    """Vectorized version for use during dataset generation/training."""
    temps = np.asarray(temperature_c_array, dtype=float)
    degradation = _iso.predict(temps)
    degradation = np.where(temps >= _SWEET_SPOT_C, 0.0, degradation)
    return np.clip(degradation, 0, 65)


def calibration_anchors():
    """Expose the anchor points (for docs/tests/validation reporting)."""
    return list(zip(_ANCHOR_TEMPS_C, _ANCHOR_RETAINED_PCT))
