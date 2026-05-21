"""
ML Training Pipeline for Cold Weather EV Range Degradation
Trains Linear Regression, Random Forest, XGBoost, and Gradient Boosting models.
"""
import os, json, joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


def generate_synthetic_dataset(n_samples=5000):
    """Generate realistic synthetic EV cold weather degradation data"""
    np.random.seed(42)

    temperatures = np.random.uniform(-30, 40, n_samples)
    humidity = np.random.uniform(20, 100, n_samples)
    wind_speed = np.random.uniform(0, 80, n_samples)
    precipitation_codes = np.random.choice([0, 1, 2], n_samples, p=[0.6, 0.25, 0.15])
    battery_pct = np.random.uniform(10, 100, n_samples)
    vehicle_speed = np.random.uniform(20, 140, n_samples)
    hvac_usage = np.random.choice([0, 1], n_samples, p=[0.3, 0.7])
    terrain_codes = np.random.choice([0, 1, 2], n_samples, p=[0.5, 0.35, 0.15])
    battery_age = np.random.uniform(0, 10, n_samples)
    battery_capacity = np.random.choice([40, 58, 60, 72, 75, 77, 82, 85, 100], n_samples)
    epa_range = battery_capacity * np.random.uniform(4.5, 6.5, n_samples)
    vehicle_weight = np.random.uniform(1500, 2800, n_samples)

    # Range degradation model (realistic physics-based)
    base_degradation = np.zeros(n_samples)

    # Temperature effect (biggest factor)
    for i in range(n_samples):
        t = temperatures[i]
        if t < -20:
            base_degradation[i] += 35 + np.random.normal(0, 3)
        elif t < -10:
            base_degradation[i] += 25 + np.random.normal(0, 2.5)
        elif t < 0:
            base_degradation[i] += 15 + np.random.normal(0, 2)
        elif t < 10:
            base_degradation[i] += 8 + np.random.normal(0, 1.5)
        elif t < 20:
            base_degradation[i] += 2 + np.random.normal(0, 1)
        elif t <= 30:
            base_degradation[i] += 0 + np.random.normal(0, 0.5)
        else:
            base_degradation[i] += 5 + np.random.normal(0, 1)

    # HVAC effect
    base_degradation += hvac_usage * np.where(temperatures < 10, 8, 3) * np.random.uniform(0.8, 1.2, n_samples)
    # Wind resistance
    base_degradation += (wind_speed / 80) * 5 * np.random.uniform(0.8, 1.2, n_samples)
    # Speed effect
    base_degradation += np.where(vehicle_speed > 100, (vehicle_speed - 100) * 0.15, 0)
    # Terrain
    base_degradation += terrain_codes * 4
    # Battery age
    base_degradation += battery_age * 1.2
    # Precipitation
    base_degradation += precipitation_codes * 2
    # Weight effect
    base_degradation += (vehicle_weight - 1800) / 1000 * 3

    base_degradation = np.clip(base_degradation, 0, 65)

    df = pd.DataFrame({
        'temperature_c': temperatures,
        'humidity': humidity,
        'wind_speed_kmh': wind_speed,
        'precipitation': precipitation_codes,
        'battery_percentage': battery_pct,
        'vehicle_speed_kmh': vehicle_speed,
        'hvac_usage': hvac_usage,
        'terrain_type': terrain_codes,
        'battery_age_years': battery_age,
        'battery_capacity_kwh': battery_capacity,
        'epa_range_km': epa_range,
        'vehicle_weight_kg': vehicle_weight,
        'range_degradation_pct': np.round(base_degradation, 2),
    })

    return df


def get_models_dir():
    base = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base, 'saved_models')
    os.makedirs(models_dir, exist_ok=True)
    return models_dir


FEATURE_COLS = [
    'temperature_c', 'humidity', 'wind_speed_kmh', 'precipitation',
    'battery_percentage', 'vehicle_speed_kmh', 'hvac_usage',
    'terrain_type', 'battery_age_years', 'battery_capacity_kwh',
    'epa_range_km', 'vehicle_weight_kg'
]


def train_all_models(df=None):
    """Train all ML models and save them"""
    if df is None:
        df = generate_synthetic_dataset(5000)

    X = df[FEATURE_COLS]
    y = df['range_degradation_pct']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        'linear_regression': LinearRegression(),
        'random_forest': RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1),
        'gradient_boosting': GradientBoostingRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42),
    }
    if HAS_XGBOOST:
        models['xgboost'] = XGBRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42)

    results = {}
    models_dir = get_models_dir()

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        # Feature importance
        if hasattr(model, 'feature_importances_'):
            importance = dict(zip(FEATURE_COLS, model.feature_importances_.tolist()))
        elif hasattr(model, 'coef_'):
            importance = dict(zip(FEATURE_COLS, np.abs(model.coef_).tolist()))
        else:
            importance = {}

        results[name] = {
            'mae': round(mae, 4),
            'rmse': round(rmse, 4),
            'r2_score': round(r2, 4),
            'feature_importance': importance,
        }

        # Save model
        joblib.dump(model, os.path.join(models_dir, f'{name}.pkl'))

    # Save metadata
    with open(os.path.join(models_dir, 'training_results.json'), 'w') as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == '__main__':
    results = train_all_models()
    for name, metrics in results.items():
        print(f"\n{name}:")
        print(f"  MAE:  {metrics['mae']}")
        print(f"  RMSE: {metrics['rmse']}")
        print(f"  R²:   {metrics['r2_score']}")
