"""Tests for EVVehicle.supports_fast_charging's threshold logic.
Duplicated here rather than imported, for the same reason as
test_recalibration_math.py: ev_vehicle.py imports db.Model (needs
flask_sqlalchemy, not installed in this project's build sandbox). See
that file's docstring for the full reasoning -- same tradeoff, same
disclosure.
"""

FAST_CHARGING_THRESHOLD_KW = 50


def supports_fast_charging(max_charging_power_kw):
    """Verbatim copy of the logic in EVVehicle.supports_fast_charging."""
    return bool(max_charging_power_kw and max_charging_power_kw >= FAST_CHARGING_THRESHOLD_KW)


def test_above_threshold_supports_fast_charging():
    assert supports_fast_charging(150) is True


def test_at_threshold_supports_fast_charging():
    assert supports_fast_charging(50) is True


def test_below_threshold_does_not_support_fast_charging():
    assert supports_fast_charging(11) is False


def test_none_power_does_not_support_fast_charging():
    assert supports_fast_charging(None) is False


def test_zero_power_does_not_support_fast_charging():
    assert supports_fast_charging(0) is False
