"""Entry point for Cold Weather EV Range Degradation Modeler"""



import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app('development')

if __name__ == '__main__':
    # Train ML models on first run
    from app.ml.train import get_models_dir
    models_dir = get_models_dir()
    if not os.path.exists(os.path.join(models_dir, 'random_forest.pkl')):
        print("[ROBOT] Training ML models for the first time...")
        from app.ml.train import train_all_models
        results = train_all_models()
        for name, metrics in results.items():
            print(f"  {name}: R²={metrics['r2_score']}, MAE={metrics['mae']}")
        print("[OK] ML models trained and saved!")

    print("\n[CAR] Cold Weather EV Range Degradation Modeler")
    print("   http://127.0.0.1:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
