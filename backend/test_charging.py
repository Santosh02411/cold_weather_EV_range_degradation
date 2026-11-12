
import sys, os
sys.path.insert(0, os.path.abspath('backend'))
from app import create_app
from app.api.charging import predict_charging_time
from app.models.ev_vehicle import EVVehicle

app = create_app('development')
with app.app_context():
    # Tesla Model 3 (75 kWh)
    v75 = EVVehicle(battery_capacity_kwh=75.0, manufacturer='Tesla', model_name='Model 3')
    
    print("--- Tesla Model 3 (75 kWh) ---")
    r1 = predict_charging_time(v75, 20, 0, 100, True)
    print(f"0-100% @ 20°C: {r1['charging_time_minutes']} min (Expect 100)")
    
    r2 = predict_charging_time(v75, 20, 0, 30, True)
    print(f"0-30% @ 20°C: {r2['charging_time_minutes']} min (Expect 30)")
    
    # Rivian R1T (135 kWh)
    v135 = EVVehicle(battery_capacity_kwh=135.0, manufacturer='Rivian', model_name='R1T')
    print("\n--- Rivian R1T (135 kWh) ---")
    r3 = predict_charging_time(v135, 20, 0, 100, True)
    print(f"0-100% @ 20°C: {r3['charging_time_minutes']} min (Expect 180)")
    
    # Cold weather
    print("\n--- Cold Weather (-15°C) ---")
    r4 = predict_charging_time(v75, -15, 0, 100, True)
    print(f"Tesla 0-100% @ -15°C: {r4['charging_time_minutes']} min (Expect 75/18*60 = 250)")
