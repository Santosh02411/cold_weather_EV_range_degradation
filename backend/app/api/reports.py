import io, csv
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file, make_response
from flask_login import login_required, current_user
from ..models.prediction import Prediction, TripSimulation
from ..models.ev_vehicle import EVVehicle
from ..models.report import ReportSchedule, ReportHistory, REPORT_TYPES, REPORT_FORMATS, REPORT_FREQUENCIES
from .. import db
from ..services.report_generation import generate_report_bytes, FORMAT_MIME_TYPES
from ..services.scheduled_reports import run_schedule

reports_bp = Blueprint('reports', __name__)


def _log_history(report_type, format, row_count, source='manual'):
    """Report History: log this generation regardless of which export
    path produced it (manual CSV/PDF, manual Excel/JSON, or a
    scheduled email send -- see services/scheduled_reports.py for the
    scheduled-send counterpart to this)."""
    db.session.add(ReportHistory(
        user_id=current_user.id, report_type=report_type, format=format,
        source=source, row_count=row_count,
    ))
    db.session.commit()


@reports_bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')


@reports_bp.route('/printable')
@login_required
def printable_dashboard():
    """Printable Dashboard: a print-friendly summary page (browser
    print / 'Save as PDF' via the OS print dialog -- see this
    template's @media print rules) rather than a server-rendered PDF,
    so it can include live Chart.js visuals a static PDF table can't."""
    from ..services import analytics as analytics_service
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    user_stats = analytics_service.user_analytics(current_user.id)
    return render_template('reports/printable.html', user_stats=user_stats, vehicles=vehicles,
                            generated_at=datetime.utcnow())


@reports_bp.route('/api/csv/predictions')
@login_required
def export_predictions_csv():
    predictions = Prediction.query.filter_by(user_id=current_user.id)\
        .order_by(Prediction.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Vehicle', 'Temperature (°C)', 'Humidity (%)',
                      'Wind Speed (km/h)', 'Battery %', 'Speed (km/h)',
                      'HVAC', 'Range Degradation (%)', 'Predicted Range (km)',
                      'Energy (Wh/km)', 'Charging Slowdown (%)', 'ML Model'])

    for p in predictions:
        vehicle = EVVehicle.query.get(p.vehicle_id)
        vname = f"{vehicle.manufacturer} {vehicle.model_name}" if vehicle else "Unknown"
        writer.writerow([
            p.created_at.strftime('%Y-%m-%d %H:%M') if p.created_at else '',
            vname, p.temperature_c, p.humidity, p.wind_speed_kmh,
            p.battery_percentage, p.vehicle_speed_kmh,
            'Yes' if p.hvac_usage else 'No',
            p.range_degradation_pct, p.predicted_range_km,
            p.energy_consumption_wh_km, p.charging_slowdown_pct,
            p.ml_model_used,
        ])

    _log_history('predictions', 'csv', len(predictions))
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=predictions_report.csv'
    return response


@reports_bp.route('/api/csv/trips')
@login_required
def export_trips_csv():
    trips = TripSimulation.query.filter_by(user_id=current_user.id)\
        .order_by(TripSimulation.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Source', 'Destination', 'Distance (km)',
                      'Temperature (°C)', 'Speed (km/h)', 'Heater',
                      'Battery Usage (%)', 'Remaining Range (km)',
                      'Charging Stops', 'Arrival Battery (%)'])
    for t in trips:
        writer.writerow([
            t.created_at.strftime('%Y-%m-%d %H:%M') if t.created_at else '',
            t.source_location, t.destination, t.distance_km,
            t.temperature_c, t.speed_kmh,
            'Yes' if t.heater_usage else 'No',
            t.estimated_battery_usage_pct, t.predicted_remaining_range_km,
            t.charging_stops_required, t.estimated_arrival_battery_pct,
        ])

    _log_history('trips', 'csv', len(trips))
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=trips_report.csv'
    return response


@reports_bp.route('/api/excel/<report_type>')
@login_required
def export_excel(report_type):
    """Excel Report Export: predictions/trips/summary as a real .xlsx
    workbook (styled header row, auto-sized columns) via
    services/report_generation.py -- shared with the scheduled-email
    path so a manual Excel download and a scheduled Excel email always
    contain identical columns."""
    if report_type not in REPORT_TYPES:
        return jsonify({'error': f"report_type must be one of {REPORT_TYPES}"}), 400
    file_bytes, row_count, mime_type = generate_report_bytes(current_user.id, report_type, 'xlsx')
    _log_history(report_type, 'xlsx', row_count)
    return send_file(
        io.BytesIO(file_bytes), mimetype=mime_type, as_attachment=True,
        download_name=f'{report_type}_report.xlsx',
    )


@reports_bp.route('/api/json/<report_type>')
@login_required
def export_json(report_type):
    """JSON Export: predictions/trips/summary as a JSON array of
    objects (one per row, keyed by the same column names the CSV/Excel
    exports use)."""
    if report_type not in REPORT_TYPES:
        return jsonify({'error': f"report_type must be one of {REPORT_TYPES}"}), 400
    file_bytes, row_count, mime_type = generate_report_bytes(current_user.id, report_type, 'json')
    _log_history(report_type, 'json', row_count)
    response = make_response(file_bytes)
    response.headers['Content-Type'] = mime_type
    response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.json'
    return response


@reports_bp.route('/api/history')
@login_required
def report_history():
    """Report History: every report generated for this user, manual or
    scheduled, most recent first."""
    history = ReportHistory.query.filter_by(user_id=current_user.id)\
        .order_by(ReportHistory.generated_at.desc()).limit(100).all()
    return jsonify([h.to_dict() for h in history])


@reports_bp.route('/api/schedules', methods=['GET'])
@login_required
def list_schedules():
    schedules = ReportSchedule.query.filter_by(user_id=current_user.id)\
        .order_by(ReportSchedule.created_at.desc()).all()
    return jsonify([s.to_dict() for s in schedules])


@reports_bp.route('/api/schedules', methods=['POST'])
@login_required
def create_schedule():
    """Scheduled Reports: set up a recurring report to be emailed
    automatically (see services/scheduled_reports.py for the periodic
    background job that acts on these)."""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    report_type = data.get('report_type', 'predictions')
    format = data.get('format', 'csv')
    frequency = data.get('frequency', 'weekly')

    if not name:
        return jsonify({'error': "'name' is required"}), 400
    if report_type not in REPORT_TYPES:
        return jsonify({'error': f"report_type must be one of {REPORT_TYPES}"}), 400
    if format not in REPORT_FORMATS:
        return jsonify({'error': f"format must be one of {REPORT_FORMATS}"}), 400
    if frequency not in REPORT_FREQUENCIES:
        return jsonify({'error': f"frequency must be one of {REPORT_FREQUENCIES}"}), 400

    schedule = ReportSchedule(
        user_id=current_user.id, name=name, report_type=report_type, format=format, frequency=frequency,
    )
    db.session.add(schedule)
    db.session.commit()
    return jsonify(schedule.to_dict()), 201


@reports_bp.route('/api/schedules/<int:schedule_id>', methods=['PATCH'])
@login_required
def update_schedule(schedule_id):
    schedule = ReportSchedule.query.filter_by(id=schedule_id, user_id=current_user.id).first()
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    data = request.get_json() or {}
    if 'enabled' in data:
        schedule.enabled = bool(data['enabled'])
    if 'frequency' in data:
        if data['frequency'] not in REPORT_FREQUENCIES:
            return jsonify({'error': f"frequency must be one of {REPORT_FREQUENCIES}"}), 400
        schedule.frequency = data['frequency']
    db.session.commit()
    return jsonify(schedule.to_dict())


@reports_bp.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
@login_required
def delete_schedule(schedule_id):
    schedule = ReportSchedule.query.filter_by(id=schedule_id, user_id=current_user.id).first()
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    db.session.delete(schedule)
    db.session.commit()
    return jsonify({'deleted': schedule_id})


@reports_bp.route('/api/schedules/<int:schedule_id>/send-now', methods=['POST'])
@login_required
def send_schedule_now(schedule_id):
    """Email Reports: trigger one schedule's report send immediately,
    regardless of whether it's actually due -- useful for testing a
    new schedule (or just wanting the report right now) without
    waiting for the next scheduled interval."""
    from flask import current_app
    schedule = ReportSchedule.query.filter_by(id=schedule_id, user_id=current_user.id).first()
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    history = run_schedule(current_app.config, schedule)
    if history is None:
        return jsonify({'error': 'Could not send report'}), 500
    return jsonify(history.to_dict())


@reports_bp.route('/api/pdf/summary')
@login_required
def export_pdf():
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        predictions = Prediction.query.filter_by(user_id=current_user.id)\
            .order_by(Prediction.created_at.desc()).limit(50).all()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Cold Weather EV Range Degradation Report", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Generated for: {current_user.full_name}", styles['Normal']))
        elements.append(Spacer(1, 20))

        if predictions:
            data = [['Date', 'Temp °C', 'Degradation %', 'Range km', 'Model']]
            for p in predictions[:30]:
                vehicle = EVVehicle.query.get(p.vehicle_id)
                data.append([
                    p.created_at.strftime('%m/%d') if p.created_at else '',
                    str(p.temperature_c),
                    f"{p.range_degradation_pct:.1f}%",
                    f"{p.predicted_range_km:.0f}",
                    p.ml_model_used or '',
                ])
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4ff')]),
            ]))
            elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        _log_history('predictions', 'pdf', len(predictions))
        return send_file(buffer, mimetype='application/pdf',
                         as_attachment=True, download_name='ev_report.pdf')
    except ImportError:
        return jsonify({'error': 'ReportLab not installed'}), 500
