"""
Battery Intelligence -- SOH prediction, degradation projection, aging
analysis, life estimation, and cold-start efficiency.

Every number here is either (a) grounded in a real, cited source, or
(b) derived from this app's own already-trained/already-computed
output (the ML prediction, SHAP explanation, or a user's real logged
BatteryHealthRecord readings) -- never a fabricated formula presented
as measured fact. Two related, commonly-requested features are
DELIBERATELY NOT implemented here: real per-pack voltage prediction and
internal resistance estimation. Both would require actual cell/pack
electrochemical data (voltage-vs-SOC curves, measured resistance vs.
temperature/age for a specific chemistry and pack design) that isn't
available to this project -- producing numbers for either would mean
presenting a fabricated formula as a real prediction, which is exactly
what this project has spent every prior phase moving away from. See
docs/MEMORY.md for the full reasoning.
"""
from datetime import datetime

# Geotab's fleet-telemetry-derived figure, already cited in
# ml/train.py's synthetic dataset generation (battery_age_years
# effect) -- reused here as the default "typical" calendar degradation
# rate when a vehicle has no real logged BatteryHealthRecord readings
# yet to fit a real trend from.
TYPICAL_CALENDAR_DEGRADATION_PCT_PER_YEAR = 2.3

# Commonly used industry convention for EV battery end-of-life / warranty
# thresholds (many manufacturer battery warranties guarantee a minimum
# ~70% capacity retention over the warranty period) -- used here as the
# default "how many more years until this counts as end-of-life"
# threshold, not a claim about any specific vehicle's actual warranty
# terms.
DEFAULT_EOL_THRESHOLD_PCT = 70


def estimate_soh_from_age(battery_age_years, decline_rate_pct_per_year=TYPICAL_CALENDAR_DEGRADATION_PCT_PER_YEAR):
    """Battery Health Prediction: a research-cited generic estimate for
    when a vehicle has no real logged SOH readings yet (FEAT-1). Once
    real readings exist, prefer the actual fitted trend
    (services/battery_trend.py) over this generic estimate -- this
    function is the honest fallback, not the preferred source.
    """
    if battery_age_years is None or battery_age_years < 0:
        return None
    soh = 100.0 - (decline_rate_pct_per_year * battery_age_years)
    return round(max(0.0, min(100.0, soh)), 1)


def classify_aging_rate(user_decline_pct_per_year, typical=TYPICAL_CALENDAR_DEGRADATION_PCT_PER_YEAR):
    """Battery Aging Analysis: compare a REAL fitted decline rate
    (from services/battery_trend.py's compute_trend, itself fit to a
    user's actual logged readings) against the cited typical rate.
    `user_decline_pct_per_year` should be a positive number (pp/year
    lost) -- battery_trend.py's slope is negative for degradation, so
    callers should pass its absolute value.
    """
    if user_decline_pct_per_year is None or typical <= 0:
        return None
    ratio = user_decline_pct_per_year / typical
    if ratio < 0.8:
        classification = 'slower_than_typical'
    elif ratio > 1.2:
        classification = 'faster_than_typical'
    else:
        classification = 'typical'
    return {
        'classification': classification,
        'ratio_to_typical': round(ratio, 2),
        'user_decline_pct_per_year': round(user_decline_pct_per_year, 2),
        'typical_decline_pct_per_year': typical,
    }


def estimate_years_to_eol(current_soh_pct, decline_pct_per_year, eol_threshold_pct=DEFAULT_EOL_THRESHOLD_PCT):
    """Battery Life Estimation: years until SOH is projected to cross
    the EOL threshold, via simple linear projection from the current
    point. Same "don't pretend a handful of points support a fancier
    curve" reasoning as battery_trend.py's linear (not sqrt-of-time)
    fit -- this is a projection, explicitly not a guarantee.
    """
    if current_soh_pct is None or decline_pct_per_year is None or decline_pct_per_year <= 0:
        return None
    if current_soh_pct <= eol_threshold_pct:
        return 0.0
    years = (current_soh_pct - eol_threshold_pct) / decline_pct_per_year
    return round(years, 1)


def cold_start_energy_multiplier(trip_distance_km, temperature_c):
    """Cold Start Efficiency: a short winter trip uses meaningfully more
    energy per km than the same trip once the pack/cabin have warmed up
    -- real, cited, but reported qualitatively ("a six-mile winter
    drive might consume double the energy of a summer one," fading on
    longer trips) rather than with a precise measured curve, because no
    real per-vehicle warm-up telemetry exists to calibrate one further.
    This function turns that cited qualitative shape into an explicit,
    documented approximation: full penalty (2x) at ~0 distance in very
    cold temperatures, fading linearly to no penalty by 25km, scaled by
    how cold it is relative to a 10C "no meaningful effect" cutoff.
    Returns a multiplier (>= 1.0) to apply to a per-km energy figure
    for the estimated first `trip_distance_km` of a trip.
    """
    if temperature_c is None or temperature_c >= 10 or trip_distance_km is None or trip_distance_km <= 0:
        return 1.0
    cold_severity = min(1.0, (10 - temperature_c) / 30.0)  # reaches 1.0 by -20C
    fade_distance_km = 25.0
    distance_factor = max(0.0, 1.0 - (trip_distance_km / fade_distance_km))
    extra = cold_severity * distance_factor  # up to +100% (2x total)
    return round(1.0 + extra, 2)


def generate_efficiency_curve(base_features, temp_range=range(-30, 41, 5)):
    """Battery Efficiency Curve: sweep temperature across a real range
    and run the ALREADY-TRAINED prediction model at each point -- this
    reuses the real model rather than inventing a separate efficiency
    formula, so the curve is guaranteed consistent with whatever a
    prediction for this vehicle would actually say at each temperature.
    `base_features` should be a fully-populated feature dict (see
    ml/predict.py's FEATURE_COLS) with everything except temperature_c
    held constant -- typically the vehicle's specs plus a "typical
    trip" backdrop (see train.py's BASELINE_TRIP_CONDITIONS for the
    same pattern used in Phase 1's calibration check).
    """
    from ..ml.predict import get_prediction

    curve = []
    for temp in temp_range:
        features = dict(base_features)
        features['temperature_c'] = temp
        result = get_prediction(features)
        curve.append({
            'temperature_c': temp,
            'energy_consumption_wh_km': result['energy_consumption_wh_km'],
            'range_degradation_pct': result['range_degradation_pct'],
        })
    return curve


def heating_energy_estimate(prediction_result, explanation, distance_km=None):
    """Battery Heating Requirement: rather than inventing a separate
    thermal model, reuse the SHAP/rule-based explanation ml/xai.py
    ALREADY computes for this exact prediction -- specifically the
    'Cabin Heater Active' factor's contribution_pct (how much of the
    total predicted degradation this run attributed to HVAC use) -- and
    translate that share into an actual kWh figure using the same
    prediction's own energy consumption output. If the explanation
    didn't attribute anything to HVAC (e.g. heater was off, or it's
    below the rule-based threshold that triggers the factor), returns
    zero explicitly rather than guessing.
    """
    hvac_share_pct = 0
    if explanation and explanation.get('explanations'):
        for factor in explanation['explanations']:
            if 'heater' in factor.get('factor', '').lower() or 'hvac' in factor.get('factor', '').lower():
                hvac_share_pct = factor.get('contribution_pct', 0)
                break

    energy_wh_km = prediction_result.get('energy_consumption_wh_km', 0)
    distance = distance_km if distance_km else 100  # default: per-100km figure if no specific trip given

    total_energy_kwh = (energy_wh_km * distance) / 1000
    heating_energy_kwh = total_energy_kwh * (hvac_share_pct / 100)

    return {
        'hvac_contribution_pct': hvac_share_pct,
        'total_energy_kwh': round(total_energy_kwh, 2),
        'estimated_heating_energy_kwh': round(heating_energy_kwh, 2),
        'distance_km': distance,
    }


def temperature_exposure_analysis(city, days_back=None):
    """Battery Temperature Analysis: rather than modeling internal
    battery temperature (no real per-vehicle thermal telemetry exists
    to ground that), this aggregates REAL logged ambient weather
    lookups for a location (models/dataset.py's WeatherLog -- every
    weather check this app has ever made gets logged there) into how
    often that location has actually been cold enough to matter. This
    is real data about a real, if limited and app-usage-dependent,
    sample -- not a fabricated climate model. Grows more meaningful the
    more this app is used for a given city; explicitly reports its own
    sample size so a thin sample doesn't look more authoritative than
    it is.
    """
    from ..models.dataset import WeatherLog
    from datetime import timedelta

    query = WeatherLog.query.filter(WeatherLog.city.ilike(city))
    if days_back:
        query = query.filter(WeatherLog.fetched_at >= datetime.utcnow() - timedelta(days=days_back))
    logs = query.all()

    if not logs:
        return {'city': city, 'sample_size': 0, 'note': 'No weather history logged for this city yet.'}

    severities = {}
    for log in logs:
        sev = log.severity or 'unknown'
        severities[sev] = severities.get(sev, 0) + 1

    below_freezing = sum(1 for l in logs if l.temperature_c is not None and l.temperature_c <= 0)

    return {
        'city': city,
        'sample_size': len(logs),
        'severity_breakdown': severities,
        'pct_readings_below_freezing': round(100 * below_freezing / len(logs), 1),
        'note': f'Based on {len(logs)} weather lookups this app has logged for {city} -- '
                f'a real but app-usage-dependent sample, not a full climate record.',
    }
