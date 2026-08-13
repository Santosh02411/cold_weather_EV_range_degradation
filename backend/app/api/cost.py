from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from ..models.ev_vehicle import EVVehicle
from ..models.cost_preference import CostPreference, ChargingSession
from .. import db
from ..services import analytics as analytics_service
from ..services.charging_cost import estimate_charging_cost
from ..services.cost_preferences import get_or_create_preferences, get_effective_rates
from ..services.electricity_rates import list_regional_rates, get_regional_rate
from ..services.grid_intensity import get_regional_intensity
from ..services.fuel_cost import compare_ev_vs_petrol, ownership_cost_analysis, savings_calculator

cost_bp = Blueprint('cost', __name__)


# ─────────────────────── Pages ───────────────────────

@cost_bp.route('/')
@login_required
def index():
    """Charging Cost Calculator."""
    return render_template('cost/calculator.html')


@cost_bp.route('/preferences')
@login_required
def preferences_page():
    """Electricity Price Integration: the user's own saved rates,
    prefillable from documented regional averages."""
    return render_template('cost/preferences.html')


@cost_bp.route('/monthly')
@login_required
def monthly_page():
    """Monthly Charging Cost -- dedicated page over the existing
    analytics_service.cost_analytics(), now defaulting to the user's
    own saved rates instead of the generic constants."""
    return render_template('cost/monthly.html')


@cost_bp.route('/compare')
@login_required
def compare_page():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return render_template('cost/compare.html', vehicles=vehicles)


@cost_bp.route('/ownership')
@login_required
def ownership_page():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return render_template('cost/ownership.html', vehicles=vehicles)


@cost_bp.route('/savings')
@login_required
def savings_page():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return render_template('cost/savings.html', vehicles=vehicles)


@cost_bp.route('/history')
@login_required
def history_page():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return render_template('cost/history.html', vehicles=vehicles)


# ─────────────────────── Calculator ───────────────────────

@cost_bp.route('/api/calculate', methods=['POST'])
@login_required
def calculate():
    data = request.get_json() or {}
    energy_needed_kwh = data.get('energy_needed_kwh')
    if energy_needed_kwh is None:
        return jsonify({'error': 'energy_needed_kwh is required'}), 400
    try:
        energy_needed_kwh = float(energy_needed_kwh)
    except (TypeError, ValueError):
        return jsonify({'error': 'energy_needed_kwh must be a number'}), 400

    fast_charging = bool(data.get('fast_charging', True))
    custom_rate = data.get('custom_rate')
    if custom_rate is not None:
        try:
            custom_rate = float(custom_rate)
        except (TypeError, ValueError):
            return jsonify({'error': 'custom_rate must be a number'}), 400
    else:
        # Default to the user's own saved rate for this tier, if set.
        rates = get_effective_rates(current_user.id)
        custom_rate = rates['public_rate_usd_per_kwh'] if fast_charging else rates['home_rate_usd_per_kwh']

    result = estimate_charging_cost(energy_needed_kwh, fast_charging=fast_charging, custom_rate=custom_rate)
    return jsonify(result)


# ─────────────────────── Electricity Price Integration ───────────────────────

@cost_bp.route('/api/regional-rates')
@login_required
def regional_rates():
    return jsonify(list_regional_rates())


@cost_bp.route('/api/preferences', methods=['GET'])
@login_required
def get_preferences():
    prefs = get_or_create_preferences(current_user.id)
    return jsonify({**prefs.to_dict(), 'effective_rates': get_effective_rates(current_user.id)})


@cost_bp.route('/api/preferences', methods=['POST'])
@login_required
def update_preferences():
    prefs = get_or_create_preferences(current_user.id)
    data = request.get_json() or {}

    region_key = data.get('use_regional_rate')
    if region_key:
        regional = get_regional_rate(region_key)
        if not regional:
            return jsonify({'error': f"Unknown region '{region_key}'"}), 400
        prefs.home_rate_usd_per_kwh = regional['home']
        prefs.public_rate_usd_per_kwh = regional['public_fast']
        prefs.rate_region_label = regional['label']
        # Same region also sets the grid carbon intensity used by
        # Sustainability (see services/grid_intensity.py) -- one region
        # picker, two derived preferences that both describe "my grid".
        intensity = get_regional_intensity(region_key)
        if intensity:
            prefs.grid_intensity_g_co2_per_kwh = intensity['intensity']
    else:
        numeric_fields = [
            'home_rate_usd_per_kwh', 'public_rate_usd_per_kwh',
            'petrol_price_per_liter', 'petrol_l_per_100km', 'annual_km',
            'grid_intensity_g_co2_per_kwh',
        ]
        for field in numeric_fields:
            if field in data:
                value = data[field]
                if value in (None, ''):
                    setattr(prefs, field, None)
                    continue
                try:
                    setattr(prefs, field, float(value))
                except (TypeError, ValueError):
                    return jsonify({'error': f'{field} must be a number'}), 400
        if any(f in data for f in ('home_rate_usd_per_kwh', 'public_rate_usd_per_kwh')):
            prefs.rate_region_label = None  # manual override supersedes any regional label

    db.session.commit()
    return jsonify({**prefs.to_dict(), 'effective_rates': get_effective_rates(current_user.id)})


# ─────────────────────── Monthly Charging Cost ───────────────────────

@cost_bp.route('/api/monthly')
@login_required
def monthly():
    period = request.args.get('period', 'monthly')
    rates = get_effective_rates(current_user.id)
    result = analytics_service.cost_analytics(
        current_user.id, period,
        home_rate_usd_per_kwh=rates['home_rate_usd_per_kwh'],
        public_rate_usd_per_kwh=rates['public_rate_usd_per_kwh'],
    )
    result['rate_sources'] = {'home': rates['home_rate_source'], 'public': rates['public_rate_source']}
    return jsonify(result)


# ─────────────────────── EV vs Petrol / Ownership / Savings ───────────────────────

def _resolve_vehicle_and_rate(data):
    vehicle_id = data.get('vehicle_id')
    if not vehicle_id:
        return None, None, (jsonify({'error': 'vehicle_id is required'}), 400)
    vehicle = EVVehicle.query.get(vehicle_id)
    if not vehicle:
        return None, None, (jsonify({'error': 'Vehicle not found'}), 404)

    rates = get_effective_rates(current_user.id)
    electricity_rate = data.get('electricity_rate_usd_per_kwh')
    electricity_rate = float(electricity_rate) if electricity_rate is not None else rates['home_rate_usd_per_kwh']
    return vehicle, electricity_rate, None


@cost_bp.route('/api/compare', methods=['POST'])
@login_required
def compare():
    data = request.get_json() or {}
    vehicle, electricity_rate, err = _resolve_vehicle_and_rate(data)
    if err:
        return err

    rates = get_effective_rates(current_user.id)
    result = compare_ev_vs_petrol(
        vehicle, electricity_rate,
        petrol_price_per_liter=data.get('petrol_price_per_liter', rates['petrol_price_per_liter']),
        petrol_l_per_100km=data.get('petrol_l_per_100km', rates['petrol_l_per_100km']),
        annual_km=data.get('annual_km', rates['annual_km']),
        years=int(data.get('years', 1)),
    )
    if result is None:
        return jsonify({'error': 'This vehicle has no energy consumption or EPA range data to base a comparison on.'}), 422
    return jsonify(result)


@cost_bp.route('/api/ownership', methods=['POST'])
@login_required
def ownership():
    data = request.get_json() or {}
    vehicle, electricity_rate, err = _resolve_vehicle_and_rate(data)
    if err:
        return err

    rates = get_effective_rates(current_user.id)
    result = ownership_cost_analysis(
        vehicle, electricity_rate, years=int(data.get('years', 5)),
        ev_purchase_price_usd=data.get('ev_purchase_price_usd'),
        petrol_purchase_price_usd=data.get('petrol_purchase_price_usd'),
        annual_maintenance_ev_usd=data.get('annual_maintenance_ev_usd'),
        annual_maintenance_petrol_usd=data.get('annual_maintenance_petrol_usd'),
        petrol_price_per_liter=data.get('petrol_price_per_liter', rates['petrol_price_per_liter']),
        petrol_l_per_100km=data.get('petrol_l_per_100km', rates['petrol_l_per_100km']),
        annual_km=data.get('annual_km', rates['annual_km']),
    )
    if result is None:
        return jsonify({'error': 'This vehicle has no energy consumption or EPA range data to base a comparison on.'}), 422
    return jsonify(result)


@cost_bp.route('/api/savings', methods=['POST'])
@login_required
def savings():
    data = request.get_json() or {}
    vehicle, electricity_rate, err = _resolve_vehicle_and_rate(data)
    if err:
        return err

    rates = get_effective_rates(current_user.id)
    result = savings_calculator(
        vehicle, electricity_rate, years=int(data.get('years', 3)),
        petrol_price_per_liter=data.get('petrol_price_per_liter', rates['petrol_price_per_liter']),
        petrol_l_per_100km=data.get('petrol_l_per_100km', rates['petrol_l_per_100km']),
        annual_km=data.get('annual_km', rates['annual_km']),
        ev_price_premium_usd=data.get('ev_price_premium_usd'),
    )
    if result is None:
        return jsonify({'error': 'This vehicle has no energy consumption or EPA range data to base a comparison on.'}), 422
    return jsonify(result)


# ─────────────────────── Charging Cost History ───────────────────────

@cost_bp.route('/api/sessions', methods=['GET'])
@login_required
def list_sessions():
    limit = min(request.args.get('limit', 100, type=int), 500)
    sessions = ChargingSession.query.filter_by(user_id=current_user.id) \
        .order_by(ChargingSession.session_date.desc()).limit(limit).all()

    total_energy = sum(s.energy_added_kwh for s in sessions)
    total_cost = sum(s.cost_usd for s in sessions if s.cost_usd is not None)

    return jsonify({
        'sessions': [s.to_dict() for s in sessions],
        'total_energy_kwh': round(total_energy, 2),
        'total_cost_usd': round(total_cost, 2),
        'session_count': len(sessions),
    })


@cost_bp.route('/api/sessions', methods=['POST'])
@login_required
def create_session():
    data = request.get_json() or {}
    energy_added_kwh = data.get('energy_added_kwh')
    if energy_added_kwh is None:
        return jsonify({'error': 'energy_added_kwh is required'}), 400
    try:
        energy_added_kwh = float(energy_added_kwh)
    except (TypeError, ValueError):
        return jsonify({'error': 'energy_added_kwh must be a number'}), 400

    source = data.get('source', 'home')
    if source not in ('home', 'level2', 'dc_fast'):
        return jsonify({'error': "source must be one of: home, level2, dc_fast"}), 400

    cost_usd = data.get('cost_usd')
    is_estimated = False
    if cost_usd is None:
        rates = get_effective_rates(current_user.id)
        rate = rates['home_rate_usd_per_kwh'] if source == 'home' else rates['public_rate_usd_per_kwh']
        cost_usd = round(energy_added_kwh * rate, 2)
        is_estimated = True
    else:
        try:
            cost_usd = float(cost_usd)
        except (TypeError, ValueError):
            return jsonify({'error': 'cost_usd must be a number'}), 400

    session_date = datetime.utcnow()
    if data.get('session_date'):
        try:
            session_date = datetime.fromisoformat(data['session_date'])
        except ValueError:
            return jsonify({'error': 'session_date must be an ISO datetime'}), 400

    session = ChargingSession(
        user_id=current_user.id,
        vehicle_id=data.get('vehicle_id'),
        station_name=data.get('station_name'),
        source=source,
        energy_added_kwh=energy_added_kwh,
        cost_usd=cost_usd,
        is_cost_estimated=is_estimated,
        session_date=session_date,
        notes=data.get('notes'),
    )
    db.session.add(session)
    db.session.commit()
    return jsonify(session.to_dict()), 201


@cost_bp.route('/api/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def delete_session(session_id):
    session = ChargingSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    db.session.delete(session)
    db.session.commit()
    return jsonify({'deleted': True})
