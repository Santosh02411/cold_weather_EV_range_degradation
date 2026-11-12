import io, csv
from flask import Blueprint, render_template, request, jsonify, send_file, make_response
from flask_login import login_required, current_user
from ..models.prediction import Prediction, TripSimulation
from ..models.ev_vehicle import EVVehicle
from .. import db

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')


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

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=trips_report.csv'
    return response


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
        return send_file(buffer, mimetype='application/pdf',
                         as_attachment=True, download_name='ev_report.pdf')
    except ImportError:
        return jsonify({'error': 'ReportLab not installed'}), 500
