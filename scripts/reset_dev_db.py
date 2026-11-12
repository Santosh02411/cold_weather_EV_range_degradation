"""Resets the local dev database to match the current models.

For when db.create_all() left an old SQLite file that's missing
columns added by later model changes -- this shows up as
`sqlite3.OperationalError: no such column: ...` on almost any page,
since create_all() only creates missing tables, never alters existing
ones (see README "Database Migrations").

This is a DESTRUCTIVE reset for local development only -- it drops
every table and recreates them empty. If you have real data you need
to keep, use the Flask-Migrate path in the README instead
(`flask db init` / `migrate` / `upgrade`), not this script.

USAGE:
    cd backend
    python ../scripts/reset_dev_db.py            # prompts for confirmation
    python ../scripts/reset_dev_db.py --yes       # skips the prompt (CI/scripted use)
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from app import create_app, db  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--yes', action='store_true', help='Skip the confirmation prompt.')
    args = parser.parse_args()

    app = create_app()
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')

    print(f"This will DROP every table in: {db_uri}")
    print("All data currently in this database will be lost.")
    if not args.yes:
        confirm = input("Type 'yes' to continue: ").strip().lower()
        if confirm != 'yes':
            print("Cancelled -- no changes made.")
            return

    with app.app_context():
        # Import every model module so their tables are registered on
        # db.metadata before drop_all()/create_all() run -- same import
        # list app/__init__.py's own create_all() call uses, kept in
        # sync with it deliberately (see that file for why the list is
        # explicit rather than relying on import side effects elsewhere).
        from app.models import (
            user, ev_vehicle, prediction, dataset, battery_health, alert_subscription,
            session as user_session_model, vehicle_interactions, trip_plan,
            charging_reservation, report, notification, cost_preference,
        )
        db.drop_all()
        db.create_all()
        print("Done -- every table recreated fresh and empty.")
        print("Next: run 'python seed_data.py' to re-seed the admin/demo accounts and vehicle catalog.")


if __name__ == '__main__':
    main()
