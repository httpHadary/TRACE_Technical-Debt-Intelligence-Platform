# Phase 6.3 — uncertainty calibration under shift

**PARTIAL — SYNTHETIC_ENGINEERING_TEST.** Numerical execution, identity/seal
checks and arithmetic verification passed. Overall phase validity is PARTIAL:
the30-day primary AP selection violated the preregistered protected fallback when
validation safety support was inadequate, and main30-day large-decrease evaluation
has no cases. These are validity/support limitations, not merely negative scores.
No registered source, coefficients, selected config, calibration, prediction, raw
outcome or cohort was changed after observing results. No corrected run occurred.

The Phase6.2 interval shortfall motivated this new comparison; its old coverages
remain unchanged. Candidate intervals here use the NEW primary AP points, with
separate training/validation/calibration roles. Native pretrained intervals are
not available and no native quantiles are sorted or repaired.

Three fixed methods: symmetric absolute normalized residual radius, signed global
10/50/90 residual quantiles, and signed residual quantiles stratified by PREDICTED
forecast direction. Actual future direction never chooses an inference bin. Bins
with fewer than12 calibration examples explicitly reuse the global distribution;
fallback flags/counts are recorded. Training in-sample residual prototypes support
validation-only choice, an acknowledged optimism/transfer limitation. Final residual
laws use only192 independent calibration cases. No test residual influences them.

The selected method at every horizon is direction_stratified with widening1.0.
Only1/1.25 widening was admitted. Validation required75–85% coverage and mean
model-scale width<=2, then minimized normalized interval score. Final quality also
requires interval score no worse than shared calibration on the SAME AP points.
If no validation option passed, its failure would remain explicit. No arbitrary
post-test widening or new choice occurred. An asymmetric interval median can differ
from the fixed point forecast; point predictions themselves are not recalibrated.

| Partition | Days | Selected coverage | Mean / median width | Shared coverage | Frozen-transfer coverage |
| --- | --- | --- | --- | --- | --- |
| test | 30 | 80.47% | 767.212 / 59.647 | 77.73% | 67.58% |
| test | 60 | 83.20% | 921.076 / 176.436 | 82.81% | 80.08% |
| test | 90 | 78.12% | 1,470.123 / 205.133 | 81.25% | 77.34% |
| ood | 30 | 44.38% | 55.954 / 56.715 | 52.50% | 61.25% |
| ood | 60 | 62.50% | 192.054 / 186.111 | 76.25% | 73.12% |
| ood | 90 | 81.25% | 235.276 / 225.715 | 86.88% | 88.75% |

Main selected interval score/normalized width improves against shared calibration,
with nominal coverages80.47/83.20/78.12%. The30d point-policy deviation still prevents
promoting that result to a compliant primary study result. On OOD, selected coverages
44.38/62.50/81.25% contrast with shared52.50/76.25/86.88%. Selected OOD interval scores
are worse than shared at every horizon.90d coverage approaches nominal80%, but it
fails the combined score criterion. No claim of reliable OOD uncertainty is justified.

Mean widths are scale-driven; medians and normalized widths are reported. The selected
intervals have0 collapsed/invalid rows, which does not establish calibration. Full
changed/unchanged/large-increase/large-decrease conditional coverage, interval score,
pinball loss and widths appear in interval_metrics.csv. Main30d large-decrease
conditional coverage is unavailable because n=0. Small strata remain exploratory.

Frozen_phase6_2_interval uses its ORIGINAL point model and original calibration on
new inputs; it is a transfer diagnostic with a different point parent. The shared
versus stratified comparison on identical AP points is the calibration-only ablation.
Do not compare old Phase6.2 and new Phase6.3 coverages as matched-cohort evidence.

Plausible causes of OOD failure include shifted residual shape, the shared/global
fallback assumption, direction misclassification, unobservable future branches,
scale mismatch and different zero-change frequency. The held-out population has
50% unchanged endpoints; prior OOD had none. No causal attribution was proven by
this experiment. A future study needs development-only conditional calibration and
shift diagnostics on a new preregistration; no test-informed width/threshold change
or distribution-free coverage guarantee is allowed here.
