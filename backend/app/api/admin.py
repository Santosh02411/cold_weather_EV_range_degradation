from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from ..models.user import User
from ..models.prediction import Prediction
from ..models.ev_vehicle import EVVehicle
from ..models.dataset import Dataset
from .. import db
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def panel():
    stats = {
        'total_users': User.query.count(),
        'total_vehicles': EVVehicle.query.filter_by(is_active=True).count(),
        'total_predictions': Prediction.query.count(),
        'total_datasets': Dataset.query.count(),
        'recent_users': User.query.order_by(User.created_at.desc()).limit(5).all(),
        'recent_predictions': Prediction.query.order_by(Prediction.created_at.desc()).limit(10).all(),
    }
    return render_template('admin/panel.html', stats=stats)


@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f"User {user.username} {'activated' if user.is_active else 'deactivated'}.", 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role', 'user')
    if user.id != current_user.id:
        user.role = new_role
        db.session.commit()
        flash(f"User {user.username} role changed to {new_role}.", 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    # Predictions by model
    model_stats = db.session.query(
        Prediction.ml_model_used, func.count(Prediction.id), func.avg(Prediction.range_degradation_pct)
    ).group_by(Prediction.ml_model_used).all()

    # Predictions per day (last 30)
    daily = db.session.query(
        func.date(Prediction.created_at), func.count(Prediction.id)
    ).group_by(func.date(Prediction.created_at))\
     .order_by(func.date(Prediction.created_at).desc()).limit(30).all()

    return render_template('admin/analytics.html',
                           model_stats=model_stats, daily_stats=daily)


@admin_bp.route('/retrain', methods=['POST'])
@login_required
@admin_required
def retrain():
    try:
        from ..ml.train import train_all_models
        results = train_all_models()
        flash('Models retrained successfully!', 'success')
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
