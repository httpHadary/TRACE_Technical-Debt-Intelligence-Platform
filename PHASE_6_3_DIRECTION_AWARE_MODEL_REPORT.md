# Direction-aware Adaptive Persistence — Phase 6.3

**PARTIAL — SYNTHETIC_ENGINEERING_TEST.** Numerical execution, identity/seal
checks and arithmetic verification passed. Overall phase validity is PARTIAL:
the30-day primary AP selection violated the preregistered protected fallback when
validation safety support was inadequate, and main30-day large-decrease evaluation
has no cases. These are validity/support limitations, not merely negative scores.
No registered source, coefficients, selected config, calibration, prediction, raw
outcome or cohort was changed after observing results. No corrected run occurred.

The integrated primary model exists and was fitted to384 NEW synthetic training
cases. It is current stock plus a conservatively chosen signed adjustment at each
horizon. Three normalized one-vs-rest logistic heads estimate unchanged/increase/
decrease scores, with optional training inverse-frequency class weights. Separate
positive/negative ridge models estimate signed conditional magnitudes. Raw component
values, sign projection, confidence gate, minimum magnitude, intentional shrinkage
and stock clipping are recorded separately. Negative signed predictions are valid.

Features reuse24 audited origin-only definitions: stock, observed changes/distinct
values, volatility, recent signed/absolute movements, slopes/averages, plateau lower
bound, extrema/scale, observation count, missingness and gap indicators. Null feature
medians/standardization use training only, with missing flags; observations are never
filled. Equal endpoints across a gap do not prove no interim change. Request/state/
config/horizon is the pure predictor signature; split/family/seed/future class and
changepoints are absent. Cached feature copies are immutable.

L2 penalties1/10; unpenalized intercepts;40 deterministic Newton half-steps. Three-
way eligibility requires at least2 training examples per class. Class counts and
coefficients are in models.json. Normalized OVR scores are not calibrated posteriors.
Binary threshold diagnostics do not equal the actual gated forecasting action.

| Days | Primary recorded AP config | Comparison champion | Validation large-decrease N |
| --- | --- | --- | --- |
| 30 | {'alpha': 1.0, 'balance': 'none', 'method': 'adaptive_persistence', 'minimum': 0.02, 'shrink': 0.5, 'threshold': 0.75} | persistence | 3 |
| 60 | {'alpha': 1.0, 'balance': 'none', 'method': 'adaptive_persistence', 'minimum': 0.02, 'shrink': 0.5, 'threshold': 0.75} | direction_gate | 18 |
| 90 | {'alpha': 1.0, 'balance': 'none', 'method': 'adaptive_persistence', 'minimum': 0.02, 'shrink': 0.5, 'threshold': 0.75} | direction_gate | 30 |

The recorded primary configuration is alpha1, no class weights, confidence0.75,
minimum0.02 and shrink0.5 at all horizons, multiplied by the origin-known gap
reliability factor. A volatility-aware minimum may suppress movement. Thirty-day
choice is not safety-admitted (3 validation large decreases versus required8); the
protected no-adjustment configuration should have been used. It was not, due to a
selector defect preserved and independently diagnosed. There is no post-test patch.
At60/90d the selected configurations satisfy the recorded validation constraints.

| Partition | Days | Direction macro-F1 | Multiclass Brier | Action precision | Action recall | Action F1 | False moves / misses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test | 30 | 0.813 | 0.263 | 0.983 | 0.351 | 0.518 | 1 / 109 |
| test | 60 | 0.756 | 0.346 | 0.983 | 0.309 | 0.470 | 1 / 132 |
| test | 90 | 0.745 | 0.365 | 0.983 | 0.280 | 0.435 | 1 / 152 |
| ood | 30 | 0.261 | 1.023 | 0.421 | 0.100 | 0.162 | 11 / 72 |
| ood | 60 | 0.198 | 1.011 | 0.370 | 0.125 | 0.187 | 17 / 70 |
| ood | 90 | 0.199 | 1.007 | 0.500 | 0.075 | 0.130 | 6 / 74 |

Raw direction head F1 is much higher than actual action F1 on main data, and both
shift poorly to OOD. Multiclass Brier is the sum over three classes (range0–2).
Action precision is high on main data because movement is rare, while recall is low.
High direction F1 does not establish useful debt forecasts. Precision/recall/F1,
PR/ROC AUC where defined, Brier, calibration bins and confusion matrices are all
published. Auxiliary0.5 OVR helper thresholds do not control the forecast; the AP
forecast confidence threshold is selected on validation, here0.75.

The primary model is not replaced by a trend or direct regressor when they win a
comparison. Protected persistence is intended as an integral valid action, not a
forced adjustment. The missing no-safe-primary guard needs a separately versioned
correction with regression coverage and a new unexposed study; it is not silently
repaired in these archived results. All prior states remain immutable.
