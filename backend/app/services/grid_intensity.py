"""Grid Carbon Intensity (for CO2 Savings Calculator / Carbon Footprint
Analysis).

Same honesty convention as services/electricity_rates.py: there's no
live grid-carbon API wired into this app (real ones like
electricityMaps/WattTime exist but need a paid account this project
doesn't have) -- so this is a small table of documented regional
AVERAGE grams-CO2-per-kWh figures a user can pick from, not a live
reading of their actual grid mix at this moment. Keyed by the SAME
region keys as electricity_rates.py so picking one region on the
Electricity Price Integration page sets both a $/kWh rate and a
gCO2/kWh grid intensity together (see api/cost.py's update_preferences
and models/cost_preference.py).
"""

# grams CO2 per kWh, broadly representative grid-mix averages, not a
# live reading -- always overridable with a user's own known figure
# (CostPreference.grid_intensity_g_co2_per_kwh).
REGIONAL_GRID_INTENSITY_G_CO2_PER_KWH = {
    'us_national_average': {'label': 'US National Average', 'intensity': 386},
    'us_northeast': {'label': 'US Northeast', 'intensity': 290},
    'us_west': {'label': 'US West Coast', 'intensity': 250},
    'us_south': {'label': 'US South', 'intensity': 430},
    'us_midwest': {'label': 'US Midwest', 'intensity': 480},
    'eu_average': {'label': 'EU Average', 'intensity': 250},
    'uk_average': {'label': 'UK Average', 'intensity': 210},
    'canada_average': {'label': 'Canada Average', 'intensity': 130},
    'australia_average': {'label': 'Australia Average', 'intensity': 520},
}

# A gasoline combustion emission factor, not a regional estimate --
# burning one liter of gasoline releases a well-established, roughly
# constant mass of CO2 regardless of where it happens (commonly-cited
# figure, e.g. EPA/IPCC combustion-chemistry sourced). Kept here rather
# than in emissions.py so both live next to the other "how much CO2
# per unit of energy" constants in one place.
PETROL_KG_CO2_PER_LITER = 2.31

DEFAULT_GRID_INTENSITY_G_CO2_PER_KWH = REGIONAL_GRID_INTENSITY_G_CO2_PER_KWH['us_national_average']['intensity']


def list_regional_intensity():
    return [
        {'key': key, **values}
        for key, values in REGIONAL_GRID_INTENSITY_G_CO2_PER_KWH.items()
    ]


def get_regional_intensity(key):
    return REGIONAL_GRID_INTENSITY_G_CO2_PER_KWH.get(key)
