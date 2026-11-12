from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from ..models.ev_vehicle import EVVehicle
from ..services.cost_preferences import get_effective_rates
from ..services.grid_intensity import list_regional_intensity
from ..services.emissions import (
    compare_ev_vs_petrol_emissions, fuel_savings, footprint_analytics, environmental_impact_summary,
)
from ..services.driving_style import green_driving_score

sustainability_bp = Blueprint('sustainability', __name__)


# ─────────────────────── Pages ───────────────────────

@sustainability_bp.route('/')
@login_required
def index():
    """CO2 Savings Calculator."""
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return render_template('sustainability/calculator.html', vehicles=vehicles)


@sustainability_bp.route('/footprint')
@login_required
def footprint_page():
    return render_template('sustainability/footprint.html')


@sustainability_bp.route('/fuel-savings')
@login_required
def fuel_savings_page():
    return render_template('sustainability/fuel_savings.html')


@sustainability_bp.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('sustainability/dashboard.html')


@sustainability_bp.route('/green-score')
@login_required
def green_score_page():
    return render_template('sustainability/green_score.html')


# ─────────────────────── CO2 Savings Calculator ───────────────────────

@sustainability_bp.route('/api/co2-savings', methods=['POST'])
@login_required
def co2_savings():
    data = request.get_json() or {}
    vehicle_id = data.get('vehicle_id')
    if not vehicle_id:
        return jsonify({'error': 'vehicle_id is required'}), 400
    vehicle = EVVehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    rates = get_effective_rates(current_user.id)
    grid_intensity = data.get('grid_intensity_g_co2_per_kwh', rates['grid_intensity_g_co2_per_kwh'])
    result = compare_ev_vs_petrol_emissions(
        vehicle, grid_intensity,
        petrol_l_per_100km=data.get('petrol_l_per_100km', rates['petrol_l_per_100km']),
        annual_km=data.get('annual_km', rates['annual_km']),
        years=int(data.get('years', 1)),
    )
    if result is None:
        return jsonify({'error': 'This vehicle has no energy consumption or EPA range data to base a comparison on.'}), 422
    return jsonify(result)


@sustainability_bp.route('/api/regional-grid-intensity')
@login_required
def regional_grid_intensity():
    return jsonify(list_regional_intensity())


# ─────────────────────── Carbon Footprint Analysis ───────────────────────

@sustainability_bp.route('/api/footprint')
@login_required
def footprint():
    period = request.args.get('period', 'monthly')
    rates = get_effective_rates(current_user.id)
    try:
        result = footprint_analytics(
            current_user.id, rates['grid_intensity_g_co2_per_kwh'], rates['petrol_l_per_100km'], period,
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    result['grid_intensity_source'] = rates['grid_intensity_source']
    return jsonify(result)


# ─────────────────────── Fuel Savings ───────────────────────

@sustainability_bp.route('/api/fuel-savings', methods=['POST'])
@login_required
def fuel_savings_api():
    data = request.get_json() or {}
    rates = get_effective_rates(current_user.id)
    result = fuel_savings(
        petrol_l_per_100km=data.get('petrol_l_per_100km', rates['petrol_l_per_100km']),
        annual_km=data.get('annual_km', rates['annual_km']),
        years=int(data.get('years', 1)),
    )
    return jsonify(result)


# ─────────────────────── Environmental Impact Dashboard ───────────────────────

@sustainability_bp.route('/api/impact-summary')
@login_required
def impact_summary():
    rates = get_effective_rates(current_user.id)
    result = environmental_impact_summary(
        current_user.id, rates['grid_intensity_g_co2_per_kwh'], rates['petrol_l_per_100km'],
    )
    result['grid_intensity_g_co2_per_kwh'] = rates['grid_intensity_g_co2_per_kwh']
    result['grid_intensity_source'] = rates['grid_intensity_source']
    return jsonify(result)


# ─────────────────────── Green Driving Score ───────────────────────

@sustainability_bp.route('/api/green-score')
@login_required
def green_score():
    return jsonify(green_driving_score(current_user.id))
