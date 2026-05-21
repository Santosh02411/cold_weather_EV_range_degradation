from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from ..models.prediction import TripSimulation
from ..models.ev_vehicle import EVVehicle
from ..ml.predict import get_prediction
from .. import db

trip_bp = Blueprint('trip', __name__)


@trip_bp.route('/')
@login_required
def index():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return render_template('trip/simulate.html', vehicles=vehicles)


@trip_bp.route('/api/simulate', methods=['POST'])
@login_required
def simulate():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    vehicle = EVVehicle.query.get(data.get('vehicle_id'))
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    distance_km = float(data.get('distance_km', 100))
    temperature_c = float(data.get('temperature_c', 20))
    speed_kmh = float(data.get('speed_kmh', 60))
    heater_usage = bool(data.get('heater_usage', True))
    num_passengers = int(data.get('num_passengers', 1))
    battery_pct = float(data.get('battery_percentage', 100))

    # Get degradation prediction
    features = {
        'temperature_c': temperature_c,
        'humidity': float(data.get('humidity', 50)),
        'wind_speed_kmh': float(data.get('wind_speed_kmh', 10)),
        'precipitation': data.get('precipitation', 'none'),
        'battery_percentage': battery_pct,
        'vehicle_speed_kmh': speed_kmh,
        'hvac_usage': heater_usage,
        'terrain_type': data.get('terrain_type', 'flat'),
        'battery_age_years': float(data.get('battery_age_years', 0)),
        'battery_capacity_kwh': vehicle.battery_capacity_kwh,
        'epa_range_km': vehicle.epa_range_km,
        'vehicle_weight_kg': vehicle.vehicle_weight_kg + (num_passengers * 75),
    }
    result = get_prediction(features, 'random_forest')

    effective_range = result['predicted_range_km'] * (battery_pct / 100)
    energy_per_km = result['energy_consumption_wh_km'] / 1000
    total_energy_kwh = distance_km * energy_per_km
    battery_usage_pct = (total_energy_kwh / vehicle.battery_capacity_kwh) * 100
    arrival_battery_pct = max(0, battery_pct - battery_usage_pct)
    charging_stops = max(0, int((battery_usage_pct - battery_pct) / 60)) if battery_usage_pct > battery_pct else 0

    trip = TripSimulation(
        user_id=current_user.id, vehicle_id=vehicle.id,
        source_location=data.get('source', 'Origin'),
        destination=data.get('destination', 'Destination'),
        distance_km=distance_km, temperature_c=temperature_c,
        speed_kmh=speed_kmh, heater_usage=heater_usage,
        num_passengers=num_passengers,
        estimated_battery_usage_pct=round(battery_usage_pct, 1),
        predicted_remaining_range_km=round(max(0, effective_range - distance_km), 1),
        charging_stops_required=charging_stops,
        estimated_arrival_battery_pct=round(arrival_battery_pct, 1),
        estimated_energy_kwh=round(total_energy_kwh, 2),
    )
    db.session.add(trip)
    db.session.commit()

    return jsonify({
        'trip': trip.to_dict(),
        'degradation': result,
    })


@trip_bp.route('/api/history')
@login_required
def trip_history():
    trips = TripSimulation.query.filter_by(user_id=current_user.id)\
        .order_by(TripSimulation.created_at.desc()).limit(20).all()
    return jsonify([t.to_dict() for t in trips])
