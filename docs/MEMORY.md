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
