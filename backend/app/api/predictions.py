from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from ..models.prediction import Prediction
from ..models.ev_vehicle import EVVehicle
from ..ml.predict import get_prediction, get_available_models
from ..ml.xai import get_shap_explanation
from ..services.ai_features import generate_trip_briefing, answer_question, detect_anomaly, narrate_anomaly
from .. import db, limiter

predictions_bp = Blueprint('predictions', __name__)


@predictions_bp.route('/')
@login_required
def index():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    models = get_available_models()
    return render_template('predictions/index.html', vehicles=vehicles, ml_models=models)


@predictions_bp.route('/api/predict', methods=['POST'])
@login_required
@limiter.limit(lambda: current_app.config.get('RATELIMIT_PREDICT', '30 per minute'))
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
        # UX-1/UX-3: expose what get_prediction() already computes but
        # the Prediction DB model doesn't have columns for, rather than
        # adding a migration for display-only fields.
        'model_details': {
            'confidence_note': result.get('confidence_note'),
            'models_in_ensemble': result.get('models_in_ensemble', []),
            'physics_baseline_degradation_pct': result.get('physics_baseline_degradation_pct'),
            'individual_predictions': result.get('individual_predictions', {}),
        },
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
@limiter.limit(lambda: current_app.config.get('RATELIMIT_AI', '15 per minute'))
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


@predictions_bp.route('/api/<int:prediction_id>/share', methods=['POST'])
@login_required
def create_share_link(prediction_id):
    """Generate (or return the existing) public share token for a
    prediction. Anyone with the resulting link can view a read-only
    summary + AI briefing, no login required -- that's the whole point
    of a "shareable link." Idempotent: calling this again on an
    already-shared prediction returns the same token/URL rather than
    invalidating the old one.
    """
    import secrets as _secrets
    prediction = _load_owned_prediction(prediction_id)
    if not prediction:
        return jsonify({'error': 'Prediction not found'}), 404

    if not prediction.share_token:
        prediction.share_token = _secrets.token_urlsafe(32)
        db.session.commit()

    share_url = request.url_root.rstrip('/') + f'/predictions/share/{prediction.share_token}'
    return jsonify({'share_token': prediction.share_token, 'share_url': share_url})


@predictions_bp.route('/api/<int:prediction_id>/unshare', methods=['POST'])
@login_required
def revoke_share_link(prediction_id):
    """Revoke a previously-created share link -- clears the token so
    the old link stops working. A new "Share" click afterward generates
    a brand new (different) token, not the same one."""
    prediction = _load_owned_prediction(prediction_id)
    if not prediction:
        return jsonify({'error': 'Prediction not found'}), 404
    prediction.share_token = None
    db.session.commit()
    return jsonify({'revoked': True})


@predictions_bp.route('/share/<token>')
def public_share_view(token):
    """Public, read-only view of a shared prediction + AI briefing. NO
    @login_required -- that's the point of a share link. Deliberately
    read-only (no ask/anomaly/report-actual actions here) and doesn't
    expose which user made the prediction, only the vehicle + conditions
    + result, to avoid leaking account info through a link meant for
    outside sharing.
    """
    prediction = Prediction.query.filter_by(share_token=token).first()
    if not prediction:
        return render_template('predictions/share_not_found.html'), 404

    vehicle = EVVehicle.query.get(prediction.vehicle_id)
    explanation = prediction.get_shap_explanation()
    briefing_text, briefing_source = generate_trip_briefing(
        current_app.config, prediction.to_dict(),
        vehicle.to_dict() if vehicle else {}, explanation
    )
    return render_template(
        'predictions/share_view.html',
        prediction=prediction, vehicle=vehicle,
        briefing=briefing_text, briefing_source=briefing_source,
    )


@predictions_bp.route('/api/<int:prediction_id>/briefing/pdf', methods=['GET'])
@login_required
def briefing_pdf(prediction_id):
    """Export the prediction + AI briefing as a downloadable PDF, reusing
    the same reportlab pattern as reports.py's existing PDF export."""
    from flask import send_file
    import io

    prediction = _load_owned_prediction(prediction_id)
    if not prediction:
        return jsonify({'error': 'Prediction not found'}), 404

    vehicle = EVVehicle.query.get(prediction.vehicle_id)
    explanation = prediction.get_shap_explanation()
    briefing_text, briefing_source = generate_trip_briefing(
        current_app.config, prediction.to_dict(),
        vehicle.to_dict() if vehicle else {}, explanation
    )

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        return jsonify({'error': 'ReportLab not installed'}), 500

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    vname = f"{vehicle.manufacturer} {vehicle.model_name}" if vehicle else "Unknown vehicle"
    elements.append(Paragraph("Cold Weather EV Trip Briefing", styles['Title']))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"{vname} &mdash; {prediction.created_at.strftime('%Y-%m-%d %H:%M') if prediction.created_at else ''}", styles['Normal']))
    elements.append(Spacer(1, 16))

    data = [
        ['Temperature', f"{prediction.temperature_c}\u00b0C"],
        ['Range Degradation', f"{prediction.range_degradation_pct}%"],
        ['Predicted Range', f"{prediction.predicted_range_km} km"],
        ['Energy Consumption', f"{prediction.energy_consumption_wh_km} Wh/km"],
        ['Confidence', f"{prediction.prediction_confidence}"],
    ]
    table = Table(data, colWidths=[160, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1a2234')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("AI Trip Briefing", styles['Heading2']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(briefing_text.replace('\n', '<br/>'), styles['Normal']))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<i>Source: {briefing_source}</i>", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                      download_name=f'trip_briefing_{prediction_id}.pdf')


@predictions_bp.route('/api/<int:prediction_id>/ask', methods=['POST'])
@login_required
@limiter.limit(lambda: current_app.config.get('RATELIMIT_AI', '15 per minute'))
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


@predictions_bp.route('/api/<int:prediction_id>/report-actual', methods=['POST'])
@login_required
def report_actual(prediction_id):
    """FEAT-6: record what the range actually turned out to be, after
    the driver really drove in these conditions. This is what lets the
    model be checked (and eventually retrained -- see
    services/recalibration.py) against real outcomes, not just its own
    synthetic test split or the Phase 1 published-study benchmarks.
    """
    from datetime import datetime
    prediction = _load_owned_prediction(prediction_id)
    if not prediction:
        return jsonify({'error': 'Prediction not found'}), 404

    data = request.get_json() or {}
    actual_range_km = data.get('actual_range_km')
    if actual_range_km is None:
        return jsonify({'error': 'actual_range_km is required'}), 400
    try:
        actual_range_km = float(actual_range_km)
    except (TypeError, ValueError):
        return jsonify({'error': 'actual_range_km must be a number'}), 400
    if actual_range_km < 0:
        return jsonify({'error': 'actual_range_km cannot be negative'}), 400

    prediction.actual_range_km = actual_range_km
    prediction.actual_range_reported_at = datetime.utcnow()
    db.session.commit()

    error_pct = None
    if prediction.predicted_range_km:
        error_pct = round(abs(prediction.predicted_range_km - actual_range_km) / prediction.predicted_range_km * 100, 1)

    return jsonify({
        'prediction': prediction.to_dict(),
        'predicted_range_km': prediction.predicted_range_km,
        'actual_range_km': actual_range_km,
        'error_pct': error_pct,
    })


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
