from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from ..models.ev_vehicle import EVVehicle
from .. import db

vehicles_bp = Blueprint('vehicles', __name__)


@vehicles_bp.route('/api/<int:vehicle_id>/efficiency-curve', methods=['GET'])
@login_required
def efficiency_curve(vehicle_id):
    """Battery Efficiency Curve: sweeps temperature through the
    already-trained prediction model for this vehicle's real specs, so
    the curve is guaranteed consistent with what an actual prediction
    would say at each point -- see services/battery_intelligence.py."""
    vehicle = EVVehicle.query.get_or_404(vehicle_id)
    from ..services.battery_intelligence import generate_efficiency_curve
    from ..services.train_baseline import typical_trip_features

    base_features = typical_trip_features(vehicle)
    curve = generate_efficiency_curve(base_features)
    return jsonify({'vehicle_id': vehicle_id, 'curve': curve})


@vehicles_bp.route('/<int:vehicle_id>/battery-health')
@login_required
def battery_health_page(vehicle_id):
    """FEAT-1 page: log/view SOH trend for one vehicle."""
    vehicle = EVVehicle.query.get_or_404(vehicle_id)
    return render_template('vehicles/battery_health.html', vehicle=vehicle)


@vehicles_bp.route('/')
@login_required
def list_vehicles():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    manufacturer = request.args.get('manufacturer', '').strip()
    chemistry = request.args.get('chemistry', '').strip()
    vehicle_type = request.args.get('vehicle_type', '').strip()
    min_capacity = request.args.get('min_capacity', type=float)
    max_capacity = request.args.get('max_capacity', type=float)
    min_range = request.args.get('min_range', type=float)
    max_range = request.args.get('max_range', type=float)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    fast_charging_only = request.args.get('fast_charging') == 'on'
    favorites_only = request.args.get('favorites_only') == 'on'

    query = EVVehicle.query.filter_by(is_active=True)

    if search:
        query = query.filter(
            (EVVehicle.model_name.ilike(f'%{search}%')) |
            (EVVehicle.manufacturer.ilike(f'%{search}%'))
        )
    if manufacturer:
        query = query.filter(EVVehicle.manufacturer.ilike(f'%{manufacturer}%'))
    if chemistry:
        query = query.filter(EVVehicle.battery_chemistry == chemistry)
    if vehicle_type:
        query = query.filter(EVVehicle.vehicle_type == vehicle_type)
    if min_capacity:
        query = query.filter(EVVehicle.battery_capacity_kwh >= min_capacity)
    if max_capacity:
        query = query.filter(EVVehicle.battery_capacity_kwh <= max_capacity)
    if min_range:
        query = query.filter(EVVehicle.epa_range_km >= min_range)
    if max_range:
        query = query.filter(EVVehicle.epa_range_km <= max_range)
    if min_price:
        query = query.filter(EVVehicle.price_usd >= min_price)
    if max_price:
        query = query.filter(EVVehicle.price_usd <= max_price)
    if fast_charging_only:
        query = query.filter(EVVehicle.max_charging_power_kw >= 50)
    if favorites_only:
        from ..models.vehicle_interactions import FavoriteVehicle
        favorite_vehicle_ids = [f.vehicle_id for f in FavoriteVehicle.query.filter_by(user_id=current_user.id).all()]
        query = query.filter(EVVehicle.id.in_(favorite_vehicle_ids))

    vehicles = query.order_by(EVVehicle.manufacturer, EVVehicle.model_name).paginate(
        page=page, per_page=12, error_out=False
    )

    manufacturers = db.session.query(EVVehicle.manufacturer).distinct().all()
    chemistries = db.session.query(EVVehicle.battery_chemistry).distinct().all()
    vehicle_types = db.session.query(EVVehicle.vehicle_type).filter(EVVehicle.vehicle_type.isnot(None)).distinct().all()

    favorite_ids = set()
    if current_user.is_authenticated:
        from ..models.vehicle_interactions import FavoriteVehicle
        favorite_ids = {f.vehicle_id for f in FavoriteVehicle.query.filter_by(user_id=current_user.id).all()}

    return render_template('vehicles/list.html',
                           vehicles=vehicles,
                           manufacturers=[m[0] for m in manufacturers],
                           chemistries=[c[0] for c in chemistries],
                           vehicle_types=[t[0] for t in vehicle_types],
                           favorite_ids=favorite_ids,
                           search=search,
                           manufacturer=manufacturer,
                           chemistry=chemistry,
                           selected_vehicle_type=vehicle_type)


def _save_vehicle_image(file, vehicle_id):
    """Same validated-upload pattern as auth.py's profile picture
    upload (extension check, size check, Pillow content validation) --
    duplicated rather than shared because the two live in different
    blueprints and the duplication is small; not worth a cross-blueprint
    import for ~15 lines. If a third upload feature is added, this is
    the point to extract a shared services/uploads.py.
    """
    from PIL import Image
    import os
    from werkzeug.utils import secure_filename
    from ..services.auth_tokens import generate_token
    from flask import current_app

    if not file or file.filename == '':
        return None, None

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in current_app.config.get('PROFILE_PICTURE_ALLOWED_EXTENSIONS', {'jpg', 'jpeg', 'png', 'webp'}):
        return None, 'Only JPG, PNG, and WEBP images are allowed.'

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    max_bytes = current_app.config.get('PROFILE_PICTURE_MAX_BYTES', 5 * 1024 * 1024)
    if size > max_bytes:
        return None, f'Image must be under {max_bytes // (1024 * 1024)}MB.'

    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)
    except Exception:
        return None, 'That file does not appear to be a valid image.'

    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'vehicle_images')
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(f"vehicle_{vehicle_id}_{generate_token()[:12]}.{ext}")
    file.save(os.path.join(upload_dir, filename))
    return f'uploads/vehicle_images/{filename}', None


@vehicles_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    if request.method == 'POST':
        vehicle = EVVehicle(
            model_name=request.form.get('model_name', '').strip(),
            manufacturer=request.form.get('manufacturer', '').strip(),
            battery_capacity_kwh=float(request.form.get('battery_capacity_kwh', 0)),
            epa_range_km=float(request.form.get('epa_range_km', 0)),
            vehicle_weight_kg=float(request.form.get('vehicle_weight_kg', 0)),
            battery_chemistry=request.form.get('battery_chemistry', '').strip(),
            charging_type=request.form.get('charging_type', '').strip(),
            max_charging_power_kw=float(request.form.get('max_charging_power_kw', 0)) or None,
            drivetrain=request.form.get('drivetrain', '').strip() or None,
            year=int(request.form.get('year', 0)) or None,
            energy_consumption_wh_km=float(request.form.get('energy_consumption_wh_km', 0)) or None,
            price_usd=float(request.form.get('price_usd', 0)) or None,
            vehicle_type=request.form.get('vehicle_type', '').strip() or None,
        )
        db.session.add(vehicle)
        db.session.commit()

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            image_path, error = _save_vehicle_image(image_file, vehicle.id)
            if error:
                flash(error, 'warning')
            elif image_path:
                vehicle.image_path = image_path
                db.session.commit()

        flash(f'{vehicle.manufacturer} {vehicle.model_name} added successfully!', 'success')
        return redirect(url_for('vehicles.list_vehicles'))

    return render_template('vehicles/add.html')


@vehicles_bp.route('/edit/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def edit_vehicle(vehicle_id):
    vehicle = EVVehicle.query.get_or_404(vehicle_id)

    if request.method == 'POST':
        vehicle.model_name = request.form.get('model_name', '').strip()
        vehicle.manufacturer = request.form.get('manufacturer', '').strip()
        vehicle.battery_capacity_kwh = float(request.form.get('battery_capacity_kwh', 0))
        vehicle.epa_range_km = float(request.form.get('epa_range_km', 0))
        vehicle.vehicle_weight_kg = float(request.form.get('vehicle_weight_kg', 0))
        vehicle.battery_chemistry = request.form.get('battery_chemistry', '').strip()
        vehicle.charging_type = request.form.get('charging_type', '').strip()
        vehicle.max_charging_power_kw = float(request.form.get('max_charging_power_kw', 0)) or None
        vehicle.drivetrain = request.form.get('drivetrain', '').strip() or None
        vehicle.year = int(request.form.get('year', 0)) or None
        vehicle.energy_consumption_wh_km = float(request.form.get('energy_consumption_wh_km', 0)) or None
        vehicle.price_usd = float(request.form.get('price_usd', 0)) or None
        vehicle.vehicle_type = request.form.get('vehicle_type', '').strip() or None

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            image_path, error = _save_vehicle_image(image_file, vehicle.id)
            if error:
                flash(error, 'warning')
            elif image_path:
                vehicle.image_path = image_path

        db.session.commit()
        flash('Vehicle updated successfully!', 'success')
        return redirect(url_for('vehicles.list_vehicles'))

    return render_template('vehicles/edit.html', vehicle=vehicle)


@vehicles_bp.route('/view/<int:vehicle_id>')
@login_required
def view_vehicle(vehicle_id):
    """Detailed Vehicle Specifications page. Recording this as a
    recently-viewed entry here (not in a separate API call) means the
    tracking can't be skipped by a client that forgets to call a
    separate endpoint -- viewing the page IS the view."""
    vehicle = EVVehicle.query.get_or_404(vehicle_id)

    from ..models.vehicle_interactions import record_view, FavoriteVehicle
    record_view(current_user.id, vehicle.id)
    is_favorite = FavoriteVehicle.query.filter_by(user_id=current_user.id, vehicle_id=vehicle.id).first() is not None

    return render_template('vehicles/detail.html', vehicle=vehicle, is_favorite=is_favorite)


@vehicles_bp.route('/api/<int:vehicle_id>/favorite', methods=['POST'])
@login_required
def add_favorite(vehicle_id):
    from ..models.vehicle_interactions import FavoriteVehicle
    EVVehicle.query.get_or_404(vehicle_id)
    if not FavoriteVehicle.query.filter_by(user_id=current_user.id, vehicle_id=vehicle_id).first():
        db.session.add(FavoriteVehicle(user_id=current_user.id, vehicle_id=vehicle_id))
        db.session.commit()
    return jsonify({'favorited': True})


@vehicles_bp.route('/api/<int:vehicle_id>/favorite', methods=['DELETE'])
@login_required
def remove_favorite(vehicle_id):
    from ..models.vehicle_interactions import FavoriteVehicle
    fav = FavoriteVehicle.query.filter_by(user_id=current_user.id, vehicle_id=vehicle_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
    return jsonify({'favorited': False})


@vehicles_bp.route('/api/favorites', methods=['GET'])
@login_required
def list_favorites():
    from ..models.vehicle_interactions import FavoriteVehicle
    favorites = FavoriteVehicle.query.filter_by(user_id=current_user.id) \
        .order_by(FavoriteVehicle.created_at.desc()).all()
    return jsonify({'vehicles': [f.vehicle.to_dict() for f in favorites if f.vehicle]})


@vehicles_bp.route('/api/recently-viewed', methods=['GET'])
@login_required
def recently_viewed():
    from ..models.vehicle_interactions import RecentlyViewedVehicle
    recent = RecentlyViewedVehicle.query.filter_by(user_id=current_user.id) \
        .order_by(RecentlyViewedVehicle.viewed_at.desc()).limit(10).all()
    return jsonify({'vehicles': [r.vehicle.to_dict() for r in recent if r.vehicle]})


@vehicles_bp.route('/delete/<int:vehicle_id>', methods=['POST'])
@login_required
def delete_vehicle(vehicle_id):
    vehicle = EVVehicle.query.get_or_404(vehicle_id)
    vehicle.is_active = False
    db.session.commit()
    flash('Vehicle removed successfully.', 'info')
    return redirect(url_for('vehicles.list_vehicles'))


@vehicles_bp.route('/api/list')
@login_required
def api_list():
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return jsonify([v.to_dict() for v in vehicles])


@vehicles_bp.route('/api/<int:vehicle_id>')
@login_required
def api_detail(vehicle_id):
    vehicle = EVVehicle.query.get_or_404(vehicle_id)
    return jsonify(vehicle.to_dict())


@vehicles_bp.route('/api/<int:vehicle_id>/battery-health', methods=['POST'])
@login_required
def log_battery_health(vehicle_id):
    """FEAT-1: log a State-of-Health reading for one of the current
    user's vehicles (most EVs expose an estimated SOH% somewhere in
    their own app -- this just tracks it here over time)."""
    from ..models.battery_health import BatteryHealthRecord

    vehicle = EVVehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Vehicle not found'}), 404

    data = request.get_json() or {}
    soh_pct = data.get('soh_pct')
    if soh_pct is None:
        return jsonify({'error': 'soh_pct is required'}), 400
    try:
        soh_pct = float(soh_pct)
    except (TypeError, ValueError):
        return jsonify({'error': 'soh_pct must be a number'}), 400
    if not (0 <= soh_pct <= 100):
        return jsonify({'error': 'soh_pct must be between 0 and 100'}), 400

    record = BatteryHealthRecord(
        user_id=current_user.id,
        vehicle_id=vehicle_id,
        soh_pct=soh_pct,
        odometer_km=data.get('odometer_km'),
        notes=data.get('notes'),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({'record': record.to_dict()}), 201


@vehicles_bp.route('/api/<int:vehicle_id>/battery-health', methods=['GET'])
@login_required
def battery_health_history(vehicle_id):
    """FEAT-1 + Battery Intelligence: this user's SOH history + fitted
    trend for one vehicle, now also including a generic research-cited
    SOH prediction (used when there's no real trend yet), an aging-rate
    classification (real trend vs. typical), and a years-to-EOL
    projection. Scoped to the requesting user's own records only
    (battery health is personal vehicle data, unlike FEAT-4's
    intentionally-shared community reports)."""
    from ..models.battery_health import BatteryHealthRecord
    from ..services.battery_trend import compute_trend
    from ..services import battery_intelligence as bi

    vehicle = EVVehicle.query.get_or_404(vehicle_id)
    records = BatteryHealthRecord.query.filter_by(
        user_id=current_user.id, vehicle_id=vehicle_id
    ).order_by(BatteryHealthRecord.recorded_at.asc()).all()

    trend = compute_trend([(r.recorded_at, r.soh_pct) for r in records]) if records else None

    # Prefer a REAL fitted trend (>= 2 logged readings) over the generic
    # research-cited estimate below -- the generic estimate exists
    # specifically for vehicles that don't have real data yet.
    if trend:
        current_soh = trend['latest_soh_pct']
        decline_rate = -trend['slope_pct_per_year'] if trend['slope_pct_per_year'] < 0 else 0.01
        soh_source = 'measured'
    else:
        current_soh = bi.estimate_soh_from_age(vehicle.year and (datetime.utcnow().year - vehicle.year))
        decline_rate = bi.TYPICAL_CALENDAR_DEGRADATION_PCT_PER_YEAR
        soh_source = 'estimated (no logged readings yet)'

    aging_analysis = bi.classify_aging_rate(decline_rate) if trend else None
    years_to_eol = bi.estimate_years_to_eol(current_soh, decline_rate) if current_soh else None

    return jsonify({
        'vehicle_id': vehicle_id,
        'records': [r.to_dict() for r in records],
        'trend': trend,
        'battery_intelligence': {
            'current_soh_pct': current_soh,
            'soh_source': soh_source,
            'aging_analysis': aging_analysis,
            'years_to_70pct_eol': years_to_eol,
        },
    })
