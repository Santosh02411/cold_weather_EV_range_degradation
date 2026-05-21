import os, json
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pandas as pd
from ..models.dataset import Dataset
from .. import db

datasets_bp = Blueprint('datasets', __name__)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'json'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

    # Analyze
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        else:
            df = pd.read_json(filepath)

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
    dataset = Dataset.query.get_or_404(dataset_id)
    try:
        df = pd.read_csv(dataset.filepath)
        original_rows = len(df)
        # Handle missing values
        df = df.dropna(thresh=len(df.columns) * 0.5)
        for col in df.select_dtypes(include='number').columns:
            df[col] = df[col].fillna(df[col].median())
        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'unknown')
        # Remove outliers (IQR method on numeric cols)
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
    db.session.delete(dataset)
    db.session.commit()
    return jsonify({'message': 'Dataset deleted'})
