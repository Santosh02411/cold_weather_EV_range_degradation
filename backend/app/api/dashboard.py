from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from ..models.prediction import Prediction
from ..models.ev_vehicle import EVVehicle
from ..models.dataset import WeatherLog
from .. import db
from sqlalchemy import func

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
