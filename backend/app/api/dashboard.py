from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from ..models.prediction import Prediction
from ..models.ev_vehicle import EVVehicle
from ..models.dataset import WeatherLog
from .. import db
from sqlalchemy import func
from ..services import analytics as analytics_service

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return render_template('dashboard/index.html', vehicles=vehicles)


@dashboard_bp.route('/api/stats')
@login_required
def stats():
    total_predictions = Prediction.query.filter_by(user_id=current_user.id).count()
    total_vehicles = EVVehicle.query.filter_by(is_active=True).count()

    # Average degradation
    avg_deg = db.session.query(func.avg(Prediction.range_degradation_pct))\
        .filter_by(user_id=current_user.id).scalar() or 0

    # Latest prediction
    latest = Prediction.query.filter_by(user_id=current_user.id)\
        .order_by(Prediction.created_at.desc()).first()

    # Recent weather
    recent_weather = WeatherLog.query.order_by(WeatherLog.fetched_at.desc()).first()

    return jsonify({
        'total_predictions': total_predictions,
        'total_vehicles': total_vehicles,
        'avg_degradation': round(avg_deg, 1),
        'latest_prediction': latest.to_dict() if latest else None,
        'recent_weather': recent_weather.to_dict() if recent_weather else None,
    })


@dashboard_bp.route('/api/charts/temp-vs-range')
@login_required
def temp_vs_range():
    predictions = Prediction.query.filter_by(user_id=current_user.id)\
        .order_by(Prediction.created_at.desc()).limit(100).all()

    data = {
        'temperatures': [p.temperature_c for p in predictions],
        'ranges': [p.predicted_range_km for p in predictions],
        'degradations': [p.range_degradation_pct for p in predictions],
    }
    return jsonify(data)


@dashboard_bp.route('/api/charts/efficiency')
@login_required
def efficiency_chart():
    predictions = Prediction.query.filter_by(user_id=current_user.id)\
        .order_by(Prediction.created_at.desc()).limit(50).all()

    data = {
        'labels': [p.created_at.strftime('%m/%d %H:%M') if p.created_at else '' for p in predictions],
        'energy': [p.energy_consumption_wh_km for p in predictions],
        'degradation': [p.range_degradation_pct for p in predictions],
    }
    return jsonify(data)


@dashboard_bp.route('/api/charts/seasonal')
@login_required
def seasonal_chart():
    """Compare performance across temperature ranges"""
    predictions = Prediction.query.filter_by(user_id=current_user.id).all()

    seasons = {
        'Extreme Cold (<-15°C)': {'temps': [], 'degradations': []},
        'Cold (-15 to 0°C)': {'temps': [], 'degradations': []},
        'Cool (0 to 15°C)': {'temps': [], 'degradations': []},
        'Mild (15 to 25°C)': {'temps': [], 'degradations': []},
        'Hot (>25°C)': {'temps': [], 'degradations': []},
    }

    for p in predictions:
        t = p.temperature_c
        if t < -15:
            key = 'Extreme Cold (<-15°C)'
        elif t < 0:
            key = 'Cold (-15 to 0°C)'
        elif t < 15:
            key = 'Cool (0 to 15°C)'
        elif t <= 25:
            key = 'Mild (15 to 25°C)'
        else:
            key = 'Hot (>25°C)'
        seasons[key]['temps'].append(t)
        seasons[key]['degradations'].append(p.range_degradation_pct)

    result = {}
    for k, v in seasons.items():
        avg_deg = sum(v['degradations']) / len(v['degradations']) if v['degradations'] else 0
        result[k] = {'count': len(v['degradations']), 'avg_degradation': round(avg_deg, 1)}

    return jsonify(result)


# ─────────────────────── Analytics Dashboard ───────────────────────
# See services/analytics.py for the implementation. Kept on this same
# blueprint (url_prefix /dashboard) since this is a fuller version of
# the same "how am I doing" surface the plain dashboard home page
# already starts -- not a separate concern needing its own blueprint.

@dashboard_bp.route('/analytics')
@login_required
def analytics_page():
    return render_template('dashboard/analytics.html')


def _period_arg():
    period = request.args.get('period', 'daily')
    if period not in analytics_service.VALID_PERIODS:
        return None
    return period


@dashboard_bp.route('/api/analytics/activity')
@login_required
def analytics_activity():
    """Daily Analytics / Weekly Analytics / Monthly Analytics -- one
    endpoint, `?period=daily|weekly|monthly` picks the granularity."""
    period = _period_arg()
    if period is None:
        return jsonify({'error': "period must be 'daily', 'weekly', or 'monthly'"}), 400
    return jsonify(analytics_service.activity_analytics(current_user.id, period))


@dashboard_bp.route('/api/analytics/battery-health')
@login_required
def analytics_battery_health():
    """Battery Health Trends across every vehicle the user has logged SOH for."""
    return jsonify(analytics_service.battery_health_trends(current_user.id))


@dashboard_bp.route('/api/analytics/weather-impact')
@login_required
def analytics_weather_impact():
    """Weather Impact Trends: temperature vs. degradation over time,
    plus temperature-bucket breakdown and overall correlation."""
    period = _period_arg()
    if period is None:
        return jsonify({'error': "period must be 'daily', 'weekly', or 'monthly'"}), 400
    return jsonify(analytics_service.weather_impact_trends(current_user.id, period))


@dashboard_bp.route('/api/analytics/energy')
@login_required
def analytics_energy():
    """Energy Consumption Trends: average predicted Wh/km over time."""
    period = _period_arg()
    if period is None:
        return jsonify({'error': "period must be 'daily', 'weekly', or 'monthly'"}), 400
    return jsonify(analytics_service.energy_consumption_trends(current_user.id, period))


@dashboard_bp.route('/api/analytics/charging')
@login_required
def analytics_charging():
    """Charging Statistics: reservations, cold-weather charging
    slowdown, and estimated cost/energy from logged trips."""
    return jsonify(analytics_service.charging_statistics(current_user.id))


@dashboard_bp.route('/api/analytics/vehicle-ranking')
@login_required
def analytics_vehicle_ranking():
    """Vehicle Ranking: fleet-wide, across popularity, favorites,
    cold-weather resilience, and efficiency."""
    limit = min(request.args.get('limit', 10, type=int), 25)
    return jsonify(analytics_service.vehicle_ranking(limit=limit))


@dashboard_bp.route('/api/analytics/cost')
@login_required
def analytics_cost():
    """Cost Analytics: estimated charging spend over time, from real
    logged trip energy."""
    period = _period_arg()
    if period is None:
        return jsonify({'error': "period must be 'daily', 'weekly', or 'monthly'"}), 400
    return jsonify(analytics_service.cost_analytics(current_user.id, period))


@dashboard_bp.route('/api/analytics/user')
@login_required
def analytics_user():
    """User Analytics: a personal activity profile."""
    return jsonify(analytics_service.user_analytics(current_user.id))


# ─────────────────────── User Dashboard (personal hub) ───────────────────────
# Personalized Dashboard / Usage Statistics / Recent Activity -- these
# are thin pages over data that mostly already existed (user_analytics,
# and the per-feature history/favorites/saved endpoints); the new work
# is recent_activity() (a real merged feed, see analytics.py) and
# wiring a "My Account" hub page that links everything together instead
# of leaving it API-only or scattered across unrelated pages.

@dashboard_bp.route('/me')
@login_required
def personalized():
    """Personalized Dashboard -- the hub for prediction history, saved
    predictions, saved/favorite vehicles, saved reports, usage
    statistics, and recent activity, all in one place.
    """
    return render_template('dashboard/personalized.html')


@dashboard_bp.route('/usage-stats')
@login_required
def usage_stats_page():
    return render_template('dashboard/usage_stats.html')


@dashboard_bp.route('/activity')
@login_required
def activity_page():
    return render_template('dashboard/activity.html')


@dashboard_bp.route('/api/activity')
@login_required
def api_activity():
    limit = min(request.args.get('limit', 20, type=int), 100)
    return jsonify(analytics_service.recent_activity(current_user.id, limit=limit))
