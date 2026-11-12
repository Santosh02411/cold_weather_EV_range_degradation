"""Speed-based Energy Consumption.

A standalone, chartable version of the same physical relationship
ml/feature_engineering.py's `speed_squared_norm` feature encodes for
the ML model (aerodynamic drag scales with speed^2) -- that feature is
one input among many the trained model learns a weight for; THIS
module is a simple, transparent, closed-form curve for showing a user
"how much does driving faster cost me" directly, independent of any
trained model. The two are deliberately not required to produce
identical numbers -- one is a learned model's internal feature, the
other is a standalone physics-based explainer.
"""

# A real EV's efficiency curve is roughly U-shaped: energy per km is
# HIGHER at low speed (motor/accessory overhead amortized over less
# distance, more stop-start) and rises again at high speed (drag
# dominates), with a efficiency sweet spot in the 40-60 km/h range for
# most passenger EVs. Modeled here as two simple regimes around that
# sweet spot rather than a single quadratic over the whole range, since
# a pure quadratic centered at 0 would (wrongly) predict city driving
# as the most efficient regime.
EFFICIENT_SPEED_KMH = 50.0


def energy_consumption_by_speed(base_wh_per_km, speed_kmh):
    """Return an adjusted Wh/km estimate for driving at `speed_kmh`,
    given `base_wh_per_km` (the vehicle's rated/baseline consumption,
    typically its EPA-derived Wh/km around EFFICIENT_SPEED_KMH).
    """
    if speed_kmh <= 0:
        return round(base_wh_per_km, 1)

    if speed_kmh <= EFFICIENT_SPEED_KMH:
        # Low-speed inefficiency: city stop-start driving costs more
        # than the sweet-spot baseline, tapering toward it as speed
        # rises. +25% at a crawl (10 km/h), ~0% at the sweet spot.
        low_speed_penalty = 0.25 * (1 - speed_kmh / EFFICIENT_SPEED_KMH)
        multiplier = 1 + low_speed_penalty
    else:
        # Above the sweet spot: aerodynamic drag scales with the SQUARE
        # of speed, so energy cost per km rises quadratically with how
        # far above the sweet spot you are (matches
        # feature_engineering.py's speed_squared_norm rationale).
        excess_ratio = (speed_kmh - EFFICIENT_SPEED_KMH) / EFFICIENT_SPEED_KMH
        multiplier = 1 + 0.6 * (excess_ratio ** 2)

    return round(base_wh_per_km * multiplier, 1)


def energy_curve(base_wh_per_km, speed_range=None):
    """Full speed -> Wh/km curve for charting ("energy vs. speed").
    Defaults to 20-140 km/h in 10 km/h steps, a reasonable range for
    highway/city trip planning.
    """
    speeds = speed_range or list(range(20, 141, 10))
    return [
        {'speed_kmh': s, 'wh_per_km': energy_consumption_by_speed(base_wh_per_km, s)}
        for s in speeds
    ]


def most_efficient_speed_kmh():
    """The sweet-spot speed this curve treats as baseline -- useful for
    a UI to highlight on the chart ("most efficient around Xkm/h")."""
    return EFFICIENT_SPEED_KMH
