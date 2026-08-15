"""EV vs Petrol Cost Comparison / Ownership Cost Analysis / Savings
Calculator -- all three share one underlying per-km/per-year cost
engine (compare_ev_vs_petrol below); they differ only in which extra
inputs (purchase price, ownership horizon) get layered on top and how
the result is framed. See docs/MEMORY.md for why these weren't built
as three separate calculations.

Documented, generic defaults below (petrol price, fuel economy, annual
mileage) -- same honesty convention as charging_cost.py's
DEFAULT_RATES_USD_PER_KWH: starting points a user should confirm or
override (services/cost_preferences.py handles that), not live pricing
or a claim about any specific petrol car. There's no live fuel-price
API wired into this app, same reasoning as
services/electricity_rates.py for electricity.
"""

DEFAULT_PETROL_PRICE_USD_PER_LITER = 1.00     # roughly representative of recent US-ish averages; override via CostPreference
DEFAULT_PETROL_L_PER_100KM = 8.5              # ~27.7 mpg -- typical mid-size sedan; override for a specific comparison car
DEFAULT_ANNUAL_KM = 15010.0                   # a commonly-cited average annual driving distance

# Documented, generic estimates -- EVs are widely reported to have
# meaningfully lower routine maintenance (no oil changes, fewer moving
# parts, regenerative braking reduces brake wear), but these are NOT
# vehicle-specific quotes; a user should override with their own real
# numbers where they have them.
DEFAULT_ANNUAL_MAINTENANCE_EV_USD = 400.0
DEFAULT_ANNUAL_MAINTENANCE_PETROL_USD = 700.0


def _ev_wh_per_km(vehicle):
    """Prefers the vehicle's own logged energy_consumption_wh_km;
    falls back to a rough estimate from battery capacity / EPA range
    (same fallback relationship used elsewhere in this app, e.g.
    energy_model.py) when that field hasn't been set for this vehicle.
    """
    if vehicle.energy_consumption_wh_km:
        return vehicle.energy_consumption_wh_km, 'vehicle_logged'
    if vehicle.epa_range_km:
        return round((vehicle.battery_capacity_kwh * 1000) / vehicle.epa_range_km, 1), 'estimated_from_epa_range'
    return None, None


def compare_ev_vs_petrol(vehicle, electricity_rate_usd_per_kwh, petrol_price_per_liter=None,
                          petrol_l_per_100km=None, annual_km=None, years=1):
    """EV vs Petrol Cost Comparison: cost per 100km and per year for
    this EV (at the given electricity rate) vs. a petrol car described
    by petrol_l_per_100km -- defaults are generic (see module
    docstring), not a specific make/model.
    """
    petrol_price_per_liter = petrol_price_per_liter if petrol_price_per_liter is not None else DEFAULT_PETROL_PRICE_USD_PER_LITER
    petrol_l_per_100km = petrol_l_per_100km if petrol_l_per_100km is not None else DEFAULT_PETROL_L_PER_100KM
    annual_km = annual_km if annual_km is not None else DEFAULT_ANNUAL_KM
    years = max(1, years)

    wh_per_km, wh_per_km_source = _ev_wh_per_km(vehicle)
    if wh_per_km is None:
        return None

    ev_cost_per_100km = round((wh_per_km / 1000) * 100 * electricity_rate_usd_per_kwh, 2)
    petrol_cost_per_100km = round(petrol_l_per_100km * petrol_price_per_liter, 2)

    ev_annual_cost = round(ev_cost_per_100km / 100 * annual_km, 2)
    petrol_annual_cost = round(petrol_cost_per_100km / 100 * annual_km, 2)
    annual_savings = round(petrol_annual_cost - ev_annual_cost, 2)

    return {
        'ev': {
            'wh_per_km': wh_per_km,
            'wh_per_km_source': wh_per_km_source,
            'electricity_rate_usd_per_kwh': electricity_rate_usd_per_kwh,
            'cost_per_100km_usd': ev_cost_per_100km,
            'annual_cost_usd': ev_annual_cost,
            'total_cost_usd': round(ev_annual_cost * years, 2),
        },
        'petrol': {
            'l_per_100km': petrol_l_per_100km,
            'price_per_liter_usd': petrol_price_per_liter,
            'cost_per_100km_usd': petrol_cost_per_100km,
            'annual_cost_usd': petrol_annual_cost,
            'total_cost_usd': round(petrol_annual_cost * years, 2),
        },
        'annual_km': annual_km,
        'years': years,
        'annual_savings_usd': annual_savings,
        'total_savings_usd': round(annual_savings * years, 2),
    }


def ownership_cost_analysis(vehicle, electricity_rate_usd_per_kwh, years,
                             ev_purchase_price_usd=None, petrol_purchase_price_usd=None,
                             annual_maintenance_ev_usd=None, annual_maintenance_petrol_usd=None,
                             petrol_price_per_liter=None, petrol_l_per_100km=None, annual_km=None):
    """Ownership Cost Analysis: total cost of ownership over `years`,
    purchase price + running costs (charging/fuel) + maintenance, for
    this EV vs. a comparably-described petrol car. Purchase price
    defaults to the vehicle catalog's price_usd where set (it's an
    unverified approximate MSRP -- see models/ev_vehicle.py), but
    there's no default for a petrol car's price since this app has no
    petrol vehicle catalog to draw one from; the caller must supply it
    for a purchase-price comparison to mean anything.
    """
    running = compare_ev_vs_petrol(
        vehicle, electricity_rate_usd_per_kwh,
        petrol_price_per_liter=petrol_price_per_liter, petrol_l_per_100km=petrol_l_per_100km,
        annual_km=annual_km, years=years,
    )
    if running is None:
        return None

    ev_purchase = ev_purchase_price_usd if ev_purchase_price_usd is not None else vehicle.price_usd
    maint_ev = annual_maintenance_ev_usd if annual_maintenance_ev_usd is not None else DEFAULT_ANNUAL_MAINTENANCE_EV_USD
    maint_petrol = annual_maintenance_petrol_usd if annual_maintenance_petrol_usd is not None else DEFAULT_ANNUAL_MAINTENANCE_PETROL_USD

    ev_total = running['ev']['total_cost_usd'] + (maint_ev * years) + (ev_purchase or 0)
    petrol_total = running['petrol']['total_cost_usd'] + (maint_petrol * years) + (petrol_purchase_price_usd or 0)

    return {
        'years': years,
        'ev': {
            **running['ev'],
            'purchase_price_usd': ev_purchase,
            'purchase_price_is_estimated': ev_purchase_price_usd is None and vehicle.price_usd is not None,
            'annual_maintenance_usd': maint_ev,
            'total_maintenance_usd': round(maint_ev * years, 2),
            'total_ownership_cost_usd': round(ev_total, 2),
        },
        'petrol': {
            **running['petrol'],
            'purchase_price_usd': petrol_purchase_price_usd,
            'annual_maintenance_usd': maint_petrol,
            'total_maintenance_usd': round(maint_petrol * years, 2),
            'total_ownership_cost_usd': round(petrol_total, 2),
        },
        'total_savings_usd': round(petrol_total - ev_total, 2),
        'purchase_price_note': (
            'EV purchase price omitted (no catalog price_usd on file and none supplied) -- '
            'total ownership cost reflects running costs and maintenance only.'
            if not ev_purchase else None
        ),
    }


def savings_calculator(vehicle, electricity_rate_usd_per_kwh, years,
                        petrol_price_per_liter=None, petrol_l_per_100km=None, annual_km=None,
                        ev_price_premium_usd=None):
    """Savings Calculator: same running-cost engine as
    compare_ev_vs_petrol, framed around 'how much would switching
    save', plus an optional payback period if the EV cost more to buy
    up front (ev_price_premium_usd = EV price minus the petrol car's
    price -- the caller computes that delta since this app has no
    petrol vehicle catalog to diff against automatically).
    """
    running = compare_ev_vs_petrol(
        vehicle, electricity_rate_usd_per_kwh,
        petrol_price_per_liter=petrol_price_per_liter, petrol_l_per_100km=petrol_l_per_100km,
        annual_km=annual_km, years=years,
    )
    if running is None:
        return None

    payback_years = None
    if ev_price_premium_usd is not None and ev_price_premium_usd > 0 and running['annual_savings_usd'] > 0:
        payback_years = round(ev_price_premium_usd / running['annual_savings_usd'], 1)

    return {
        **running,
        'ev_price_premium_usd': ev_price_premium_usd,
        'payback_period_years': payback_years,
        'payback_note': (
            "The EV's running costs are lower, but at this premium and these rates it never fully pays back "
            "within the projection -- try a longer horizon or check your rates."
            if ev_price_premium_usd and ev_price_premium_usd > 0 and running['annual_savings_usd'] <= 0
            else None
        ),
    }
