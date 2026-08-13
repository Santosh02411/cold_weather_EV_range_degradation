# Test Suite (INFRA-2)

## Running

```bash
pip install -r requirements-dev.txt
pytest                    # everything
pytest tests/test_physics.py tests/test_train.py tests/test_geo.py \
       tests/test_battery_trend.py tests/test_recalibration_math.py \
       tests/test_train_slow.py tests/test_auth_tokens.py \
       # fast + slow pure-logic tests, no Flask/DB needed
pytest tests/test_api_smoke.py     # Flask + DB tests
```

## What's actually been run, honestly

Every test in **`test_physics.py`, `test_train.py`, `test_battery_trend.py`,
`test_geo.py`, `test_recalibration_math.py`, `test_train_slow.py`,
`test_auth_tokens.py`, `test_vehicle_fast_charging.py`, and
`test_battery_intelligence.py`** (82 tests
total) was written AND executed during this project's
development, using a minimal manual test runner instead of `pytest`
itself (`pytest` isn't installed in the sandbox this project was built
in — no outbound network there to install it). All 82 pass. The manual
runner does the same thing `pytest` would for these particular tests
(import the file, call every `test_*` function, report pass/fail) — but
it is not `pytest`, and hasn't been cross-checked against it. **Run
`pytest` for real before trusting this suite as CI-ready.**

**`test_api_smoke.py`** (the Flask + real SQLAlchemy models test file)
was written but **never executed** — it needs `flask_sqlalchemy`, which
also isn't installed in the build sandbox. It uses
`pytest.importorskip('flask_sqlalchemy')` so it skips cleanly (not an
error) rather than crashing the rest of the suite in an environment
that can't run it. **This is the single most valuable file to actually
run** — it's the first time the real HTTP request/response layer (not
just the underlying logic) would be exercised anywhere in this
project's history. See `docs/PROJECT_WORKFLOW.md` for the full,
repeated pattern this follows across every phase.

## Why some tests duplicate logic instead of importing it

`test_recalibration_math.py` copies `_degradation_from_actual()`'s
formula verbatim instead of importing it from `services/recalibration.py`,
because that module imports SQLAlchemy models at the top level (needed
for its real job), which pulls in `flask_sqlalchemy`. This is a real,
acknowledged tradeoff — if the formula in `recalibration.py` changes and
this test file isn't updated to match, the test would keep passing
while silently testing the wrong thing. The fix (extracting the pure
formula into a Flask-free module that both `recalibration.py` and this
test import) is straightforward but wasn't done here — noted as a
concrete follow-up rather than silently accepted.

## Why `services/ai_features.py` and `services/llm.py` have no test file

Both make real HTTP calls to Anthropic's API and, like `test_api_smoke.py`'s
dependency situation, weren't executed in the build sandbox (no network
there either). Their template-fallback paths (what runs when no
`ANTHROPIC_API_KEY` is set) WERE manually verified during Phase 3
development (see `docs/PROJECT_WORKFLOW.md`) but that verification was
never converted into a permanent test file. A reasonable next step, not
done here for time reasons.
