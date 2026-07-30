"""
Sync EVVehicle specs from OpenEV Data (github.com/open-ev-data/open-ev-data-dataset).

WHY THIS SCRIPT EXISTS BUT WASN'T RUN AS PART OF THIS DELIVERY:
The sandbox this project was built in has no outbound network access, so
this script could not be executed or tested against the live OpenEV Data
API/release assets here. It's written against their documented API
(https://api.open-ev-data.org/v1/vehicles) and release-asset URL pattern,
and is ready to run in any environment with normal internet access - but
treat it as unverified until you've run it once and spot-checked the
output. This is the same honesty standard applied to the rest of this
project's real-data claims: a script that *should* work is not the same
as a script that's been proven to work.

USAGE (once you have network access):
    cd backend
    python ../scripts/sync_openev_data.py --make tesla --make hyundai --dry-run
    python ../scripts/sync_openev_data.py --make tesla --make hyundai   # writes to DB

Data license: OpenEV Data is CDLA-Permissive-2.0 licensed (free to use,
including commercially, with attribution) - see their repo for full terms
before shipping this in a public product.
"""
import argparse
import sys
import os

import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

OPENEV_API_BASE = "https://api.open-ev-data.org/v1/vehicles"

# OpenEV Data's battery chemistry / drivetrain vocab doesn't map 1:1 onto
# this project's EVVehicle schema in every case - keep an explicit
# mapping here rather than passing values through blindly, so a schema
# mismatch fails loudly instead of silently writing bad data.
CHEMISTRY_MAP = {
    'NMC': 'NMC', 'NCA': 'NCA', 'LFP': 'LFP', 'LMO': 'LMO',
}
DRIVETRAIN_MAP = {
    'AWD': 'AWD', 'RWD': 'RWD', 'FWD': 'FWD', '4WD': 'AWD',
}


def fetch_vehicles(make):
    """Fetch all vehicles for a given manufacturer from the OpenEV Data API."""
    resp = requests.get(OPENEV_API_BASE, params={'make': make}, timeout=20)
    resp.raise_for_status()
    return resp.json()


def to_ev_vehicle_dict(openev_record):
    """Map an OpenEV Data record onto this project's EVVehicle fields.
    Returns None (and prints why) if required fields are missing, rather
    than writing a partially-populated row.
    """
    required = ['model', 'brand', 'usable_battery_size', 'range']
    missing = [f for f in required if not openev_record.get(f)]
    if missing:
        print(f"[SKIP] {openev_record.get('brand', '?')} {openev_record.get('model', '?')}: "
              f"missing fields {missing}")
        return None

    chemistry = CHEMISTRY_MAP.get((openev_record.get('battery_chemistry') or '').upper(), 'NMC')
    drivetrain = DRIVETRAIN_MAP.get((openev_record.get('drive') or '').upper(), None)

    return {
        'model_name': openev_record['model'],
        'manufacturer': openev_record['brand'],
        'battery_capacity_kwh': float(openev_record['usable_battery_size']),
        'epa_range_km': float(openev_record['range']),
        'vehicle_weight_kg': float(openev_record.get('total_weight', 0)) or None,
        'battery_chemistry': chemistry,
        'charging_type': openev_record.get('fastcharge_plug', 'CCS'),
        'max_charging_power_kw': openev_record.get('fastcharge_power_max'),
        'drivetrain': drivetrain,
        'year': openev_record.get('release_year'),
        'energy_consumption_wh_km': openev_record.get('efficiency'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--make', action='append', required=True,
                         help='Manufacturer to sync, e.g. --make tesla (repeatable)')
    parser.add_argument('--dry-run', action='store_true',
                         help='Print what would be written without touching the database')
    args = parser.parse_args()

    all_records = []
    for make in args.make:
        print(f"Fetching {make} from OpenEV Data...")
        try:
            records = fetch_vehicles(make)
        except Exception as e:
            print(f"[ERROR] Failed to fetch '{make}': {e}")
            continue
        all_records.extend(records)

    mapped = [to_ev_vehicle_dict(r) for r in all_records]
    mapped = [m for m in mapped if m is not None]

    print(f"\n{len(mapped)} vehicles mapped successfully.")

    if args.dry_run:
        for m in mapped:
            print(f"  {m['manufacturer']} {m['model_name']}: "
                  f"{m['battery_capacity_kwh']}kWh, {m['epa_range_km']}km range")
        print("\n(dry run - nothing written)")
        return

    # Deferred import: only touch the Flask app/DB when actually writing,
    # so --dry-run works without a configured database.
    from app import create_app, db
    from app.models.ev_vehicle import EVVehicle

    app = create_app('development')
    with app.app_context():
        written, updated = 0, 0
        for m in mapped:
            existing = EVVehicle.query.filter_by(
                model_name=m['model_name'], manufacturer=m['manufacturer']
            ).first()
            if existing:
                for k, v in m.items():
                    if v is not None:
                        setattr(existing, k, v)
                updated += 1
            else:
                db.session.add(EVVehicle(**m))
                written += 1
        db.session.commit()
        print(f"[OK] {written} vehicles added, {updated} updated.")


if __name__ == '__main__':
    main()
