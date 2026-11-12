from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
from ..models.ev_vehicle import EVVehicle
from ..models.charging_reservation import ChargingReservation
from ..services.geo import geocode_place
from ..services.charging_stations import find_charging_stations
from ..services.charging_time import predict_charging_time
from ..services.charger_matching import annotate_compatibility
from ..services.charger_recommendation import recommend_fastest, recommend_cheapest
from ..services.charging_availability import estimate_queue_time
from ..services.home_charging import recommend_home_vs_public
from .. import db

charging_bp = Blueprint('charging', __name__)


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


@charging_bp.route('/api/stations', methods=['GET'])
@login_required
def stations():
    """Nearby Charging Stations, via Open Charge Map. Accepts either a
    place name (geocoded via the same Nominatim service the trip/route
    feature uses) or explicit lat/lon. When `vehicle_id` is also given,
    each station is annotated with Charger Type Detection compatibility
    and a Charger Availability estimate (see services/charger_matching.py,
    services/charging_availability.py)."""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    place = request.args.get('place')
    distance_km = request.args.get('distance_km', 25, type=float)
    max_results = min(request.args.get('max_results', 15, type=int), 50)

    resolved_place = None
    if lat is None or lon is None:
        if not place:
            return jsonify({'error': 'Provide either lat/lon or a place name'}), 400
        lat, lon, resolved_place = geocode_place(place, provider_config=current_app.config)
        if lat is None:
            return jsonify({'error': f"Could not geocode '{place}'"}), 502

    api_key = current_app.config.get('OCM_API_KEY') or None
    stations_list = find_charging_stations(lat, lon, distance_km, max_results, api_key=api_key)
    if stations_list is None:
        return jsonify({'error': 'Could not fetch charging stations right now'}), 502

    vehicle_id = request.args.get('vehicle_id', type=int)
    if vehicle_id:
        vehicle = EVVehicle.query.get(vehicle_id)
        if vehicle:
            annotate_compatibility(vehicle.charging_type, stations_list)
            for s in stations_list:
                s['availability'] = estimate_queue_time(s)

    return jsonify({
        'location': {'lat': lat, 'lon': lon, 'resolved_place': resolved_place},
        'distance_km': distance_km,
        'stations': stations_list,
        'count': len(stations_list),
    })


@charging_bp.route('/api/recommend', methods=['GET'])
@login_required
def recommend():
    """Fastest Charger Recommendation + Cheapest Charger Recommendation:
    find nearby real stations and rank them by predicted total time
    (queue wait + charging) or estimated cost for a specific vehicle
    and charging need (see services/charger_recommendation.py)."""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    place = request.args.get('place')
    priority = request.args.get('priority', 'fastest')
    if priority not in ('fastest', 'cheapest'):
        return jsonify({'error': "priority must be 'fastest' or 'cheapest'"}), 400

    vehicle = EVVehicle.query.get(request.args.get('vehicle_id', type=int))
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    resolved_place = None
    if lat is None or lon is None:
        if not place:
            return jsonify({'error': 'Provide either lat/lon or a place name'}), 400
        lat, lon, resolved_place = geocode_place(place, provider_config=current_app.config)
        if lat is None:
            return jsonify({'error': f"Could not geocode '{place}'"}), 502

    distance_km = request.args.get('distance_km', 25, type=float)
    api_key = current_app.config.get('OCM_API_KEY') or None
    stations_list = find_charging_stations(lat, lon, distance_km, min(request.args.get('max_results', 15, type=int), 50), api_key=api_key)
    if stations_list is None:
        return jsonify({'error': 'Could not fetch charging stations right now'}), 502
    if not stations_list:
        return jsonify({'location': {'lat': lat, 'lon': lon, 'resolved_place': resolved_place}, 'stations': [], 'recommendation': None})

    current_pct = request.args.get('current_pct', 20, type=float)
    target_pct = request.args.get('target_pct', 80, type=float)
    temperature_c = request.args.get('temperature_c', 0, type=float)
    fast_charging = request.args.get('fast_charging', 'true').lower() != 'false'

    ranker = recommend_fastest if priority == 'fastest' else recommend_cheapest
    ranked = ranker(vehicle, stations_list, current_pct, target_pct, temperature_c, fast_charging)

    return jsonify({
        'location': {'lat': lat, 'lon': lon, 'resolved_place': resolved_place},
        'priority': priority,
        'stations': ranked,
        'recommendation': ranked[0] if ranked else None,
    })


@charging_bp.route('/api/home-recommendation', methods=['POST'])
@login_required
def home_recommendation():
    """Home Charging Recommendation: compare charging at home overnight
    against a public DC fast stop for the same top-up, and recommend
    one (see services/home_charging.py)."""
    data = request.get_json() or {}
    vehicle = EVVehicle.query.get(data.get('vehicle_id'))
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    result = recommend_home_vs_public(
        vehicle,
        current_pct=float(data.get('current_pct', 20)),
        target_pct=float(data.get('target_pct', 80)),
        temperature_c=float(data.get('temperature_c', 0)),
        hours_available_at_home=float(data.get('hours_available_at_home', 8)),
        home_rate_usd_per_kwh=data.get('home_rate_usd_per_kwh'),
    )
    result['vehicle'] = vehicle.to_dict()
    return jsonify(result)


@charging_bp.route('/api/reservations', methods=['GET'])
@login_required
def list_reservations():
    """Charging Reservation history/upcoming list -- see
    models/charging_reservation.py's docstring for what this is (and
    isn't -- a personal plan, not a real network booking)."""
    reservations = ChargingReservation.query.filter_by(user_id=current_user.id)\
        .order_by(ChargingReservation.reserved_start.desc()).limit(50).all()
    return jsonify([r.to_dict() for r in reservations])


@charging_bp.route('/api/reservations', methods=['POST'])
@login_required
def create_reservation():
    data = request.get_json() or {}
    vehicle = EVVehicle.query.get(data.get('vehicle_id'))
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    station_name = (data.get('station_name') or '').strip()
    reserved_start_raw = data.get('reserved_start')
    if not station_name or not reserved_start_raw:
        return jsonify({'error': "'station_name' and 'reserved_start' are required"}), 400
    try:
        reserved_start = datetime.fromisoformat(reserved_start_raw)
    except ValueError:
        return jsonify({'error': "'reserved_start' must be an ISO 8601 datetime"}), 400

    duration_minutes = int(data.get('duration_minutes', 30))

    existing = ChargingReservation.query.filter_by(user_id=current_user.id, cancelled=False).all()
    if any(r.overlaps(reserved_start, duration_minutes) for r in existing):
        return jsonify({'error': 'This overlaps another upcoming reservation you already have.'}), 409

    reservation = ChargingReservation(
        user_id=current_user.id, vehicle_id=vehicle.id, station_name=station_name,
        station_ocm_id=data.get('station_ocm_id'), latitude=data.get('latitude'), longitude=data.get('longitude'),
        reserved_start=reserved_start, duration_minutes=duration_minutes,
        target_pct=data.get('target_pct'), notes=data.get('notes'),
    )
    db.session.add(reservation)
    db.session.commit()
    return jsonify(reservation.to_dict()), 201


@charging_bp.route('/api/reservations/<int:reservation_id>', methods=['DELETE'])
@login_required
def cancel_reservation(reservation_id):
    reservation = ChargingReservation.query.filter_by(id=reservation_id, user_id=current_user.id).first()
    if not reservation:
        return jsonify({'error': 'Reservation not found'}), 404
    reservation.cancelled = True
    db.session.commit()
    return jsonify(reservation.to_dict())
