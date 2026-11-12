"""
FEAT-6 / FEAT-4: turn real user-reported outcomes into actual training
data, instead of only ever tracking them for display.

Two real-data sources feed the same pipeline:
  - Prediction.actual_range_km (FEAT-6): a user reports what really
    happened after a prediction they already made.
  - CommunityRangeReport (FEAT-4): anyone reports a real drive's outcome
    directly, without needing a prior prediction -- the broader,
    standalone crowdsourcing mechanism.

Both get converted into the same feature-row + real-degradation-label
shape `train.py` already expects (see FEATURE_COLS), then blended into
the synthetic dataset for retraining. This is deliberately kept in
`services/`, not `ml/`, because `ml/` is intentionally kept DB-free and
directly testable without a running Flask app (see
docs/PROJECT_WORKFLOW.md's "importlib bypass" testing pattern used
throughout this project) -- this module is the DB-aware glue layer
that assembles real data and hands a plain DataFrame to `ml/train.py`,
which stays exactly as DB-agnostic as it was before.
"""
import pandas as pd
import numpy as np

from ..models.prediction import Prediction, CommunityRangeReport
from ..models.ev_vehicle import EVVehicle
from ..ml.train import FEATURE_COLS, generate_synthetic_dataset, train_all_models
from ..ml.physics import physics_baseline_degradation_pct
from ..ml import feature_engineering as fe


def _degradation_from_actual(reported_range_km, epa_range_km, battery_pct):
    """The real label: how much range was actually lost, computed from
    what the user reported actually happened, not predicted. Guards
    against nonsensical inputs (zero/negative battery %, etc.) by
    returning None rather than raising or silently producing an
    invalid percentage that would corrupt training data.
    """
    if not epa_range_km or not battery_pct or battery_pct <= 0:
        return None
    expected_range_at_this_charge = epa_range_km * (battery_pct / 100.0)
    if expected_range_at_this_charge <= 0:
        return None
    degradation = 100.0 * (1 - (reported_range_km / expected_range_at_this_charge))
    return float(np.clip(degradation, 0, 65))


def collect_real_outcomes():
    """Query both real-data sources and return a single DataFrame in
    the same shape generate_synthetic_dataset() produces (FEATURE_COLS +
    range_degradation_pct), ready to concatenate with synthetic data.
    Rows that don't resolve to a sane degradation value (see
    _degradation_from_actual) are dropped rather than guessed at.
    """
    rows = []

    # --- FEAT-6: predictions with a later-reported actual range ---
    reported_predictions = Prediction.query.filter(Prediction.actual_range_km.isnot(None)).all()
    for p in reported_predictions:
        vehicle = EVVehicle.query.get(p.vehicle_id)
        if not vehicle:
            continue
        degradation = _degradation_from_actual(p.actual_range_km, vehicle.epa_range_km, p.battery_percentage)
        if degradation is None:
            continue
        rows.append({
            'temperature_c': p.temperature_c,
            'humidity': p.humidity or 50.0,
            'wind_speed_kmh': p.wind_speed_kmh or 10.0,
            'precipitation': {'none': 0, 'rain': 1, 'snow': 2}.get((p.precipitation or 'none').lower(), 0),
            'battery_percentage': p.battery_percentage or 100.0,
            'vehicle_speed_kmh': p.vehicle_speed_kmh or 60.0,
            'hvac_usage': 1 if p.hvac_usage else 0,
            'terrain_type': {'flat': 0, 'hilly': 1, 'mountainous': 2}.get((p.terrain_type or 'flat').lower(), 0),
            'battery_age_years': p.battery_age_years or 0.0,
            'battery_capacity_kwh': vehicle.battery_capacity_kwh,
            'epa_range_km': vehicle.epa_range_km,
            'vehicle_weight_kg': vehicle.vehicle_weight_kg,
            'physics_baseline_degradation': physics_baseline_degradation_pct(p.temperature_c),
            'range_degradation_pct': degradation,
            'source': 'prediction_followup',
        })

    # --- FEAT-4: standalone community reports ---
    community_reports = CommunityRangeReport.query.filter_by(is_flagged=False).all()
    for r in community_reports:
        vehicle = EVVehicle.query.get(r.vehicle_id)
        if not vehicle:
            continue
        degradation = _degradation_from_actual(r.reported_range_km, vehicle.epa_range_km, r.starting_battery_pct)
        if degradation is None:
            continue
        rows.append({
            'temperature_c': r.temperature_c,
            'humidity': r.humidity or 50.0,
            'wind_speed_kmh': r.wind_speed_kmh or 10.0,
            'precipitation': {'none': 0, 'rain': 1, 'snow': 2}.get((r.precipitation or 'none').lower(), 0),
            'battery_percentage': r.starting_battery_pct,
            'vehicle_speed_kmh': r.vehicle_speed_kmh or 60.0,
            'hvac_usage': 1 if r.hvac_usage else 0,
            'terrain_type': {'flat': 0, 'hilly': 1, 'mountainous': 2}.get((r.terrain_type or 'flat').lower(), 0),
            'battery_age_years': r.battery_age_years or 0.0,
            'battery_capacity_kwh': vehicle.battery_capacity_kwh,
            'epa_range_km': vehicle.epa_range_km,
            'vehicle_weight_kg': vehicle.vehicle_weight_kg,
            'physics_baseline_degradation': physics_baseline_degradation_pct(r.temperature_c),
            'range_degradation_pct': degradation,
            'source': 'community_report',
        })

    if not rows:
        return pd.DataFrame(columns=FEATURE_COLS + ['range_degradation_pct', 'source'])
    # Rows above only carry the RAW inputs -- add the same engineered
    # interaction features (wind chill, HVAC-cold interaction, etc.)
    # training data gets, via the same shared function, so real data
    # lines up with FEATURE_COLS exactly like synthetic data does (see
    # feature_engineering.py's docstring for why this is one shared
    # function rather than a second copy of the logic).
    return fe.engineer_features(pd.DataFrame(rows))


def real_data_summary():
    """Lightweight stats for the admin panel -- how much real data
    exists, and (if any) how the model's own predictions have compared
    to what was actually reported so far. This comparison uses each
    Prediction's OWN stored range_degradation_pct (what the model said
    at the time) against the real outcome-derived degradation -- a
    direct, real accuracy check, distinct from Phase 1's benchmark-table
    calibration check (that one validates against published studies;
    this one validates against this app's own users' real results).
    """
    real_df = collect_real_outcomes()
    followups = real_df[real_df['source'] == 'prediction_followup'] if not real_df.empty else real_df
    community = real_df[real_df['source'] == 'community_report'] if not real_df.empty else real_df

    accuracy = None
    if len(followups) > 0:
        reported_predictions = Prediction.query.filter(Prediction.actual_range_km.isnot(None)).all()
        errors = []
        for p in reported_predictions:
            vehicle = EVVehicle.query.get(p.vehicle_id)
            if not vehicle or p.range_degradation_pct is None:
                continue
            actual_degradation = _degradation_from_actual(p.actual_range_km, vehicle.epa_range_km, p.battery_percentage)
            if actual_degradation is None:
                continue
            errors.append(abs(p.range_degradation_pct - actual_degradation))
        if errors:
            accuracy = {
                'n': len(errors),
                'mae_vs_real_user_outcomes_pct': round(float(np.mean(errors)), 2),
            }

    return {
        'total_real_samples': len(real_df),
        'from_prediction_followups': len(followups),
        'from_community_reports': len(community),
        'model_accuracy_vs_real_outcomes': accuracy,
    }


def retrain_with_real_data(min_real_samples=10, real_weight=5, n_synthetic=8000):
    """FEAT-6/FEAT-4's actual payoff: blend real reported outcomes into
    the training data and retrain, instead of only ever displaying them.

    `real_weight`: each real row is duplicated this many times before
    blending with synthetic data. Real data is (by definition, at least
    early on) a tiny fraction of total rows -- without oversampling,
    a handful of real rows would have negligible influence against
    thousands of synthetic ones. This is a real, documented tradeoff
    (see docs/MEMORY.md): weight too high overfits to a small, possibly
    unrepresentative real sample; weight too low means "real data" barely
    moves the model at all. real_weight=5 is a starting judgment call,
    not a tuned value -- revisit once there's enough real volume to
    validate the choice against a held-out slice of real data itself.

    Raises ValueError if fewer than `min_real_samples` real rows exist,
    rather than silently retraining on synthetic data alone under a
    misleading "used real data" label.
    """
    real_df = collect_real_outcomes()
    if len(real_df) < min_real_samples:
        raise ValueError(
            f'Only {len(real_df)} real outcome(s) available; need at least '
            f'{min_real_samples} before retraining with real data (to avoid '
            f'overfitting to a handful of reports). Collect more via '
            f'prediction follow-ups (FEAT-6) or community reports (FEAT-4).'
        )

    real_df = real_df[FEATURE_COLS + ['range_degradation_pct']]
    weighted_real = pd.concat([real_df] * real_weight, ignore_index=True)

    synthetic_df = generate_synthetic_dataset(n_samples=n_synthetic)
    combined_df = pd.concat([synthetic_df, weighted_real], ignore_index=True)

    real_data_info = {
        'real_data_used': {
            'raw_real_samples': len(real_df),
            'real_weight': real_weight,
            'weighted_real_rows_in_training': len(weighted_real),
            'synthetic_rows_in_training': len(synthetic_df),
        }
    }
    metadata = train_all_models(df=combined_df, n_samples=len(combined_df), extra_metadata=real_data_info)
    return metadata
