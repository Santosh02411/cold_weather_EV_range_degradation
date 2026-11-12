import os, json
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pandas as pd
from ..models.dataset import Dataset, DatasetVersion
from .. import db
from ..services import dataset_analysis as da

datasets_bp = Blueprint('datasets', __name__)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'json'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _read_dataframe(filepath):
    if filepath.endswith('.csv'):
        return pd.read_csv(filepath)
    if filepath.endswith('.xlsx'):
        return pd.read_excel(filepath)
    return pd.read_json(filepath)


def _load_dataset_df(dataset_id):
    """Load a Dataset's CURRENT (original, unversioned) file. Version-
    specific loading is _load_version_df() below -- most analysis
    endpoints operate on the original upload unless a version_id is
    explicitly given, since that's almost always what "analyze this
    dataset" means."""
    dataset = Dataset.query.get_or_404(dataset_id)
    return dataset, _read_dataframe(dataset.filepath)


def _load_version_df(version_id):
    version = DatasetVersion.query.get_or_404(version_id)
    return version, _read_dataframe(version.filepath)


def _versions_dir(dataset_id):
    base = current_app.config.get('UPLOAD_FOLDER', 'data/uploads')
    path = os.path.join(base, 'versions', str(dataset_id))
    os.makedirs(path, exist_ok=True)
    return path


def _save_version(dataset_id, df, transformation, params, parent_version_id=None):
    """Dataset Versioning: persist `df` as a new, numbered
    DatasetVersion row + CSV file on disk, linked to its parent
    version (or the original dataset if this is the first
    transformation) -- see models/dataset.py's DatasetVersion
    docstring for why this never overwrites in place.
    """
    existing = DatasetVersion.query.filter_by(dataset_id=dataset_id).count()
    version_num = existing + 1
    filepath = os.path.join(_versions_dir(dataset_id), f'v{version_num}_{transformation}.csv')
    df.to_csv(filepath, index=False)

    version = DatasetVersion(
        dataset_id=dataset_id, parent_version_id=parent_version_id,
        version_num=version_num, transformation=transformation,
        transformation_params=json.dumps(params, default=str),
        filepath=filepath, num_rows=len(df), num_columns=len(df.columns),
        created_by=current_user.id,
    )
    db.session.add(version)
    db.session.commit()
    return version


@datasets_bp.route('/')
@login_required
def index():
    datasets = Dataset.query.order_by(Dataset.created_at.desc()).all()
    return render_template('datasets/index.html', datasets=datasets)


@datasets_bp.route('/api/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Use CSV, XLSX, or JSON.'}), 400

    filename = secure_filename(file.filename)
    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'data/uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    try:
        df = _read_dataframe(filepath)

        dataset = Dataset(
            name=request.form.get('name', filename),
            filename=filename, filepath=filepath,
            file_size=os.path.getsize(filepath),
            num_rows=len(df), num_columns=len(df.columns),
            columns=json.dumps(list(df.columns)),
            description=request.form.get('description', ''),
            uploaded_by=current_user.id,
        )
        db.session.add(dataset)
        db.session.commit()

        return jsonify({
            'dataset': dataset.to_dict(),
            'preview': df.head(10).to_dict(orient='records'),
            'stats': {
                'missing_values': df.isnull().sum().to_dict(),
                'dtypes': {col: str(dt) for col, dt in df.dtypes.items()},
            }
        })
    except Exception as e:
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500


@datasets_bp.route('/api/preprocess/<int:dataset_id>', methods=['POST'])
@login_required
def preprocess(dataset_id):
    """Legacy one-shot cleanup (missing-value imputation + IQR outlier
    removal), kept for backward compatibility -- overwrites the
    dataset's own file in place. For anything more granular (just
    dedupe, just scaling, just encoding) or that should be versioned
    rather than overwritten, use the dedicated endpoints below instead.
    """
    dataset = Dataset.query.get_or_404(dataset_id)
    try:
        df = pd.read_csv(dataset.filepath)
        original_rows = len(df)
        df = df.dropna(thresh=len(df.columns) * 0.5)
        for col in df.select_dtypes(include='number').columns:
            df[col] = df[col].fillna(df[col].median())
        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'unknown')
        for col in df.select_dtypes(include='number').columns:
            Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            IQR = Q3 - Q1
            df = df[(df[col] >= Q1 - 3 * IQR) & (df[col] <= Q3 + 3 * IQR)]

        df.to_csv(dataset.filepath, index=False)
        dataset.num_rows = len(df)
        dataset.is_processed = True
        db.session.commit()

        return jsonify({
            'message': 'Preprocessing complete',
            'original_rows': original_rows,
            'cleaned_rows': len(df),
            'removed': original_rows - len(df),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@datasets_bp.route('/api/<int:dataset_id>')
@login_required
def detail(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    return jsonify(dataset.to_dict())


@datasets_bp.route('/api/delete/<int:dataset_id>', methods=['POST'])
@login_required
def delete(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    if os.path.exists(dataset.filepath):
        os.remove(dataset.filepath)
    for version in DatasetVersion.query.filter_by(dataset_id=dataset_id).all():
        if os.path.exists(version.filepath):
            os.remove(version.filepath)
        db.session.delete(version)
    db.session.delete(dataset)
    db.session.commit()
    return jsonify({'message': 'Dataset deleted'})


# ─────────────────────────── Analysis endpoints ───────────────────────────

@datasets_bp.route('/api/<int:dataset_id>/missing-values')
@login_required
def missing_values(dataset_id):
    """Missing Value Detection."""
    _, df = _load_dataset_df(dataset_id)
    return jsonify(da.detect_missing_values(df))


@datasets_bp.route('/api/<int:dataset_id>/duplicates')
@login_required
def duplicates(dataset_id):
    """Duplicate Detection. `?columns=a,b,c` restricts comparison to a
    subset of columns instead of requiring every column to match."""
    _, df = _load_dataset_df(dataset_id)
    subset = request.args.get('columns')
    subset_cols = [c.strip() for c in subset.split(',')] if subset else None
    return jsonify(da.detect_duplicates(df, subset=subset_cols))


@datasets_bp.route('/api/<int:dataset_id>/correlations')
@login_required
def correlations(dataset_id):
    """Correlation Analysis."""
    _, df = _load_dataset_df(dataset_id)
    threshold = request.args.get('threshold', da.STRONG_CORRELATION_THRESHOLD, type=float)
    return jsonify(da.analyze_correlations(df, threshold=threshold))


@datasets_bp.route('/api/<int:dataset_id>/distributions')
@login_required
def distributions(dataset_id):
    """Feature Distribution Analysis."""
    _, df = _load_dataset_df(dataset_id)
    return jsonify(da.analyze_feature_distributions(df))


@datasets_bp.route('/api/<int:dataset_id>/validate', methods=['POST'])
@login_required
def validate(dataset_id):
    """Data Validation. Optional JSON body: {"required_columns": [...],
    "column_types": {...}, "column_ranges": {...}} -- see
    services/dataset_analysis.validate_dataset()'s docstring for the
    exact schema shape. No body still runs the structural checks."""
    _, df = _load_dataset_df(dataset_id)
    schema = request.get_json(silent=True) or {}
    return jsonify(da.validate_dataset(df, schema=schema))


# ─────────────────────── Transformation endpoints (versioned) ───────────────────────

@datasets_bp.route('/api/<int:dataset_id>/dedupe', methods=['POST'])
@login_required
def dedupe(dataset_id):
    """Duplicate Detection's companion action: remove the duplicates
    and save the result as a new DatasetVersion."""
    data = request.get_json(silent=True) or {}
    subset = data.get('columns')
    dataset, df = _load_dataset_df(dataset_id)
    deduped_df, removed = da.remove_duplicates(df, subset=subset)
    version = _save_version(dataset_id, deduped_df, 'dedupe', {'columns': subset, 'removed': removed})
    return jsonify({'version': version.to_dict(), 'removed': removed})


@datasets_bp.route('/api/<int:dataset_id>/scale', methods=['POST'])
@login_required
def scale(dataset_id):
    """Feature Scaling. Body: {"columns": [...], "method": "standard"|"minmax", "version_id": optional}."""
    data = request.get_json(silent=True) or {}
    method = data.get('method', 'standard')
    columns = data.get('columns')
    version_id = data.get('version_id')

    if version_id:
        source, df = _load_version_df(version_id)
    else:
        source, df = _load_dataset_df(dataset_id)

    try:
        scaled_df, params = da.scale_features(df, columns=columns, method=method)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    version = _save_version(dataset_id, scaled_df, 'scale', params,
                             parent_version_id=version_id)
    return jsonify({'version': version.to_dict(), 'scaling_params': params})


@datasets_bp.route('/api/<int:dataset_id>/encode', methods=['POST'])
@login_required
def encode(dataset_id):
    """Encoding. Body: {"columns": [...], "method": "onehot"|"label", "version_id": optional}."""
    data = request.get_json(silent=True) or {}
    method = data.get('method', 'onehot')
    columns = data.get('columns')
    version_id = data.get('version_id')

    if version_id:
        source, df = _load_version_df(version_id)
    else:
        source, df = _load_dataset_df(dataset_id)

    try:
        encoded_df, mapping = da.encode_features(df, columns=columns, method=method)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    version = _save_version(dataset_id, encoded_df, 'encode', mapping,
                             parent_version_id=version_id)
    return jsonify({'version': version.to_dict(), 'encoding': mapping})


@datasets_bp.route('/api/<int:dataset_id>/split', methods=['POST'])
@login_required
def split(dataset_id):
    """Train/Test Split (optionally also a validation split). Saves
    each resulting split as its own DatasetVersion (transformation
    'split_train'/'split_test'/'split_val') so they can be downloaded
    or fed into training independently."""
    data = request.get_json(silent=True) or {}
    test_size = data.get('test_size', 0.2)
    val_size = data.get('val_size', 0.0)
    random_state = data.get('random_state', 42)
    stratify_col = data.get('stratify_col')
    version_id = data.get('version_id')

    if version_id:
        source, df = _load_version_df(version_id)
    else:
        source, df = _load_dataset_df(dataset_id)

    try:
        splits, summary = da.train_test_split_summary(
            df, test_size=test_size, val_size=val_size, random_state=random_state, stratify_col=stratify_col,
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    saved_versions = {}
    for split_name, split_df in splits.items():
        v = _save_version(dataset_id, split_df, f'split_{split_name}', summary, parent_version_id=version_id)
        saved_versions[split_name] = v.to_dict()

    return jsonify({'summary': summary, 'versions': saved_versions})


# ───────────────────────────── Versioning ─────────────────────────────

@datasets_bp.route('/api/<int:dataset_id>/versions')
@login_required
def list_versions(dataset_id):
    """Dataset Versioning: every transformation applied to this
    dataset, most recent first."""
    Dataset.query.get_or_404(dataset_id)
    versions = DatasetVersion.query.filter_by(dataset_id=dataset_id)\
        .order_by(DatasetVersion.version_num.desc()).all()
    return jsonify([v.to_dict() for v in versions])


@datasets_bp.route('/api/versions/<int:version_id>')
@login_required
def version_detail(version_id):
    version = DatasetVersion.query.get_or_404(version_id)
    return jsonify(version.to_dict())


@datasets_bp.route('/api/versions/<int:version_id>/preview')
@login_required
def version_preview(version_id):
    _, df = _load_version_df(version_id)
    return jsonify({'preview': df.head(10).to_dict(orient='records'), 'columns': list(df.columns)})
