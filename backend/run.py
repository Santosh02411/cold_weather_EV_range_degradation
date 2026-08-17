"""Entry point for Cold Weather EV Range Degradation Modeler"""



import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Reads FLASK_ENV so a production deploy (Render sets this, or set it
# yourself in the web service's environment variables) gets
# ProductionConfig (DEBUG off) instead of quietly running in dev mode
# with the Werkzeug debugger exposed. Defaults to 'development' so
# nothing changes for local use with plain `python run.py`.
app = create_app(os.environ.get('FLASK_ENV', 'development'))


def _ensure_models_trained():
    """Trains the ML models on first run if no saved model exists yet.
    Called unconditionally at import time (not gated behind
    `if __name__ == '__main__':`) because gunicorn imports this module
    rather than executing it as a script -- the old version of this
    check only ran under `python run.py` directly, which meant a
    gunicorn-served deploy would silently skip training and every
    prediction request would fail with no model file found.
    """
    from app.ml.train import get_models_root
    models_dir = get_models_root()
    if not os.path.exists(os.path.join(models_dir, 'random_forest.pkl')):
        print("[ROBOT] Training ML models for the first time...")
        from app.ml.train import train_all_models
        meta = train_all_models()
        for name, metrics in meta['metrics'].items():
            val = metrics['validation_set']
            print(f"  {name}: R2={val['r2_score']}, MAE={val['mae']}")
        cal = meta.get('real_world_calibration', {})
        if cal.get('status') == 'ok':
            print(f"  Real-world calibration MAE (vs {cal['num_benchmark_points']} published "
                  f"benchmarks): {cal['mae_vs_real_world_benchmarks_pct']} pp")
        print("[OK] ML models trained and saved!")


_ensure_models_trained()

def _ensure_seeded():
    """Creates the admin account (and demo account, unless
    SEED_DEMO_USER=false) and seeds the vehicle catalog if the
    database is empty -- same idempotent seed() function `python
    seed_data.py` runs standalone, called automatically here instead
    because some hosts (Render's free tier, notably) don't offer shell
    access to run that command manually after a deploy. Safe to run on
    every startup: seed_data.seed() checks for existing users/vehicles
    before creating anything, so this is a no-op after the first real
    boot.

    Set ADMIN_PASSWORD (and DEMO_PASSWORD, if SEED_DEMO_USER=true) in
    your host's environment variables for a fixed password instead of
    letting this generate and log a random one once -- see README
    "Seed the Database".
    """
    import seed_data
    seed_data.seed(app)


_ensure_seeded()
if __name__ == '__main__':
    print("\n[CAR] Cold Weather EV Range Degradation Modeler")
    print("   http://127.0.0.1:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=True)