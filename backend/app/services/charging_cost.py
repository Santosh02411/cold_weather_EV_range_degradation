"""Charging Cost Estimation.

Open Charge Map's `usage_cost` field (see
services/charging_stations.py's simplified station dict) is a freeform
string set by whoever submitted the station -- "Free", "$0.35/kWh",
"0.42 USD per kWh", "Membership required", or often just missing
entirely. This module makes a best effort to parse a real $/kWh out of
that text, and falls back to documented DEFAULT_RATES_USD_PER_KWH
otherwise -- always labeling which happened in the result, so a UI
never presents a guessed rate as if it were the station's actual
listed price.

Rates are USD-denominated estimates based on commonly-cited US
averages for each charging tier as of this being written, NOT live
utility or network pricing -- see the `source` field in every result.
"""
import re

# Documented estimates, not live pricing -- see module docstring.
DEFAULT_RATES_USD_PER_KWH = {
    'dc_fast': 0.42,
    'level2': 0.24,
    'home': 0.14,
}

# Matches things like "$0.35/kWh", "0.42 USD per kWh", "£0.30 / kWh"
_PRICE_PATTERN = re.compile(r'[\$£€]?\s*(\d+(?:\.\d+)?)\s*(?:usd|dollars?)?\s*/?\s*(?:per\s*)?kwh', re.IGNORECASE)
_FREE_PATTERN = re.compile(r'\bfree\b', re.IGNORECASE)


def parse_price_per_kwh(usage_cost_text):
    """Best-effort extraction of a $/kWh rate from a station's freeform
    usage_cost text. Returns 0.0 if the text says the station is free,
    a float if a rate could be parsed, or None if neither (missing,
    unparseable, or describes a non-per-kWh scheme like a flat session
    fee or membership requirement -- those aren't representable as a
    $/kWh rate, so None correctly signals "couldn't determine a rate"
    rather than silently returning 0).
    """
    if not usage_cost_text:
        return None
    if _FREE_PATTERN.search(usage_cost_text):
        return 0.0
    match = _PRICE_PATTERN.search(usage_cost_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _default_tier(fast_charging):
    return 'dc_fast' if fast_charging else 'level2'


def estimate_charging_cost(energy_needed_kwh, fast_charging=True, usage_cost_text=None, custom_rate=None):
    """Estimate the cost of one charging session. Prefers, in order:
    1. `custom_rate` if the caller supplies one (e.g. a user's own
       known home electricity rate -- see services/home_charging.py),
    2. a rate parsed from the station's own listed usage_cost_text,
    3. the documented DEFAULT_RATES_USD_PER_KWH fallback for the
       relevant charging tier.
    """
    if custom_rate is not None:
        rate, source = custom_rate, 'custom_rate'
    else:
        parsed = parse_price_per_kwh(usage_cost_text)
        if parsed is not None:
            rate, source = parsed, 'station_listed'
        else:
            tier = _default_tier(fast_charging)
            rate, source = DEFAULT_RATES_USD_PER_KWH[tier], 'default_estimate'

    return {
        'price_per_kwh_usd': round(rate, 3),
        'source': source,
        'estimated_cost_usd': round(energy_needed_kwh * rate, 2),
        'energy_needed_kwh': round(energy_needed_kwh, 2),
    }
