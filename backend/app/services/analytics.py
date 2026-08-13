"""Analytics Dashboard.

DB-aware (queries Prediction, TripSimulation, BatteryHealthRecord,
ChargingReservation, FavoriteVehicle, CommunityRangeReport, User), so
this lives in services/, not ml/ -- same split as
services/drift_monitor.py's docstring.

Date bucketing (Daily/Weekly/Monthly Analytics) is done in Python after
fetching rows, not via DB-specific SQL date functions (SQLite's
strftime, Postgres's date_trunc, ...) -- this app's default is SQLite
but DATABASE_URL can point anywhere (see config.py), so portable
grouping logic beats a marginally faster but DB-specific query, the
same choice api/dashboard.py's existing seasonal_chart() already made.

Most of these functions reuse an existing piece rather than
reimplementing it: battery_trend.compute_trend() for Battery Health
Trends, charging_cost.estimate_charging_cost() for Cost Analytics --
consistent with the rest of this project's "one shared implementation,
not a second copy" convention (see feature_engineering.py's docstring
for the same principle applied elsewhere).
"""
import calendar
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np

from ..models.prediction import Prediction, TripSimulation, CommunityRangeReport, SavedPrediction
from ..models.battery_health import BatteryHealthRecord
from ..models.charging_reservation import ChargingReservation
from ..models.vehicle_interactions import FavoriteVehicle
from ..models.report import ReportHistory
from ..models.ev_vehicle import EVVehicle
from ..models.user import User
from .. import db
from sqlalchemy import func
from .battery_trend import compute_trend
from .charging_cost import estimate_charging_cost, DEFAULT_RATES_USD_PER_KWH

VALID_PERIODS = ('daily', 'weekly', 'monthly')
_DEFAULT_LOOKBACK_DAYS = {'daily': 30, 'weekly': 90, 'monthly': 365}


def _validate_period(period):
    if period not in VALID_PERIODS:
        raise ValueError(f"period must be one of {VALID_PERIODS}, got '{period}'")


def _bucket_key(dt, period):
    if period == 'daily':
        return dt.strftime('%Y-%m-%d')
    if period == 'weekly':
        iso_year, iso_week, _ = dt.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    return dt.strftime('%Y-%m')


def _bucket_label(key, period):
    if period == 'monthly':
        year, month = key.split('-')
        return f"{calendar.month_abbr[int(month)]} {year}"
    return key


def _avg(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 2) if values else None


# ─────────────────── Daily / Weekly / Monthly Analytics ───────────────────

def activity_analytics(user_id, period='daily'):
    """Prediction volume + average degradation/confidence, bucketed by
    day, week, or month, for one user's own activity. Covers Daily
    Analytics, Weekly Analytics, and Monthly Analytics with one
    function -- they differ only in bucket granularity.
    """
    _validate_period(period)
    lookback_days = _DEFAULT_LOOKBACK_DAYS[period]
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)

    predictions = Prediction.query.filter(
        Prediction.user_id == user_id, Prediction.created_at >= cutoff
    ).order_by(Prediction.created_at.asc()).all()

    buckets = defaultdict(list)
    for p in predictions:
        if p.created_at:
            buckets[_bucket_key(p.created_at, period)].append(p)

    series = []
    for key in sorted(buckets.keys()):
        rows = buckets[key]
        series.append({
            'period': key,
            'label': _bucket_label(key, period),
            'prediction_count': len(rows),
            'avg_degradation_pct': _avg([r.range_degradation_pct for r in rows]),
            'avg_confidence': _avg([r.prediction_confidence for r in rows]),
        })

    return {
        'period': period,
        'lookback_days': lookback_days,
        'total_predictions': len(predictions),
        'series': series,
    }


# ───────────────────────── Battery Health Trends ─────────────────────────

def battery_health_trends(user_id):
    """Battery Health Trends across every vehicle the user has logged
    SOH readings for, reusing battery_trend.compute_trend() per
    vehicle (the same fitted-trend logic /vehicles/api/<id>/battery-health
    already exposes one vehicle at a time -- this is the multi-vehicle
    dashboard rollup of the same thing).
    """
    records = BatteryHealthRecord.query.filter_by(user_id=user_id).all()
    by_vehicle = defaultdict(list)
    for r in records:
        by_vehicle[r.vehicle_id].append((r.recorded_at, r.soh_pct))

    vehicles = []
    for vehicle_id, readings in by_vehicle.items():
        vehicle = EVVehicle.query.get(vehicle_id)
        trend = compute_trend(readings)
        vehicles.append({
            'vehicle_id': vehicle_id,
            'vehicle_name': f"{vehicle.manufacturer} {vehicle.model_name}" if vehicle else 'Unknown',
            'num_readings': len(readings),
            'trend': trend,
        })

    return {'vehicles': vehicles}


# ───────────────────────── Weather Impact Trends ─────────────────────────

_TEMP_BUCKETS = [
    ('Extreme Cold (<-15C)', lambda t: t < -15),
    ('Cold (-15 to 0C)', lambda t: -15 <= t < 0),
    ('Cool (0 to 15C)', lambda t: 0 <= t < 15),
    ('Mild (15 to 25C)', lambda t: 15 <= t <= 25),
    ('Hot (>25C)', lambda t: t > 25),
]


def weather_impact_trends(user_id, period='monthly'):
    """How temperature's effect on predicted degradation has looked
    over time: per-period average temperature and degradation, plus
    the overall correlation between the two (Pearson's r) as a single
    "how strong is the relationship in this user's own data" number.
    """
    _validate_period(period)
    predictions = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.asc()).all()
    if not predictions:
        return {'period': period, 'series': [], 'correlation': None, 'temperature_buckets': []}

    buckets = defaultdict(list)
    for p in predictions:
        if p.created_at:
            buckets[_bucket_key(p.created_at, period)].append(p)

    series = []
    for key in sorted(buckets.keys()):
        rows = buckets[key]
        series.append({
            'period': key,
            'label': _bucket_label(key, period),
            'avg_temperature_c': _avg([r.temperature_c for r in rows]),
            'avg_degradation_pct': _avg([r.range_degradation_pct for r in rows]),
        })

    temps = [p.temperature_c for p in predictions if p.temperature_c is not None]
    degradations = [p.range_degradation_pct for p in predictions if p.range_degradation_pct is not None]
    correlation = None
    if len(temps) == len(degradations) and len(temps) >= 2 and np.std(temps) > 0:
        correlation = round(float(np.corrcoef(temps, degradations)[0, 1]), 3)

    temp_buckets = []
    for label, predicate in _TEMP_BUCKETS:
        matching = [p for p in predictions if p.temperature_c is not None and predicate(p.temperature_c)]
        temp_buckets.append({
            'label': label,
            'count': len(matching),
            'avg_degradation_pct': _avg([p.range_degradation_pct for p in matching]),
        })

    return {'period': period, 'series': series, 'correlation': correlation, 'temperature_buckets': temp_buckets}


# ─────────────────────── Energy Consumption Trends ───────────────────────

def energy_consumption_trends(user_id, period='daily'):
    """Average predicted energy consumption (Wh/km), bucketed over
    time -- rising trend can flag a vehicle's real-world efficiency
    drifting from its rated spec (aging, tire wear, etc.), independent
    of any single trip's weather conditions.
    """
    _validate_period(period)
    lookback_days = _DEFAULT_LOOKBACK_DAYS[period]
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    predictions = Prediction.query.filter(
        Prediction.user_id == user_id, Prediction.created_at >= cutoff
    ).order_by(Prediction.created_at.asc()).all()

    buckets = defaultdict(list)
    for p in predictions:
        if p.created_at:
            buckets[_bucket_key(p.created_at, period)].append(p)

    series = [
        {
            'period': key,
            'label': _bucket_label(key, period),
            'avg_energy_wh_km': _avg([r.energy_consumption_wh_km for r in buckets[key]]),
            'sample_count': len(buckets[key]),
        }
        for key in sorted(buckets.keys())
    ]
    return {'period': period, 'series': series}


# ─────────────────────────── Charging Statistics ───────────────────────────

def charging_statistics(user_id):
    """Charging Statistics: reservation activity, average cold-weather
    charging slowdown (from logged predictions), and estimated total
    energy/cost from real logged trips (TripSimulation.estimated_energy_kwh
    -- an actual distance-linked figure, not a guess) run through the
    same documented default rates services/charging_cost.py uses
    elsewhere.
    """
    reservations = ChargingReservation.query.filter_by(user_id=user_id).all()
    status_counts = defaultdict(int)
    for r in reservations:
        status_counts[r.status] += 1

    predictions = Prediction.query.filter_by(user_id=user_id).all()
    avg_slowdown = _avg([p.charging_slowdown_pct for p in predictions])

    trips = TripSimulation.query.filter_by(user_id=user_id).all()
    total_energy_kwh = sum(t.estimated_energy_kwh for t in trips if t.estimated_energy_kwh)
    cost_estimate = estimate_charging_cost(total_energy_kwh, fast_charging=True) if total_energy_kwh else None

    return {
        'reservations': {
            'total': len(reservations),
            'upcoming': status_counts.get('upcoming', 0),
            'completed': status_counts.get('completed', 0),
            'cancelled': status_counts.get('cancelled', 0),
        },
        'avg_cold_weather_charging_slowdown_pct': avg_slowdown,
        'total_logged_trip_energy_kwh': round(total_energy_kwh, 1) if total_energy_kwh else 0,
        'estimated_total_charging_cost': cost_estimate,
    }


# ─────────────────────────── Vehicle Ranking ───────────────────────────

def vehicle_ranking(limit=10, min_predictions=3):
    """Fleet-wide Vehicle Ranking across four criteria: popularity
    (prediction volume), user favorites, cold-weather resilience
    (lowest average degradation -- only among vehicles with at least
    `min_predictions` logged predictions, so one lucky mild-weather
    prediction can't top the list), and predicted efficiency (lowest
    average Wh/km).
    """
    by_popularity = db.session.query(
        EVVehicle.id, EVVehicle.manufacturer, EVVehicle.model_name, func.count(Prediction.id).label('cnt')
    ).join(Prediction, Prediction.vehicle_id == EVVehicle.id) \
        .group_by(EVVehicle.id).order_by(func.count(Prediction.id).desc()).limit(limit).all()

    by_favorites = db.session.query(
        EVVehicle.id, EVVehicle.manufacturer, EVVehicle.model_name, func.count(FavoriteVehicle.id).label('cnt')
    ).join(FavoriteVehicle, FavoriteVehicle.vehicle_id == EVVehicle.id) \
        .group_by(EVVehicle.id).order_by(func.count(FavoriteVehicle.id).desc()).limit(limit).all()

    resilience_rows = db.session.query(
        EVVehicle.id, EVVehicle.manufacturer, EVVehicle.model_name,
        func.avg(Prediction.range_degradation_pct).label('avg_deg'), func.count(Prediction.id).label('cnt')
    ).join(Prediction, Prediction.vehicle_id == EVVehicle.id) \
        .group_by(EVVehicle.id).having(func.count(Prediction.id) >= min_predictions) \
        .order_by(func.avg(Prediction.range_degradation_pct).asc()).limit(limit).all()

    efficiency_rows = db.session.query(
        EVVehicle.id, EVVehicle.manufacturer, EVVehicle.model_name,
        func.avg(Prediction.energy_consumption_wh_km).label('avg_energy'), func.count(Prediction.id).label('cnt')
    ).join(Prediction, Prediction.vehicle_id == EVVehicle.id) \
        .group_by(EVVehicle.id).having(func.count(Prediction.id) >= min_predictions) \
        .order_by(func.avg(Prediction.energy_consumption_wh_km).asc()).limit(limit).all()

    def _name(manufacturer, model_name):
        return f"{manufacturer} {model_name}"

    return {
        'most_predicted': [
            {'vehicle_id': vid, 'name': _name(m, mo), 'prediction_count': cnt}
            for vid, m, mo, cnt in by_popularity
        ],
        'most_favorited': [
            {'vehicle_id': vid, 'name': _name(m, mo), 'favorite_count': cnt}
            for vid, m, mo, cnt in by_favorites
        ],
        'best_cold_weather_resilience': [
            {'vehicle_id': vid, 'name': _name(m, mo), 'avg_degradation_pct': round(deg, 1), 'sample_count': cnt}
            for vid, m, mo, deg, cnt in resilience_rows
        ],
        'most_efficient': [
            {'vehicle_id': vid, 'name': _name(m, mo), 'avg_energy_wh_km': round(e, 1), 'sample_count': cnt}
            for vid, m, mo, e, cnt in efficiency_rows
        ],
        'min_predictions_for_resilience_efficiency_ranking': min_predictions,
    }


# ─────────────────────────── Cost Analytics ───────────────────────────

def cost_analytics(user_id, period='monthly', home_rate_usd_per_kwh=None, public_rate_usd_per_kwh=None):
    """Cost Analytics: estimated charging spend over time, from real
    logged trip energy (TripSimulation.estimated_energy_kwh) rather
    than a synthetic distance assumption. Two cost estimates are given
    per period -- as if every logged trip were charged entirely at
    home vs. entirely on public DC fast charging -- so a user can see
    the real spread rather than one number presented as certain.
    """
    _validate_period(period)
    trips = TripSimulation.query.filter_by(user_id=user_id).order_by(TripSimulation.created_at.asc()).all()

    buckets = defaultdict(list)
    for t in trips:
        if t.created_at and t.estimated_energy_kwh:
            buckets[_bucket_key(t.created_at, period)].append(t.estimated_energy_kwh)

    home_rate = home_rate_usd_per_kwh if home_rate_usd_per_kwh is not None else DEFAULT_RATES_USD_PER_KWH['home']
    public_rate = public_rate_usd_per_kwh if public_rate_usd_per_kwh is not None else DEFAULT_RATES_USD_PER_KWH['dc_fast']

    series = []
    for key in sorted(buckets.keys()):
        energy_values = buckets[key]
        total_energy = sum(energy_values)
        series.append({
            'period': key,
            'label': _bucket_label(key, period),
            'total_energy_kwh': round(total_energy, 1),
            'estimated_cost_if_home_usd': round(total_energy * home_rate, 2),
            'estimated_cost_if_public_usd': round(total_energy * public_rate, 2),
        })

    total_energy_all = sum(v for values in buckets.values() for v in values)
    return {
        'period': period,
        'home_rate_usd_per_kwh': home_rate,
        'public_rate_usd_per_kwh': public_rate,
        'total_energy_kwh': round(total_energy_all, 1),
        'total_estimated_cost_if_home_usd': round(total_energy_all * home_rate, 2),
        'total_estimated_cost_if_public_usd': round(total_energy_all * public_rate, 2),
        'series': series,
    }


# ─────────────────────────── User Analytics ───────────────────────────

def _current_streak_days(dates):
    """Consecutive days (ending today or yesterday -- a streak isn't
    broken until a full day is skipped) with at least one activity."""
    if not dates:
        return 0
    day_set = {d.date() for d in dates}
    today = datetime.utcnow().date()
    streak = 0
    cursor = today
    if cursor not in day_set:
        cursor -= timedelta(days=1)
        if cursor not in day_set:
            return 0
    while cursor in day_set:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def user_analytics(user_id):
    """User Analytics: a personal activity profile -- distinct from
    admin.py's fleet_stats(), which aggregates across ALL users. This
    is "how have I been using this app", not "how is the app doing
    overall."
    """
    user = User.query.get(user_id)
    if not user:
        return None

    predictions = Prediction.query.filter_by(user_id=user_id).all()
    trips = TripSimulation.query.filter_by(user_id=user_id).all()
    community_reports = CommunityRangeReport.query.filter_by(user_id=user_id).count()
    favorites = FavoriteVehicle.query.filter_by(user_id=user_id).count()

    model_usage = defaultdict(int)
    for p in predictions:
        if p.ml_model_used:
            model_usage[p.ml_model_used] += 1
    most_used_model = max(model_usage.items(), key=lambda kv: kv[1])[0] if model_usage else None

    activity_dates = [p.created_at for p in predictions if p.created_at] + [t.created_at for t in trips if t.created_at]

    return {
        'username': user.username,
        'member_since': user.created_at.isoformat() if user.created_at else None,
        'total_predictions': len(predictions),
        'total_trips_simulated': len(trips),
        'total_community_reports': community_reports,
        'favorite_vehicles_count': favorites,
        'most_used_model': most_used_model,
        'avg_confidence': _avg([p.prediction_confidence for p in predictions]),
        'avg_degradation_pct': _avg([p.range_degradation_pct for p in predictions]),
        'current_activity_streak_days': _current_streak_days(activity_dates),
    }


def recent_activity(user_id, limit=20):
    """Recent Activity: a single reverse-chronological feed merged
    from every distinct thing a user actually does in this app
    (predicting, simulating a trip, favoriting/saving, generating a
    report), rather than five separate lists the user has to check.

    Each source table already has its own dedicated list somewhere
    (Prediction History, Trip history, Favorite Vehicles, Report
    History) -- this doesn't replace any of those, it's a merged,
    capped-at-`limit` view across all of them for a single "what have
    I been doing" glance, same relationship the Personalized Dashboard
    has to the more detailed pages it links out to.

    Pulling `limit` rows from *each* source table (not one global
    query) means this stays a handful of small, indexed
    user_id+created_at queries -- cheap even as any one table grows --
    at the cost of only being exactly accurate when a user has fewer
    than `limit` very recent items in a single category, which is the
    normal case this feed is for.
    """
    items = []

    for p in Prediction.query.filter_by(user_id=user_id)\
            .order_by(Prediction.created_at.desc()).limit(limit).all():
        items.append({
            'type': 'prediction',
            'icon': '🤖',
            'title': f'Ran a prediction ({p.temperature_c}°C, {p.vehicle.model_name if p.vehicle else "vehicle"})',
            'timestamp': p.created_at.isoformat() if p.created_at else None,
            'ref_id': p.id,
        })

    for t in TripSimulation.query.filter_by(user_id=user_id)\
            .order_by(TripSimulation.created_at.desc()).limit(limit).all():
        items.append({
            'type': 'trip',
            'icon': '🗺️',
            'title': f'Simulated a trip: {t.source_location} → {t.destination}',
            'timestamp': t.created_at.isoformat() if t.created_at else None,
            'ref_id': t.id,
        })

    for f in FavoriteVehicle.query.filter_by(user_id=user_id)\
            .order_by(FavoriteVehicle.created_at.desc()).limit(limit).all():
        items.append({
            'type': 'favorite_vehicle',
            'icon': '❤️',
            'title': f'Favorited {f.vehicle.manufacturer} {f.vehicle.model_name}' if f.vehicle else 'Favorited a vehicle',
            'timestamp': f.created_at.isoformat() if f.created_at else None,
            'ref_id': f.vehicle_id,
        })

    for s in SavedPrediction.query.filter_by(user_id=user_id)\
            .order_by(SavedPrediction.created_at.desc()).limit(limit).all():
        items.append({
            'type': 'saved_prediction',
            'icon': '🔖',
            'title': f'Saved a prediction ({s.prediction.temperature_c}°C)' if s.prediction else 'Saved a prediction',
            'timestamp': s.created_at.isoformat() if s.created_at else None,
            'ref_id': s.prediction_id,
        })

    for r in ReportHistory.query.filter_by(user_id=user_id)\
            .order_by(ReportHistory.generated_at.desc()).limit(limit).all():
        items.append({
            'type': 'report',
            'icon': '📄',
            'title': f'Generated a {r.report_type} report ({r.format.upper()})',
            'timestamp': r.generated_at.isoformat() if r.generated_at else None,
            'ref_id': r.id,
        })

    items = [i for i in items if i['timestamp']]
    items.sort(key=lambda i: i['timestamp'], reverse=True)
    return items[:limit]
