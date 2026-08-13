"""Flask + DB integration tests for the Data Visualization API
endpoints (api/visualize.py). Same skip-if-flask_sqlalchemy-missing
convention as the other DB-backed test files. Uploads a real CSV
through the datasets upload endpoint (same as test_datasets_api.py)
so dataset-based visualization endpoints have real data to operate on.
"""
import io
import pytest
from datetime import datetime, timedelta

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.ev_vehicle import EVVehicle
from app.models.prediction import Prediction


@pytest.fixture
def app(tmp_path):
    app = create_app('testing')
    app.config['UPLOAD_FOLDER'] = str(tmp_path / 'uploads')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    with app.app_context():
        user = User(username='vizapiuser', email='vizapiuser@example.com')
        user.set_password('pass12345')
        vehicle = EVVehicle(
            model_name='Test Model', manufacturer='TestCo', battery_capacity_kwh=75,
            epa_range_km=400, vehicle_weight_kg=1900, battery_chemistry='NMC',
            charging_type='CCS', max_charging_power_kw=150, drivetrain='AWD', year=2024,
        )
        db.session.add_all([user, vehicle])
        db.session.commit()
    client.post('/login', data={'username': 'vizapiuser', 'password': 'pass12345'})
    return client


_SAMPLE_CSV = (
    "temperature_c,humidity,terrain,degradation_pct\n"
    "-20,80,flat,35\n-10,70,hilly,28\n0,60,flat,20\n10,50,mountainous,12\n"
    "20,40,flat,5\n-5,65,hilly,25\n-25,85,mountainous,38\n5,55,flat,10\n"
)


def _upload_sample(auth_client):
    data = {
        'name': 'Viz Test Dataset',
        'file': (io.BytesIO(_SAMPLE_CSV.encode('utf-8')), 'sample.csv'),
    }
    resp = auth_client.post('/datasets/api/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()['dataset']['id']


def test_visualize_page_requires_login(client):
    resp = client.get('/visualize/')
    assert resp.status_code in (302, 401)


def test_visualize_page_loads(auth_client):
    resp = auth_client.get('/visualize/')
    assert resp.status_code == 200


def test_dataset_columns_endpoint(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/visualize/api/dataset/{dataset_id}/columns')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'temperature_c' in data['numeric']
    assert 'terrain' in data['categorical']


def test_heatmap_endpoint(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/visualize/api/dataset/{dataset_id}/heatmap')
    assert resp.status_code == 200
    assert resp.get_json()['available'] is True


def test_scatter_endpoint_requires_x_and_y(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/visualize/api/dataset/{dataset_id}/scatter?x=temperature_c')
    assert resp.status_code == 400


def test_scatter_endpoint_success(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/visualize/api/dataset/{dataset_id}/scatter?x=temperature_c&y=degradation_pct')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is True
    assert data['n_points'] == 8


def test_scatter_endpoint_with_grouping(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/visualize/api/dataset/{dataset_id}/scatter?x=temperature_c&y=degradation_pct&color=terrain')
    assert resp.status_code == 200
    assert resp.get_json()['color_col'] == 'terrain'


def test_histogram_endpoint_requires_column(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/visualize/api/dataset/{dataset_id}/histogram')
    assert resp.status_code == 400


def test_histogram_endpoint_success(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/visualize/api/dataset/{dataset_id}/histogram?column=temperature_c&bins=4')
    assert resp.status_code == 200
    assert resp.get_json()['available'] is True


def test_boxplot_endpoint_ungrouped(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/visualize/api/dataset/{dataset_id}/boxplot?column=degradation_pct')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is True
    assert len(data['groups']) == 1


def test_boxplot_endpoint_grouped(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/visualize/api/dataset/{dataset_id}/boxplot?column=degradation_pct&group_by=terrain')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['groups']) == 3  # flat, hilly, mountainous


def test_violin_endpoint_success(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/visualize/api/dataset/{dataset_id}/violin?column=degradation_pct')
    assert resp.status_code == 200
    assert resp.get_json()['available'] is True


def test_dataset_endpoints_404_for_unknown_dataset(auth_client):
    resp = auth_client.get('/visualize/api/dataset/99999/heatmap')
    assert resp.status_code == 404


def test_line_chart_endpoint_no_data(auth_client):
    resp = auth_client.get('/visualize/api/line-chart?field=range_degradation_pct')
    assert resp.status_code == 200
    assert resp.get_json()['available'] is False


def test_line_chart_endpoint_with_data(auth_client, app):
    with app.app_context():
        user = User.query.filter_by(username='vizapiuser').first()
        vehicle = EVVehicle.query.first()
        db.session.add(Prediction(
            user_id=user.id, vehicle_id=vehicle.id, temperature_c=-10, humidity=50,
            wind_speed_kmh=10, precipitation='none', battery_percentage=80,
            vehicle_speed_kmh=70, hvac_usage=True, terrain_type='flat', battery_age_years=1,
            range_degradation_pct=22.0, predicted_range_km=300, ml_model_used='random_forest',
        ))
        db.session.commit()

    resp = auth_client.get('/visualize/api/line-chart?field=range_degradation_pct')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['available'] is True
    assert len(data['points']) == 1


def test_prediction_timeline_endpoint(auth_client):
    resp = auth_client.get('/visualize/api/prediction-timeline')
    assert resp.status_code == 200
    assert resp.get_json()['available'] is False  # no predictions yet


def test_battery_performance_endpoint_no_data(auth_client):
    resp = auth_client.get('/visualize/api/battery-performance')
    assert resp.status_code == 200
    assert resp.get_json()['available'] is False


def test_weather_map_endpoint_no_data(auth_client):
    resp = auth_client.get('/visualize/api/weather-map')
    assert resp.status_code == 200
    assert resp.get_json()['available'] is False
