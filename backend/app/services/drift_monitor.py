"""Data drift monitoring + Live Model Retraining glue layer.

DB-aware (queries Prediction/EVVehicle), so this lives in services/,
not ml/ -- same convention services/recalibration.py already
established (see that module's docstring): ml/ stays importable and
testable without a running Flask app; services/ is where the DB-aware
assembly happens and hands plain DataFrames/dicts to ml/.

Two things live here:
  1. get_current_drift_report() -- compares recent real prediction
     inputs against the ACTIVE model version's stored training-time
     distribution baseline (see ml/drift.py's PSI machinery, and
     ml/train.py's feature_distribution_baseline in metadata.json).
  2. Live-retrain runtime state -- a small JSON file (same pattern as
     ml/train.py's current_version.json) holding an admin-toggleable
     enabled/disabled flag plus a short check history. The scheduler
     job (services/scheduler.py) reads/writes this every periodic
     check so toggling live retraining on/off from the admin panel
     takes effect on the very next check, no app restart required.
"""
import os
import json
from datetime import datetime, timezone

import pandas as pd

from ..ml.train import FEATURE_COLS, RAW_FEATURE_COLS, get_active_model_dir, get_models_root, train_all_models
from ..ml.predict import clear_model_cache, _encode_precipitation, _encode_terrain
from ..ml import drift as drift_mod
from ..ml import feature_engineering as fe
from ..ml.physics import physics_baseline_degradation_pct
from ..models.prediction import Prediction
from ..models.ev_vehicle import EVVehicle


def _state_path():
    return os.path.join(get_models_root(), 'live_retrain_state.json')


def get_live_retrain_state():
    path = _state_path()
    default = {'enabled': False, 'last_check_utc': None, 'last_drift_report': None,
               'last_retrain_utc': None, 'history': []}
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            state = json.load(f)
        for key, val in default.items():
            state.setdefault(key, val)
        return state
    except Exception:
        return default


def set_live_retrain_enabled(enabled):
    state = get_live_retrain_state()
    state['enabled'] = bool(enabled)
    _write_state(state)
    return state


def _write_state(state):
    # Cap history so this file doesn't grow unbounded over months of
    # periodic checks -- keep only the most recent entries.
    state['history'] = state.get('history', [])[-50:]
    os.makedirs(get_models_root(), exist_ok=True)
    with open(_state_path(), 'w') as f:
        json.dump(state, f, indent=2)


def _recent_features_df(limit=500):
    """Pull the most recent Prediction rows' RAW input features (plus
    the vehicle spec fields that live on EVVehicle, not Prediction),
    engineered the exact same way training data is (see
    feature_engineering.py), as a plain DataFrame ready for
    drift.compute_drift_report().
    """
    rows = Prediction.query.order_by(Prediction.created_at.desc()).limit(limit).all()
    data = []
    for p in rows:
        vehicle = EVVehicle.query.get(p.vehicle_id)
        if not vehicle:
            continue
        data.append({
            'temperature_c': p.temperature_c,
            'humidity': p.humidity if p.humidity is not None else 50.0,
            'wind_speed_kmh': p.wind_speed_kmh if p.wind_speed_kmh is not None else 10.0,
            'precipitation': _encode_precipitation(p.precipitation or 'none'),
            'battery_percentage': p.battery_percentage if p.battery_percentage is not None else 100.0,
            'vehicle_speed_kmh': p.vehicle_speed_kmh if p.vehicle_speed_kmh is not None else 60.0,
            'hvac_usage': 1 if p.hvac_usage else 0,
            'terrain_type': _encode_terrain(p.terrain_type or 'flat'),
            'battery_age_years': p.battery_age_years if p.battery_age_years is not None else 0.0,
            'battery_capacity_kwh': vehicle.battery_capacity_kwh,
            'epa_range_km': vehicle.epa_range_km,
            'vehicle_weight_kg': vehicle.vehicle_weight_kg,
        })
    if not data:
        return pd.DataFrame(columns=RAW_FEATURE_COLS)
    df = pd.DataFrame(data)
    df['physics_baseline_degradation'] = df['temperature_c'].apply(physics_baseline_degradation_pct)
    return fe.engineer_features(df)


def _load_active_baseline():
    version_dir = get_active_model_dir()
    meta_path = os.path.join(version_dir, 'metadata.json')
    if not os.path.exists(meta_path):
        return None
    with open(meta_path) as f:
        meta = json.load(f)
    return meta.get('feature_distribution_baseline')


def get_current_drift_report(limit=500):
    """Compare recent real prediction inputs to the active model
    version's training-time distribution. Returns a dict safe to
    serialize straight to JSON for the admin dashboard.
    """
    baseline = _load_active_baseline()
    if not baseline:
        return {
            'status': 'no_baseline',
            'reason': "Active model version has no stored distribution baseline "
                      "(trained before drift detection was added, or no version trained yet).",
        }

    current_df = _recent_features_df(limit=limit)
    if len(current_df) == 0:
        return {'status': 'no_recent_data', 'reason': 'No recent predictions to compare against yet.'}

    report = drift_mod.compute_drift_report(baseline, current_df, FEATURE_COLS)
    report['n_recent_predictions_checked'] = len(current_df)
    return report


def run_scheduled_drift_check(app, drift_psi_threshold=None, min_recent_predictions=None):
    """Called by the scheduler on its periodic interval. Always
    records a drift snapshot into the state file (so the dashboard
    shows monitoring activity even while auto-retrain is paused);
    only actually retrains when ALL of:
      - the runtime 'enabled' toggle is on,
      - enough recent predictions exist to trust the comparison,
      - the worst feature's drift has crossed the significant PSI
        threshold.
    """
    threshold = drift_psi_threshold if drift_psi_threshold is not None else app.config.get('LIVE_RETRAIN_DRIFT_PSI_THRESHOLD', 0.25)
    min_recent = min_recent_predictions if min_recent_predictions is not None else app.config.get('LIVE_RETRAIN_MIN_RECENT_PREDICTIONS', 50)

    state = get_live_retrain_state()
    report = get_current_drift_report()
    now = datetime.now(timezone.utc).isoformat()
    state['last_check_utc'] = now
    state['last_drift_report'] = report

    triggered = False
    if report.get('status') != 'ok':
        reason = f"skipped: {report.get('reason', report.get('status'))}"
    elif report.get('n_recent_predictions_checked', 0) < min_recent:
        reason = f"skipped: only {report.get('n_recent_predictions_checked', 0)} recent predictions, need >= {min_recent}"
    elif not state.get('enabled'):
        reason = 'skipped: live retraining is paused (drift monitoring stays on)'
    elif report.get('worst_psi', 0) >= threshold:
        triggered = True
        reason = f"triggered: '{report.get('worst_feature')}' PSI={report.get('worst_psi')} >= {threshold}"
    else:
        reason = f"ok: worst PSI {report.get('worst_psi')} below threshold {threshold}"

    entry = {
        'checked_at_utc': now, 'triggered': triggered, 'reason': reason,
        'worst_feature': report.get('worst_feature'), 'worst_psi': report.get('worst_psi'),
    }

    if triggered:
        try:
            meta = train_all_models(extra_metadata={
                'triggered_by': 'live_drift_retrain',
                'drift_report_at_trigger': report,
            })
            clear_model_cache()
            state['last_retrain_utc'] = now
            entry['new_version'] = meta.get('version')
        except Exception as e:
            entry['error'] = str(e)

    state.setdefault('history', []).append(entry)
    _write_state(state)
    return entry
