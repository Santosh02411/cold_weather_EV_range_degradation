"""FEAT-4: crowdsourced real-world range reports -- the direct fix for
the row-level-real-data gap documented since Phase 1
(docs/TECHNICAL_ARCHITECTURE.md Sec 5/6), not tied to any specific
prediction the way FEAT-6's Prediction.actual_range_km is.
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from ..models.prediction import CommunityRangeReport
from ..models.ev_vehicle import EVVehicle
from .. import db, limiter

community_bp = Blueprint('community', __name__)


@community_bp.route('/')
@login_required
def index():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return render_template('community/index.html', vehicles=vehicles)


@community_bp.route('/api/reports', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def submit_report():
    """Anyone can submit a real-world outcome for any vehicle in the
    database -- no prior prediction required. Kept intentionally simple
    (no manual review gate before it counts toward recalibration -- see
    CommunityRangeReport.is_flagged's docstring for why) but real,
    numeric-only inputs are validated before saving.
    """
    data = request.get_json() or {}

    required = ['vehicle_id', 'temperature_c', 'starting_battery_pct', 'reported_range_km']
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({'error': f'Missing required field(s): {missing}'}), 400

    vehicle = EVVehicle.query.get(data['vehicle_id'])
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    try:
        starting_battery_pct = float(data['starting_battery_pct'])
        reported_range_km = float(data['reported_range_km'])
        temperature_c = float(data['temperature_c'])
    except (TypeError, ValueError):
        return jsonify({'error': 'temperature_c, starting_battery_pct, and reported_range_km must be numbers'}), 400

    if not (0 < starting_battery_pct <= 100):
        return jsonify({'error': 'starting_battery_pct must be between 0 and 100'}), 400
    if reported_range_km < 0:
        return jsonify({'error': 'reported_range_km cannot be negative'}), 400

    report = CommunityRangeReport(
        user_id=current_user.id,
        vehicle_id=vehicle.id,
        temperature_c=temperature_c,
        humidity=data.get('humidity'),
        wind_speed_kmh=data.get('wind_speed_kmh'),
        precipitation=data.get('precipitation', 'none'),
        vehicle_speed_kmh=data.get('vehicle_speed_kmh'),
        hvac_usage=bool(data.get('hvac_usage', True)),
        terrain_type=data.get('terrain_type', 'flat'),
        battery_age_years=data.get('battery_age_years'),
        starting_battery_pct=starting_battery_pct,
        reported_range_km=reported_range_km,
        notes=data.get('notes'),
    )
    db.session.add(report)
    db.session.commit()

    return jsonify({'report': report.to_dict()}), 201


@community_bp.route('/api/reports', methods=['GET'])
@login_required
def list_reports():
    """Browse recent community reports, optionally filtered by vehicle.
    No cross-user private data here -- reports are inherently meant to
    be shared (that's the point of crowdsourcing), so unlike
    predictions/trips there's no ownership check on reads.
    """
    vehicle_id = request.args.get('vehicle_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    query = CommunityRangeReport.query.filter_by(is_flagged=False)
    if vehicle_id:
        query = query.filter_by(vehicle_id=vehicle_id)
    query = query.order_by(CommunityRangeReport.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'reports': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages,
    })


@community_bp.route('/api/reports/stats', methods=['GET'])
@login_required
def report_stats():
    """Aggregate view: how much real data exists and how the model's
    own predictions compare to what's actually been reported so far.
    Thin wrapper around services/recalibration.py's summary so this
    number is computed the same way whether it's shown here or in the
    admin panel.
    """
    from ..services.recalibration import real_data_summary
    try:
        return jsonify(real_data_summary())
    except Exception as e:
        return jsonify({'error': str(e)}), 500
