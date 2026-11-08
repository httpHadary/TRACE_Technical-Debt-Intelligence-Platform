# Change-aware forecasting: proposed research, not a fitted model

No classifier, calibrator, blend or residual model was trained in Phase 6.0.
`predictors.py` implements only past-only descriptive features and mathematical
reconstruction/gating/blending interfaces, tested with generated inputs.

Let `C_h = 1[Debt(t+h) != Debt(t)]`. Stage 1 estimates `P(C_h=1 | X_past)`;
Stage 2 estimates the signed conditional change distribution. Reconstruct stock
with `max(0, current + delta)`, retaining raw estimates in an actual experiment.
Negative delta is valid even though stock cannot be negative. A mean forecast
could use `p_change * E[delta | change]`; **this is not generally the optimal median
for MAE**. A mixture median or validation-selected rule must be studied explicitly.
Do not assume a 0.5 gate or a probability is remediation effort.

Past inputs can include current stock, observed changes, distinct observed values,
observed transition fraction, volatility and elapsed time since an observed
transition. With gaps, transitions and last-change times are censored: identical
adjacent observations do not prove nothing happened between them. The implemented
features mark gaps and call these *observed* transitions, not true event rates.
No previous value replaces an unknown origin. Git/process features remain outside
this synthetic harness and need their own availability/domain/rights evidence.

## Research hypotheses and falsifiable plans

All costs below are **planning budgets**, not measured model throughput. A later
CPU experiment starts with ≤2 GiB worker RSS, ≤2 computational threads and ≤900 s
per bounded worker. Refuse a candidate exceeding admission; do not weaken limits.

| ID | Motivation, inputs and proposed method | Mandatory comparison / metrics | Leakage risks and falsification |
| --- | --- | --- | --- |
| H1 | Stock persistence can hide rare changes. Use admitted past stock and a pinned direct pretrained model; score changing cases after prediction. | Persistence on identical full IDs and changed strata; macro MAE/skill, RMSE, large-change error, failures. | Selecting origins because future changes are large is oracle selection. Falsified for a registered setting if independent full/changed-case paired gains fail the registered improvement criterion. |
| H2 | 90 daily positions may contain little independent information. Compare predeclared 90/180/512 contexts where genuinely measured/admitted histories exist; include distinct measurement/state counts. | Matched persistence and same model/checkpoint; macro MAE, skill, runtime/RSS. Report context-related coverage losses. | Different eligible populations, padding and future-informed context choice confound comparisons. Falsified if longer-context gains disappear on matched new families or costs exceed budget. |
| H3 | Unnecessary movement harms unchanged cases. Train a small change classifier plus conditional magnitude model on admitted training origins. | Persistence, direct pretrained, ungated residual; full/changed/unchanged MAE, PR-AUC/Brier for the *separate change task*, calibration and inference cost. | Future deltas define training labels only; no future status at inference. Falsified if gating reduces unchanged error but worsens preregistered overall/large-change risk. |
| H4 | Signed increments may be easier to model than stock levels in some domains. Compare anchored residual/delta regression and past-only differenced contexts. | Same stock-level endpoints and persistence; macro MAE/RMSE, signed bias, failure/clip rate. | Origin anchoring, inverse transforms and differencing masks must be past-only; no future scaling. Falsified if residual reconstruction fails to generalize or merely shifts bias. |
| H5 | Complementary error patterns might support a blend. Freeze `current + w*(candidate-current)`, or a trained past-feature gate. | Both parents and persistence; paired macro skill, changed/unchanged performance and cost. | Weight/gate selection uses validation only; test results cannot choose the blend. Falsified if no validated weight beats persistence on new frozen families. |
| H6 | Risk ranges may help even without lower MAE. Use native valid intervals, then a separately registered train/calibration-only block/conformal or residual procedure. | Uncalibrated intervals, simple historical-change intervals; nominal 80% coverage, width, interval score, pinball loss, conditional collapse/misses. | Calibration cannot see test residuals or overlapping future windows. Falsified if coverage misses its tolerance or only improves by unacceptably broad intervals on new families. No iid conformal guarantee for overlapping origins. |
| H7 | Origin-known Git/process activity may anticipate changes. Compare debt-only features against F0/F1 plus verified Git activity with Ridge or bounded CatBoost. | Identical origins, persistence and debt-only controls; macro skill, ablation, bias and failures. | Commit/availability clocks, churn conflicts, analyzer drift and SZZ future fixes. Falsified if gains vanish with strict as-of admission, domain control and family holdout. |

## Data and independence required before any real test

These are study-design gates, **not a claim of statistical power**:

- H1/H3/H4/H5/H7 require enough observed changing and unchanged origin-endpoint
  pairs at each exact horizon in disjoint training/validation/new-test families.
  Plan ≥20 independent test families and ≥10 nonoverlapping changing windows per
  horizon as a feasibility screen, then perform power/precision planning from
  development-only repository-level paired variability. If infeasible, label
  results exploratory and report actual cluster/event counts; do not reuse the
  published Java holdout as a new confirmatory test.
- H2 additionally needs legitimate 180/512-day histories with known masks and
  sufficient distinct underlying measurements. A 512-day repeated-state grid is
  not 512 independent observations. Freeze a common-origin comparison and a
  separate coverage analysis; never fabricate context by padding or upsampling.
- H6 needs separate calibration families or temporally purged calibration blocks,
  with measured future endpoints, enough independent errors for the chosen
  quantile and explicit dependence assumptions. A handful of constant sequences
  cannot establish calibrated risk.
- H7 needs complete past Git/event availability and compatible analyzer/scope
  domains. Existing F2 churn remains disabled; 23,321 conflicting keys were not
  resolved by this phase. Analyzer licensing and derived-data rights remain blocked.

All hypotheses can receive mechanical checks on synthetic data: leakage rejection,
exact endpoint mapping, reconstruction, sign handling, scoring, coverage and
resource behavior. **None can be confirmed for technical debt by synthetic gains.**
Simple linear trajectories deliberately reward extrapolation; unobservable future
jumps demonstrate limits rather than prove a learned predictor is deficient.

## Later protocol and decision rule

Register the estimand, native units, candidate/context grid, data admission,
origin/endpoint policy, missingness, failure policy, large-change definition and
metric formulas before fitting. Use chronology with a ≥90-day target purge plus
context/measurement-overlap audit; group related repositories/forks together.
Fit transforms/models on training only, choose settings on validation, calibrate
on a separate permitted partition, then freeze configuration and seal all new
family-test predictions before label access. Compare identical IDs, show full
attempt/failure coverage and success-matched sensitivity analyses. Bootstrap
repository families with paired draws; account for within-family overlapping
windows and report context diversity separately from effective sample size.

A proposed confirmatory success criterion is positive paired macro-MAE skill with
95% repository-family CI excluding zero, alongside predeclared practical benefit,
large-change safety and resource criteria. The practical effect and precision
requirements must be set with development-only planning, before test outcomes.
Negative results, blocked candidates and persistence retention are valid outcomes.
No dataset, fit or test execution is authorized by this document.
