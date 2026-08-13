from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from ..models.prediction import TripSimulation
from ..models.trip_plan import SavedTrip, TripPlan
from ..models.ev_vehicle import EVVehicle
from ..ml.predict import get_prediction
from ..services.geo import (
    geocode_place, get_route, get_route_alternatives, get_elevation_profile,
    classify_terrain_from_elevations, select_route_waypoints, elevation_profile_stats,
)
from ..services import traffic as traffic_mod
from ..services import route_optimization
from ..services import route_planning
from ..services.driving_style import analyze_driving_style
from ..services.energy_model import energy_curve, most_efficient_speed_kmh
from ..services.destination_recommender import recommend_destinations, CATEGORY_TAGS
from .weather import fetch_openweathermap, fetch_openweathermap_by_coords, get_demo_weather
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


@trip_bp.route('/api/route-predict', methods=['POST'])
@login_required
def route_predict():
    """Phase 2 (RT-1/RT-2): given real place names instead of a manual
    distance + terrain guess, geocode both ends, fetch a real driving
    route, derive terrain from the route's actual elevation profile, and
    pull real current weather at the origin - then run the same
    prediction model as /api/simulate on top of that real data.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    origin_name = data.get('source')
    dest_name = data.get('destination')
    if not origin_name or not dest_name:
        return jsonify({'error': 'source and destination place names are required'}), 400

    vehicle = EVVehicle.query.get(data.get('vehicle_id'))
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    origin_lat, origin_lon, origin_display = geocode_place(origin_name)
    if origin_lat is None:
        return jsonify({'error': f"Could not geocode source '{origin_name}'"}), 502
    dest_lat, dest_lon, dest_display = geocode_place(dest_name)
    if dest_lat is None:
        return jsonify({'error': f"Could not geocode destination '{dest_name}'"}), 502

    route = get_route(origin_lat, origin_lon, dest_lat, dest_lon, provider_config=current_app.config)
    if route is None:
        return jsonify({'error': 'Could not fetch a driving route between these locations'}), 502

    # Traffic-aware Prediction / ETA Prediction: real traffic-aware
    # duration when routed through Google (see geo.py's
    # _get_route_google), a documented time-of-day heuristic otherwise
    # (see services/traffic.py).
    departure_time = data.get('departure_time')  # 'now', a unix timestamp, or omitted
    traffic_report = traffic_mod.apply_traffic(route['duration_min'], route=route, departure_time=None)

    elevations = get_elevation_profile(route['coordinates'])
    if elevations:
        terrain_type, elevation_gain_m = classify_terrain_from_elevations(elevations)
        terrain_source = 'measured'
    else:
        # Elevation lookup failing shouldn't block the whole prediction -
        # fall back to the user's manual choice (or 'flat') and say so,
        # rather than silently guessing.
        terrain_type = data.get('terrain_type_fallback', 'flat')
        elevation_gain_m = None
        terrain_source = 'fallback (elevation lookup unavailable)'

    api_key = current_app.config.get('OPENWEATHERMAP_API_KEY', 'demo')

    def _fetch_weather_for(place_name):
        if api_key and api_key != 'demo':
            w, err = fetch_openweathermap(place_name, api_key)
            if err:
                return get_demo_weather(place_name)
            return w
        return get_demo_weather(place_name)

    def _fetch_weather_at(lat, lon, label):
        if api_key and api_key != 'demo':
            w, err = fetch_openweathermap_by_coords(lat, lon, api_key)
            if err:
                return get_demo_weather(label)
            return w
        return get_demo_weather(label)

    # RT-6: full multi-waypoint sampling, OFF by default (see config.py's
    # WEATHER_MULTI_WAYPOINT_ENABLED docstring for the real cost tradeoff
    # against the free OpenWeatherMap tier). When enabled, replaces the
    # RT-5 2-point (origin+destination) sampling with N evenly-spaced
    # points along the route's real path.
    multi_waypoint_enabled = current_app.config.get('WEATHER_MULTI_WAYPOINT_ENABLED', False)
    weather_samples = []

    if multi_waypoint_enabled and route.get('coordinates'):
        interval_km = current_app.config.get('WEATHER_WAYPOINT_INTERVAL_KM', 150)
        max_waypoints = current_app.config.get('WEATHER_MAX_WAYPOINTS', 6)
        waypoints = select_route_waypoints(route['coordinates'], interval_km, max_waypoints)
        for i, (lat, lon) in enumerate(waypoints):
            label = origin_name if i == 0 else (dest_name if i == len(waypoints) - 1 else f"waypoint {i}")
            w = _fetch_weather_at(lat, lon, label)
            weather_samples.append({'label': label, 'lat': lat, 'lon': lon,
                                     'temperature_c': w['temperature_c'], 'data_source': w.get('data_source', 'unknown')})
        # Same worst-case (coldest) selection principle as the 2-point
        # version below -- just across however many points were sampled.
        coldest = min(weather_samples, key=lambda s: s['temperature_c'])
        weather = _fetch_weather_at(coldest['lat'], coldest['lon'], coldest['label'])
    else:
        # RT-5 (Phase 3): sample weather at BOTH ends of the route. Full
        # multi-waypoint sampling (RT-6, above) is available but opt-in.
        origin_weather = _fetch_weather_for(origin_name)
        dest_weather = _fetch_weather_for(dest_name)
        weather_samples = [
            {'label': origin_name, 'temperature_c': origin_weather['temperature_c'], 'data_source': origin_weather.get('data_source', 'unknown')},
            {'label': dest_name, 'temperature_c': dest_weather['temperature_c'], 'data_source': dest_weather.get('data_source', 'unknown')},
        ]
        # Use whichever end is colder for the prediction: colder
        # conditions are the binding constraint on range for a cold-
        # weather-focused tool (arriving with less charge than the
        # optimistic estimate is a worse failure mode than the reverse).
        weather = origin_weather if origin_weather['temperature_c'] <= dest_weather['temperature_c'] else dest_weather

    battery_pct = float(data.get('battery_percentage', 100))
    heater_usage = bool(data.get('heater_usage', True))
    num_passengers = int(data.get('num_passengers', 1))
    distance_km = route['distance_km']

    features = {
        'temperature_c': weather['temperature_c'],
        'humidity': weather.get('humidity', 50),
        'wind_speed_kmh': weather.get('wind_speed_kmh', 10),
        'precipitation': weather.get('precipitation', 'none'),
        'battery_percentage': battery_pct,
        'vehicle_speed_kmh': float(data.get('speed_kmh', 60)),
        'hvac_usage': heater_usage,
        'terrain_type': terrain_type,
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
        source_location=origin_display or origin_name,
        destination=dest_display or dest_name,
        distance_km=distance_km, temperature_c=weather['temperature_c'],
        speed_kmh=features['vehicle_speed_kmh'], heater_usage=heater_usage,
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
        'route': {
            'origin': origin_display or origin_name,
            'destination': dest_display or dest_name,
            'distance_km': distance_km,
            'duration_min': route['duration_min'],
        },
        'terrain': {
            'type': terrain_type,
            'elevation_gain_m': elevation_gain_m,
            'source': terrain_source,
            'profile': elevation_profile_stats(elevations) if elevations else None,
        },
        'traffic': traffic_report,
        'eta': {
            'driving_duration_min': route['duration_min'],
            'traffic_adjusted_duration_min': traffic_report['adjusted_duration_min'],
        },
        'weather': {
            'temperature_c': weather['temperature_c'],
            'data_source': weather.get('data_source', 'unknown'),
            'sampling_mode': 'multi_waypoint' if multi_waypoint_enabled else 'two_point',
            'note': 'coldest of the sampled points was used for the prediction (worst-case, not average)',
            'samples': weather_samples,
        },
    })


@trip_bp.route('/api/history')
@login_required
def trip_history():
    trips = TripSimulation.query.filter_by(user_id=current_user.id)\
        .order_by(TripSimulation.created_at.desc()).limit(20).all()
    return jsonify([t.to_dict() for t in trips])


@trip_bp.route('/api/route-optimize', methods=['POST'])
@login_required
def route_optimize():
    """Route Optimization: fetch multiple candidate routes between two
    places and recommend both the fastest and the most range-efficient
    one, instead of only ever returning a single fixed route (see
    services/route_optimization.py)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    origin_name, dest_name = data.get('source'), data.get('destination')
    if not origin_name or not dest_name:
        return jsonify({'error': 'source and destination place names are required'}), 400

    vehicle = EVVehicle.query.get(data.get('vehicle_id'))
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    origin_lat, origin_lon, origin_display = geocode_place(origin_name, provider_config=current_app.config)
    if origin_lat is None:
        return jsonify({'error': f"Could not geocode source '{origin_name}'"}), 502
    dest_lat, dest_lon, dest_display = geocode_place(dest_name, provider_config=current_app.config)
    if dest_lat is None:
        return jsonify({'error': f"Could not geocode destination '{dest_name}'"}), 502

    routes = get_route_alternatives(origin_lat, origin_lon, dest_lat, dest_lon, provider_config=current_app.config)
    if not routes:
        return jsonify({'error': 'Could not fetch any route between these locations'}), 502

    # Elevation lookups are real extra API calls, so only fetch them for
    # a bounded number of alternatives (typically <=3 from OSRM).
    elevation_gains = []
    for route in routes:
        elevations = get_elevation_profile(route['coordinates'], provider_config=current_app.config)
        _, gain = classify_terrain_from_elevations(elevations) if elevations else (None, None)
        elevation_gains.append(gain)

    base_wh_per_km = vehicle.energy_consumption_wh_km or 170
    ranked = route_optimization.optimize_routes(routes, base_wh_per_km, elevation_gains)
    for r in ranked:
        r.pop('coordinates', None)  # not needed in this summary response

    return jsonify({
        'origin': origin_display or origin_name,
        'destination': dest_display or dest_name,
        'routes': ranked,
    })


@trip_bp.route('/plan')
@login_required
def plan_page():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    saved = SavedTrip.query.filter_by(user_id=current_user.id).order_by(SavedTrip.created_at.desc()).all()
    return render_template('trip/plan.html', vehicles=vehicles, saved_trips=saved)


@trip_bp.route('/api/plan', methods=['POST'])
@login_required
def plan_trip():
    """Multi-stop Trip Planning + Round Trip Planning + ETA Prediction:
    plan an itinerary across an arbitrary ordered list of stops (see
    services/route_planning.py for the leg-by-leg + charging-insertion
    logic), and log the result as a TripPlan."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    vehicle = EVVehicle.query.get(data.get('vehicle_id'))
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    stops = data.get('stops') or []
    if not isinstance(stops, list) or len(stops) < 2:
        return jsonify({'error': "'stops' must be a list of at least 2 place names"}), 400

    consumption_multiplier = 1.0
    driving_style = data.get('driving_style')
    if driving_style == 'auto':
        style_report = analyze_driving_style(current_user.id)
        if style_report['status'] == 'ok':
            consumption_multiplier = style_report['consumption_multiplier']
            driving_style = style_report['driving_style']
        else:
            driving_style = None

    result = route_planning.plan_multi_stop_trip(
        vehicle, stops,
        round_trip=bool(data.get('round_trip', False)),
        start_battery_pct=float(data.get('battery_percentage', 100)),
        heater_usage=bool(data.get('heater_usage', True)),
        num_passengers=int(data.get('num_passengers', 1)),
        battery_age_years=float(data.get('battery_age_years', 0)),
        speed_kmh=float(data.get('speed_kmh', 80)),
        ambient_temperature_c=float(data.get('temperature_c', 0)),
        fast_charging=bool(data.get('fast_charging', True)),
        consumption_multiplier=consumption_multiplier,
        provider_config=current_app.config,
        departure_time=data.get('departure_time'),
    )
    if 'error' in result:
        return jsonify(result), 502

    plan = TripPlan(
        user_id=current_user.id, vehicle_id=vehicle.id,
        round_trip=result['round_trip'], driving_style=driving_style,
        total_distance_km=result['total_distance_km'],
        total_driving_duration_min=result['total_driving_duration_min'],
        total_charging_time_min=result['total_charging_time_min'],
        total_eta_min=result['total_eta_min'],
        num_charging_stops=result['num_charging_stops'],
        feasible=result['feasible'],
    )
    plan.stops = result['stops']
    plan.legs = result['legs']
    db.session.add(plan)
    db.session.commit()

    response = plan.to_dict()
    response['final_battery_pct'] = result['final_battery_pct']
    return jsonify(response)


@trip_bp.route('/api/plans')
@login_required
def plan_history():
    """Trip History for multi-stop plans specifically (kept separate
    from /api/history's single-leg TripSimulation log -- see
    models/trip_plan.py's docstring for why)."""
    plans = TripPlan.query.filter_by(user_id=current_user.id)\
        .order_by(TripPlan.created_at.desc()).limit(20).all()
    return jsonify([p.to_dict(include_legs=False) for p in plans])


@trip_bp.route('/api/plans/<int:plan_id>')
@login_required
def plan_detail(plan_id):
    plan = TripPlan.query.filter_by(id=plan_id, user_id=current_user.id).first()
    if not plan:
        return jsonify({'error': 'Trip plan not found'}), 404
    return jsonify(plan.to_dict(include_legs=True))


@trip_bp.route('/api/saved-trips', methods=['GET'])
@login_required
def list_saved_trips():
    """Saved Trips: bookmarked trip configurations for quick reuse --
    distinct from trip HISTORY (an automatic log of trips already
    simulated/planned), these are trips a user explicitly wants to
    save and re-plan later with fresh conditions."""
    trips = SavedTrip.query.filter_by(user_id=current_user.id).order_by(SavedTrip.created_at.desc()).all()
    return jsonify([t.to_dict() for t in trips])


@trip_bp.route('/api/saved-trips', methods=['POST'])
@login_required
def create_saved_trip():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    name = (data.get('name') or '').strip()
    stops = data.get('stops') or []
    vehicle_id = data.get('vehicle_id')
    if not name or not isinstance(stops, list) or len(stops) < 2 or not vehicle_id:
        return jsonify({'error': "'name', 'vehicle_id', and at least 2 'stops' are required"}), 400
    if not EVVehicle.query.get(vehicle_id):
        return jsonify({'error': 'Vehicle not found'}), 404

    trip = SavedTrip(user_id=current_user.id, vehicle_id=vehicle_id, name=name,
                      round_trip=bool(data.get('round_trip', False)))
    trip.stops = stops
    db.session.add(trip)
    db.session.commit()
    return jsonify(trip.to_dict()), 201


@trip_bp.route('/api/saved-trips/<int:trip_id>', methods=['DELETE'])
@login_required
def delete_saved_trip(trip_id):
    trip = SavedTrip.query.filter_by(id=trip_id, user_id=current_user.id).first()
    if not trip:
        return jsonify({'error': 'Saved trip not found'}), 404
    db.session.delete(trip)
    db.session.commit()
    return jsonify({'deleted': trip_id})


@trip_bp.route('/api/driving-style')
@login_required
def driving_style():
    """Driving Style Analysis for the current user, based on their own
    prediction/trip history (see services/driving_style.py)."""
    return jsonify(analyze_driving_style(current_user.id))


@trip_bp.route('/api/energy-curve')
@login_required
def energy_by_speed():
    """Speed-based Energy Consumption: a Wh/km-vs-speed curve for
    charting, based on a vehicle's baseline consumption (see
    services/energy_model.py)."""
    vehicle = EVVehicle.query.get(request.args.get('vehicle_id', type=int))
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404
    base_wh_per_km = vehicle.energy_consumption_wh_km or 170
    return jsonify({
        'vehicle_id': vehicle.id,
        'base_wh_per_km': base_wh_per_km,
        'most_efficient_speed_kmh': most_efficient_speed_kmh(),
        'curve': energy_curve(base_wh_per_km),
    })


@trip_bp.route('/api/recommend-destinations')
@login_required
def recommend_destinations_route():
    """Destination Recommendation: real nearby places reachable within
    the vehicle's SAFE range (accounting for the cold-weather
    degradation model, not just raw EPA range) from a given location
    (see services/route_planning.safe_range_km() and
    services/destination_recommender.py)."""
    place = request.args.get('place')
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    category = request.args.get('category', 'tourism')
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

    battery_pct = request.args.get('battery_percentage', 100, type=float)
    temperature_c = request.args.get('temperature_c', 0, type=float)

    features = {
        'temperature_c': temperature_c, 'humidity': 60, 'wind_speed_kmh': 15, 'precipitation': 'none',
        'battery_percentage': battery_pct, 'vehicle_speed_kmh': 80, 'hvac_usage': True, 'terrain_type': 'flat',
        'battery_age_years': 0, 'battery_capacity_kwh': vehicle.battery_capacity_kwh,
        'epa_range_km': vehicle.epa_range_km, 'vehicle_weight_kg': vehicle.vehicle_weight_kg,
    }
    prediction = get_prediction(features, 'random_forest')
    effective_range_km = prediction['predicted_range_km'] * (battery_pct / 100)
    margin_pct = current_app.config.get('TRIP_SAFETY_MARGIN_PCT', 15)
    # Halved, since a "reachable destination" implies driving there AND
    # back on the same charge -- see round_trip_distance_km in each
    # result, which reflects this same halving in reverse.
    safe_radius_km = route_planning.safe_range_km(effective_range_km, margin_pct) / 2

    destinations = recommend_destinations(lat, lon, safe_radius_km, category=category)
    if destinations is None:
        return jsonify({'error': 'Could not fetch destination recommendations right now'}), 502

    return jsonify({
        'location': {'lat': lat, 'lon': lon, 'resolved_place': resolved_place},
        'category': category,
        'available_categories': list(CATEGORY_TAGS.keys()),
        'safe_one_way_radius_km': round(safe_radius_km, 1),
        'safety_margin_pct': margin_pct,
        'destinations': destinations,
    })
