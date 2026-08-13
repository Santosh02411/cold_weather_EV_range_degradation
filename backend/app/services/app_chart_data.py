"""Data Visualization (app-data variants): Line Charts, Geographic
Weather Map, Battery Performance Charts, and Prediction Timeline --
DB-aware (Prediction, BatteryHealthRecord, WeatherLog), so this lives
in services/, not alongside chart_data.py's pure DataFrame functions
(same split as services/drift_monitor.py's docstring establishes
elsewhere in this project).
"""
from collections import defaultdict

from ..models.prediction import Prediction
from ..models.battery_health import BatteryHealthRecord
from ..models.ev_vehicle import EVVehicle
from ..models.dataset import WeatherLog
from .geo import geocode_place

# field -> display label. Deliberately a small curated set of
# Prediction columns rather than exposing every column -- these are
# the ones meaningful to plot as a trend over time.
LINE_CHART_FIELDS = {
    'range_degradation_pct': 'Range Degradation (%)',
    'predicted_range_km': 'Predicted Range (km)',
    'energy_consumption_wh_km': 'Energy Consumption (Wh/km)',
    'temperature_c': 'Temperature (C)',
    'prediction_confidence': 'Prediction Confidence',
    'charging_slowdown_pct': 'Charging Slowdown (%)',
}


def line_chart_data(user_id, field, limit=200):
    """Line Charts: any of a user's own logged Prediction fields,
    plotted against time (most recent `limit` predictions, oldest
    first so a chart reads left-to-right chronologically)."""
    if field not in LINE_CHART_FIELDS:
        return {'available': False, 'reason': f"field must be one of {list(LINE_CHART_FIELDS)}"}

    predictions = Prediction.query.filter_by(user_id=user_id) \
        .order_by(Prediction.created_at.desc()).limit(limit).all()
    predictions.reverse()

    points = [
        {'timestamp': p.created_at.isoformat(), 'value': getattr(p, field)}
        for p in predictions if p.created_at and getattr(p, field) is not None
    ]
    return {'available': len(points) > 0, 'field': field, 'label': LINE_CHART_FIELDS[field], 'points': points}


_SEVERITY_MARKER_COLORS = {'mild': '#34d399', 'moderate': '#fbbf24', 'severe': '#f87171', 'extreme': '#991b1b'}


def geographic_weather_map_data(limit=100, provider_config=None):
    """Geographic Weather Map: recently logged WeatherLog entries,
    geocoded to lat/lon. WeatherLog itself only stores the city NAME,
    not coordinates (see models/dataset.py) -- this geocodes each
    DISTINCT city once via the same free Nominatim service
    services/geo.py already uses elsewhere, rather than one geocode
    call per row (a handful of cities usually cover many log entries).
    """
    logs = WeatherLog.query.order_by(WeatherLog.fetched_at.desc()).limit(limit).all()
    if not logs:
        return {'available': False, 'reason': 'No weather data logged yet.'}

    coordinates_cache = {}
    points = []
    for log in logs:
        key = f"{log.city},{log.country or ''}"
        if key not in coordinates_cache:
            place = f"{log.city}, {log.country}" if log.country else log.city
            lat, lon, _ = geocode_place(place, provider_config=provider_config)
            coordinates_cache[key] = (lat, lon)
        lat, lon = coordinates_cache[key]
        if lat is None:
            continue
        points.append({
            'city': log.city, 'country': log.country, 'lat': lat, 'lon': lon,
            'temperature_c': log.temperature_c, 'severity': log.severity,
            'color': _SEVERITY_MARKER_COLORS.get(log.severity, '#638cff'),
            'fetched_at': log.fetched_at.isoformat() if log.fetched_at else None,
        })

    return {'available': len(points) > 0, 'n_points': len(points), 'points': points}


def battery_performance_chart_data(user_id, vehicle_id=None):
    """Battery Performance Charts: SOH readings over time, one series
    per vehicle -- chart-ready and distinct from
    services/analytics.py's battery_health_trends(), which reports the
    fitted TREND slope; this is the raw plottable series behind it.
    """
    query = BatteryHealthRecord.query.filter_by(user_id=user_id)
    if vehicle_id:
        query = query.filter_by(vehicle_id=vehicle_id)
    records = query.order_by(BatteryHealthRecord.recorded_at.asc()).all()

    by_vehicle = defaultdict(list)
    for r in records:
        by_vehicle[r.vehicle_id].append({'timestamp': r.recorded_at.isoformat(), 'soh_pct': r.soh_pct})

    series = []
    for vid, points in by_vehicle.items():
        vehicle = EVVehicle.query.get(vid)
        series.append({
            'vehicle_id': vid,
            'vehicle_name': f"{vehicle.manufacturer} {vehicle.model_name}" if vehicle else 'Unknown',
            'points': points,
        })
    return {'available': len(series) > 0, 'series': series}


def prediction_timeline_data(user_id, limit=50):
    """Prediction Timeline: a user's predictions in chronological
    order with the key details a timeline UI wants per entry --
    distinct from services/analytics.py's activity_analytics(), which
    aggregates into time BUCKETS rather than listing individual
    predictions.
    """
    predictions = Prediction.query.filter_by(user_id=user_id) \
        .order_by(Prediction.created_at.desc()).limit(limit).all()

    entries = []
    for p in predictions:
        vehicle = EVVehicle.query.get(p.vehicle_id)
        entries.append({
            'id': p.id,
            'timestamp': p.created_at.isoformat() if p.created_at else None,
            'vehicle_name': f"{vehicle.manufacturer} {vehicle.model_name}" if vehicle else 'Unknown',
            'temperature_c': p.temperature_c,
            'degradation_pct': p.range_degradation_pct,
            'predicted_range_km': p.predicted_range_km,
            'confidence': p.prediction_confidence,
            'model': p.ml_model_used,
        })
    return {'available': len(entries) > 0, 'entries': entries}
