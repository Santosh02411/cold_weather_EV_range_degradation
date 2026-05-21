from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from ..models.ev_vehicle import EVVehicle

charging_bp = Blueprint('charging', __name__)


def predict_charging_time(vehicle, temperature_c, current_pct, target_pct, fast_charging=True):
    """Predict charging time using a capacity-dependent linear model as requested"""
    delta_pct = max(0, target_pct - current_pct)
    capacity = vehicle.battery_capacity_kwh
    energy_needed = capacity * (delta_pct / 100)
    
    # Base Power in kW (Scales with temperature)
    if fast_charging:
        # DC Fast Charging baseline
        if temperature_c < -20:
            base_power = 12.0
            efficiency = 0.25
        elif temperature_c < -10:
            base_power = 18.0
            efficiency = 0.40
        elif temperature_c < 0:
            base_power = 25.0
            efficiency = 0.60
        elif temperature_c < 10:
            base_power = 35.0
            efficiency = 0.80
        else:
            # Optimal temp: 45kW baseline ensures a 75kWh car takes 100min for 0-100%
            base_power = 45.0
            efficiency = 1.0
    else:
        # AC Level 2 charging baseline
        if temperature_c < 0:
            base_power = 4.5
            efficiency = 0.80
        else:
            base_power = 6.0
            efficiency = 1.0

    # Linear time calculation: Time = Energy / Power
    charging_time_minutes = (energy_needed / base_power) * 60 if base_power > 0 else 0
    
    # Derived stats for UI
    max_power = vehicle.max_charging_power_kw or 150

    return {
        'energy_needed_kwh': round(energy_needed, 2),
        'effective_power_kw': round(base_power, 1),
        'avg_power_kw': round(base_power, 1),
        'charging_time_minutes': round(charging_time_minutes, 1),
        'efficiency_pct': round(efficiency * 100, 1),
        'slowdown_pct': round((1 - (base_power/max_power)) * 100, 1) if max_power > 0 else 0,
        'fast_charging': fast_charging,
        'temperature_c': temperature_c,
    }


@charging_bp.route('/')
@login_required
def index():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return render_template('charging/index.html', vehicles=vehicles)


@charging_bp.route('/api/predict', methods=['POST'])
@login_required
def predict():
    data = request.get_json() or {}
    vehicle = EVVehicle.query.get(data.get('vehicle_id'))
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    result = predict_charging_time(
        vehicle,
        float(data.get('temperature_c', 20)),
        float(data.get('current_pct', 20)),
        float(data.get('target_pct', 80)),
        bool(data.get('fast_charging', True)),
    )
    result['vehicle'] = vehicle.to_dict()
    return jsonify(result)


@charging_bp.route('/api/compare', methods=['POST'])
@login_required
def compare_temps():
    data = request.get_json() or {}
    vehicle = EVVehicle.query.get(data.get('vehicle_id'))
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    fast_charging = bool(data.get('fast_charging', True))
    temps = [-20, -10, 0, 10, 20, 30]
    results = []
    for t in temps:
        r = predict_charging_time(vehicle, t, 20, 80, fast_charging)
        r['label'] = f"{t}°C"
        results.append(r)
    return jsonify({'vehicle': vehicle.to_dict(), 'comparisons': results})
