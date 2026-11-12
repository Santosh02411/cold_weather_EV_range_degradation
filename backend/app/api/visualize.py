"""Data Visualization API: Heatmaps, Correlation Matrix, Scatter Plot,
Histogram, Box Plot, and Violin Plot over an uploaded Dataset (see
services/chart_data.py); Line Charts, Geographic Weather Map, Battery
Performance Charts, and Prediction Timeline over the user's own app
data (see services/app_chart_data.py).
"""
import pandas as pd
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from ..models.dataset import Dataset
from ..models.ev_vehicle import EVVehicle
from ..services import chart_data
from ..services import app_chart_data

visualize_bp = Blueprint('visualize', __name__)


def _load_dataset_df(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    if dataset.filepath.endswith('.csv'):
        return pd.read_csv(dataset.filepath)
    if dataset.filepath.endswith('.xlsx'):
        return pd.read_excel(dataset.filepath)
    return pd.read_json(dataset.filepath)


@visualize_bp.route('/')
@login_required
def index():
    datasets = Dataset.query.order_by(Dataset.created_at.desc()).all()
    vehicles = EVVehicle.query.filter_by(is_active=True).all()
    return render_template('visualize/index.html', datasets=datasets, vehicles=vehicles,
                            line_chart_fields=app_chart_data.LINE_CHART_FIELDS)


# ─────────────────── Dataset-based visualizations ───────────────────

@visualize_bp.route('/api/dataset/<int:dataset_id>/columns')
@login_required
def dataset_columns(dataset_id):
    df = _load_dataset_df(dataset_id)
    return jsonify({
        'numeric': df.select_dtypes(include='number').columns.tolist(),
        'categorical': df.select_dtypes(exclude='number').columns.tolist(),
    })


@visualize_bp.route('/api/dataset/<int:dataset_id>/heatmap')
@login_required
def heatmap(dataset_id):
    """Heatmaps / Correlation Matrix."""
    df = _load_dataset_df(dataset_id)
    return jsonify(chart_data.heatmap_data(df))


@visualize_bp.route('/api/dataset/<int:dataset_id>/scatter')
@login_required
def scatter(dataset_id):
    """Scatter Plot. ?x=col&y=col&color=col (color optional)."""
    x_col, y_col = request.args.get('x'), request.args.get('y')
    if not x_col or not y_col:
        return jsonify({'error': "'x' and 'y' query params are required"}), 400
    df = _load_dataset_df(dataset_id)
    return jsonify(chart_data.scatter_data(df, x_col, y_col, color_col=request.args.get('color')))


@visualize_bp.route('/api/dataset/<int:dataset_id>/histogram')
@login_required
def histogram(dataset_id):
    """Histogram. ?column=col&bins=10."""
    column = request.args.get('column')
    if not column:
        return jsonify({'error': "'column' query param is required"}), 400
    df = _load_dataset_df(dataset_id)
    return jsonify(chart_data.histogram_data(df, column, num_bins=request.args.get('bins', 10, type=int)))


@visualize_bp.route('/api/dataset/<int:dataset_id>/boxplot')
@login_required
def boxplot(dataset_id):
    """Box Plot. ?column=col&group_by=col (group_by optional)."""
    column = request.args.get('column')
    if not column:
        return jsonify({'error': "'column' query param is required"}), 400
    df = _load_dataset_df(dataset_id)
    return jsonify(chart_data.box_plot_data(df, column, group_by=request.args.get('group_by')))


@visualize_bp.route('/api/dataset/<int:dataset_id>/violin')
@login_required
def violin(dataset_id):
    """Violin Plot. ?column=col&group_by=col (group_by optional)."""
    column = request.args.get('column')
    if not column:
        return jsonify({'error': "'column' query param is required"}), 400
    df = _load_dataset_df(dataset_id)
    return jsonify(chart_data.violin_plot_data(df, column, group_by=request.args.get('group_by')))


# ─────────────────────── App-data visualizations ───────────────────────

@visualize_bp.route('/api/line-chart')
@login_required
def line_chart():
    """Line Charts over the user's own prediction history."""
    field = request.args.get('field', 'range_degradation_pct')
    return jsonify(app_chart_data.line_chart_data(current_user.id, field))


@visualize_bp.route('/api/weather-map')
@login_required
def weather_map():
    """Geographic Weather Map."""
    return jsonify(app_chart_data.geographic_weather_map_data(provider_config=current_app.config))


@visualize_bp.route('/api/battery-performance')
@login_required
def battery_performance():
    """Battery Performance Charts. ?vehicle_id=N (optional)."""
    vehicle_id = request.args.get('vehicle_id', type=int)
    return jsonify(app_chart_data.battery_performance_chart_data(current_user.id, vehicle_id=vehicle_id))


@visualize_bp.route('/api/prediction-timeline')
@login_required
def prediction_timeline():
    """Prediction Timeline."""
    return jsonify(app_chart_data.prediction_timeline_data(current_user.id))
