"""FEAT-3: manage cold-snap alert subscriptions. The actual checking/
sending logic lives in services/alerts.py, run periodically by
services/scheduler.py -- this blueprint is just CRUD for subscriptions,
plus a manual "check now" endpoint useful for testing without waiting
for the scheduler's next tick.
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from ..models.alert_subscription import AlertSubscription
from .. import db, limiter

alerts_bp = Blueprint('alerts', __name__)


@alerts_bp.route('/')
@login_required
def index():
    return render_template('alerts/index.html')


@alerts_bp.route('/api/subscriptions', methods=['GET'])
@login_required
def list_subscriptions():
    subs = AlertSubscription.query.filter_by(user_id=current_user.id).order_by(AlertSubscription.created_at.desc()).all()
    return jsonify({'subscriptions': [s.to_dict() for s in subs]})


@alerts_bp.route('/api/subscriptions', methods=['POST'])
@login_required
def create_subscription():
    data = request.get_json() or {}
    location = (data.get('location') or '').strip()
    if not location:
        return jsonify({'error': 'location is required'}), 400
    try:
        threshold = float(data.get('temperature_threshold_c', -10))
    except (TypeError, ValueError):
        return jsonify({'error': 'temperature_threshold_c must be a number'}), 400

    sub = AlertSubscription(user_id=current_user.id, location=location, temperature_threshold_c=threshold)
    db.session.add(sub)
    db.session.commit()
    return jsonify({'subscription': sub.to_dict()}), 201


@alerts_bp.route('/api/subscriptions/<int:sub_id>', methods=['DELETE'])
@login_required
def delete_subscription(sub_id):
    sub = AlertSubscription.query.get(sub_id)
    if not sub or sub.user_id != current_user.id:
        return jsonify({'error': 'Subscription not found'}), 404
    db.session.delete(sub)
    db.session.commit()
    return jsonify({'deleted': True})


@alerts_bp.route('/api/subscriptions/<int:sub_id>/toggle', methods=['POST'])
@login_required
def toggle_subscription(sub_id):
    sub = AlertSubscription.query.get(sub_id)
    if not sub or sub.user_id != current_user.id:
        return jsonify({'error': 'Subscription not found'}), 404
    sub.enabled = not sub.enabled
    db.session.commit()
    return jsonify({'subscription': sub.to_dict()})


@alerts_bp.route('/api/check-now', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def check_now():
    """Manually trigger a check across ALL subscriptions (not just this
    user's) -- useful for testing/admin without waiting for the
    scheduler's next tick. Not admin-gated: any logged-in user
    triggering an earlier check is harmless (cooldown logic still
    applies per-subscription), just rate-limited to avoid abuse.
    """
    from ..services.alerts import check_and_send_alerts
    try:
        results = check_and_send_alerts(current_app)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
