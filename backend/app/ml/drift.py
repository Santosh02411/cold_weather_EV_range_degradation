"""Data drift detection: Population Stability Index (PSI) between the
distribution a model was trained on and the distribution of inputs
it's actually being asked to predict on in production.

Kept Flask/DB-free (same convention as the rest of app/ml/, see
tests/conftest.py) -- the piece that actually pulls recent prediction
rows out of the database lives in services/drift_monitor.py instead.
This module only knows how to bin a DataFrame and compare two sets of
bin proportions; it doesn't know or care where either DataFrame came
from.

PSI is the standard metric for this in production ML monitoring
(insurance/credit-risk modeling is where it originates): bin a
reference distribution, bin a comparison distribution using the SAME
bin edges, then sum (comparison% - reference%) * ln(comparison% /
reference%) across bins. It's 0 when the distributions are identical
and grows as they diverge. Common industry rule-of-thumb thresholds
(used below): <0.1 no meaningful drift, 0.1-0.25 moderate drift worth
watching, >0.25 significant drift worth acting on.
"""
import numpy as np
import pandas as pd

PSI_MODERATE_THRESHOLD = 0.1
PSI_SIGNIFICANT_THRESHOLD = 0.25

# A tiny floor so an empty bin doesn't produce a divide-by-zero / -inf
# in the PSI log term -- standard PSI implementations do this too.
_EPS = 1e-4


def compute_baseline_distribution(df, feature_cols, n_bins=10):
    """Bin each feature into `n_bins` quantile-based buckets computed
    from `df` (normally the training set), and record both the bin
    edges and the resulting proportions. This is what gets saved into
    a trained version's metadata.json as the drift-detection
    reference point for that version.
    """
    baseline = {}
    for col in feature_cols:
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors='coerce').dropna().to_numpy(dtype=float)
        if len(values) == 0:
            continue
        # Quantile edges -> roughly equal-count bins on the training
        # data itself, which is what makes the *baseline* proportions
        # close to uniform (1/n_bins each) by construction.
        edges = np.unique(np.quantile(values, np.linspace(0, 1, n_bins + 1)))
        if len(edges) < 3:
            # Degenerate/near-constant feature (e.g. a flag column) --
            # not enough distinct values for quantile binning to be
            # meaningful. Record it but skip PSI for it later.
            baseline[col] = {'bin_edges': edges.tolist(), 'bin_proportions': [], 'degenerate': True}
            continue
        counts, _ = np.histogram(values, bins=edges)
        proportions = (counts / counts.sum()).tolist()
        baseline[col] = {'bin_edges': edges.tolist(), 'bin_proportions': proportions, 'degenerate': False}
    return baseline


def _bin_proportions(values, edges):
    values = np.asarray(values, dtype=float)
    edges = np.array(edges)
    # Clip so values outside the training-time min/max still land in
    # the first/last bin rather than being silently dropped -- drift
    # from a value going out of the previously-seen range is exactly
    # the kind of thing this is supposed to catch.
    clipped = np.clip(values, edges[0], edges[-1])
    counts, _ = np.histogram(clipped, bins=edges)
    total = counts.sum()
    if total == 0:
        return np.zeros(len(counts))
    return counts / total


def psi(baseline_proportions, current_proportions):
    """Population Stability Index between two same-length proportion
    arrays (already binned with the same edges)."""
    base = np.clip(np.asarray(baseline_proportions, dtype=float), _EPS, None)
    curr = np.clip(np.asarray(current_proportions, dtype=float), _EPS, None)
    return float(np.sum((curr - base) * np.log(curr / base)))


def _severity(psi_value):
    if psi_value >= PSI_SIGNIFICANT_THRESHOLD:
        return 'significant'
    if psi_value >= PSI_MODERATE_THRESHOLD:
        return 'moderate'
    return 'none'


def compute_drift_report(baseline, current_df, feature_cols):
    """Compare `current_df` (recent real-world prediction inputs)
    against the stored `baseline` distribution (from
    compute_baseline_distribution() at training time) for every
    feature both sides have. Returns per-feature PSI plus an overall
    verdict driven by the worst offending feature.
    """
    per_feature = []
    for col in feature_cols:
        ref = baseline.get(col)
        if not ref or ref.get('degenerate') or col not in current_df.columns:
            continue
        current_values = pd.to_numeric(current_df[col], errors='coerce').dropna()
        if len(current_values) == 0:
            continue
        current_props = _bin_proportions(current_values.to_numpy(), ref['bin_edges'])
        value = psi(ref['bin_proportions'], current_props)
        per_feature.append({
            'feature': col,
            'psi': round(value, 4),
            'severity': _severity(value),
        })

    per_feature.sort(key=lambda r: r['psi'], reverse=True)
    worst = per_feature[0] if per_feature else None

    return {
        'status': 'ok' if per_feature else 'insufficient_data',
        'n_features_checked': len(per_feature),
        'overall_severity': worst['severity'] if worst else 'none',
        'worst_feature': worst['feature'] if worst else None,
        'worst_psi': worst['psi'] if worst else 0.0,
        'per_feature': per_feature,
        'thresholds': {'moderate': PSI_MODERATE_THRESHOLD, 'significant': PSI_SIGNIFICANT_THRESHOLD},
    }
