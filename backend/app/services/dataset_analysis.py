"""Dataset Management: pandas-based analysis and transformation
functions for uploaded datasets. Deliberately Flask/DB-free (every
function here takes a plain pandas DataFrame and returns plain
dicts/DataFrames) -- same convention as ml/feature_engineering.py and
the rest of this project's "pure logic separate from the web layer"
split. api/datasets.py is responsible for loading a Dataset's file
into a DataFrame, calling these, and persisting results as a new
DatasetVersion (see models/dataset.py).

Covers: Missing Value Detection, Duplicate Detection, Feature Scaling,
Encoding, Correlation Analysis, Train/Test Split, Data Validation, and
Feature Distribution Analysis. Dataset Versioning itself lives in
models/dataset.py + api/datasets.py, not here -- this module doesn't
know anything about persistence.
"""
import numpy as np
import pandas as pd

STRONG_CORRELATION_THRESHOLD = 0.7


# ─────────────────────── Missing Value Detection ───────────────────────

def detect_missing_values(df):
    """Per-column missing-value count/percentage + dtype, plus which
    rows are affected for columns with a manageable number of gaps
    (capped so a mostly-empty column doesn't dump thousands of row
    indices into the response)."""
    total_rows = len(df)
    columns = []
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        columns.append({
            'column': col,
            'dtype': str(df[col].dtype),
            'missing_count': missing_count,
            'missing_pct': round(100 * missing_count / total_rows, 2) if total_rows else 0.0,
            'missing_row_indices': df.index[df[col].isna()].tolist()[:50] if 0 < missing_count <= 500 else None,
        })
    columns.sort(key=lambda c: c['missing_count'], reverse=True)
    return {
        'total_rows': total_rows,
        'total_columns': len(df.columns),
        'columns_with_missing': sum(1 for c in columns if c['missing_count'] > 0),
        'total_missing_cells': sum(c['missing_count'] for c in columns),
        'columns': columns,
    }


# ───────────────────────── Duplicate Detection ─────────────────────────

def detect_duplicates(df, subset=None):
    """Exact duplicate row detection. `subset` restricts comparison to
    specific columns (e.g. a natural key) instead of every column --
    default (None) matches pandas' own default of "every column must
    match."""
    duplicate_mask = df.duplicated(subset=subset, keep='first')
    duplicate_indices = df.index[duplicate_mask].tolist()
    return {
        'total_rows': len(df),
        'duplicate_row_count': int(duplicate_mask.sum()),
        'duplicate_pct': round(100 * duplicate_mask.sum() / len(df), 2) if len(df) else 0.0,
        'unique_row_count': len(df) - int(duplicate_mask.sum()),
        'duplicate_row_indices': duplicate_indices[:100],
        'subset_columns': subset,
    }


def remove_duplicates(df, subset=None):
    """Returns (deduplicated_df, num_removed) -- keeps the first
    occurrence of each duplicate group, same as detect_duplicates()'s
    keep='first' so the count these two report always agrees."""
    before = len(df)
    deduped = df.drop_duplicates(subset=subset, keep='first').reset_index(drop=True)
    return deduped, before - len(deduped)


# ─────────────────────────── Correlation Analysis ───────────────────────────

def analyze_correlations(df, threshold=STRONG_CORRELATION_THRESHOLD):
    """Pearson correlation matrix over numeric columns, plus a
    flattened list of pairs whose absolute correlation exceeds
    `threshold` (the actually-actionable part of a correlation
    analysis -- "which features are basically redundant with each
    other" -- rather than making the caller scan an NxN matrix)."""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return {'available': False, 'reason': 'Need at least 2 numeric columns for a correlation analysis.'}

    corr = numeric_df.corr(numeric_only=True)
    strong_pairs = []
    cols = corr.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            value = corr.iloc[i, j]
            if pd.notna(value) and abs(value) >= threshold:
                strong_pairs.append({
                    'feature_a': cols[i], 'feature_b': cols[j],
                    'correlation': round(float(value), 4),
                    'strength': 'strong positive' if value > 0 else 'strong negative',
                })
    strong_pairs.sort(key=lambda p: abs(p['correlation']), reverse=True)

    return {
        'available': True,
        'columns': cols,
        'matrix': {c: {c2: (round(float(v), 4) if pd.notna(v) else None) for c2, v in corr[c].items()} for c in cols},
        'threshold': threshold,
        'strong_pairs': strong_pairs,
    }


# ───────────────────── Feature Distribution Analysis ─────────────────────

def analyze_feature_distributions(df, max_categories=15, num_bins=10):
    """Per-column distribution summary: full numeric stats (mean, std,
    quartiles, skewness) + a histogram for numeric columns; top value
    counts for categorical/object columns."""
    numeric_summary = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col].dropna()
        if series.empty:
            continue
        counts, bin_edges = np.histogram(series, bins=min(num_bins, series.nunique()) or 1)
        numeric_summary[col] = {
            'count': int(series.count()),
            'mean': round(float(series.mean()), 4),
            'std': round(float(series.std()), 4) if len(series) > 1 else 0.0,
            'min': round(float(series.min()), 4),
            'q25': round(float(series.quantile(0.25)), 4),
            'median': round(float(series.median()), 4),
            'q75': round(float(series.quantile(0.75)), 4),
            'max': round(float(series.max()), 4),
            'skewness': round(float(series.skew()), 4) if len(series) > 2 else None,
            'histogram': {
                'bin_edges': [round(float(e), 4) for e in bin_edges],
                'counts': [int(c) for c in counts],
            },
        }

    categorical_summary = {}
    for col in df.select_dtypes(exclude=[np.number]).columns:
        series = df[col].dropna()
        if series.empty:
            continue
        value_counts = series.value_counts().head(max_categories)
        categorical_summary[col] = {
            'count': int(series.count()),
            'unique_values': int(series.nunique()),
            'top_values': [{'value': str(v), 'count': int(c)} for v, c in value_counts.items()],
        }

    return {'numeric': numeric_summary, 'categorical': categorical_summary}


# ─────────────────────────── Data Validation ───────────────────────────

def validate_dataset(df, schema=None):
    """Data Validation against an optional schema dict shaped like:
        {'required_columns': ['temperature_c', ...],
         'column_ranges': {'temperature_c': {'min': -60, 'max': 60}, ...},
         'column_types': {'temperature_c': 'numeric'}}
    Every key is optional. With no schema at all, still reports basic
    structural issues (empty dataset, fully-empty columns, constant
    columns) that are worth flagging regardless of domain knowledge.
    Returns a list of issues (empty list = no issues found), each
    tagged with a severity so a UI can distinguish "should look into
    this" from "this will likely break downstream use."
    """
    schema = schema or {}
    issues = []

    if df.empty:
        issues.append({'severity': 'error', 'message': 'Dataset has no rows.'})
        return {'valid': False, 'issues': issues}

    for col in schema.get('required_columns', []):
        if col not in df.columns:
            issues.append({'severity': 'error', 'message': f"Required column '{col}' is missing."})

    for col, expected_type in schema.get('column_types', {}).items():
        if col not in df.columns:
            continue
        is_numeric = pd.api.types.is_numeric_dtype(df[col])
        if expected_type == 'numeric' and not is_numeric:
            issues.append({'severity': 'error', 'message': f"Column '{col}' expected numeric, found {df[col].dtype}."})
        elif expected_type == 'categorical' and is_numeric:
            issues.append({'severity': 'warning', 'message': f"Column '{col}' expected categorical, found numeric dtype."})

    for col, bounds in schema.get('column_ranges', {}).items():
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        series = df[col].dropna()
        lo, hi = bounds.get('min'), bounds.get('max')
        if lo is not None:
            below = int((series < lo).sum())
            if below:
                issues.append({'severity': 'warning', 'message': f"{below} value(s) in '{col}' are below the expected minimum ({lo})."})
        if hi is not None:
            above = int((series > hi).sum())
            if above:
                issues.append({'severity': 'warning', 'message': f"{above} value(s) in '{col}' are above the expected maximum ({hi})."})

    # Structural checks that apply regardless of a schema being given.
    for col in df.columns:
        if df[col].isna().all():
            issues.append({'severity': 'warning', 'message': f"Column '{col}' is entirely missing/empty."})
        elif df[col].nunique(dropna=True) == 1 and df[col].notna().any():
            issues.append({'severity': 'info', 'message': f"Column '{col}' has only one distinct value -- unlikely to be useful as a model feature."})

    has_errors = any(i['severity'] == 'error' for i in issues)
    return {'valid': not has_errors, 'issues': issues}


# ─────────────────────────── Feature Scaling ───────────────────────────

def scale_features(df, columns=None, method='standard'):
    """Feature Scaling: standardize (z-score) or min-max normalize the
    given numeric columns (defaults to every numeric column). Returns
    (scaled_df, params) where `params` records exactly what was
    applied per column (mean/std, or min/max) -- needed to later
    inverse-transform, and useful on its own as a transparency record
    of what a downstream model actually saw.
    """
    if method not in ('standard', 'minmax'):
        raise ValueError("method must be 'standard' or 'minmax'")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    target_cols = [c for c in (columns or numeric_cols) if c in numeric_cols]
    if not target_cols:
        return df.copy(), {'method': method, 'columns': {}}

    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    scaler = StandardScaler() if method == 'standard' else MinMaxScaler()

    scaled_df = df.copy()
    scaled_values = scaler.fit_transform(df[target_cols])
    scaled_df[target_cols] = scaled_values

    params = {'method': method, 'columns': {}}
    for i, col in enumerate(target_cols):
        if method == 'standard':
            params['columns'][col] = {'mean': round(float(scaler.mean_[i]), 6), 'std': round(float(scaler.scale_[i]), 6)}
        else:
            params['columns'][col] = {'min': round(float(scaler.data_min_[i]), 6), 'max': round(float(scaler.data_max_[i]), 6)}

    return scaled_df, params


# ────────────────────────────── Encoding ──────────────────────────────

def encode_features(df, columns=None, method='onehot'):
    """Encoding: one-hot or label-encode the given categorical
    (object/category dtype) columns (defaults to every categorical
    column). Returns (encoded_df, mapping) -- for label encoding,
    `mapping` records the category->integer assignment per column
    (needed to interpret/reverse the encoding later); for one-hot,
    it records which new columns came from which original column.
    """
    if method not in ('onehot', 'label'):
        raise ValueError("method must be 'onehot' or 'label'")

    categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    target_cols = [c for c in (columns or categorical_cols) if c in categorical_cols]
    if not target_cols:
        return df.copy(), {'method': method, 'columns': {}}

    if method == 'onehot':
        encoded_df = pd.get_dummies(df, columns=target_cols, prefix=target_cols)
        mapping = {
            col: [c for c in encoded_df.columns if c.startswith(f'{col}_')]
            for col in target_cols
        }
        return encoded_df, {'method': method, 'columns': mapping}

    # label encoding
    encoded_df = df.copy()
    mapping = {}
    for col in target_cols:
        categories = sorted(df[col].dropna().unique().tolist(), key=str)
        code_map = {cat: i for i, cat in enumerate(categories)}
        encoded_df[col] = df[col].map(code_map)
        mapping[col] = code_map
    return encoded_df, {'method': method, 'columns': mapping}


# ────────────────────────── Train/Test Split ──────────────────────────

def train_test_split_summary(df, test_size=0.2, val_size=0.0, random_state=42, stratify_col=None):
    """Train/Test Split (optionally also a validation split, carved out
    of the training portion). Returns the actual split DataFrames plus
    a summary of the resulting sizes -- callers persist the splits as
    new DatasetVersions if they want them kept (see api/datasets.py).
    """
    from sklearn.model_selection import train_test_split

    if not 0 < test_size < 1:
        raise ValueError('test_size must be between 0 and 1 (exclusive)')
    if not 0 <= val_size < 1:
        raise ValueError('val_size must be between 0 and 1')

    stratify = df[stratify_col] if stratify_col and stratify_col in df.columns else None
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state, stratify=stratify)

    val_df = None
    if val_size > 0:
        relative_val_size = val_size / (1 - test_size)
        stratify_train = train_df[stratify_col] if stratify_col and stratify_col in train_df.columns else None
        train_df, val_df = train_test_split(train_df, test_size=relative_val_size, random_state=random_state, stratify=stratify_train)

    splits = {'train': train_df.reset_index(drop=True), 'test': test_df.reset_index(drop=True)}
    if val_df is not None:
        splits['val'] = val_df.reset_index(drop=True)

    summary = {
        'total_rows': len(df),
        'test_size': test_size, 'val_size': val_size, 'random_state': random_state,
        'stratify_col': stratify_col if stratify is not None else None,
        'splits': {name: {'rows': len(split_df), 'pct': round(100 * len(split_df) / len(df), 1)} for name, split_df in splits.items()},
    }
    return splits, summary
