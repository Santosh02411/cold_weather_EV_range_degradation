"""Data Visualization (dataset-generic variants): chart-ready data for
Heatmaps, Correlation Matrix, Scatter Plot, Histogram, Box Plot, and
Violin Plot. Pure pandas-in/dict-out functions (Flask/DB-free), same
convention as services/dataset_analysis.py -- which this module reuses
for the correlation matrix and quartile logic rather than recomputing
them from scratch.

Line Charts, Geographic Weather Map, Battery Performance Charts, and
Prediction Timeline are APP-DATA visualizations (predictions, trips,
battery health, weather logs) rather than generic dataset charts --
those live in services/app_chart_data.py instead, which IS DB-aware.
"""
import numpy as np
import pandas as pd

from . import dataset_analysis as da


# ─────────────────────── Heatmap / Correlation Matrix ───────────────────────

def heatmap_data(df, columns=None):
    """Heatmap / Correlation Matrix: reuses
    dataset_analysis.analyze_correlations()'s matrix, reshaped into a
    flat list of {x, y, value} cells -- the shape a generic grid/
    heatmap renderer consumes, instead of a nested column->column dict.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if columns:
        numeric_df = numeric_df[[c for c in columns if c in numeric_df.columns]]

    corr_result = da.analyze_correlations(numeric_df, threshold=da.STRONG_CORRELATION_THRESHOLD)
    if not corr_result['available']:
        return corr_result

    cols = corr_result['columns']
    cells = [
        {'x': x, 'y': y, 'value': corr_result['matrix'][x][y]}
        for x in cols for y in cols
    ]
    return {'available': True, 'labels': cols, 'cells': cells}


# ─────────────────────────────── Scatter Plot ───────────────────────────────

def scatter_data(df, x_col, y_col, color_col=None, max_points=2000):
    """Scatter Plot: (x, y[, group]) points for two numeric columns,
    optionally grouped/colored by a third column. Randomly samples
    down to `max_points` for very large datasets rather than shipping
    the whole thing to the browser.
    """
    missing = [c for c in (x_col, y_col) if c not in df.columns]
    if missing:
        return {'available': False, 'reason': f"Column(s) not found: {missing}"}

    cols = [x_col, y_col] + ([color_col] if color_col and color_col in df.columns else [])
    clean = df[cols].dropna()
    if clean.empty:
        return {'available': False, 'reason': 'No rows with both columns present.'}
    if len(clean) > max_points:
        clean = clean.sample(max_points, random_state=42)

    has_group = color_col and color_col in clean.columns
    points = [
        {
            'x': float(row[x_col]), 'y': float(row[y_col]),
            'group': str(row[color_col]) if has_group else None,
        }
        for _, row in clean.iterrows()
    ]

    correlation = None
    if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]) and len(clean) > 1:
        correlation = round(float(clean[x_col].corr(clean[y_col])), 4)

    return {
        'available': True, 'x_col': x_col, 'y_col': y_col, 'color_col': color_col if has_group else None,
        'n_points': len(points), 'correlation': correlation, 'points': points,
    }


# ──────────────────────────────── Histogram ────────────────────────────────

def histogram_data(df, column, num_bins=10):
    """Histogram for one numeric column -- same binning approach
    dataset_analysis.analyze_feature_distributions() uses per-column,
    exposed standalone so a user can pick one column and a custom bin
    count instead of getting every numeric column's histogram at once.
    """
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return {'available': False, 'reason': f"'{column}' is not a numeric column in this dataset."}
    series = df[column].dropna()
    if series.empty:
        return {'available': False, 'reason': f"'{column}' has no non-missing values."}

    counts, bin_edges = np.histogram(series, bins=min(num_bins, series.nunique()) or 1)
    bin_labels = [f"{bin_edges[i]:.2f}\u2013{bin_edges[i + 1]:.2f}" for i in range(len(bin_edges) - 1)]
    return {
        'available': True, 'column': column, 'n': int(series.count()),
        'bin_edges': [round(float(e), 4) for e in bin_edges],
        'bin_labels': bin_labels,
        'counts': [int(c) for c in counts],
    }


# ────────────────────────── Box Plot / Violin Plot ──────────────────────────

def _quartile_stats(series):
    """Tukey's 1.5*IQR box-plot convention: whiskers extend to the
    most extreme non-outlier value, everything beyond is listed as an
    individual outlier point rather than stretching the whisker."""
    q1, median, q3 = series.quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    lower_fence, upper_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    within_fence = series[(series >= lower_fence) & (series <= upper_fence)]
    outliers = series[(series < lower_fence) | (series > upper_fence)]
    return {
        'min': round(float(series.min()), 4), 'q1': round(float(q1), 4),
        'median': round(float(median), 4), 'q3': round(float(q3), 4),
        'max': round(float(series.max()), 4),
        'whisker_low': round(float(within_fence.min()), 4) if not within_fence.empty else round(float(series.min()), 4),
        'whisker_high': round(float(within_fence.max()), 4) if not within_fence.empty else round(float(series.max()), 4),
        'outliers': [round(float(o), 4) for o in outliers.tolist()][:50],
        'n': int(series.count()),
    }


def box_plot_data(df, column, group_by=None):
    """Box Plot: quartiles/whiskers/outliers for one numeric column,
    optionally split into one box per group of a categorical column.
    """
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return {'available': False, 'reason': f"'{column}' is not a numeric column in this dataset."}

    if group_by and group_by in df.columns:
        groups = []
        for group_value, group_df in df.groupby(group_by):
            series = group_df[column].dropna()
            if series.empty:
                continue
            groups.append({'group': str(group_value), **_quartile_stats(series)})
        if not groups:
            return {'available': False, 'reason': 'No groups with data.'}
        return {'available': True, 'column': column, 'group_by': group_by, 'groups': groups}

    series = df[column].dropna()
    if series.empty:
        return {'available': False, 'reason': f"'{column}' has no non-missing values."}
    return {'available': True, 'column': column, 'group_by': None, 'groups': [{'group': column, **_quartile_stats(series)}]}


def _kde_curve(series, num_points=50):
    """Gaussian KDE (Silverman's rule-of-thumb bandwidth) for a violin
    plot's density curve. Implemented directly with numpy instead of
    pulling in scipy just for gaussian_kde -- this project doesn't
    otherwise depend on scipy, and a plain Gaussian-kernel sum over a
    fixed grid is a handful of lines.
    """
    values = series.to_numpy(dtype=float)
    n = len(values)
    if n < 2:
        return [], []
    std = values.std(ddof=1)
    if std == 0:
        std = 1.0
    bandwidth = 1.06 * std * n ** (-1 / 5)
    if bandwidth <= 0:
        bandwidth = 1.0

    grid = np.linspace(values.min(), values.max(), num_points)
    diffs = (grid[:, None] - values[None, :]) / bandwidth
    density = np.exp(-0.5 * diffs ** 2).sum(axis=1) / (n * bandwidth * np.sqrt(2 * np.pi))
    return grid.tolist(), density.tolist()


def violin_plot_data(df, column, group_by=None, num_points=50):
    """Violin Plot: a kernel-density-estimated distribution curve per
    group (or one curve for the whole column), alongside the same
    quartile stats a box plot reports -- most violin renderers overlay
    both.
    """
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return {'available': False, 'reason': f"'{column}' is not a numeric column in this dataset."}

    def _violin_for(series, label):
        grid, density = _kde_curve(series, num_points)
        return {
            'group': label,
            'density_x': [round(g, 4) for g in grid],
            'density_y': [round(d, 6) for d in density],
            **_quartile_stats(series),
        }

    if group_by and group_by in df.columns:
        violins = []
        for group_value, group_df in df.groupby(group_by):
            series = group_df[column].dropna()
            if len(series) < 2:
                continue
            violins.append(_violin_for(series, str(group_value)))
        if not violins:
            return {'available': False, 'reason': 'No groups with at least 2 values.'}
        return {'available': True, 'column': column, 'group_by': group_by, 'violins': violins}

    series = df[column].dropna()
    if len(series) < 2:
        return {'available': False, 'reason': f"'{column}' needs at least 2 non-missing values for a density estimate."}
    return {'available': True, 'column': column, 'group_by': None, 'violins': [_violin_for(series, column)]}
