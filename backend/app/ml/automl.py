"""Model registry + hyperparameter tuning ("AutoML") for the
range-degradation models.

Kept Flask/DB-free like the rest of app/ml/. train.py owns the actual
fit/evaluate/save loop (so every model, tuned or not, still goes
through the exact same CV / val / test / real-world-calibration
pipeline) -- this module only supplies WHICH estimators exist and HOW
to search their hyperparameters.

Optional model families (xgboost, lightgbm, catboost) follow the same
"degrade gracefully if not installed" convention train.py already used
for xgboost: a missing package means that entry is silently absent
from the registry, not a crash. This matters in this project's own dev
sandbox specifically -- see train.py's module docstring / MEMORY.md.
"""
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, StackingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import RandomizedSearchCV, KFold

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from lightgbm import LGBMRegressor
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    from catboost import CatBoostRegressor
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False


def _neural_network_estimator():
    # MLPRegressor is gradient-based and sensitive to unscaled inputs
    # (unlike the tree models above) -- wrapped in a Pipeline so
    # scaling always happens together with the model, both at fit time
    # and inside cross_val_score/RandomizedSearchCV folds (fitting the
    # scaler on the full training set before CV would leak validation-
    # fold information into the scaler; the Pipeline refits it per fold
    # automatically).
    return Pipeline([
        ('scaler', StandardScaler()),
        ('mlp', MLPRegressor(
            hidden_layer_sizes=(64, 32), activation='relu', solver='adam',
            alpha=0.001, max_iter=800, early_stopping=True,
            n_iter_no_change=15, random_state=42,
        )),
    ])


def build_model_registry(include_ensemble=True):
    """Returns {name: {'estimator': fresh unfitted instance,
    'param_distributions': dict-or-None}}. `param_distributions` is
    None for models this project doesn't tune (linear regression has
    no meaningful hyperparameters here; the stacking ensemble is
    composed of already-configured base learners rather than
    independently searched, to keep AutoML runtime bounded).
    """
    registry = {
        'linear_regression': {
            'estimator': LinearRegression(),
            'param_distributions': None,
        },
        'random_forest': {
            'estimator': RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=1),
            'param_distributions': {
                'n_estimators': [100, 200, 300],
                'max_depth': [8, 12, 15, 20, None],
                'min_samples_leaf': [1, 2, 4],
            },
        },
        'gradient_boosting': {
            'estimator': GradientBoostingRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42),
            'param_distributions': {
                'n_estimators': [100, 150, 250],
                'max_depth': [3, 5, 6, 8],
                'learning_rate': [0.03, 0.05, 0.1, 0.2],
            },
        },
        'neural_network': {
            'estimator': _neural_network_estimator(),
            'param_distributions': {
                'mlp__hidden_layer_sizes': [(64, 32), (128, 64), (64,), (32, 16)],
                'mlp__alpha': [0.0001, 0.001, 0.01],
            },
        },
    }

    if HAS_XGBOOST:
        registry['xgboost'] = {
            'estimator': XGBRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42),
            'param_distributions': {
                'n_estimators': [100, 150, 250],
                'max_depth': [3, 5, 6, 8],
                'learning_rate': [0.03, 0.05, 0.1, 0.2],
            },
        }
    if HAS_LIGHTGBM:
        registry['lightgbm'] = {
            'estimator': LGBMRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1),
            'param_distributions': {
                'n_estimators': [100, 150, 250],
                'num_leaves': [15, 31, 63],
                'learning_rate': [0.03, 0.05, 0.1, 0.2],
            },
        }
    if HAS_CATBOOST:
        registry['catboost'] = {
            'estimator': CatBoostRegressor(iterations=150, depth=6, learning_rate=0.1, random_state=42, verbose=False, allow_writing_files=False),
            'param_distributions': {
                'iterations': [100, 150, 250],
                'depth': [4, 6, 8],
                'learning_rate': [0.03, 0.05, 0.1, 0.2],
            },
        }

    if include_ensemble:
        base_estimators = [
            ('rf', RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42, n_jobs=1)),
            ('gb', GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)),
        ]
        if HAS_XGBOOST:
            base_estimators.append(('xgb', XGBRegressor(n_estimators=100, max_depth=5, random_state=42)))
        if HAS_LIGHTGBM:
            base_estimators.append(('lgbm', LGBMRegressor(n_estimators=100, max_depth=5, random_state=42, verbose=-1)))
        # Stacking Ensemble Learning: a meta-model (ridge regression)
        # learns how to best combine the base learners' predictions,
        # rather than just averaging them like predict.py's ensemble-
        # agreement confidence score does. Genuinely different from
        # that averaging -- this one is itself a trained model.
        # cv=3 here (StackingRegressor's own internal fold count for
        # generating out-of-fold base-learner predictions) rather than
        # sklearn's default of 5 -- with N base learners each getting
        # its own internal k-fold fit, this is already the most
        # expensive model in the registry; 3 folds keeps it usable in
        # an interactive admin "retrain now" click instead of tying up
        # the request for several minutes.
        registry['stacking_ensemble'] = {
            'estimator': StackingRegressor(estimators=base_estimators, final_estimator=Ridge(alpha=1.0), cv=3, n_jobs=1),
            'param_distributions': None,
        }

    return registry


def tune_hyperparameters(estimator, param_distributions, X_train, y_train, n_iter=8, cv=3, random_state=42):
    """Randomized hyperparameter search. Deliberately small (n_iter,
    cv) by default so a tuning/AutoML run stays usable interactively
    from the admin panel (roughly comparable in cost to training a
    couple of extra models) rather than tying up the request for
    minutes -- raise both for an offline/overnight search instead.

    Returns (best_estimator, best_params, best_cv_mae).
    """
    kf = KFold(n_splits=cv, shuffle=True, random_state=random_state)
    search = RandomizedSearchCV(
        estimator, param_distributions, n_iter=n_iter, cv=kf,
        scoring='neg_mean_absolute_error', random_state=random_state,
        n_jobs=1,  # n_jobs=1 here would nest under train.py's own parallel model loop
    )
    search.fit(X_train, y_train)
    return search.best_estimator_, search.best_params_, float(-search.best_score_)
