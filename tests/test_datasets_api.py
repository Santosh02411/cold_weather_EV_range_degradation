"""Flask + DB integration tests for the Dataset Management API:
upload, the analysis endpoints (missing values, duplicates,
correlations, distributions, validate), the versioned transformation
endpoints (dedupe, scale, encode, split), and Dataset Versioning
listing. Same skip-if-flask_sqlalchemy-missing convention as the other
DB-backed test files.
"""
import io
import pytest

flask_sqlalchemy = pytest.importorskip("flask_sqlalchemy", reason="flask_sqlalchemy not installed in this environment")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db
from app.models.user import User


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
        user = User(username='datauser', email='datauser@example.com')
        user.set_password('pass12345')
        db.session.add(user)
        db.session.commit()
    client.post('/login', data={'username': 'datauser', 'password': 'pass12345'})
    return client


_SAMPLE_CSV = (
    "temperature_c,humidity,terrain,degradation_pct\n"
    "-20,80,flat,35\n"
    "-10,70,hilly,28\n"
    "0,60,flat,20\n"
    "10,50,mountainous,12\n"
    "20,40,flat,5\n"
    ",30,hilly,30\n"
    "-20,80,flat,35\n"
    "-10,70,hilly,28\n"
)


def _upload_sample(auth_client):
    data = {
        'name': 'Test Dataset',
        'description': 'A sample dataset for testing',
        'file': (io.BytesIO(_SAMPLE_CSV.encode('utf-8')), 'sample.csv'),
    }
    resp = auth_client.post('/datasets/api/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()['dataset']['id']


def test_datasets_page_requires_login(client):
    resp = client.get('/datasets/')
    assert resp.status_code in (302, 401)


def test_datasets_page_loads(auth_client):
    resp = auth_client.get('/datasets/')
    assert resp.status_code == 200


def test_upload_rejects_bad_extension(auth_client):
    data = {'file': (io.BytesIO(b'not a real file'), 'sample.exe')}
    resp = auth_client.post('/datasets/api/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400


def test_upload_and_analyze_success(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/datasets/api/{dataset_id}')
    assert resp.status_code == 200
    assert resp.get_json()['num_rows'] == 8


def test_missing_values_endpoint(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/datasets/api/{dataset_id}/missing-values')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total_missing_cells'] == 1
    temp_col = next(c for c in data['columns'] if c['column'] == 'temperature_c')
    assert temp_col['missing_count'] == 1


def test_duplicates_endpoint(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/datasets/api/{dataset_id}/duplicates')
    assert resp.status_code == 200
    assert resp.get_json()['duplicate_row_count'] == 2


def test_duplicates_endpoint_with_column_subset(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/datasets/api/{dataset_id}/duplicates?columns=terrain')
    assert resp.status_code == 200
    # terrain has only 3 distinct values across 8 rows -- lots of "duplicates" by this narrow definition
    assert resp.get_json()['duplicate_row_count'] >= 2


def test_correlations_endpoint(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/datasets/api/{dataset_id}/correlations')
    assert resp.status_code == 200
    assert resp.get_json()['available'] is True


def test_distributions_endpoint(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.get(f'/datasets/api/{dataset_id}/distributions')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'temperature_c' in data['numeric']
    assert 'terrain' in data['categorical']


def test_validate_endpoint_with_schema(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.post(f'/datasets/api/{dataset_id}/validate', json={
        'required_columns': ['temperature_c', 'nonexistent_col'],
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['valid'] is False


def test_validate_endpoint_no_body(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.post(f'/datasets/api/{dataset_id}/validate')
    assert resp.status_code == 200


def test_dedupe_creates_new_version(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.post(f'/datasets/api/{dataset_id}/dedupe', json={})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['removed'] == 2
    assert data['version']['version_num'] == 1
    assert data['version']['num_rows'] == 6


def test_scale_creates_new_version(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.post(f'/datasets/api/{dataset_id}/scale', json={'method': 'standard'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'temperature_c' in data['scaling_params']['columns']


def test_scale_invalid_method_400s(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.post(f'/datasets/api/{dataset_id}/scale', json={'method': 'bogus'})
    assert resp.status_code == 400


def test_encode_creates_new_version(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.post(f'/datasets/api/{dataset_id}/encode', json={'method': 'onehot'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'terrain' in data['encoding']['columns']


def test_split_creates_multiple_versions(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.post(f'/datasets/api/{dataset_id}/split', json={'test_size': 0.25})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'train' in data['versions']
    assert 'test' in data['versions']
    assert data['summary']['splits']['train']['rows'] + data['summary']['splits']['test']['rows'] == 8


def test_split_invalid_test_size_400s(auth_client):
    dataset_id = _upload_sample(auth_client)
    resp = auth_client.post(f'/datasets/api/{dataset_id}/split', json={'test_size': 1.5})
    assert resp.status_code == 400


def test_transformation_chain_scale_then_split_via_version_id(auth_client):
    """Dataset Versioning: a transformation can chain off a PREVIOUS
    version instead of the raw original, and the resulting version
    correctly records that lineage via parent_version_id."""
    dataset_id = _upload_sample(auth_client)
    scale_resp = auth_client.post(f'/datasets/api/{dataset_id}/scale', json={'method': 'standard'})
    scaled_version_id = scale_resp.get_json()['version']['id']

    split_resp = auth_client.post(f'/datasets/api/{dataset_id}/split', json={
        'test_size': 0.25, 'version_id': scaled_version_id,
    })
    assert split_resp.status_code == 200
    train_version_id = split_resp.get_json()['versions']['train']['id']

    detail_resp = auth_client.get(f'/datasets/api/versions/{train_version_id}')
    assert detail_resp.get_json()['parent_version_id'] == scaled_version_id


def test_list_versions_after_transformations(auth_client):
    dataset_id = _upload_sample(auth_client)
    auth_client.post(f'/datasets/api/{dataset_id}/dedupe', json={})
    auth_client.post(f'/datasets/api/{dataset_id}/scale', json={'method': 'minmax'})

    resp = auth_client.get(f'/datasets/api/{dataset_id}/versions')
    assert resp.status_code == 200
    versions = resp.get_json()
    assert len(versions) == 2
    assert {v['transformation'] for v in versions} == {'dedupe', 'scale'}


def test_version_preview_endpoint(auth_client):
    dataset_id = _upload_sample(auth_client)
    dedupe_resp = auth_client.post(f'/datasets/api/{dataset_id}/dedupe', json={})
    version_id = dedupe_resp.get_json()['version']['id']

    resp = auth_client.get(f'/datasets/api/versions/{version_id}/preview')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['preview']) == 6


def test_delete_dataset_also_removes_versions(auth_client, app):
    dataset_id = _upload_sample(auth_client)
    auth_client.post(f'/datasets/api/{dataset_id}/dedupe', json={})

    resp = auth_client.post(f'/datasets/api/delete/{dataset_id}')
    assert resp.status_code == 200

    with app.app_context():
        from app.models.dataset import DatasetVersion
        assert DatasetVersion.query.filter_by(dataset_id=dataset_id).count() == 0


def test_unknown_dataset_404s(auth_client):
    resp = auth_client.get('/datasets/api/99999/missing-values')
    assert resp.status_code == 404


def test_unknown_version_404s(auth_client):
    resp = auth_client.get('/datasets/api/versions/99999')
    assert resp.status_code == 404
