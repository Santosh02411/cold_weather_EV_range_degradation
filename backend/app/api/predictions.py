from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from ..models.prediction import Prediction
from ..models.ev_vehicle import EVVehicle
from ..ml.predict import get_prediction, get_available_models
from ..ml.xai import get_shap_explanation
from ..services.ai_features import generate_trip_briefing, answer_question, detect_anomaly, narrate_anomaly
from .. import db

predictions_bp = Blueprint('predictions', __name__)


@predictions_bp.route('/')
@login_required
def index():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    models = get_available_models()
    return render_template('predictions/index.html', vehicles=vehicles, ml_models=models)


@predictions_bp.route('/api/predict', methods=['POST'])
@login_required
def predict():
    print(f"[DEBUG] Incoming prediction request from user {current_user.username}")
    data = request.get_json()
    if not data:
        print("[DEBUG] Error: No JSON data received")
        return jsonify({'error': 'No data provided'}), 400
    
    print(f"[DEBUG] Vehicle ID: {data.get('vehicle_id')}, Temp: {data.get('temperature_c')}")

    vehicle_id = data.get('vehicle_id')
    vehicle = EVVehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    features = {
        'temperature_c': float(data.get('temperature_c', 20)),
        'humidity': float(data.get('humidity', 50)),
        'wind_speed_kmh': float(data.get('wind_speed_kmh', 10)),
        'precipitation': data.get('precipitation', 'none'),
        'battery_percentage': float(data.get('battery_percentage', 100)),
        'vehicle_speed_kmh': float(data.get('vehicle_speed_kmh', 60)),
        'hvac_usage': bool(data.get('hvac_usage', True)),
        'terrain_type': data.get('terrain_type', 'flat'),
        'battery_age_years': float(data.get('battery_age_years', 0)),
        'battery_capacity_kwh': vehicle.battery_capacity_kwh,
        'epa_range_km': vehicle.epa_range_km,
        'vehicle_weight_kg': vehicle.vehicle_weight_kg,
    }
    model_name = data.get('ml_model', 'random_forest')
    result = get_prediction(features, model_name)
    explanation = get_shap_explanation(features, model_name)

    prediction = Prediction(
        user_id=current_user.id, vehicle_id=vehicle_id,
        temperature_c=features['temperature_c'], humidity=features['humidity'],
        wind_speed_kmh=features['wind_speed_kmh'], precipitation=features['precipitation'],
        battery_percentage=features['battery_percentage'],
        vehicle_speed_kmh=features['vehicle_speed_kmh'],
        hvac_usage=features['hvac_usage'], terrain_type=features['terrain_type'],
        battery_age_years=features['battery_age_years'],
        range_degradation_pct=result['range_degradation_pct'],
        predicted_range_km=result['predicted_range_km'],
        energy_consumption_wh_km=result['energy_consumption_wh_km'],
        charging_slowdown_pct=result['charging_slowdown_pct'],
        ml_model_used=model_name,
        prediction_confidence=result.get('confidence', 0),
    )
    if explanation:
        prediction.set_shap_explanation(explanation)
    db.session.add(prediction)
    db.session.commit()

    anomaly = detect_anomaly(prediction.to_dict())

    return jsonify({
        'prediction': prediction.to_dict(),
        'explanation': explanation,
        'vehicle': vehicle.to_dict(),
        'anomaly': anomaly,
    })


def _load_owned_prediction(prediction_id):
    """Shared ownership check for the AI endpoints below - a prediction
    belongs to the user who made it, same rule as /api/history."""
    prediction = Prediction.query.get(prediction_id)
    if not prediction or prediction.user_id != current_user.id:
        return None
    return prediction


@predictions_bp.route('/api/<int:prediction_id>/briefing', methods=['GET'])
@login_required
def briefing(prediction_id):
    """AI-1: natural-language trip briefing for a saved prediction,
    grounded in that prediction's own stored facts (never regenerated
    or recomputed - same numbers the user already saw)."""
    prediction = _load_owned_prediction(prediction_id)
    if not prediction:
        return jsonify({'error': 'Prediction not found'}), 404

    vehicle = EVVehicle.query.get(prediction.vehicle_id)
    explanation = prediction.get_shap_explanation()
    text, source = generate_trip_briefing(
        current_app.config, prediction.to_dict(),
        vehicle.to_dict() if vehicle else {}, explanation
    )
    return jsonify({'briefing': text, 'source': source})


@predictions_bp.route('/api/<int:prediction_id>/ask', methods=['POST'])
@login_required
def ask(prediction_id):
    """AI-2: answer a free-form question about a saved prediction,
    grounded in that prediction's own facts only."""
    prediction = _load_owned_prediction(prediction_id)
    if not prediction:
        return jsonify({'error': 'Prediction not found'}), 404

    data = request.get_json() or {}
    question = data.get('question', '')

    vehicle = EVVehicle.query.get(prediction.vehicle_id)
    explanation = prediction.get_shap_explanation()
    text, source = answer_question(
        current_app.config, prediction.to_dict(),
        vehicle.to_dict() if vehicle else {}, explanation, question
    )
    return jsonify({'answer': text, 'source': source})


@predictions_bp.route('/api/<int:prediction_id>/anomaly', methods=['GET'])
@login_required
def anomaly_check(prediction_id):
    """AI-3: re-run the (real, non-LLM) anomaly check for a saved
    prediction and optionally narrate it in natural language."""
    prediction = _load_owned_prediction(prediction_id)
    if not prediction:
        return jsonify({'error': 'Prediction not found'}), 404

    anomaly = detect_anomaly(prediction.to_dict())
    explanation = prediction.get_shap_explanation()
    note, source = narrate_anomaly(current_app.config, anomaly, prediction.to_dict(), explanation)
    return jsonify({'anomaly': anomaly, 'note': note, 'note_source': source})


@predictions_bp.route('/api/history')
@login_required
def history():
    predictions = Prediction.query.filter_by(user_id=current_user.id)\
        .order_by(Prediction.created_at.desc()).limit(50).all()
    return jsonify([p.to_dict() for p in predictions])


@predictions_bp.route('/api/models')
@login_required
def list_models():
    return jsonify(get_available_models())
