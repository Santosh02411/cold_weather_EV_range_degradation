from flask import Blueprint, jsonify, request
from flask_login import login_required

recommendations_bp = Blueprint('recommendations', __name__)


def generate_recommendations(temperature_c, hvac_usage, speed_kmh, battery_pct, battery_age_years, terrain_type):
    """Generate smart recommendations based on conditions"""
    recs = []

    if temperature_c < 0:
        recs.append({
            'icon': '🔋', 'priority': 'high',
            'title': 'Precondition Your Battery',
            'description': 'Precondition the battery while plugged in before departure to warm it up and reduce range loss.',
            'impact': 'Can recover 10-20% of cold weather range loss'
        })
    if temperature_c < -10:
        recs.append({
            'icon': '⚡', 'priority': 'high',
            'title': 'Charge Before Trip',
            'description': 'Charge to at least 90% before departing in extreme cold. Charging is slower in freezing temps.',
            'impact': 'Ensures sufficient range buffer for cold conditions'
        })
    if hvac_usage and temperature_c < 5:
        recs.append({
            'icon': '♨️', 'priority': 'medium',
            'title': 'Use Seat Heaters Instead of Cabin Heat',
            'description': 'Seat and steering wheel heaters use much less energy than cabin heating.',
            'impact': 'Can save 5-15% battery compared to full cabin heating'
        })
    if speed_kmh > 100:
        recs.append({
            'icon': '🚗', 'priority': 'medium',
            'title': 'Reduce Highway Speed',
            'description': f'Current speed {speed_kmh} km/h increases aerodynamic drag. Reducing to 90 km/h improves range.',
            'impact': 'Every 10 km/h reduction above 90 saves ~5-8% range'
        })
    if temperature_c < 10:
        recs.append({
            'icon': '🌿', 'priority': 'medium',
            'title': 'Enable Eco Mode',
            'description': 'Eco mode limits power output and optimizes energy use for maximum range.',
            'impact': 'Typically saves 5-12% energy in cold conditions'
        })
    if battery_pct < 30 and temperature_c < 0:
        recs.append({
            'icon': '🔌', 'priority': 'high',
            'title': 'Find Charging Station Soon',
            'description': f'Battery at {battery_pct}% in cold weather. Range may drop faster than expected.',
            'impact': 'Prevents being stranded with depleted battery'
        })
    if battery_age_years > 3:
        recs.append({
            'icon': '🔧', 'priority': 'low',
            'title': 'Battery Health Check',
            'description': f'Battery is {battery_age_years:.1f} years old. Consider a health check at your service center.',
            'impact': 'Older batteries degrade more in cold weather'
        })
    if terrain_type == 'mountainous':
        recs.append({
            'icon': '⛰️', 'priority': 'medium',
            'title': 'Plan for Elevation Changes',
            'description': 'Mountainous terrain increases energy consumption significantly.',
            'impact': 'Uphill driving can use 30-50% more energy'
        })
    if temperature_c < 5:
        recs.append({
            'icon': '🅿️', 'priority': 'low',
            'title': 'Park in Heated Garage',
            'description': 'Parking indoors keeps the battery warmer and reduces preconditioning time.',
            'impact': 'Can improve morning range by 5-10%'
        })
    if not recs:
        recs.append({
            'icon': '✅', 'priority': 'low',
            'title': 'Conditions Look Good',
            'description': 'Current conditions are favorable for EV driving. Enjoy your trip!',
            'impact': 'Minimal range degradation expected'
        })
    return recs


@recommendations_bp.route('/api/get', methods=['POST'])
@login_required
def get_recommendations():
    data = request.get_json() or {}
    recs = generate_recommendations(
        float(data.get('temperature_c', 20)),
        bool(data.get('hvac_usage', True)),
        float(data.get('speed_kmh', 60)),
        float(data.get('battery_percentage', 100)),
        float(data.get('battery_age_years', 0)),
        data.get('terrain_type', 'flat'),
    )
    return jsonify({'recommendations': recs})
