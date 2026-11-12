"""
Shared pytest configuration.

Path setup only, deliberately -- no Flask app fixture here. Splitting
tests into "pure logic, no Flask/DB needed" (test_physics.py,
test_train.py, test_battery_trend.py, test_geo.py,
test_recalibration_math.py) vs. "needs a real Flask app + DB"
(test_api_smoke.py) means the pure-logic tests can run in ANY
environment with just the scientific-computing stack installed, no
Flask/Flask-SQLAlchemy required -- which matters because this whole
project was built in a sandbox that has the former but not the latter
(see docs/PROJECT_WORKFLOW.md). Those pure-logic tests were verified
correct in that sandbox before this suite was written; test_api_smoke.py
needs `pip install -r requirements.txt` in a real environment to run at
all, and was NOT executed as part of building this project (documented
honestly rather than claimed as verified).
"""
import os
import sys
import types
import importlib.util

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
APP_DIR = os.path.join(BACKEND_DIR, 'app')
sys.path.insert(0, BACKEND_DIR)


def load_app_module(dotted_name):
    """Import a module under `app.*` WITHOUT triggering `app/__init__.py`
    (which requires flask_sqlalchemy, flask_login, etc. to be
    installed). This project's `ml/` and `services/` modules are
    intentionally kept free of any hard Flask/DB dependency at import
    time specifically so they can be tested this way -- see
    docs/PROJECT_WORKFLOW.md for why (this sandbox never had
    flask_sqlalchemy installed, so this technique was the only way
    anything in this project got tested before shipping).

    Registers fake `app`, `app.ml`, `app.services` package stubs in
    sys.modules (empty except for __path__) so relative imports inside
    the real modules (e.g. predict.py's `from .train import ...`)
    resolve correctly, then loads the requested module for real from
    its actual file. Safe to call multiple times -- already-loaded
    modules are returned from sys.modules directly.
    """
    if dotted_name in sys.modules:
        return sys.modules[dotted_name]

    parts = dotted_name.split('.')
    assert parts[0] == 'app', "load_app_module expects a dotted name starting with 'app.'"

    # Ensure parent packages exist as (mostly empty) stubs first.
    built = 'app'
    if built not in sys.modules:
        stub = types.ModuleType('app')
        stub.__path__ = [APP_DIR]
        sys.modules['app'] = stub

    for part in parts[1:-1]:
        built = f'{built}.{part}'
        sub_dir = os.path.join(APP_DIR, *built.split('.')[1:])
        if built not in sys.modules:
            stub = types.ModuleType(built)
            stub.__path__ = [sub_dir]
            sys.modules[built] = stub

    file_path = os.path.join(APP_DIR, *parts[1:-1], f'{parts[-1]}.py')
    spec = importlib.util.spec_from_file_location(dotted_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[dotted_name] = module
    spec.loader.exec_module(module)
    return module
