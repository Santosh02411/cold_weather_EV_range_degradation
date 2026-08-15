#!/usr/bin/env bash
set -e

pip install -r requirements.txt

cd backend
python -c "
import os
from app.ml.train import get_models_root, train_all_models

models_dir = get_models_root()
marker = os.path.join(models_dir, 'random_forest.pkl')

if os.path.exists(marker):
    print('[BUILD] ML models already present, skipping training.')
else:
    print('[BUILD] Training ML models (this can take a minute)...')
    train_all_models()
    print('[BUILD] Done training.')
"