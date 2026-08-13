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

---

## Phase 4 additions

**Decision: `model_details` added as a new response field rather than
new columns on the `Prediction` model.**
Why: `confidence_note`, `models_in_ensemble`, and
`physics_baseline_degradation_pct` are display-only — nothing queries
or filters on them. Adding DB columns for display-only data means a
schema migration (and this project has no Alembic yet — see ticket
INFRA-1) for zero query-side benefit. Computing them fresh into the
response is cheap since `get_prediction()` already computes all three
internally either way.

**Decision: SEC-3 makes the demo account opt-out (`SEED_DEMO_USER=false`
to disable), not opt-in.**
Why: local development is still this project's primary use case right
now, and requiring an extra env var just to get a working demo login
locally would add friction to the common case. The real risk (a
well-known demo login reachable from the public internet) only exists
once this is actually deployed somewhere public — at which point
setting `SEED_DEMO_USER=false` is one line, clearly documented in the
README's Credentials section. Defaults optimize for the case that
happens 95% of the time (local dev) while making the production case a
one-line opt-out, not a research project.

**Decision: `load_model()`'s auto-train fallback checks "has ANY
required model ever been trained" (`REQUIRED_MODEL_FILES`), not "does
THIS specific requested model's file exist."**
Why: this is the fix for a real bug found during ML-4 testing (see
`PROJECT_WORKFLOW.md`) — checking the specific requested file meant an
optional, never-installed model (xgboost) triggered a full retrain on
every single request forever, since that file could never come to
exist. Checking against the *required* set (models every version is
guaranteed to produce) correctly distinguishes "nothing has been
trained yet" (auto-train once) from "this one optional model isn't
available for this version" (report unavailable, move on) — these are
different situations that need different responses, and conflating
them was the actual bug.

**Decision: model cache in `predict.py` is keyed by `(active_dir,
model_name)`, not just `model_name`.**
Why: this makes stale-cache-after-rollback structurally impossible
rather than something that has to be remembered to handle at every call
site. A version switch changes `active_dir`, which is part of the cache
key, so the next `load_model()` call naturally misses the cache and
reads the newly-active version's file from disk — no explicit
invalidation step required at the call site, though `clear_model_cache()`
is still called explicitly after `set_active_version()`/retrain anyway,
for prompt memory cleanup rather than correctness.

**Decision: ML-4's admin UI shows held-out test MAE AND real-world
calibration MAE per version, not just one.**
Why: these answer different questions — held-out test MAE says how well
a version fits its own (partly synthetic) training distribution;
real-world calibration MAE (Phase 1's benchmark-table check) says how
well it matches published field studies. A version could look better on
one and worse on the other. Showing only one would let an admin
"improve" the model by a metric that doesn't reflect real-world
accuracy — exactly the kind of misleading-single-number problem this
whole project has been correcting since Phase 1.

---

## Phase 4 additions (continued)

**Decision: CORS defaults to permissive (`*`) with a loud runtime
warning, rather than defaulting to a locked-down empty origin list.**
Why: a locked-down default would silently break the app for anyone
running it locally for the first time (the frontend and backend share
an origin in the default dev setup, but any deviation — a different
port, a proxy — would 403 with no obvious cause). A loud warning at
startup is the honest middle ground: nothing breaks by default, but
leaving it permissive can't happen silently or by accident.

**Decision: `retrain_with_real_data()` uses a fixed `real_weight=5`
oversampling factor rather than a formula that scales with how much
real data exists.**
Why: with too little real data (the expected state for a while), any
formula "tuned" against that same tiny sample is really just
overfitting the weighting scheme to noise. A flat, documented, easy-to
-change constant is more honest about being a judgment call than a
formula that looks principled but isn't actually validated against
anything. Revisit once there's enough real volume (dozens to hundreds
of reports) to hold out a real validation slice and actually tune this.

**Decision: `retrain_with_real_data()` is a separate admin action from
the plain `/admin/retrain`, not a checkbox on the same button.**
Why: blending in real data changes what "retrain" means in a way an
admin should consciously choose, not opt into by leaving a checkbox at
its default state. Keeping them as two distinct, clearly-labeled actions
makes it obvious after the fact which kind of training run produced any
given version (also visible in that version's `real_data_used` field in
its metadata, or its absence).

**Decision: community reports have an `is_flagged` moderation column
that nothing currently sets or checks in any UI.**
Why: added now because retrofitting a moderation flag onto an existing
table later is a real migration; leaving the column unused until a
moderation feature is actually built is a schema decision, not a
half-finished feature — `collect_real_outcomes()` already filters on it
so a future moderation UI has something to set without touching the
recalibration pipeline at all.

**Decision: FEAT-6 and FEAT-4 share one recalibration pipeline
(`services/recalibration.py`) instead of two separate ones.**
Why: both are fundamentally the same operation — "convert a real
reported outcome into a training row" — with different provenance
(tied to a prior prediction vs. standalone). Maintaining two conversion
pipelines that need to independently stay correct and in sync with
`train.py`'s `FEATURE_COLS` would be a real risk of the two silently
drifting apart over time; one shared function with two callers avoids
that by construction, the same reasoning as Phase 3's decision to give
`xai.py` and `predict.py` one shared feature-row builder instead of two.

---

## Phase 4 additions (continued: FEAT-1/2/3/5, RT-6, INFRA-1/2/3)

**Decision: RT-6 multi-waypoint weather is opt-in (`WEATHER_MULTI_WAYPOINT_ENABLED=false`
by default), not automatic for long routes.**
Why: it's a real, uncapped-by-default increase in weather-API call
volume proportional to route length. Auto-enabling it for "long enough"
routes would mean the app's API usage grows with usage patterns nobody
explicitly opted into. An explicit flag keeps that growth a deliberate
choice tied to whatever weather-API tier is actually being paid for.

**Decision: FEAT-3's scheduler uses APScheduler (in-process) rather than
a separate task queue (Celery + Redis/RabbitMQ).**
Why: this project's deployment target is a single Flask process; a real
task queue is real operational overhead (a broker, a worker process, its
own failure modes) that isn't justified until there's an actual
multi-worker deployment. The real limitation this creates (the job would
run once per worker process, not once total, under multiple gunicorn
workers) is documented in `scheduler.py`'s docstring rather than
discovered the hard way later.

**Decision: FEAT-3 logs "would have sent" instead of silently doing
nothing when `MAIL_USERNAME`/`MAIL_PASSWORD` aren't configured.**
Why: consistent with every other fail-soft pattern in this project
(weather demo fallback, physics prediction fallback, AI template
fallback) -- a misconfigured feature that quietly does nothing is worse
than one that's loud about not being able to do its job, because the
former looks like "it's working, nothing to alert on" instead of "it's
not configured yet."

**Decision: INFRA-1 did not include hand-written Alembic migration
files.**
Why: a migration file is supposed to be Alembic's own diff between the
models and the database schema, autogenerated by actually running
`flask db migrate` against a real database. Hand-writing one to
*simulate* having run that command would be presenting fabricated output
as a real tool's output -- a worse form of dishonesty than plainly
saying "wire the tool correctly (done) and run these three commands
yourself (not done here, no live DB in this sandbox)."

**Decision: INFRA-2's test suite duplicates one formula
(`_degradation_from_actual`) as a verbatim copy rather than importing it,
and says so directly in both the test file and `tests/README.md`.**
Why: the real function lives in a module that imports SQLAlchemy models
at load time, which isn't importable without `flask_sqlalchemy`. The
alternative (skip testing this formula at all) would leave real,
math-bearing logic with zero regression coverage. Duplication has a
real, named risk (drift between the copy and the original) that's
written down rather than hidden -- the honest tradeoff, not the clean
one.

**Decision: the manual test runner used throughout this project's
development is explicitly NOT presented as equivalent to `pytest`.**
Why: it does less than `pytest` (no fixtures beyond what's hand-rolled,
no parametrization, no proper test isolation, no reporting) -- claiming
"the test suite passes" without that distinction would overstate how
verified this code actually is. `tests/README.md` states plainly that
`pytest` itself needs to be run for real before trusting this as CI-ready.

---

## Final round additions (forecast predictions, share/PDF, model comparison, confidence tooltip)

**Decision: share tokens are generated lazily (on first "Share" click),
not at prediction creation time.**
Why: the overwhelming majority of predictions are never shared. Minting
a random token for every single prediction would be pure waste (and a
larger, permanently-unused attack surface of guessable-in-aggregate
tokens sitting in the database) for a feature most rows will never use.

**Decision: the public share page is a standalone template, not an
extension of `base.html`.**
Why: `base.html` does handle an anonymous `current_user` without
crashing, so extending it was technically possible -- but a share link
is meant for someone outside the app entirely. Showing them the full
authenticated sidebar (Trip Simulation, Community Reports, Admin, etc.)
would be confusing UI for an audience who can't use any of it without
first creating an account. The standalone page is a better-fit
audience decision, not a technical necessity.

**Decision: `individual_predictions` was added to the response instead
of being computed fresh by a new endpoint.**
Why: `get_prediction()` already computes every model's raw value
internally as part of deriving ensemble confidence (since Phase 1) --
it was being thrown away after use. Adding a new endpoint that
recomputes the same predictions a second time would waste real
compute for data the first call already had in hand.

---

## Authentication & User Management additions

**Decision: `CommunityRangeReport.user_id` was made nullable
specifically to support account-deletion anonymization.**
Why: on deletion, the choices were (a) cascade-delete a user's
community reports too, destroying real shared data other users might
be relying on for recalibration (`services/recalibration.py`), or
(b) leave a dangling foreign key, which isn't a real option, or
(c) null out the attribution and keep the data. (c) preserves the
data's real value (a temperature/range data point doesn't stop being
useful just because we no longer know who submitted it) while still
honestly deleting everything that's personally identifying about that
user. This required a real, deliberate schema change (nullable
column), not something papered over.

**Decision: email verification is a soft gate
(`REQUIRE_EMAIL_VERIFICATION=false` by default), not a hard login
block.**
Why: without `MAIL_USERNAME`/`MAIL_PASSWORD` configured, verification
emails are logged, not sent (same fail-soft pattern as FEAT-3's
alerts) -- a hard gate would mean nobody running this locally without
mail configured could ever get past registration. A banner + resend
button is the honest middle ground: verification is real and available,
but doesn't brick the app for the common local-dev case.

**Decision: OTP codes are hashed with plain SHA-256, not werkzeug's
slower `generate_password_hash`.**
Why: an OTP is a 6-digit code that expires in 5 minutes and is
rate-limited to 5 verification attempts -- its threat model is
completely different from a long-lived password hash sitting in a
database indefinitely. Using a slow, salted hash designed to resist
offline brute-forcing over years adds real latency for a value that's
already dead in minutes and can only be tried 5 times online anyway.

**Decision: OAuth-authenticated users get `email_verified=True`
immediately, no separate verification email.**
Why: Google and GitHub have already verified that email address as
part of their own account creation process (GitHub's case required
explicitly fetching the verified primary email via their `/user/emails`
endpoint rather than trusting a possibly-unverified public profile
email, precisely to make this true). Sending a redundant verification
email for an already-verified address would be pure friction.

**Decision: revoking a session takes effect via a `before_request`
hook checking a server-side `UserSession` table, not just by deleting
a row a UI happens to stop displaying.**
Why: Flask-Login's default cookie session has no server-side record at
all -- a "sessions" feature built only on top of that would be a list
that looks real but does nothing when you click "revoke." The
`before_request` check (validate the session cookie's token against
`UserSession.revoked_at`) is what makes revocation actually end that
device's access on its next request, not just remove a row from a
page.

---

## Battery Intelligence additions

**Decision: Battery Voltage Prediction and Internal Resistance
Estimation were declined outright, not implemented with a caveat
label.**
Why: unlike the temperature-degradation curve (Phase 1) or the
cold-start multiplier (this round), there is no real, citable,
general-purpose source for either of these that isn't specific to a
particular cell chemistry, pack design, and manufacturer's engineering
choices. A "rough approximation, not measured" label works when the
underlying phenomenon is at least qualitatively well-established and
citable in general terms (cold start, calendar aging). It does not
work here -- any number produced would be closer to invented than
approximated. The honest move was declining, not softening a fabricated
number with a caveat that most users would skim past anyway.

**Decision: the efficiency curve reuses the real trained prediction
model via a temperature sweep, instead of a dedicated formula.**
Why: a separate formula could silently drift from what the actual
prediction model says for the same vehicle and conditions -- two
numbers that are supposed to describe the same thing but come from two
different code paths is a real, avoidable risk. Sweeping the real model
guarantees consistency by construction, the same reasoning as Phase 3's
decision to give `xai.py` and `predict.py` one shared feature-builder.

**Decision: Battery Temperature Analysis aggregates this app's own
logged `WeatherLog` history instead of pulling a general climate
dataset.**
Why: a general climate dataset would need a new external API
integration and would describe a location's typical weather, not
anything about how THIS app's users have actually experienced it. Using
the real logged history is honest about being a smaller, app-usage-
dependent sample (explicitly reported as a sample size in the response)
rather than presenting a borrowed climate dataset as more authoritative
than it is.

**Decision: cold-start efficiency is informational (shown on the
Battery Health Dashboard), not silently blended into the main
`/api/predict` prediction.**
Why: the main prediction pipeline is already trained, tested, and
calibrated against real published benchmarks (Phase 1). Quietly adding
a cold-start multiplier on top would change already-verified numbers
based on a much rougher, qualitative approximation, without re-running
any of Phase 1's calibration work against the new combined output.
Keeping it as a separate, clearly-labeled estimate avoids
contaminating a more rigorously grounded number with a less rigorous
one.

---

## Phase 6 — User Dashboard (sidebar hub)

**Decision: "Saved Predictions" is a new bookmark table
(`SavedPrediction`), not a repurposing of `share_token`.**
Why: `share_token` (UX-5) answers "can a stranger view this without
logging in" -- an orthogonal concern to "do I personally want this
pinned for quick reference." Overloading share-token-is-set to also
mean "saved" would make revoking a share link accidentally unsave a
prediction the user still wanted bookmarked, and vice versa. A
separate join table, same shape as `FavoriteVehicle`
(`vehicle_interactions.py`), keeps the two concerns independent and
matches this project's existing "one small join table per interaction"
pattern instead of inventing a second one.

**Decision: "Saved Vehicles" in the sidebar is backed by the existing
`RecentlyViewedVehicle` table, not a new model.**
Why: `EVVehicle` has no per-user ownership column (it's a shared
catalog, not a garage), so "saved" can't mean "vehicles I added."
`RecentlyViewedVehicle` was already the only other real per-user
vehicle-interaction table besides favorites, already auto-populated by
`record_view()`, and already capped at 20 entries. Renaming its
surfaced label to "Saved Vehicles" (with a one-line explanation on the
page itself, and a link over to Favorites for anything meant to stick
around) was more honest than inventing a second, functionally
identical bookmarking table that would just duplicate
`SavedPrediction`'s job for a different model.

**Decision: Recent Activity is a merged read across five existing
tables (`recent_activity()` in `services/analytics.py`), not a new
`ActivityLog` table written on every user action.**
Why: an `ActivityLog` table would need a write hook added to every
existing action (predict, simulate trip, favorite, save, generate
report) -- more surface area for the log to silently drift out of sync
with what actually happened, for a feature that's read far more rarely
than it would be written. Every one of those actions already has its
own authoritative row in its own table; merging five small
`user_id`-scoped queries at read time is slower per-request but can
never desync from the real data, and needed zero changes to any
existing write path. Revisit only if this feed needs to show action
types that don't already have a backing table of their own.

**Decision: the "User Dashboard" sidebar section links out to
existing feature pages (Reports, the vehicle catalog's favorites
filter) rather than cloning their data into new dashboard-only views.**
Why: Report History (`reports/index.html`) and the favorites/recently-
viewed data were already fully built, tested surfaces. A second copy
of the same table on a new page would be one more place for the two
to drift out of sync (same "one shared implementation, not a second
copy" convention `feature_engineering.py` already documents) --
Favorite Vehicles got its own thin page anyway since the catalog page
buries it behind a filter checkbox, but Saved Reports links straight
to the existing Reports page rather than re-rendering its history
table a second time.

---

## Phase 7 — Admin Dashboard (sidebar hub)

**Decision: "Feedback Management" moderates `CommunityRangeReport` via
its existing `is_flagged` column, rather than a new feedback/bug-report
system.** Why: there was no other "feedback" concept anywhere in this
app to build a UI for -- but `is_flagged` on community reports has
existed since FEAT-4 specifically so a moderation feature could be
added without a schema change, and it was never actually wired to
anything. `community.list_reports()` already excludes flagged reports
from the public feed, and the recalibration pipeline already excludes
them from retraining data -- so this UI activates two enforcement
paths that were already live and silently waiting for an admin control
surface, rather than adding a new one.

**Decision: "System Logs" merges `LoginHistory` (already written on
every login attempt) with the live-retrain drift-check history, read
at request time -- no new `SystemLog`/audit table.** Same reasoning as
Phase 6's `recent_activity()`: every event surfaced here already has
its own authoritative row for its own reason (security audit trail,
drift monitoring), so merging at read time can't drift out of sync
with what actually happened, and needed zero new write hooks.

**Decision: "Weather API Monitoring" required two new nullable columns
on `WeatherLog` (`data_source`, `error_note`)**, unlike every other
Admin Dashboard page. Why: this is the one case where the data
literally didn't exist anywhere yet -- `get_current_weather()` already
computed live-vs-demo-fallback status transiently per-request but
never persisted it, so there was nothing to aggregate retroactively.
Both columns are nullable specifically so older `WeatherLog` rows
(from before this phase) don't need a backfill -- they just show as
"unknown" source, which the admin page states plainly rather than
guessing.

**Decision: "Analytics Dashboard" is a new page over the existing
`/admin/api/fleet-stats` endpoint (already used by the panel's
embedded Fleet Dashboard section), not a new data source.** "Prediction
Statistics" (the existing `/admin/analytics` -- per-model accuracy,
daily prediction counts) and "Analytics Dashboard" (whole-app usage:
users, vehicles, trips, community reports, top users) were kept as two
separate sidebar links because they answer different questions, but
both reuse data that already existed rather than each computing their
own copy.

**Decision: "Vehicle Management" and "Report Management" are
admin-wide *views* over existing per-user-scoped data, not new write
paths.** Vehicle Management surfaces `is_active=False` vehicles (the
public catalog always filters them out, and there was previously no
way to see -- or undo -- a soft-delete). Report Management shows every
user's `ReportSchedule`/`ReportHistory` rows, read-only; editing a
schedule stays the owner's action from their own Reports page, exactly
like Phase 6 kept Saved Reports pointed at the existing per-user
Reports page instead of cloning it.

---

## Phase 8 — Notifications (sidebar hub)

**Decision: Severe Weather Alerts has NO toggle in the new
`NotificationPreference` table.** It already has its own dedicated,
richer subscription model (`AlertSubscription`: per-location,
per-threshold, multiple subscriptions per user, own scheduler job)
from FEAT-3. A single boolean here would be strictly worse than what
already exists, so the sidebar item just links straight to the
existing `/alerts` page instead of duplicating a weaker version of it.

**Decision: Low Battery Alerts and Battery Health Warning are checked
synchronously (right when a trip is simulated / a SOH reading is
logged), not on a scheduler tick.** Both need data that's only computed
once, right at that moment (`estimated_arrival_battery_pct`, a new
`soh_pct` reading) -- there's no ongoing state to poll between then and
now, so a periodic job would just be re-checking the same already-known
answer. Charging Reminder and Maintenance Reminder DO need a scheduler
job, because "is now within N minutes of an upcoming reservation" and
"has the odometer passed the service threshold" are both time-dependent
questions that need to be re-asked as time passes, not just once at
write time.

**Decision: Maintenance Reminder is grounded in
`BatteryHealthRecord.odometer_km`** (the only mileage data this app
tracks anywhere) **compared against a user-set interval + baseline**,
not a real service-history log. This app has no concept of "vehicle
maintenance" at all otherwise (no service records, no dealer
integration) -- rather than inventing one, the reminder reuses data a
user already has a reason to log (via Battery Health) and asks them to
set one baseline (`/notifications/api/maintenance/mark-serviced`)
before it activates. Deliberately opt-in (`maintenance_reminders_enabled`
defaults False) since, unlike the other three alert types, it can't
produce a meaningful answer until the user has done that one-time setup.

**Decision: Push Notifications is real (uses the browser's
`Notification` API and requests permission), but explicitly scoped to
"while this tab is open."** True push notifications that work with the
tab closed need a service worker + a push subscription server (VAPID
keys, a push endpoint, background sync) -- infrastructure this project
doesn't have and that's out of scope to bootstrap for one toggle. The
preferences page says this outright rather than implying more than
what's actually implemented, same as `charging_reservation.py`'s
docstring being upfront that reservations aren't real bookings with any
charging network.

**Decision: Email Notifications' master switch stays on `User`
(`email_notifications_enabled`, pre-existing) rather than being
duplicated onto `NotificationPreference`.** `NotificationPreference.to_dict()`
reads it through the relationship so the API still returns one flat
preferences object; the notification-type-specific toggles (which
notifications are even eligible to email) live on
`NotificationPreference`, and the single account-wide on/off switch
stays exactly where it already was. `profile.html`'s existing
notification form was trimmed to just the two things that are genuinely
account-level (email master switch, new-device security alerts) and now
points to `/notifications/preferences` for everything else, rather than
forking the same settings across two pages.

---

## Phase 9 — Cost Analysis (sidebar hub)

**Decision: Electricity Price Integration is a regional-average lookup
table + a per-user saved-rate override, NOT a live utility-rate API.**
There's no free public API for residential electricity pricing the
way OpenWeatherMap exists for weather -- so, same honesty convention
as `charging_cost.py`'s `DEFAULT_RATES_USD_PER_KWH`,
`services/electricity_rates.py` is an explicitly-labeled table of
documented averages a user can pick from to prefill their own rate,
never presented as their actual bill. Every other Cost Analysis
feature reads through one resolver
(`services/cost_preferences.py::get_effective_rates()`) so "what rate
did this calculation use" always has one answer, and every result
labels whether it came from the user's own saved rate or a default.

**Decision: EV vs Petrol Cost Comparison, Ownership Cost Analysis, and
Savings Calculator share ONE engine
(`services/fuel_cost.py::compare_ev_vs_petrol()`).** They differ only
in which extra inputs get layered on top (purchase price + maintenance
for Ownership; an optional price premium + payback period for
Savings) and how the result is framed -- not in the underlying
cost-per-km math. Petrol-side defaults (price/liter, L/100km, annual
km) are documented generic estimates, explicitly not a specific
make/model, since this app has no petrol vehicle catalog and no live
fuel-price feed to draw real ones from.

**Decision: Ownership Cost Analysis defaults the EV purchase price
from `EVVehicle.price_usd` where set, but has NO default for the
petrol side.** The vehicle catalog already carries an (unverified,
nullable) approximate MSRP for exactly this kind of estimate; there's
no equivalent petrol-car catalog to draw a default from, so the result
says outright when a purchase-price comparison couldn't be completed
rather than silently comparing running costs alone as if that were the
whole picture.

**Decision: Charging Cost History (`ChargingSession`, a real logged
ledger) is a SEPARATE feature from Monthly Charging Cost
(`analytics_service.cost_analytics()`, which projects spend from
*simulated* trip energy).** Conflating "what you told us you actually
paid" with "what your simulated driving would cost" would misrepresent
one as the other. Both pages say explicitly which kind of number
they're showing and link to the other. A session's cost can be left
blank and auto-estimated from the user's saved rate (flagged
`is_cost_estimated: true`) rather than forcing manual entry for every
log, but a user-entered figure is never overwritten by an estimate.
