"""Entry point for Cold Weather EV Range Degradation Modeler"""



import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app('development')

if __name__ == '__main__':
    # Train ML models on first run
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

    print("\n[CAR] Cold Weather EV Range Degradation Modeler")
    print("   http://127.0.0.1:5005\n")
    app.run(host='0.0.0.0', port=5005, debug=True)
