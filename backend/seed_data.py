"""Seed database with EV vehicles and admin user"""
import sys, os, secrets
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
    # price_usd: null -- "Standard Range Plus" is a discontinued Tesla
    # trim name, no reliable current price to verify against.
    {'model_name': 'Model 3 Standard Range Plus', 'manufacturer': 'Tesla', 'battery_capacity_kwh': 60,
     'epa_range_km': 423, 'vehicle_weight_kg': 1752, 'battery_chemistry': 'LFP',
     'charging_type': 'Tesla Supercharger / CCS', 'max_charging_power_kw': 170, 'drivetrain': 'RWD',
     'year': 2024, 'energy_consumption_wh_km': 142, 'price_usd': None, 'vehicle_type': 'sedan'},
    # verified: EPA-rated 342 mi (=550 km) range, 82.1 kWh battery, 1851 kg
    # curb weight. Source: evspecifications.com 2024 Tesla Model 3 Long
    # Range AWD; corroborated by KBB reporting Tesla's own "325+ mi" listing
    # and prior EPA rating of 358mi for an earlier configuration. Original
    # seed value was 82 kWh / 580 km / 1830 kg (close but not exact).
    # price_usd verified: $47,490 starting price, 2024 Model 3 Long Range
    # AWD, per the same evspecifications.com-corroborated pricing search
    # used for the range/weight correction above.
    {'model_name': 'Model 3 Long Range', 'manufacturer': 'Tesla', 'battery_capacity_kwh': 82.1,
     'epa_range_km': 550, 'vehicle_weight_kg': 1851, 'battery_chemistry': 'NCA',
     'charging_type': 'Tesla Supercharger / CCS', 'max_charging_power_kw': 250, 'drivetrain': 'AWD',
     'year': 2024, 'energy_consumption_wh_km': 149, 'price_usd': 47490, 'vehicle_type': 'sedan'},
    # price_usd verified: $44,990 starting price, 2024 Model Y Long Range.
    {'model_name': 'Model Y Long Range', 'manufacturer': 'Tesla', 'battery_capacity_kwh': 75,
     'epa_range_km': 533, 'vehicle_weight_kg': 1979, 'battery_chemistry': 'NCA',
     'charging_type': 'Tesla Supercharger / CCS', 'max_charging_power_kw': 250, 'drivetrain': 'AWD',
     'year': 2024, 'energy_consumption_wh_km': 149, 'price_usd': 44990, 'vehicle_type': 'crossover'},
    # price_usd: not independently verified this round -- left null
    # rather than repeating a widely-cited but unconfirmed public figure.
    {'model_name': 'Model S Plaid', 'manufacturer': 'Tesla', 'battery_capacity_kwh': 100,
     'epa_range_km': 600, 'vehicle_weight_kg': 2162, 'battery_chemistry': 'NCA',
     'charging_type': 'Tesla Supercharger / CCS', 'max_charging_power_kw': 250, 'drivetrain': 'AWD',
     'year': 2024, 'energy_consumption_wh_km': 167, 'price_usd': None, 'vehicle_type': 'sedan'},
    # BYD
    # price_usd: null for all BYD entries -- not sold new in the US
    # market as of this data, so a USD MSRP isn't a meaningful/reliable
    # figure to attach (price varies enormously by the actual market
    # BYD sells in).
    {'model_name': 'Han EV', 'manufacturer': 'BYD', 'battery_capacity_kwh': 85.4,
     'epa_range_km': 521, 'vehicle_weight_kg': 2150, 'battery_chemistry': 'LFP',
     'charging_type': 'CCS', 'max_charging_power_kw': 120, 'drivetrain': 'RWD',
     'year': 2024, 'energy_consumption_wh_km': 164, 'price_usd': None, 'vehicle_type': 'sedan'},
    {'model_name': 'Atto 3', 'manufacturer': 'BYD', 'battery_capacity_kwh': 60.48,
     'epa_range_km': 420, 'vehicle_weight_kg': 1750, 'battery_chemistry': 'LFP',
     'charging_type': 'CCS', 'max_charging_power_kw': 88, 'drivetrain': 'FWD',
     'year': 2024, 'energy_consumption_wh_km': 144, 'price_usd': None, 'vehicle_type': 'crossover'},
    {'model_name': 'Seal', 'manufacturer': 'BYD', 'battery_capacity_kwh': 82.56,
     'epa_range_km': 570, 'vehicle_weight_kg': 2150, 'battery_chemistry': 'LFP',
     'charging_type': 'CCS', 'max_charging_power_kw': 150, 'drivetrain': 'RWD',
     'year': 2024, 'energy_consumption_wh_km': 145, 'price_usd': None, 'vehicle_type': 'sedan'},
    {'model_name': 'Dolphin', 'manufacturer': 'BYD', 'battery_capacity_kwh': 44.9,
     'epa_range_km': 340, 'vehicle_weight_kg': 1520, 'battery_chemistry': 'LFP',
     'charging_type': 'CCS', 'max_charging_power_kw': 60, 'drivetrain': 'FWD',
     'year': 2024, 'energy_consumption_wh_km': 132, 'price_usd': None, 'vehicle_type': 'hatchback'},
    # Hyundai
    # verified: EPA-rated 303 mi (=488 km) range for RWD Long Range trim
    # (77.4 kWh battery). Source: Consumer Reports 2024 Ioniq 5 Road Test
    # Report ("EPA-rated driving range is ... 303 miles for the single-
    # motor, rear-wheel-drive versions with the 77.4-kWh battery"),
    # corroborated by TopSpeed and Checkered Flag Hyundai World. Original
    # seed value was 507 km, overstated vs. the real 488 km RWD figure.
    # price_usd: not independently verified this round for the Long
    # Range trim specifically (search results covered SE Standard Range
    # pricing, a different trim) -- left null rather than misapplying
    # another trim's price.
    {'model_name': 'IONIQ 5 Long Range', 'manufacturer': 'Hyundai Motor Company', 'battery_capacity_kwh': 77.4,
     'epa_range_km': 488, 'vehicle_weight_kg': 2010, 'battery_chemistry': 'NMC',
     'charging_type': 'CCS', 'max_charging_power_kw': 233, 'drivetrain': 'RWD',
     'year': 2024, 'energy_consumption_wh_km': 159, 'price_usd': None, 'vehicle_type': 'crossover'},
    {'model_name': 'IONIQ 6 Long Range', 'manufacturer': 'Hyundai Motor Company', 'battery_capacity_kwh': 77.4,
     'epa_range_km': 581, 'vehicle_weight_kg': 1945, 'battery_chemistry': 'NMC',
     'charging_type': 'CCS', 'max_charging_power_kw': 233, 'drivetrain': 'RWD',
     'year': 2024, 'energy_consumption_wh_km': 133, 'price_usd': None, 'vehicle_type': 'sedan'},
    {'model_name': 'Kona Electric', 'manufacturer': 'Hyundai Motor Company', 'battery_capacity_kwh': 64,
     'epa_range_km': 418, 'vehicle_weight_kg': 1740, 'battery_chemistry': 'NMC',
     'charging_type': 'CCS', 'max_charging_power_kw': 100, 'drivetrain': 'FWD',
     'year': 2024, 'energy_consumption_wh_km': 153, 'price_usd': None, 'vehicle_type': 'crossover'},
    # Nissan
    # price_usd: not independently verified for the e+ (larger battery)
    # trim specifically -- search results covered the base Leaf S trim,
    # a different (cheaper, smaller-battery) configuration.
    {'model_name': 'Leaf e+', 'manufacturer': 'Nissan', 'battery_capacity_kwh': 62,
     'epa_range_km': 363, 'vehicle_weight_kg': 1745, 'battery_chemistry': 'NMC',
     'charging_type': 'CHAdeMO', 'max_charging_power_kw': 100, 'drivetrain': 'FWD',
     'year': 2024, 'energy_consumption_wh_km': 171, 'price_usd': None, 'vehicle_type': 'hatchback'},
]


def _resolve_password(env_var_name, label):
    """SEC-3: never fall back to a hardcoded default password. Use an
    explicit env var if the operator set one, otherwise generate a real
    random password with `secrets` (cryptographically secure, unlike
    `random`) and print it exactly once so it can be captured now -- it
    is never stored anywhere in plaintext after this, only its hash.
    """
    env_value = os.environ.get(env_var_name)
    if env_value:
        return env_value, False
    generated = secrets.token_urlsafe(12)
    print(f"[GENERATED] No {env_var_name} set -- generated a random password for {label}.")
    return generated, True


def seed():
    app = create_app('development')
    with app.app_context():
        db.create_all()

        generated_credentials = []

        # Create admin user
        if not User.query.filter_by(username='admin').first():
            password, was_generated = _resolve_password('ADMIN_PASSWORD', 'admin')
            admin = User(username='admin', email='admin@ev-modeler.com',
                         first_name='Admin', last_name='User', role='admin')
            admin.set_password(password)
            db.session.add(admin)
            print("[OK] Admin user created (username: admin)")
            if was_generated:
                generated_credentials.append(('admin', password))

        # Create demo user -- only if explicitly opted into. A public-
        # facing demo login is arguably a bigger real-world risk than an
        # admin account with a random password (it's *meant* to be easy
        # to find and use), so unlike the admin account this one is
        # opt-in rather than always-created-with-a-random-password.
        create_demo = os.environ.get('SEED_DEMO_USER', 'true').lower() == 'true'
        if create_demo and not User.query.filter_by(username='demo').first():
            password, was_generated = _resolve_password('DEMO_PASSWORD', 'demo')
            demo = User(username='demo', email='demo@ev-modeler.com',
                        first_name='Demo', last_name='User', role='user')
            demo.set_password(password)
            db.session.add(demo)
            print("[OK] Demo user created (username: demo)")
            if was_generated:
                generated_credentials.append(('demo', password))
        elif not create_demo:
            print("[SKIP] SEED_DEMO_USER=false -- no demo account created.")

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

        if generated_credentials:
            print("\n" + "=" * 60)
            print("  GENERATED CREDENTIALS -- SAVE THESE NOW")
            print("  They are hashed in the database and cannot be")
            print("  recovered from this script again. Set ADMIN_PASSWORD /")
            print("  DEMO_PASSWORD in .env instead if you want a fixed value.")
            print("=" * 60)
            for username, password in generated_credentials:
                print(f"    {username} / {password}")
            print("=" * 60 + "\n")

        print("[OK] Database seeding complete!")


if __name__ == '__main__':
    seed()
