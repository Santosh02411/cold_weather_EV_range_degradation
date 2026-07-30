"""Seed database with EV vehicles and admin user"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.ev_vehicle import EVVehicle


VEHICLES = [
    # --- Phase 2 (DATA-1) note ---
    # Only the two entries marked "verified" below were checked against
    # real, cited sources during Phase 2 (see docs/PROJECT_WORKFLOW.md
    # for the two corrections this produced). The rest of this list is
    # unchanged from the original project and has NOT been independently
    # verified yet -- treat other entries as reasonable estimates, not
    # confirmed real specs, until they go through the same check (or
    # until scripts/sync_openev_data.py is run against a real network
    # connection to bulk-refresh this list from OpenEV Data).
    # Tesla
    {'model_name': 'Model 3 Standard Range Plus', 'manufacturer': 'Tesla', 'battery_capacity_kwh': 60,
     'epa_range_km': 423, 'vehicle_weight_kg': 1752, 'battery_chemistry': 'LFP',
     'charging_type': 'Tesla Supercharger / CCS', 'max_charging_power_kw': 170, 'drivetrain': 'RWD',
     'year': 2024, 'energy_consumption_wh_km': 142},
    # verified: EPA-rated 342 mi (=550 km) range, 82.1 kWh battery, 1851 kg
    # curb weight. Source: evspecifications.com 2024 Tesla Model 3 Long
    # Range AWD; corroborated by KBB reporting Tesla's own "325+ mi" listing
    # and prior EPA rating of 358mi for an earlier configuration. Original
    # seed value was 82 kWh / 580 km / 1830 kg (close but not exact).
    {'model_name': 'Model 3 Long Range', 'manufacturer': 'Tesla', 'battery_capacity_kwh': 82.1,
     'epa_range_km': 550, 'vehicle_weight_kg': 1851, 'battery_chemistry': 'NCA',
     'charging_type': 'Tesla Supercharger / CCS', 'max_charging_power_kw': 250, 'drivetrain': 'AWD',
     'year': 2024, 'energy_consumption_wh_km': 149},
    {'model_name': 'Model Y Long Range', 'manufacturer': 'Tesla', 'battery_capacity_kwh': 75,
     'epa_range_km': 533, 'vehicle_weight_kg': 1979, 'battery_chemistry': 'NCA',
     'charging_type': 'Tesla Supercharger / CCS', 'max_charging_power_kw': 250, 'drivetrain': 'AWD',
     'year': 2024, 'energy_consumption_wh_km': 149},
    {'model_name': 'Model S Plaid', 'manufacturer': 'Tesla', 'battery_capacity_kwh': 100,
     'epa_range_km': 600, 'vehicle_weight_kg': 2162, 'battery_chemistry': 'NCA',
     'charging_type': 'Tesla Supercharger / CCS', 'max_charging_power_kw': 250, 'drivetrain': 'AWD',
     'year': 2024, 'energy_consumption_wh_km': 167},
    # BYD
    {'model_name': 'Han EV', 'manufacturer': 'BYD', 'battery_capacity_kwh': 85.4,
     'epa_range_km': 521, 'vehicle_weight_kg': 2150, 'battery_chemistry': 'LFP',
     'charging_type': 'CCS', 'max_charging_power_kw': 120, 'drivetrain': 'RWD',
     'year': 2024, 'energy_consumption_wh_km': 164},
    {'model_name': 'Atto 3', 'manufacturer': 'BYD', 'battery_capacity_kwh': 60.48,
     'epa_range_km': 420, 'vehicle_weight_kg': 1750, 'battery_chemistry': 'LFP',
     'charging_type': 'CCS', 'max_charging_power_kw': 88, 'drivetrain': 'FWD',
     'year': 2024, 'energy_consumption_wh_km': 144},
    {'model_name': 'Seal', 'manufacturer': 'BYD', 'battery_capacity_kwh': 82.56,
     'epa_range_km': 570, 'vehicle_weight_kg': 2150, 'battery_chemistry': 'LFP',
     'charging_type': 'CCS', 'max_charging_power_kw': 150, 'drivetrain': 'RWD',
     'year': 2024, 'energy_consumption_wh_km': 145},
    {'model_name': 'Dolphin', 'manufacturer': 'BYD', 'battery_capacity_kwh': 44.9,
     'epa_range_km': 340, 'vehicle_weight_kg': 1520, 'battery_chemistry': 'LFP',
     'charging_type': 'CCS', 'max_charging_power_kw': 60, 'drivetrain': 'FWD',
     'year': 2024, 'energy_consumption_wh_km': 132},
    # Hyundai
    # verified: EPA-rated 303 mi (=488 km) range for RWD Long Range trim
    # (77.4 kWh battery). Source: Consumer Reports 2024 Ioniq 5 Road Test
    # Report ("EPA-rated driving range is ... 303 miles for the single-
    # motor, rear-wheel-drive versions with the 77.4-kWh battery"),
    # corroborated by TopSpeed and Checkered Flag Hyundai World. Original
    # seed value was 507 km, overstated vs. the real 488 km RWD figure.
    {'model_name': 'IONIQ 5 Long Range', 'manufacturer': 'Hyundai Motor Company', 'battery_capacity_kwh': 77.4,
     'epa_range_km': 488, 'vehicle_weight_kg': 2010, 'battery_chemistry': 'NMC',
     'charging_type': 'CCS', 'max_charging_power_kw': 233, 'drivetrain': 'RWD',
     'year': 2024, 'energy_consumption_wh_km': 159},
    {'model_name': 'IONIQ 6 Long Range', 'manufacturer': 'Hyundai Motor Company', 'battery_capacity_kwh': 77.4,
     'epa_range_km': 581, 'vehicle_weight_kg': 1945, 'battery_chemistry': 'NMC',
     'charging_type': 'CCS', 'max_charging_power_kw': 233, 'drivetrain': 'RWD',
     'year': 2024, 'energy_consumption_wh_km': 133},
    {'model_name': 'Kona Electric', 'manufacturer': 'Hyundai Motor Company', 'battery_capacity_kwh': 64,
     'epa_range_km': 418, 'vehicle_weight_kg': 1740, 'battery_chemistry': 'NMC',
     'charging_type': 'CCS', 'max_charging_power_kw': 100, 'drivetrain': 'FWD',
     'year': 2024, 'energy_consumption_wh_km': 153},
    # Nissan
    {'model_name': 'Leaf e+', 'manufacturer': 'Nissan', 'battery_capacity_kwh': 62,
     'epa_range_km': 363, 'vehicle_weight_kg': 1745, 'battery_chemistry': 'NMC',
     'charging_type': 'CHAdeMO', 'max_charging_power_kw': 100, 'drivetrain': 'FWD',
     'year': 2024, 'energy_consumption_wh_km': 171},
]


def seed():
    app = create_app('development')
    with app.app_context():
        db.create_all()

        # Create admin user
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@ev-modeler.com',
                         first_name='Admin', last_name='User', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("[OK] Admin user created (admin / admin123)")

        # Create demo user
        if not User.query.filter_by(username='demo').first():
            demo = User(username='demo', email='demo@ev-modeler.com',
                        first_name='Demo', last_name='User', role='user')
            demo.set_password('demo123')
            db.session.add(demo)
            print("[OK] Demo user created (demo / demo123)")

        # Seed vehicles
        existing = EVVehicle.query.count()
        if existing == 0:
            for v_data in VEHICLES:
                vehicle = EVVehicle(**v_data)
                db.session.add(vehicle)
            print(f"[OK] {len(VEHICLES)} EV vehicles seeded")
        else:
            print(f"[INFO] {existing} vehicles already exist, skipping seed")

        db.session.commit()
        print("[OK] Database seeding complete!")


if __name__ == '__main__':
    seed()
