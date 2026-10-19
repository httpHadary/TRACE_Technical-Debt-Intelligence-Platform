# Change detection model — Phase 6.2

**SYNTHETIC_ENGINEERING_TEST.** Three horizon-specific regularized logistic heads
estimate `P(Debt(t+h)!=Debt(t) | past)`. This is endpoint change, not any interim
change event. Only384 original synthetic training cases provide labels.

The24 features are enumerated by `features.NAMES`: current stock, observed changes,
observed transition fraction, elapsed time since last observed endpoint transition,
distinct value count, volatility, recent signed/absolute observed differences,
short/long OLS slopes and averages, contiguous observed plateau lower bound,
min/max, historical scale, relative variability, observed sample count, missing
fraction, mean/max measurement gap, contiguous daily transition fraction, gap flag
and zero-scale flag. Count/time features use registered180-day reference units.
Stock/delta features use the explicitly floored model scale. Log scale is past-only.

Across-gap differences do not identify when or how often actual changes occurred.
Equal observed endpoints across a gap do not prove unchanged debt. The plateau
lower bound stops at a gap. Null feature columns (for example undefined variation
at zero stock) use training-only medians and additional missing indicators; no
observed history is imputed. A measured origin and at least two observations are
required. No Git/process, family, split, source ID hash or future flag enters X.

Preprocessing means/scales, null medians and all coefficients are in
[models.json](examples/phase6_2/models.json). Features/indicators are standardized
using training only; constant columns have unit scale. The model uses float64,
no stochastic fitting, no class weights, L2 penalties1/10 and40 fixed half-step
Newton iterations. The intercept is unpenalized. Single-class samples return an
explicit ineligible-logistic diagnostic and empirical constant probability rather
than silently claiming a valid classifier fit. Insufficient conditional magnitude
support is separately rejected. Training seed provenance is fixed generator seed
62020261020 and distinct SHA-derived per-case streams.

Thresholds0.1/0.25/0.5/0.75/0.9 were considered before fitting. Selection optimizes
forecasting error, not F1;0.5 is not an automatic rule. The chosen hard-gate thresholds
are0.75/0.5/0.75. Logistic/ridge penalty for the hard gate is1/10/10 at30/60/90d.
Every transform and fit uses training only, threshold/config selection validation
only. No classifier is fitted again after test evaluation.

| Days | Threshold | Precision | Recall | F1 | PR-AUC (AP) | ROC-AUC | Brier | Positive prevalence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 30 | 0.75 | 1.0000 | 0.9493 | 0.9740 | 0.9974 | 0.9924 | 0.0226 | 0.7188 |
| 60 | 0.5 | 0.9401 | 0.9691 | 0.9544 | 0.9943 | 0.9677 | 0.0579 | 0.8438 |
| 90 | 0.75 | 0.9880 | 0.9322 | 0.9593 | 0.9957 | 0.9507 | 0.0436 | 0.9219 |

These192-case test classification results use true change only as an evaluator
label. Positive prevalence increases with horizon; unchanged counts are54/30/15.
The synthetic population is not intended to replicate the Java unchanged rate.
Precision/recall/F1 and PR/ROC AUC do not measure continuous forecasting accuracy.
PR-AUC is stepwise average precision with probability ties grouped; ROC uses pair
ranking with half credit for ties. Undefined single-class AUCs are null. All48 OOD
cases are positive at each horizon, so their ROC/PR summaries are undefined.
Brier scores and five fixed probability bins are reported without claiming perfect
calibration or adding a test-selected calibrator.

At30d hard gating makes0 false-change decisions and7 missed-change decisions.
At60d it makes10 false positives and5 false negatives; at90d2 and12. Point-stock
movement diagnostics can differ from class decisions because a conditional delta
may be zero or clipping may map a forecast back to the origin stock. Both are
reported separately. Full bins/confusion counts:
[classification_metrics.json](examples/phase6_2/classification_metrics.json).
No real debt labels or pretrained classifier was used.
