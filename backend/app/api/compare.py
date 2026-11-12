from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..models.ev_vehicle import EVVehicle
from ..ml.predict import get_prediction

compare_bp = Blueprint('compare', __name__)


@compare_bp.route('/')
@login_required
def index():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return render_template('compare/index.html', vehicles=vehicles)


@compare_bp.route('/api/compare', methods=['POST'])
@login_required
def compare_vehicles():
    data = request.get_json() or {}
    vehicle_ids = data.get('vehicle_ids', [])
    temperature_c = float(data.get('temperature_c', -10))

    if len(vehicle_ids) < 2:
        return jsonify({'error': 'Select at least 2 vehicles'}), 400

    results = []
    for vid in vehicle_ids[:5]:
        vehicle = EVVehicle.query.get(vid)
        if not vehicle:
            continue
        features = {
            'temperature_c': temperature_c,
            'humidity': 60, 'wind_speed_kmh': 15,
            'precipitation': 'none', 'battery_percentage': 100,
            'vehicle_speed_kmh': 60, 'hvac_usage': True,
            'terrain_type': 'flat', 'battery_age_years': 0,
            'battery_capacity_kwh': vehicle.battery_capacity_kwh,
            'epa_range_km': vehicle.epa_range_km,
            'vehicle_weight_kg': vehicle.vehicle_weight_kg,
        }
        pred = get_prediction(features, 'random_forest')
        results.append({
            'vehicle': vehicle.to_dict(),
            'prediction': pred,
        })
    return jsonify({'comparisons': results, 'temperature_c': temperature_c})


@compare_bp.route('/api/temperature-sweep', methods=['POST'])
@login_required
def temperature_sweep():
    data = request.get_json() or {}
    vehicle_id = data.get('vehicle_id')
    vehicle = EVVehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    temps = list(range(-30, 41, 5))
    results = []
    for t in temps:
        features = {
            'temperature_c': t, 'humidity': 50, 'wind_speed_kmh': 10,
            'precipitation': 'none', 'battery_percentage': 100,
            'vehicle_speed_kmh': 60, 'hvac_usage': t < 15,
            'terrain_type': 'flat', 'battery_age_years': 0,
            'battery_capacity_kwh': vehicle.battery_capacity_kwh,
            'epa_range_km': vehicle.epa_range_km,
            'vehicle_weight_kg': vehicle.vehicle_weight_kg,
        }
        pred = get_prediction(features, 'random_forest')
        results.append({'temperature_c': t, **pred})
    return jsonify({'vehicle': vehicle.to_dict(), 'sweep': results})
