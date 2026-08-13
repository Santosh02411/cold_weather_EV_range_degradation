"""Home Charging Recommendation.

Compares charging at home overnight (AC Level 2, using
charging_time.predict_charging_time's slow-charging branch) against a
public DC fast charging stop, on both time and cost, and gives a plain
recommendation: home charging is almost always cheaper (see
charging_cost.py's default rate difference between the two tiers) but
takes much longer, so the deciding factor is usually whether it FITS
in the time actually available at home before the vehicle is needed
again.
"""
from .charging_time import predict_charging_time
from .charging_cost import estimate_charging_cost, DEFAULT_RATES_USD_PER_KWH


def recommend_home_vs_public(vehicle, current_pct, target_pct, temperature_c,
                              hours_available_at_home=8.0, home_rate_usd_per_kwh=None,
                              public_rate_usd_per_kwh=None):
    """Compare a home overnight charge against a public DC fast stop
    for the same current_pct -> target_pct top-up, and recommend one.

    `hours_available_at_home`: how long the vehicle will realistically
    sit at home before it's needed again (e.g. overnight = ~8h) -- the
    single most important input, since it's what determines whether
    home charging can even finish in time.
    """
    home_result = predict_charging_time(vehicle, temperature_c, current_pct, target_pct, fast_charging=False)
    public_result = predict_charging_time(vehicle, temperature_c, current_pct, target_pct, fast_charging=True)

    home_cost = estimate_charging_cost(
        home_result['energy_needed_kwh'], fast_charging=False,
        custom_rate=home_rate_usd_per_kwh,
    )
    public_cost = estimate_charging_cost(
        public_result['energy_needed_kwh'], fast_charging=True,
        custom_rate=public_rate_usd_per_kwh,
    )

    home_fits_in_window = home_result['charging_time_minutes'] <= hours_available_at_home * 60
    savings_usd = round(public_cost['estimated_cost_usd'] - home_cost['estimated_cost_usd'], 2)

    if home_fits_in_window:
        recommendation = 'home'
        reason = (f"Home charging finishes in {round(home_result['charging_time_minutes'] / 60, 1)}h, "
                   f"within your {hours_available_at_home}h window, and saves an estimated ${savings_usd} "
                   "compared to a public fast-charging stop.")
    else:
        recommendation = 'public_fast'
        reason = (f"Home charging would take {round(home_result['charging_time_minutes'] / 60, 1)}h -- longer than "
                   f"the {hours_available_at_home}h you have available -- so a public DC fast charger is needed "
                   f"to be ready in time, at an estimated ${public_cost['estimated_cost_usd'] - home_cost['estimated_cost_usd']:.2f} "
                   "premium over what the same charge would cost at home.")

    return {
        'recommendation': recommendation,
        'reason': reason,
        'home': {**home_result, 'cost': home_cost, 'fits_in_available_window': home_fits_in_window},
        'public_fast': {**public_result, 'cost': public_cost},
        'estimated_savings_charging_at_home_usd': savings_usd,
        'hours_available_at_home': hours_available_at_home,
    }
