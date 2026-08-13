from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
import os
import json
from ..models.user import User
from ..models.prediction import Prediction, TripSimulation, CommunityRangeReport
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


@admin_bp.route('/api/real-data-stats', methods=['GET'])
@login_required
@admin_required
def real_data_stats():
    """FEAT-6/FEAT-4: how much real user-reported data exists, and how
    the model's own predictions have compared to real outcomes so far."""
    from ..services.recalibration import real_data_summary
    try:
        return jsonify(real_data_summary())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/retrain-with-real-data', methods=['POST'])
@login_required
@admin_required
def retrain_with_real_data():
    """FEAT-6/FEAT-4's actual payoff: retrain blending real reported
    outcomes into the training data, not just synthetic data. Separate
    from the plain /admin/retrain (synthetic-only) so an admin has to
    explicitly choose this -- see docs/MEMORY.md for why real_weight
    oversampling is a judgment call worth keeping visible, not hidden
    behind the default retrain button."""
    from ..services.recalibration import retrain_with_real_data as do_retrain
    from ..ml.predict import clear_model_cache
    try:
        meta = do_retrain()
        clear_model_cache()
        flash('Models retrained using real user-reported data!', 'success')
        return jsonify(meta)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/retrain', methods=['POST'])
@login_required
@admin_required
def retrain():
    try:
        from ..ml.train import train_all_models
        from ..ml.predict import clear_model_cache
        results = train_all_models()
        clear_model_cache()  # new version is now active; drop any stale cached models
        flash('Models retrained successfully!', 'success')
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/model-versions', methods=['GET'])
@login_required
@admin_required
def model_versions():
    """ML-4: list every trained model version with its metrics, so an
    admin can see what a rollback target actually looked like before
    activating it -- not just a bare version number."""
    from ..ml.train import list_versions
    try:
        return jsonify({'versions': list_versions()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/model-versions/<int:version_num>/activate', methods=['POST'])
@login_required
@admin_required
def activate_model_version(version_num):
    """ML-4: instant rollback (or roll-forward) to an already-trained
    version. No retraining -- just repoints current_version.json and
    clears the in-memory model cache so the very next prediction uses
    the newly-activated version."""
    from ..ml.train import set_active_version
    from ..ml.predict import clear_model_cache
    try:
        meta = set_active_version(version_num)
        clear_model_cache()
        flash(f'Activated model version v{version_num}.', 'success')
        return jsonify({'activated_version': version_num, 'metadata': meta})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/ml-dashboard')
@login_required
@admin_required
def ml_dashboard():
    """Model Comparison Dashboard: per-model metrics/hyperparameters/
    feature importance for the active version, feature selection, data
    drift status, and Live Model Retraining controls. Data is fetched
    client-side (see the page's own JS) so a slow drift check or
    AutoML run doesn't block the page from rendering."""
    return render_template('admin/ml_dashboard.html')


@admin_bp.route('/api/model-comparison', methods=['GET'])
@login_required
@admin_required
def model_comparison():
    """Model Comparison Dashboard's data source: every model in the
    ACTIVE version reshaped for side-by-side comparison (CV/val/test
    metrics, hyperparameters if tuned, ranked feature importance),
    plus that version's feature-selection report. `?version=N` looks
    at a specific past version instead of the active one (e.g. to
    compare a candidate before activating it).
    """
    from ..ml.train import get_models_root, get_active_version_info
    version_num = request.args.get('version', type=int)
    models_root = get_models_root()

    if version_num is not None:
        version_dir = next((d for d in os.listdir(models_root) if d.startswith(f'v{version_num}_')), None)
        if not version_dir:
            return jsonify({'error': f'No trained version v{version_num} found'}), 404
        meta_path = os.path.join(models_root, version_dir, 'metadata.json')
    else:
        active = get_active_version_info()
        if not active:
            return jsonify({'error': 'No trained model version yet -- retrain first.'}), 404
        meta_path = os.path.join(models_root, active['active_dir'], 'metadata.json')

    if not os.path.exists(meta_path):
        return jsonify({'error': 'Metadata not found for that version.'}), 404
    try:
        with open(meta_path) as f:
            meta = json.load(f)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    models = []
    for name, m in meta.get('metrics', {}).items():
        importance = m.get('feature_importance') or {}
        top_features = sorted(importance.items(), key=lambda kv: kv[1], reverse=True)[:8]
        models.append({
            'name': name,
            'cross_validation': m.get('cross_validation'),
            'validation_set': m.get('validation_set'),
            'held_out_test_set': m.get('held_out_test_set'),
            'hyperparameter_tuning': m.get('hyperparameter_tuning'),
            'top_features': [{'feature': f, 'importance': round(v, 5)} for f, v in top_features],
            'is_recommended': name == meta.get('recommended_model'),
        })
    models.sort(key=lambda mo: (mo['held_out_test_set'] or {}).get('mae', float('inf')))

    return jsonify({
        'version': meta.get('version'),
        'trained_at_utc': meta.get('trained_at_utc'),
        'n_samples': meta.get('n_samples'),
        'recommended_model': meta.get('recommended_model'),
        'hyperparameter_tuning_used': meta.get('hyperparameter_tuning_used', False),
        'automl_run': meta.get('automl_run', False),
        'has_xgboost': meta.get('has_xgboost'),
        'has_lightgbm': meta.get('has_lightgbm'),
        'has_catboost': meta.get('has_catboost'),
        'training_errors': meta.get('training_errors', {}),
        'models': models,
        'feature_selection': meta.get('feature_selection'),
        'real_world_calibration': meta.get('real_world_calibration'),
    })


@admin_bp.route('/api/automl', methods=['POST'])
@login_required
@admin_required
def run_automl():
    """AutoML: hyperparameter-search every tunable model family and
    save the result as a new version (does not auto-activate it --
    review the comparison, then activate like any other version).
    Slower than a plain retrain (each tunable model runs a small
    RandomizedSearchCV on top of its normal fit), so this is a
    separate explicit action rather than the default retrain button.
    """
    from ..ml.train import run_automl as do_run_automl
    try:
        n_iter = request.json.get('n_iter', 8) if request.is_json else 8
        meta = do_run_automl(tuning_n_iter=n_iter)
        flash(f"AutoML run complete -- created v{meta['version']}, recommended model: {meta.get('recommended_model')}.", 'success')
        return jsonify(meta)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/drift-report', methods=['GET'])
@login_required
@admin_required
def drift_report():
    """Data Drift Detection: how much recent real prediction inputs
    have diverged from what the active model version was trained on
    (Population Stability Index per feature -- see ml/drift.py)."""
    from ..services.drift_monitor import get_current_drift_report
    try:
        return jsonify(get_current_drift_report())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/live-retrain', methods=['GET'])
@login_required
@admin_required
def live_retrain_status():
    """Live Model Retraining: current runtime state (enabled/disabled,
    last drift check, recent history of checks/retrains)."""
    from ..services.drift_monitor import get_live_retrain_state
    try:
        return jsonify(get_live_retrain_state())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/live-retrain/toggle', methods=['POST'])
@login_required
@admin_required
def live_retrain_toggle():
    """Pause/resume Live Model Retraining. Takes effect on the very
    next scheduled drift check -- no app restart needed (see
    services/drift_monitor.py's state-file docstring for why)."""
    from ..services.drift_monitor import set_live_retrain_enabled
    enabled = bool(request.json.get('enabled', True)) if request.is_json else True
    try:
        state = set_live_retrain_enabled(enabled)
        flash(f"Live model retraining {'enabled' if enabled else 'paused'}.", 'success')
        return jsonify(state)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/live-retrain/check-now', methods=['POST'])
@login_required
@admin_required
def live_retrain_check_now():
    """Manually run the same drift check the background scheduler runs
    periodically, right now -- useful for testing the feature (or
    acting on drift) without waiting for the next scheduled interval.
    Works even if LIVE_RETRAIN_ENABLED never started the background
    job, since it's just calling the same check function directly.
    """
    from flask import current_app
    from ..services.drift_monitor import run_scheduled_drift_check
    try:
        entry = run_scheduled_drift_check(current_app._get_current_object())
        return jsonify(entry)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/fleet-stats', methods=['GET'])
@login_required
@admin_required
def fleet_stats():
    """FEAT-5: aggregate view across all users -- only matters once
    this app is used by more than a single driver, hence "fleet"."""
    total_users = User.query.count()
    total_vehicles = EVVehicle.query.filter_by(is_active=True).count()
    total_predictions = Prediction.query.count()
    total_trips = TripSimulation.query.count()
    total_community_reports = CommunityRangeReport.query.count()

    avg_confidence = db.session.query(func.avg(Prediction.prediction_confidence)).scalar()
    avg_degradation = db.session.query(func.avg(Prediction.range_degradation_pct)).scalar()

    # Predictions grouped by vehicle (top 10 by volume)
    by_vehicle = db.session.query(
        EVVehicle.manufacturer, EVVehicle.model_name,
        func.count(Prediction.id), func.avg(Prediction.range_degradation_pct)
    ).join(Prediction, Prediction.vehicle_id == EVVehicle.id) \
     .group_by(EVVehicle.id) \
     .order_by(func.count(Prediction.id).desc()) \
     .limit(10).all()

    # Most active users (top 5 by prediction count) -- usernames only,
    # no other personal data exposed here
    top_users = db.session.query(
        User.username, func.count(Prediction.id)
    ).join(Prediction, Prediction.user_id == User.id) \
     .group_by(User.id) \
     .order_by(func.count(Prediction.id).desc()) \
     .limit(5).all()

    return jsonify({
        'totals': {
            'users': total_users,
            'active_vehicles': total_vehicles,
            'predictions': total_predictions,
            'trips': total_trips,
            'community_reports': total_community_reports,
        },
        'avg_confidence': round(avg_confidence, 2) if avg_confidence is not None else None,
        'avg_degradation_pct': round(avg_degradation, 1) if avg_degradation is not None else None,
        'by_vehicle': [
            {'manufacturer': m, 'model_name': mo, 'prediction_count': c, 'avg_degradation_pct': round(a, 1) if a is not None else None}
            for m, mo, c, a in by_vehicle
        ],
        'top_users': [{'username': u, 'prediction_count': c} for u, c in top_users],
    })
