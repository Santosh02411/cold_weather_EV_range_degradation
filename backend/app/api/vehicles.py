from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..models.ev_vehicle import EVVehicle
from .. import db

vehicles_bp = Blueprint('vehicles', __name__)


@vehicles_bp.route('/')
@login_required
def list_vehicles():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    manufacturer = request.args.get('manufacturer', '').strip()
    chemistry = request.args.get('chemistry', '').strip()
    min_capacity = request.args.get('min_capacity', type=float)
    max_capacity = request.args.get('max_capacity', type=float)
    min_range = request.args.get('min_range', type=float)
    max_range = request.args.get('max_range', type=float)

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
    if min_capacity:
        query = query.filter(EVVehicle.battery_capacity_kwh >= min_capacity)
    if max_capacity:
        query = query.filter(EVVehicle.battery_capacity_kwh <= max_capacity)
    if min_range:
        query = query.filter(EVVehicle.epa_range_km >= min_range)
    if max_range:
        query = query.filter(EVVehicle.epa_range_km <= max_range)

    vehicles = query.order_by(EVVehicle.manufacturer, EVVehicle.model_name).paginate(
        page=page, per_page=12, error_out=False
    )

    manufacturers = db.session.query(EVVehicle.manufacturer).distinct().all()
    chemistries = db.session.query(EVVehicle.battery_chemistry).distinct().all()

    return render_template('vehicles/list.html',
                           vehicles=vehicles,
                           manufacturers=[m[0] for m in manufacturers],
                           chemistries=[c[0] for c in chemistries],
                           search=search,
                           manufacturer=manufacturer,
                           chemistry=chemistry)


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
        )
        db.session.add(vehicle)
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

        db.session.commit()
        flash('Vehicle updated successfully!', 'success')
        return redirect(url_for('vehicles.list_vehicles'))

    return render_template('vehicles/edit.html', vehicle=vehicle)


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
