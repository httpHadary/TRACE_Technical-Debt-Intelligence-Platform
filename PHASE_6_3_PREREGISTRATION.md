# Phase 6.3 — preregistered Adaptive Persistence protocol

SYNTHETIC_ENGINEERING_TEST. This protocol is fixed before fitting the registered
research population or scoring its forecasts. Earlier unit fits use only separate
analytical toy fixtures, not this population. The read-only failure audit was
published first in commit d116343, before the new design. All prior studies remain
frozen and all24 Phase C permission decisions remain NOT_APPROVED.

## Research questions and falsifiable targets

The primary candidate at30/60/90d is integrated **Adaptive Persistence**: current
stock plus an origin-known confidence-gated, direction-aware, conservatively shrunk
signed adjustment, clipped only afterward to nonnegative stock. Trend/direct models
are baselines or ablations. A separately labelled comparison champion may beat the
primary model, without replacing its research role or altering validation choices.

- H-AP: positive unfloored equal-family normalized MAE skill on the new main test
  at every horizon, with nonnegative changed-case skill and unchanged model-scale
  MAE<=0.02. Failure of any condition falsifies this registered combined target.
- H-direction: the three-way head and separate signed magnitude approach reduce
  matched normalized forecasting error relative to the new binary architecture,
  without either raw or normalized large-decrease skill falling below−5%. Report
  every horizon; a high classification F1 alone does not support the hypothesis.
- H-conservative: confidence/minimum-magnitude/gap-aware shrinkage reduces false
  movements versus the ungated asymmetric expectation, with full-population results
  and both sign-specific large-change errors retained. No subgroup-only success.
- H-shift: the fixed Adaptive Persistence model has nonnegative normalized skill
  at all horizons on eight wholly held-out mechanisms containing both endpoint
  classes. Main/OOD failures are retained. No OOD labels may select a model.
- H-interval: the fixed selected derived interval has75–85% coverage, mean
  model-scale width<=2, and normalized interval score no higher than the shared
  symmetric calibration baseline on the same AP points, separately on main/OOD.
  Failure is reported; no test-based widening or coverage guarantee is allowed.

These are proposed engineering tolerances, not universal scientific safety
thresholds, formal power calculations or real-world forecasting claims. Valid
execution with negative research results can still receive phase PASS.

## Fixed population and partitions

Root seed63020261020, new version phase6_3.adaptive-robustness.v1. SHA-derived case
seeds and separate observation/future noise streams. One origin per synthetic case.
Counts:384 train,192 validation,192 calibration,256 test,160 held-out-mechanism OOD.
The16 development mechanisms and eight OOD mechanisms are listed in population.py
and the machine registration. They cover plateaus, sudden/gradual reductions,
recovery/regression, returns to origin, repeated/reversing changes, hidden future
jumps, missing/irregular histories, noise, near-zero and mixed-scale debt.

Each OOD mechanism has20 cases: five stable-future, five interim-excursion/return,
five increased-endpoint and five decreased-endpoint cases at each horizon. This
balance is a predefined generator construction, not outcome-based filtering.
OOD mechanisms are absent from every training/validation/calibration partition.
Shared development families imply dependence, not independent software repositories.
Case/history/parameter identities must be unique and old Phase6.2 history hashes
must be disjoint. Violations block registration, with no post-outcome deduplication.

Histories contain180 genuinely generated calendar positions. Only actual retained
observations enter requests; sparse values retain explicit nulls, irregular dates
remain irregular, and the origin is measured. At least two observations must be
present within the final90 calendar days for common all-method eligibility; any
failure blocks registration. No method receives privileged eligibility or fills.
Targets are exact origin+30/60/90-day stock, signed difference and endpoint class.
An interim event that returns to origin is an unchanged endpoint, not a change.

## Models and fixed search budget

Twelve reported methods including a comparison alias: persistence; rolling mean
(last7 actual observations); anchored90-calendar-day trend; direct ridge delta;
trend shrinkage; residual blending; new binary adaptive model; three-way direction
gate; asymmetric probability-weighted signed changes; primary Adaptive Persistence;
frozen Phase6.2 selected-state transfer; and comparison_champion.

Exactly73 configurations per horizon,219 total; all grids are recorded in POLICY.
L2 penalties1/10, unpenalized intercepts,40 deterministic half-step Newton updates.
Direction classification is three normalized one-vs-rest logistic scores, none or
training inverse-frequency class weighting. They are not certified posterior
probabilities. Separate positive/negative conditional ridge heads keep raw
components and sign projections distinct. Unsupported classes are explicit failures.
Only NEW synthetic training data fit any new state or preprocessing.

The primary AP grid has33 configurations: one protected no-adjustment option, plus
penalties1/10 x none/balanced weighting x confidence0.75/0.9 x minimum0.02/0.1 x
shrink0.25/0.5. The magnitude floor is max(grid minimum,0.25*past normalized
volatility); shrink also multiplies1/(1+maximum observed gap days/30). There is no
future-derived reliability, true-direction gate, automatic0.5 forecasting threshold
or test-dependent rule. A protected no-adjustment selection is a valid negative
research result, not evidence of anticipated changes.

The original Phase6.2 coefficients, preprocessing, selected configs and calibration
must match exact registered hashes. They are applied only to NEW requests, never
retrained or silently replaced. A separately labelled binary architecture is fitted
to the new training data. Old cohorts/labels are not used for fitting or selection.

## Model selection and safety

Primary objective: equal-family validation MAE normalized by
max(1 minute,mean(abs(observed past))). Secondary raw MAE and persistence skill are
reported. Each candidate must satisfy unchanged normalized error<=0.02 and both
raw and equal-family normalized large-decrease MAE<=1.05 times persistence, with
at least eight examples in each safety stratum. A large change is
abs(delta)>=max(10 minutes,0.2*current). Insufficient strata make safety unverified.

Choose the best eligible candidate within each method; within1% of minimum error,
prefer the first registered config. Global comparison selection uses the registered
method order and same1% rule. If no safety evidence is sufficient, comparison
fallback is persistence; the primary remains AP and its protected no-adjustment
option. Thresholds, class weights, magnitude settings and blends never use final
main/OOD scores. All selected models and transforms are frozen, with no refit.

Reported normalized metrics use the UNFLOORED historical mean, excluding/counting
zero denominators. The explicit one-minute model/selection scale is not silently
substituted for those metrics. Raw and zero-history results remain in full coverage.

## Independent uncertainty protocol

Point model selection occurs first. Interval candidates: shared symmetric absolute
residuals, global signed10/50/90 residual quantiles, predicted-direction-stratified
signed residuals. Training in-sample residual prototypes support validation-only
choice (an acknowledged limitation); final distributions are refitted exclusively
on the separate calibration partition. Bins use predicted direction, not true future
direction. Bins with fewer than12 examples explicitly fall back to global residuals.

Widening is restricted to1 or1.25. Validation interval eligibility requires75–85%
coverage and mean model-scale width<=2. Choose minimum equal-family normalized
interval score among eligible options; if none qualify, choose minimum score but
record the quality failure. Final calibration never selects another configuration.
All three fixed calibration algorithms and the selected alias are reported on the
same AP points. Frozen Phase6.2 intervals are a separately labelled transfer
comparison with a different frozen point model. Asymmetric interval median may
differ from the fixed point forecast. No native quantiles or conformal guarantee.

## Scoring, sealing and failures

Train labels fit models; validation labels select; calibration labels fit final
intervals; main/OOD labels and interim-return diagnostics open only after complete
prediction/model/config/request/calibration seals verify. Inference receives only
Request/state/config/horizon. Split/family/seed/future flags are not features.
This is a logical role/file/interface boundary, not an adversarial OS sandbox.

Report raw/case/family MAE, RMSE, median error, bias, raw/normalized persistence
skill, excluding-mixed-scale sensitivity, unchanged/changed/increase/decrease/large
change/return-to-origin strata, false movements/missed changes, classification
precision/recall/F1/PR/ROC/Brier/calibration, per-family errors and matched pairs.
Direction metrics and actual forecast actions are distinguished. Undefined metrics
stay null.500 paired whole-family bootstrap draws, seed620, preserve16 main/eight
OOD mechanism clusters; no real-world significance or effective-repository claim.
Counterexamples use the largest model-scale excess per family after scoring only.

Interval reports include mean/median width, coverage and conditional coverage,
normalized width/score, interval score, pinball loss, collapse/ordering failures.
Complete populations and all failures remain accounted for. Unexpected software or
integrity failures abort, retaining evidence; no silent prediction fallback,
population reduction, quantile repair, retuning or automatic retry.

One sequential CPU worker,2GiB RSS, two numerical threads,900seconds,8MiB logs and
64MiB outputs. No native pretrained loading, networking, installation or new
checkpoint. Sampled RSS/HWM plus final ru_maxrss are recorded on success/ordinary
failure; abrupt-kill missing measurements stay unavailable. No limit increase.
All earlier sources/artifacts/rights decisions remain immutable. Publish results,
then STOP. This protocol grants no Phase6.4, scanning or real-data authorization.
