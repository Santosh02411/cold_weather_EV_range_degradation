"""CO2 Savings Calculator / Carbon Footprint Analysis / Fuel Savings /
Environmental Impact Dashboard -- all four share the same underlying
per-km emissions comparison (compare_ev_vs_petrol_emissions below),
mirroring how services/fuel_cost.py's compare_ev_vs_petrol() backs EV
vs Petrol Cost Comparison / Ownership / Savings in Cost Analysis. Grid
intensity and petrol emission factor come from services/grid_intensity.py;
petrol consumption/annual distance defaults come from the SAME
CostPreference-backed resolver as Cost Analysis
(services/cost_preferences.py) rather than a second copy of those
numbers, so a user's petrol comparison car is one car across both
feature areas, not two different assumed cars.
"""
from collections import defaultdict

from ..models.prediction import TripSimulation
from .grid_intensity import PETROL_KG_CO2_PER_LITER
from .fuel_cost import _ev_wh_per_km
from .analytics import _bucket_key, _bucket_label, _validate_period


def _ev_g_co2_per_km(wh_per_km, grid_intensity_g_co2_per_kwh):
    return (wh_per_km / 1000) * grid_intensity_g_co2_per_kwh


def _petrol_g_co2_per_km(l_per_100km):
    return (l_per_100km / 100) * PETROL_KG_CO2_PER_LITER * 1000


def compare_ev_vs_petrol_emissions(vehicle, grid_intensity_g_co2_per_kwh, petrol_l_per_100km, annual_km, years=1):
    """CO2 Savings Calculator: grams CO2 per km and per year for this
    EV (at the given grid intensity) vs. a petrol car described by
    petrol_l_per_100km."""
    years = max(1, years)
    wh_per_km, wh_per_km_source = _ev_wh_per_km(vehicle)
    if wh_per_km is None:
        return None

    ev_g_per_km = round(_ev_g_co2_per_km(wh_per_km, grid_intensity_g_co2_per_kwh), 1)
    petrol_g_per_km = round(_petrol_g_co2_per_km(petrol_l_per_100km), 1)

    ev_annual_kg = round(ev_g_per_km * annual_km / 1000, 1)
    petrol_annual_kg = round(petrol_g_per_km * annual_km / 1000, 1)
    annual_savings_kg = round(petrol_annual_kg - ev_annual_kg, 1)

    return {
        'ev': {
            'wh_per_km': wh_per_km,
            'wh_per_km_source': wh_per_km_source,
            'grid_intensity_g_co2_per_kwh': grid_intensity_g_co2_per_kwh,
            'g_co2_per_km': ev_g_per_km,
            'annual_kg_co2': ev_annual_kg,
            'total_kg_co2': round(ev_annual_kg * years, 1),
        },
        'petrol': {
            'l_per_100km': petrol_l_per_100km,
            'kg_co2_per_liter': PETROL_KG_CO2_PER_LITER,
            'g_co2_per_km': petrol_g_per_km,
            'annual_kg_co2': petrol_annual_kg,
            'total_kg_co2': round(petrol_annual_kg * years, 1),
        },
        'annual_km': annual_km,
        'years': years,
        'annual_savings_kg_co2': annual_savings_kg,
        'total_savings_kg_co2': round(annual_savings_kg * years, 1),
    }


def fuel_savings(petrol_l_per_100km, annual_km, years=1):
    """Fuel Savings: liters of petrol NOT burned by driving an EV
    instead, over `years` at `annual_km`/year -- a physical-volume
    number, deliberately separate from the dollar-denominated Savings
    Calculator in Cost Analysis (see docs/MEMORY.md Phase 10)."""
    years = max(1, years)
    annual_liters = round((annual_km / 100) * petrol_l_per_100km, 1)
    return {
        'petrol_l_per_100km': petrol_l_per_100km,
        'annual_km': annual_km,
        'years': years,
        'annual_liters_saved': annual_liters,
        'total_liters_saved': round(annual_liters * years, 1),
    }


def footprint_analytics(user_id, grid_intensity_g_co2_per_kwh, petrol_l_per_100km, period='monthly'):
    """Carbon Footprint Analysis: emissions over time from real logged
    trip energy (TripSimulation.estimated_energy_kwh), same source and
    bucketing helpers as analytics.cost_analytics() uses for Monthly
    Charging Cost -- but converted to kg CO2 (at the EV's actual grid
    intensity) instead of dollars, alongside what the same driving
    would have emitted in the comparison petrol car.
    """
    _validate_period(period)
    trips = TripSimulation.query.filter_by(user_id=user_id).order_by(TripSimulation.created_at.asc()).all()

    buckets = defaultdict(list)
    for t in trips:
        if t.created_at and t.estimated_energy_kwh and t.distance_km:
            buckets[_bucket_key(t.created_at, period)].append((t.estimated_energy_kwh, t.distance_km))

    series = []
    for key in sorted(buckets.keys()):
        rows = buckets[key]
        total_energy_kwh = sum(e for e, _ in rows)
        total_km = sum(km for _, km in rows)
        ev_kg = round(total_energy_kwh * grid_intensity_g_co2_per_kwh / 1000, 1)
        petrol_kg = round(_petrol_g_co2_per_km(petrol_l_per_100km) * total_km / 1000, 1)
        series.append({
            'period': key,
            'label': _bucket_label(key, period),
            'total_energy_kwh': round(total_energy_kwh, 1),
            'total_km': round(total_km, 1),
            'ev_kg_co2': ev_kg,
            'petrol_equivalent_kg_co2': petrol_kg,
            'kg_co2_saved': round(petrol_kg - ev_kg, 1),
        })

    total_ev_kg = sum(s['ev_kg_co2'] for s in series)
    total_petrol_kg = sum(s['petrol_equivalent_kg_co2'] for s in series)

    return {
        'period': period,
        'grid_intensity_g_co2_per_kwh': grid_intensity_g_co2_per_kwh,
        'petrol_l_per_100km': petrol_l_per_100km,
        'total_ev_kg_co2': round(total_ev_kg, 1),
        'total_petrol_equivalent_kg_co2': round(total_petrol_kg, 1),
        'total_kg_co2_saved': round(total_petrol_kg - total_ev_kg, 1),
        'series': series,
    }


# Commonly-cited equivalence figures for making a kg-CO2 number
# tangible -- documented, rounded estimates (e.g. widely-cited EPA
# reforestation figures), not a precise scientific claim about any
# specific tree or car.
KG_CO2_ABSORBED_PER_TREE_PER_YEAR = 21.0


def environmental_impact_summary(user_id, grid_intensity_g_co2_per_kwh, petrol_l_per_100km):
    """Environmental Impact Dashboard: an all-time total (not a
    projection) -- sums every logged trip's real emissions vs. the
    petrol-equivalent, directly from TripSimulation (not through
    footprint_analytics(), which only buckets by daily/weekly/monthly
    and has no 'all time' period), plus tangibility equivalences.
    """
    trips = TripSimulation.query.filter_by(user_id=user_id).all()
    valid_trips = [t for t in trips if t.estimated_energy_kwh and t.distance_km]

    total_energy_kwh = sum(t.estimated_energy_kwh for t in valid_trips)
    total_km = sum(t.distance_km for t in valid_trips)

    total_ev_kg = round(total_energy_kwh * grid_intensity_g_co2_per_kwh / 1000, 1)
    total_petrol_kg = round(_petrol_g_co2_per_km(petrol_l_per_100km) * total_km / 1000, 1)
    saved_kg = round(total_petrol_kg - total_ev_kg, 1)

    return {
        'total_ev_kg_co2': total_ev_kg,
        'total_petrol_equivalent_kg_co2': total_petrol_kg,
        'total_kg_co2_saved': saved_kg,
        'trip_count': len(valid_trips),
        'total_km': round(total_km, 1),
        'equivalent_trees_planted_per_year': round(saved_kg / KG_CO2_ABSORBED_PER_TREE_PER_YEAR, 1) if saved_kg > 0 else 0.0,
    }
