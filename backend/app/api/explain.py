"""Explainable AI API: LIME, counterfactuals, PDP/ICE, SHAP waterfall/
force plots, a global explanation dashboard, and a richer confidence
breakdown -- see ml/explainability.py for the implementation and the
reasoning behind each method's scope.

Every endpoint here takes the same request shape as
/predictions/api/predict (vehicle_id + trip conditions), via the
shared build_features_from_request() helper -- these are exploratory
"explain this scenario" tools, not tied to an already-saved Prediction
row, so a user can freely try different conditions without saving one
each time.
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
from ..models.ev_vehicle import EVVehicle
from ..ml.predict import get_prediction, ALL_SELECTABLE_MODEL_NAMES
from ..ml.explainability import (
    lime_explanation, counterfactual_explanations, pdp_ice, PDP_SELECTABLE_FEATURES, FEATURE_DISPLAY_NAMES,
    shap_waterfall, shap_force, global_shap_summary, confidence_breakdown,
)
from .predictions import build_features_from_request

explain_bp = Blueprint('explain', __name__)


@explain_bp.route('/')
@login_required
def index():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    pdp_features = [{'name': f, 'display_name': FEATURE_DISPLAY_NAMES.get(f, f)} for f in PDP_SELECTABLE_FEATURES]
    return render_template('explain/dashboard.html', vehicles=vehicles, pdp_features=pdp_features,
                            models=ALL_SELECTABLE_MODEL_NAMES)


def _features_from_request():
    data = request.get_json() or {}
    vehicle = EVVehicle.query.get(data.get('vehicle_id'))
    if not vehicle:
        return None, None, (jsonify({'error': 'Vehicle not found'}), 404)
    model_name = data.get('model_name', 'random_forest')
    return build_features_from_request(data, vehicle), model_name, None


@explain_bp.route('/api/lime', methods=['POST'])
@login_required
def lime():
    features, model_name, error = _features_from_request()
    if error:
        return error
    num_features = request.get_json().get('num_features', 8)
    return jsonify(lime_explanation(features, model_name, num_features=num_features))


@explain_bp.route('/api/counterfactual', methods=['POST'])
@login_required
def counterfactual():
    features, model_name, error = _features_from_request()
    if error:
        return error
    return jsonify(counterfactual_explanations(features, model_name))


@explain_bp.route('/api/pdp', methods=['POST'])
@login_required
def pdp():
    features, model_name, error = _features_from_request()
    if error:
        return error
    feature_name = request.get_json().get('feature')
    if not feature_name:
        return jsonify({'error': "'feature' is required", 'selectable_features': PDP_SELECTABLE_FEATURES}), 400
    return jsonify(pdp_ice(features, feature_name, model_name))


@explain_bp.route('/api/pdp/features', methods=['GET'])
@login_required
def pdp_features():
    return jsonify({
        'features': [{'name': f, 'display_name': FEATURE_DISPLAY_NAMES.get(f, f)} for f in PDP_SELECTABLE_FEATURES],
    })


@explain_bp.route('/api/shap-waterfall', methods=['POST'])
@login_required
def waterfall():
    features, model_name, error = _features_from_request()
    if error:
        return error
    return jsonify(shap_waterfall(features, model_name))


@explain_bp.route('/api/shap-force', methods=['POST'])
@login_required
def force():
    features, model_name, error = _features_from_request()
    if error:
        return error
    return jsonify(shap_force(features, model_name))


@explain_bp.route('/api/confidence', methods=['POST'])
@login_required
def confidence():
    features, model_name, error = _features_from_request()
    if error:
        return error
    return jsonify(confidence_breakdown(features, model_name))


@explain_bp.route('/api/global', methods=['GET'])
@login_required
def global_dashboard():
    model_name = request.args.get('model_name', 'random_forest')
    n_samples = min(request.args.get('n_samples', 150, type=int), 500)
    return jsonify(global_shap_summary(model_name, n_samples))
