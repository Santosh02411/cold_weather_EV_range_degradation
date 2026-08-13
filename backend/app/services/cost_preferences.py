"""Resolves a user's effective cost-calculation inputs: their own
saved CostPreference values where set, falling back to the documented
defaults in charging_cost.py / fuel_cost.py otherwise. Every other
Cost Analysis feature (calculator, Monthly Charging Cost, EV vs
Petrol, Ownership, Savings) goes through this instead of each having
its own fallback logic, so "what rate did this calculation actually
use" has one answer.
"""
from ..models.cost_preference import CostPreference
from .charging_cost import DEFAULT_RATES_USD_PER_KWH
from .fuel_cost import DEFAULT_PETROL_PRICE_USD_PER_LITER, DEFAULT_PETROL_L_PER_100KM, DEFAULT_ANNUAL_KM
from .grid_intensity import DEFAULT_GRID_INTENSITY_G_CO2_PER_KWH
from .. import db


def get_or_create_preferences(user_id):
    prefs = CostPreference.query.filter_by(user_id=user_id).first()
    if not prefs:
        prefs = CostPreference(user_id=user_id)
        db.session.add(prefs)
        db.session.commit()
    return prefs


def get_effective_rates(user_id):
    """Returns the rates/defaults a cost calculation should actually
    use for this user, plus whether each came from their own saved
    preference or a documented default -- so a UI can label it."""
    prefs = get_or_create_preferences(user_id)

    def _resolve(value, default):
        return (value, 'user_saved') if value is not None else (default, 'default_estimate')

    home_rate, home_source = _resolve(prefs.home_rate_usd_per_kwh, DEFAULT_RATES_USD_PER_KWH['home'])
    public_rate, public_source = _resolve(prefs.public_rate_usd_per_kwh, DEFAULT_RATES_USD_PER_KWH['dc_fast'])
    petrol_price, petrol_price_source = _resolve(prefs.petrol_price_per_liter, DEFAULT_PETROL_PRICE_USD_PER_LITER)
    petrol_consumption, petrol_consumption_source = _resolve(prefs.petrol_l_per_100km, DEFAULT_PETROL_L_PER_100KM)
    annual_km, annual_km_source = _resolve(prefs.annual_km, DEFAULT_ANNUAL_KM)
    grid_intensity, grid_intensity_source = _resolve(prefs.grid_intensity_g_co2_per_kwh, DEFAULT_GRID_INTENSITY_G_CO2_PER_KWH)

    return {
        'home_rate_usd_per_kwh': home_rate, 'home_rate_source': home_source,
        'public_rate_usd_per_kwh': public_rate, 'public_rate_source': public_source,
        'petrol_price_per_liter': petrol_price, 'petrol_price_source': petrol_price_source,
        'petrol_l_per_100km': petrol_consumption, 'petrol_l_per_100km_source': petrol_consumption_source,
        'annual_km': annual_km, 'annual_km_source': annual_km_source,
        'grid_intensity_g_co2_per_kwh': grid_intensity, 'grid_intensity_source': grid_intensity_source,
    }
