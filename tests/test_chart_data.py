"""Fast, pure-logic tests for services/chart_data.py (plain pandas
DataFrames in/out, no Flask/DB) -- same convention as
test_dataset_analysis.py.
"""
import numpy as np
import pandas as pd
from conftest import load_app_module

chart_data = load_app_module('app.services.chart_data')


def _sample_df():
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        'temperature_c': rng.uniform(-30, 30, 60),
        'degradation_pct': rng.uniform(0, 40, 60),
        'humidity': rng.uniform(20, 90, 60),
        'terrain': rng.choice(['flat', 'hilly', 'mountainous'], 60),
    })


# --- Heatmap / Correlation Matrix ---

def test_heatmap_data_returns_square_matrix():
    df = _sample_df()
    result = chart_data.heatmap_data(df)
    assert result['available'] is True
    n = len(result['labels'])
    assert len(result['cells']) == n * n


def test_heatmap_data_diagonal_is_self_correlation_one():
    df = _sample_df()
    result = chart_data.heatmap_data(df)
    diag_cells = [c for c in result['cells'] if c['x'] == c['y']]
    assert all(abs(c['value'] - 1.0) < 1e-9 for c in diag_cells)


def test_heatmap_data_insufficient_numeric_columns():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
    result = chart_data.heatmap_data(df)
    assert result['available'] is False


def test_heatmap_data_respects_column_subset():
    df = _sample_df()
    result = chart_data.heatmap_data(df, columns=['temperature_c', 'degradation_pct'])
    assert set(result['labels']) == {'temperature_c', 'degradation_pct'}


# --- Scatter Plot ---

def test_scatter_data_basic():
    df = _sample_df()
    result = chart_data.scatter_data(df, 'temperature_c', 'degradation_pct')
    assert result['available'] is True
    assert result['n_points'] == 60
    assert result['correlation'] is not None


def test_scatter_data_missing_column():
    df = _sample_df()
    result = chart_data.scatter_data(df, 'temperature_c', 'nonexistent')
    assert result['available'] is False


def test_scatter_data_with_group_color():
    df = _sample_df()
    result = chart_data.scatter_data(df, 'temperature_c', 'degradation_pct', color_col='terrain')
    assert result['color_col'] == 'terrain'
    assert all(p['group'] in ('flat', 'hilly', 'mountainous') for p in result['points'])


def test_scatter_data_samples_down_to_max_points():
    df = pd.DataFrame({'x': range(5010), 'y': range(5010)})
    result = chart_data.scatter_data(df, 'x', 'y', max_points=100)
    assert result['n_points'] == 100


def test_scatter_data_empty_after_dropna():
    df = pd.DataFrame({'x': [1.0, np.nan], 'y': [np.nan, 2.0]})
    result = chart_data.scatter_data(df, 'x', 'y')
    assert result['available'] is False


# --- Histogram ---

def test_histogram_data_basic():
    df = _sample_df()
    result = chart_data.histogram_data(df, 'temperature_c', num_bins=8)
    assert result['available'] is True
    assert len(result['counts']) <= 8
    assert sum(result['counts']) == 60


def test_histogram_data_non_numeric_column():
    df = _sample_df()
    result = chart_data.histogram_data(df, 'terrain')
    assert result['available'] is False


def test_histogram_data_unknown_column():
    df = _sample_df()
    result = chart_data.histogram_data(df, 'nonexistent')
    assert result['available'] is False


# --- Box Plot ---

def test_box_plot_data_single_group():
    df = pd.DataFrame({'x': [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]})  # 100 is an outlier
    result = chart_data.box_plot_data(df, 'x')
    assert result['available'] is True
    group = result['groups'][0]
    assert 100 in group['outliers']
    assert group['whisker_high'] < 100


def test_box_plot_data_grouped():
    df = pd.DataFrame({'value': [1, 2, 3, 10, 11, 12], 'category': ['a', 'a', 'a', 'b', 'b', 'b']})
    result = chart_data.box_plot_data(df, 'value', group_by='category')
    assert result['available'] is True
    assert len(result['groups']) == 2
    a_group = next(g for g in result['groups'] if g['group'] == 'a')
    assert a_group['median'] == 2


def test_box_plot_data_no_outliers_when_data_is_uniform():
    df = pd.DataFrame({'x': [5, 5, 5, 5, 5]})
    result = chart_data.box_plot_data(df, 'x')
    assert result['groups'][0]['outliers'] == []


def test_box_plot_data_non_numeric_column():
    df = pd.DataFrame({'x': ['a', 'b', 'c']})
    result = chart_data.box_plot_data(df, 'x')
    assert result['available'] is False


# --- Violin Plot ---

def test_violin_plot_data_basic():
    df = pd.DataFrame({'x': list(range(30))})
    result = chart_data.violin_plot_data(df, 'x', num_points=20)
    assert result['available'] is True
    violin = result['violins'][0]
    assert len(violin['density_x']) == 20
    assert len(violin['density_y']) == 20
    assert all(d >= 0 for d in violin['density_y'])  # density is never negative


def test_violin_plot_data_grouped():
    df = pd.DataFrame({'value': [1, 2, 3, 4, 10, 11, 12, 13], 'category': ['a'] * 4 + ['b'] * 4})
    result = chart_data.violin_plot_data(df, 'value', group_by='category')
    assert result['available'] is True
    assert len(result['violins']) == 2


def test_violin_plot_data_insufficient_points():
    df = pd.DataFrame({'x': [1.0]})
    result = chart_data.violin_plot_data(df, 'x')
    assert result['available'] is False


def test_violin_plot_data_density_integrates_to_roughly_one():
    """Sanity check the KDE math: integrating the density curve over
    its support should be close to 1.0 (it's a probability density)."""
    df = pd.DataFrame({'x': np.random.default_rng(1).normal(0, 1, 200)})
    result = chart_data.violin_plot_data(df, 'x', num_points=200)
    violin = result['violins'][0]
    xs, ys = violin['density_x'], violin['density_y']
    integral = np.trapezoid(ys, xs) if hasattr(np, 'trapezoid') else np.trapz(ys, xs)
    assert 0.7 < integral < 1.3  # loose bound -- grid is clipped to data range, not full support
