"""Electricity Price Integration.

There's no live utility-rate API wired into this app (no account/API
key for one, and residential electricity pricing isn't something a
free public API exposes the way OpenWeatherMap does for weather) --
so this is a small, explicitly-labeled table of documented regional
AVERAGES a user can pick from to prefill their own rate, not a live
lookup. Same honesty convention as
services/charging_cost.py's DEFAULT_RATES_USD_PER_KWH: every value
here is a starting point for the user to confirm or override, and the
UI must say so, not present it as their actual bill.
"""

# residential $/kWh averages, broadly representative rather than
# precisely current -- a user should always be able to override with
# their own known rate instead (see CostPreference.home_rate_usd_per_kwh).
REGIONAL_AVERAGE_RATES_USD_PER_KWH = {
    'us_national_average': {'label': 'US National Average', 'home': 0.16, 'public_fast': 0.42},
    'us_northeast': {'label': 'US Northeast', 'home': 0.22, 'public_fast': 0.48},
    'us_west': {'label': 'US West Coast', 'home': 0.24, 'public_fast': 0.50},
    'us_south': {'label': 'US South', 'home': 0.13, 'public_fast': 0.38},
    'us_midwest': {'label': 'US Midwest', 'home': 0.14, 'public_fast': 0.36},
    'eu_average': {'label': 'EU Average', 'home': 0.28, 'public_fast': 0.55},
    'uk_average': {'label': 'UK Average', 'home': 0.27, 'public_fast': 0.60},
    'canada_average': {'label': 'Canada Average', 'home': 0.13, 'public_fast': 0.40},
    'australia_average': {'label': 'Australia Average', 'home': 0.25, 'public_fast': 0.55},
}


def list_regional_rates():
    return [
        {'key': key, **values}
        for key, values in REGIONAL_AVERAGE_RATES_USD_PER_KWH.items()
    ]


def get_regional_rate(key):
    return REGIONAL_AVERAGE_RATES_USD_PER_KWH.get(key)
