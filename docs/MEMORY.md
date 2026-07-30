# Memory — Key Design Decisions & Reasoning

A running record of *why*, not just *what*, for decisions that aren't
obvious from reading the code alone. Intended for future-you (or anyone
picking this up) to avoid re-litigating settled questions, and to know
which decisions were deliberate trade-offs vs. accidents of history.

---

**Decision: ground only the temperature→degradation relationship in
real data, and be explicit that other factors (HVAC, terrain, wind,
battery age, speed, weight) remain engineering estimates.**
Why: real row-level telemetry linking all of these simultaneously isn't
publicly available without a login-gated or non-commercial-licensed
source (checked — see `TECHNICAL_ARCHITECTURE.md` §5). The alternative
was either (a) keep everything synthetic and call it "AI-powered" anyway
(the original problem), or (b) ground what real data actually supports
and say so plainly for the rest. (b) is more defensible and, honestly,
more useful — a half-real model that's labeled accurately beats a
fully-synthetic model that's oversold.

**Decision: isotonic regression instead of a parametric curve fit
(e.g. polynomial or exponential) for the physics baseline.**
Why: isotonic regression's only assumption is monotonicity, which is
physically true here (colder = at least as much degradation, up to the
sweet spot) and nothing more. A polynomial fit would impose a specific
*shape* assumption that isn't supported by only ~7-8 anchor points and
risks overfitting an artifact of few points rather than the real
relationship. Isotonic regression is also easy to explain to a
non-specialist reviewer: "the curve only gets worse as it gets colder,
fit as closely as possible to the real numbers" — no coefficients to
justify.

**Decision: cap the physics baseline's scope at ~21.5°C (the Geotab
"sweet spot") and treat everything warmer as 0% degradation.**
Why: this project is titled and scoped as *cold*-weather degradation.
Geotab's data shows a real U-shape (heat also degrades range), but heat
degradation is a different mechanism (thermal management, cooling loads)
without comparable citation coverage gathered here. Modeling the hot
side without equal rigor would reintroduce the exact "looks precise but
isn't grounded" problem this phase was meant to fix. Flagged as a
deliberate scope boundary, not an oversight — if hot-weather degradation
becomes in-scope later, it deserves its own calibration pass, not a
guess bolted onto this curve.

**Decision: expose `physics_baseline_degradation` as an ML input
feature, rather than either (a) using the ML model alone, or (b) using
a residual-correction architecture where the ML model predicts
`degradation - physics_baseline` directly.**
Why: (a) was the original problem — a model with no grounding to
correct toward. A pure residual architecture (b) is arguably more
"proper" physics-informed ML, but it changes the target variable's
shape and would require larger changes to `predict.py`'s downstream
math (range/energy/charging calculations, which all currently expect a
degradation percentage) and to the SHAP explanation path, for a project
where the priority was shipping a real, verified fix quickly. Feeding
the baseline in as a feature is a lighter-weight, well-established
middle ground (the model can learn to weight it however it wants,
including effectively reproducing residual behavior) and kept the
blast radius of the change contained. Revisit if a future phase adds
enough real training data to justify the more complex architecture.

**Decision: fixed `BASELINE_TRIP_CONDITIONS` for the calibration check,
not `X_train.median()`.**
Why: found via a real bug (see `PROJECT_WORKFLOW.md` Bug #3) — training
medians reflect the synthetic sampling distribution, not what the field
studies actually measured (ordinary daily commuting). A calibration
check is only meaningful if it isolates the same thing the ground truth
measured. This is a deliberately hand-picked, documented baseline
rather than something derived from the data, on purpose.

**Decision: model versioning writes a new `v<N>_<timestamp>/` directory
every run, but `predict.py` still reads from the flat `saved_models/`
copy rather than `current_version.json`.**
Why: full version-awareness in `predict.py` (hot-swappable rollback,
etc.) is real future work (ticket ML-4), but doing it properly means
deciding on a rollback UX, possibly a version-selection admin control,
and testing concurrent-request behavior during a version switch — scope
that didn't belong in "make the model honest," which was Phase 1's job.
Shipping the versioned storage now (even if `predict.py` doesn't fully
exploit it yet) means the metadata/history isn't lost while that follow-up
work is designed properly.

**Decision: confidence is ensemble disagreement (std dev across models),
not a formal statistical uncertainty method (e.g. quantile regression
forests, conformal prediction).**
Why: ensemble disagreement is simple, requires no architecture change
to any of the four models, and directly answers the practically useful
question ("do independently-trained models agree on this input, or is
it in a weird region they extrapolate differently on?"). It is *not* a
calibrated probability — the 12-percentage-point spread → 0 confidence
scaling in `_ensemble_confidence()` is a judgment call, documented as
such in the function's docstring, not dressed up as more rigorous than
it is. A formal method is a reasonable Phase 2+ upgrade once there's
real held-out data to calibrate against, rather than synthetic data
that would make a "calibrated" number circular in the same way the
original confidence=0.85 was.

**Decision: keep the rule-based (non-ML) explanations in `xai.py`
as-is, rather than trying to make everything ML-derived.**
Why: they're legitimate, honestly-labeled expert-system rules (if
temp < -15, say so) — the actual problem this phase targeted was code
that *pretended* to be more than it was (fake confidence, uncoupled
synthetic training data), not the existence of rule-based logic itself.
Rule-based explanations that are clearly rule-based are fine.

**Decision: document what wasn't tested (full Flask app, XGBoost path)
rather than imply full coverage.**
Why: consistent with the whole point of this phase — the original
project's core flaw was presenting untested/ungrounded work as more
solid than it was. Applying a lower bar to this phase's own delivery
would be self-defeating.

---

## Phase 2 additions

**Decision: three separate free/keyless providers (Nominatim, OSRM,
Open-Elevation) instead of one paid all-in-one provider (e.g. Google
Maps Platform, Mapbox).**
Why: the project has no API budget signal from the project owner, and
Phase 1 already established a pattern of preferring free/verifiable
sources over convenient-but-costly ones. The tradeoff is documented
explicitly (OSRM's demo server isn't production-grade — ticket RT-4)
rather than hidden, so switching to a paid provider later is a clear,
scoped upgrade, not a surprise.

**Decision: fail loudly on geocoding/routing failure, fail softly (with
a labeled fallback) on elevation failure, in `route_predict()`.**
Why: geocoding/routing are load-bearing — without them there's no route
to predict over at all. Elevation is an enrichment of one input feature
(`terrain_type`), which already has a reasonable manual-input fallback
from Phase 1. Failing the whole request over a secondary enrichment
would make the feature more fragile than it needs to be. This mirrors
the physics-fallback pattern from Phase 1's `predict.py` — always keep
serving a (labeled) answer over refusing outright, wherever the missing
piece isn't actually essential.

**Decision: elevation-gain thresholds (150m / 500m per 100 sampled
points) for terrain classification are a documented judgment call, not
derived from a cited standard.**
Why: unlike the temperature curve (where real published anchor points
exist), no equivalent public "elevation gain → EV range impact"
benchmark was found during Phase 2. Rather than either (a) invent a
false citation, or (b) skip real terrain classification entirely, the
honest middle ground is: use a *real, measured* elevation profile (not
a guess) and be explicit that the bucket boundaries mapping that real
number onto flat/hilly/mountainous are engineering judgment. This is
the same "ground what's groundable, label the rest honestly" pattern
from Phase 1, applied to a new input.

**Decision: hand-verify two vehicle spec entries via web search rather
than wait until `sync_openev_data.py` can be run.**
Why: the sync script needs network access this sandbox doesn't have, but
"we'll fix the data later" with zero real corrections delivered now
would repeat the exact pattern (claiming groundwork without doing any of
it) that Phase 1 was meant to move away from. Two real, cited
corrections shipped now, with the rest explicitly labeled unverified
(not silently implied to be fixed), is more honest than either extreme.

**Decision: `scripts/sync_openev_data.py` ships even though it was never
executed.**
Why: it's clearly labeled as unverified in its own docstring, has a
`--dry-run` mode specifically so it can be sanity-checked before writing
to a database, and captures real engineering work (the field-mapping
logic between OpenEV Data's schema and this project's `EVVehicle`
schema) that would otherwise need redoing from scratch later. Shipping
labeled-unverified code is fine; shipping it *unlabeled* would not be.

---

## Phase 3 additions

**Decision: the LLM only ever phrases already-computed facts; it never
computes a number.**
Why: this is the load-bearing decision for the entire phase, made before
any code was written. An LLM asked to "estimate" or "adjust" a range
figure would be reintroducing an ungrounded number dressed up as more
credible than a hardcoded constant, since fluent prose reads as more
authoritative than a bare number — arguably a regression from Phase 1's
whole point, not a step forward. Every prompt in `ai_features.py`
enforces this via `GROUNDING_RULES`, repeated in every system prompt
rather than assumed to carry over.

**Decision: anomaly detection (AI-3) is split into a pure-arithmetic
`detect_anomaly()` and an LLM-only `narrate_anomaly()`, never combined
into one LLM call.**
Why: "is this anomalous" is a factual question with a real, computable
answer (deviation from the Phase 1 calibrated baseline) — asking an LLM
to make that judgment would substitute a real computation for a guess,
which is strictly worse. The LLM's only job is turning an
already-true finding into a sentence. This mirrors the physics-baseline
architecture decision from Phase 1 (ground what's groundable, use the
model only where it adds value on top).

**Decision: 20 percentage-point anomaly threshold, not tuned further
after the first test surprised us.**
Why: initial testing (see `PROJECT_WORKFLOW.md`) showed extreme-cold
scenarios don't trigger the flag, because both the physics baseline and
the ML prediction share the same 65% cap and can't diverge past it by
much. This was left as-is rather than "fixed" to catch extreme-cold
cases too, because the threshold is correctly catching what it's
actually good at catching (mild-temperature trips where non-temperature
factors are doing unusually heavy lifting) — chasing a lower threshold
just to catch capped-value scenarios would mean flagging routine extreme
cold as "anomalous" by definition, which isn't useful. Documented as a
known shape of the detector, not silently left unexplained.

**Decision: `services/llm.py` returns `(text, error)` tuples, matching
`services/geo.py`'s pattern from Phase 2, rather than raising
exceptions.**
Why: consistency across the two external-API service modules means a
future contributor only needs to learn this error-handling pattern
once. Both modules wrap third-party HTTP calls with the same "can fail
for lots of reasons outside this app's control" profile, so the same
shape fits both.

**Decision: `/predictions/api/<id>/ask` takes free-form driver input and
passes it into an LLM prompt, with only instruction-following as the
prompt-injection defense (no input sanitization or output filtering).**
Why: the blast radius is deliberately limited — the LLM has no tool
access and can't take actions, so a successful injection only affects
what text is shown back to the same user who wrote the prompt (see
`SECURITY_AND_ACCESS.md` §7). Building a hardened defense (classifier-
based guards, etc.) for an endpoint with this limited a blast radius
would be effort spent on the wrong risk relative to what's actually
exposed. Revisit if a future phase gives this endpoint tool access or
cross-user data visibility — that would change the risk calculus
entirely.

**Decision: worst-case (colder) weather selection between origin and
destination for RT-5, not an average.**
Why: this is a cold-weather-focused range prediction tool — the failure
mode that matters most is a driver arriving with less charge than
expected, not more. Optimistically averaging two temperature readings
would understate the risk in exactly the direction that matters. This
mirrors treating "which failure mode is worse" as the deciding factor,
same reasoning style as Phase 2's fail-loud-vs-fail-soft decision for
`route_predict()`.

**Decision: full multi-waypoint weather sampling (RT-6) was scoped out
rather than attempted as part of RT-5.**
Why: it has a real, distinct cost/rate-limit tradeoff against the free
OpenWeatherMap tier (one API call per waypoint vs. two fixed calls per
route) that deserves its own explicit decision once there's a real
signal about API budget/tier, rather than silently defaulting to
"more calls" or "fewer calls" inside an unrelated change.
