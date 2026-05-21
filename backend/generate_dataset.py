import pandas as pd
import numpy as np
import os

def generate_large_dataset(num_samples=10000):
    np.random.seed(42)
    
    # 1. Base Variables
    temp = np.random.uniform(-30, 40, num_samples)
    humidity = np.random.uniform(10, 100, num_samples)
    wind_speed = np.random.uniform(0, 80, num_samples)
    precip_types = ['none', 'rain', 'snow']
    precip = np.random.choice(precip_types, num_samples, p=[0.7, 0.2, 0.1])
    
    battery_pct = np.random.uniform(10, 100, num_samples)
    vehicle_speed = np.random.uniform(30, 130, num_samples)
    hvac_usage = (temp < 15) | (temp > 30) # HVAC usually on if cold or very hot
    # Randomly flip some hvac for variety
    hvac_usage = hvac_usage ^ (np.random.random(num_samples) < 0.1)
    
    terrain_types = ['flat', 'hilly', 'mountainous']
    terrain = np.random.choice(terrain_types, num_samples, p=[0.6, 0.3, 0.1])
    
    age = np.random.uniform(0, 10, num_samples)
    
    # 2. Vehicle Specs (Randomly pick from realistic ranges)
    capacity = np.random.uniform(40, 100, num_samples)
    epa_range = capacity * np.random.uniform(5, 7, num_samples)
    weight = np.random.uniform(1500, 2500, num_samples)
    
    # 3. Calculate Degradation (Physics-based logic)
    # Base degradation starts at 0
    deg = np.zeros(num_samples)
    
    # Temperature impact (Non-linear)
    # Below 20C, degradation starts increasing
    cold_impact = np.where(temp < 20, (20 - temp)**1.5 * 0.15, 0)
    # Extra impact for extreme cold
    extreme_cold = np.where(temp < -10, (-10 - temp)**2 * 0.05, 0)
    
    # HVAC impact
    hvac_penalty = np.where(hvac_usage, np.random.uniform(5, 15, num_samples), 0)
    
    # Speed impact (Air resistance increases with square of speed)
    speed_penalty = (vehicle_speed / 100)**2 * 5
    
    # Terrain impact
    terrain_map = {'flat': 0, 'hilly': 5, 'mountainous': 15}
    terrain_penalty = np.array([terrain_map[t] for t in terrain])
    
    # Age impact
    age_penalty = age * 0.8
    
    # Wind impact
    wind_penalty = (wind_speed / 50) * 2
    
    # Precipitation impact
    precip_map = {'none': 0, 'rain': 3, 'snow': 8}
    precip_penalty = np.array([precip_map[p] for p in precip])
    
    # Sum it up with some noise
    deg = cold_impact + extreme_cold + hvac_penalty + speed_penalty + terrain_penalty + age_penalty + wind_penalty + precip_penalty
    deg += np.random.normal(0, 2, num_samples) # Add noise
    
    # Clip to realistic range (0 to 60%)
    deg = np.clip(deg, 0, 65)
    
    # Create DataFrame
    df = pd.DataFrame({
        'temperature_c': np.round(temp, 1),
        'humidity': np.round(humidity, 0).astype(int),
        'wind_speed_kmh': np.round(wind_speed, 1),
        'precipitation': precip,
        'battery_percentage': np.round(battery_pct, 0).astype(int),
        'vehicle_speed_kmh': np.round(vehicle_speed, 1),
        'hvac_usage': hvac_usage,
        'terrain_type': terrain,
        'battery_age_years': np.round(age, 1),
        'battery_capacity_kwh': np.round(capacity, 1),
        'epa_range_km': np.round(epa_range, 1),
        'vehicle_weight_kg': np.round(weight, 0).astype(int),
        'range_degradation_pct': np.round(deg, 2)
    })
    
    output_path = r'c:\Users\santo\Projects\Cold_Weather_EV\data\ev_range_large_dataset.csv'
    df.to_csv(output_path, index=False)
    print(f"Generated large dataset with {num_samples} rows at {output_path}")

if __name__ == "__main__":
    generate_large_dataset(10000)
