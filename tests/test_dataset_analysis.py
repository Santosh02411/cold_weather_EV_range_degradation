"""Fast, pure-logic tests for services/dataset_analysis.py (plain
pandas DataFrames in/out, no Flask/DB) -- same convention as
test_trip_planning_services.py and test_charging_management_services.py.
"""
import numpy as np
import pandas as pd
from conftest import load_app_module

da = load_app_module('app.services.dataset_analysis')


def _sample_df():
    return pd.DataFrame({
        'temperature_c': [-20.0, -10.0, 0.0, 10.0, 20.0, np.nan, -20.0, -10.0],
        'humidity': [80, 70, 60, 50, 40, 30, 80, 70],
        'terrain': ['flat', 'hilly', 'flat', 'mountainous', 'flat', 'hilly', 'flat', 'hilly'],
        'degradation_pct': [35, 28, 20, 12, 5, 30, 35, 28],
    })


# --- Missing Value Detection ---

def test_detect_missing_values_counts_correctly():
    result = da.detect_missing_values(_sample_df())
    temp_col = next(c for c in result['columns'] if c['column'] == 'temperature_c')
    assert temp_col['missing_count'] == 1
    assert result['total_missing_cells'] == 1
    assert result['columns_with_missing'] == 1


def test_detect_missing_values_no_missing_data():
    df = pd.DataFrame({'a': [1, 2, 3]})
    result = da.detect_missing_values(df)
    assert result['total_missing_cells'] == 0
    assert result['columns_with_missing'] == 0


def test_detect_missing_values_reports_row_indices_for_small_gaps():
    result = da.detect_missing_values(_sample_df())
    temp_col = next(c for c in result['columns'] if c['column'] == 'temperature_c')
    assert temp_col['missing_row_indices'] == [5]


# --- Duplicate Detection ---

def test_detect_duplicates_finds_exact_dupes():
    result = da.detect_duplicates(_sample_df())
    assert result['duplicate_row_count'] == 2  # rows 6,7 duplicate rows 0,1
    assert result['unique_row_count'] == 6


def test_detect_duplicates_no_dupes():
    df = pd.DataFrame({'a': [1, 2, 3]})
    result = da.detect_duplicates(df)
    assert result['duplicate_row_count'] == 0


def test_remove_duplicates_matches_detect_duplicates_count():
    df = _sample_df()
    detected = da.detect_duplicates(df)
    deduped, removed = da.remove_duplicates(df)
    assert removed == detected['duplicate_row_count']
    assert len(deduped) == detected['unique_row_count']


def test_detect_duplicates_with_subset():
    df = pd.DataFrame({'a': [1, 1, 2], 'b': [10, 20, 30]})
    full = da.detect_duplicates(df)
    subset = da.detect_duplicates(df, subset=['a'])
    assert full['duplicate_row_count'] == 0  # b differs, so no full-row dupes
    assert subset['duplicate_row_count'] == 1  # a=1 appears twice


# --- Correlation Analysis ---

def test_analyze_correlations_finds_strong_pair():
    df = _sample_df()
    result = da.analyze_correlations(df, threshold=0.7)
    assert result['available'] is True
    pair_features = {(p['feature_a'], p['feature_b']) for p in result['strong_pairs']}
    assert ('temperature_c', 'degradation_pct') in pair_features or ('degradation_pct', 'temperature_c') in pair_features


def test_analyze_correlations_insufficient_numeric_columns():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
    result = da.analyze_correlations(df)
    assert result['available'] is False


def test_analyze_correlations_matrix_is_symmetric():
    df = _sample_df()
    result = da.analyze_correlations(df, threshold=0.99)
    assert result['matrix']['humidity']['degradation_pct'] == result['matrix']['degradation_pct']['humidity']


# --- Feature Distribution Analysis ---

def test_analyze_feature_distributions_numeric_stats():
    result = da.analyze_feature_distributions(_sample_df())
    humidity = result['numeric']['humidity']
    assert humidity['min'] == 30
    assert humidity['max'] == 80
    assert humidity['count'] == 8


def test_analyze_feature_distributions_categorical_value_counts():
    result = da.analyze_feature_distributions(_sample_df())
    terrain = result['categorical']['terrain']
    assert terrain['unique_values'] == 3
    top = {v['value']: v['count'] for v in terrain['top_values']}
    assert top['flat'] == 4


def test_analyze_feature_distributions_histogram_present():
    result = da.analyze_feature_distributions(_sample_df())
    hist = result['numeric']['temperature_c']['histogram']
    assert sum(hist['counts']) == 7  # excludes the 1 NaN


# --- Data Validation ---

def test_validate_dataset_empty_df():
    result = da.validate_dataset(pd.DataFrame())
    assert result['valid'] is False
    assert any(i['severity'] == 'error' for i in result['issues'])


def test_validate_dataset_missing_required_column():
    df = pd.DataFrame({'a': [1, 2]})
    result = da.validate_dataset(df, schema={'required_columns': ['a', 'b']})
    assert result['valid'] is False
    assert any("'b'" in i['message'] for i in result['issues'])


def test_validate_dataset_type_mismatch():
    df = pd.DataFrame({'temperature_c': ['cold', 'warm']})
    result = da.validate_dataset(df, schema={'column_types': {'temperature_c': 'numeric'}})
    assert result['valid'] is False


def test_validate_dataset_range_violation_is_warning_not_error():
    df = pd.DataFrame({'temperature_c': [-100, 20, 30]})
    result = da.validate_dataset(df, schema={'column_ranges': {'temperature_c': {'min': -60, 'max': 60}}})
    assert result['valid'] is True  # warnings don't fail validity
    assert any(i['severity'] == 'warning' for i in result['issues'])


def test_validate_dataset_flags_constant_column():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [5, 5, 5]})
    result = da.validate_dataset(df)
    assert any('only one distinct value' in i['message'] for i in result['issues'])


def test_validate_dataset_flags_fully_empty_column():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [None, None, None]})
    result = da.validate_dataset(df)
    assert any('entirely missing' in i['message'] for i in result['issues'])


def test_validate_dataset_no_schema_no_issues_on_clean_data():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    result = da.validate_dataset(df)
    assert result['valid'] is True
    assert result['issues'] == []


# --- Feature Scaling ---

def test_scale_features_standard_zero_mean():
    df = pd.DataFrame({'x': [10.0, 20.0, 30.0, 40.0, 50.0]})
    scaled_df, params = da.scale_features(df, method='standard')
    assert abs(scaled_df['x'].mean()) < 1e-9
    assert params['method'] == 'standard'
    assert 'mean' in params['columns']['x']


def test_scale_features_minmax_bounds():
    df = pd.DataFrame({'x': [10.0, 20.0, 30.0, 40.0, 50.0]})
    scaled_df, params = da.scale_features(df, method='minmax')
    assert scaled_df['x'].min() == 0.0
    assert scaled_df['x'].max() == 1.0


def test_scale_features_only_touches_specified_columns():
    df = pd.DataFrame({'x': [1.0, 2.0, 3.0], 'y': [100.0, 200.0, 300.0]})
    scaled_df, params = da.scale_features(df, columns=['x'], method='standard')
    assert list(params['columns'].keys()) == ['x']
    assert scaled_df['y'].tolist() == [100.0, 200.0, 300.0]  # untouched


def test_scale_features_invalid_method_raises():
    df = pd.DataFrame({'x': [1.0, 2.0]})
    try:
        da.scale_features(df, method='bogus')
        assert False, "should have raised"
    except ValueError:
        pass


def test_scale_features_no_numeric_columns_is_noop():
    df = pd.DataFrame({'a': ['x', 'y']})
    scaled_df, params = da.scale_features(df)
    assert params['columns'] == {}


# --- Encoding ---

def test_encode_features_onehot_creates_dummy_columns():
    df = pd.DataFrame({'terrain': ['flat', 'hilly', 'flat']})
    encoded_df, mapping = da.encode_features(df, method='onehot')
    assert 'terrain_flat' in encoded_df.columns
    assert 'terrain_hilly' in encoded_df.columns
    assert mapping['columns']['terrain'] == ['terrain_flat', 'terrain_hilly']


def test_encode_features_label_assigns_integer_codes():
    df = pd.DataFrame({'terrain': ['flat', 'hilly', 'flat']})
    encoded_df, mapping = da.encode_features(df, method='label')
    assert set(encoded_df['terrain'].unique()) == {0, 1}
    assert mapping['columns']['terrain']['flat'] in (0, 1)


def test_encode_features_invalid_method_raises():
    df = pd.DataFrame({'a': ['x']})
    try:
        da.encode_features(df, method='bogus')
        assert False, "should have raised"
    except ValueError:
        pass


def test_encode_features_no_categorical_columns_is_noop():
    df = pd.DataFrame({'a': [1, 2, 3]})
    encoded_df, mapping = da.encode_features(df)
    assert mapping['columns'] == {}


# --- Train/Test Split ---

def test_train_test_split_summary_proportions():
    df = pd.DataFrame({'x': range(100)})
    splits, summary = da.train_test_split_summary(df, test_size=0.2)
    assert summary['splits']['train']['rows'] == 80
    assert summary['splits']['test']['rows'] == 20
    assert len(splits['train']) + len(splits['test']) == 100


def test_train_test_split_summary_with_validation():
    df = pd.DataFrame({'x': range(100)})
    splits, summary = da.train_test_split_summary(df, test_size=0.2, val_size=0.1)
    assert 'val' in splits
    assert len(splits['train']) + len(splits['test']) + len(splits['val']) == 100
    # val should be roughly 10% of the total
    assert 5 <= len(splits['val']) <= 15


def test_train_test_split_summary_invalid_test_size_raises():
    df = pd.DataFrame({'x': range(10)})
    try:
        da.train_test_split_summary(df, test_size=1.5)
        assert False, "should have raised"
    except ValueError:
        pass


def test_train_test_split_summary_no_overlap_between_splits():
    df = pd.DataFrame({'x': range(50)})
    splits, _ = da.train_test_split_summary(df, test_size=0.3, random_state=1)
    train_values = set(splits['train']['x'])
    test_values = set(splits['test']['x'])
    assert train_values.isdisjoint(test_values)
