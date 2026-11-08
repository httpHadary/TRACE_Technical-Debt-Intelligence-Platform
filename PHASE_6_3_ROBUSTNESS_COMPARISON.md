# Phase 6.3 robustness comparison

**PARTIAL — SYNTHETIC_ENGINEERING_TEST.** Numerical execution, identity/seal
checks and arithmetic verification passed. Overall phase validity is PARTIAL:
the30-day primary AP selection violated the preregistered protected fallback when
validation safety support was inadequate, and main30-day large-decrease evaluation
has no cases. These are validity/support limitations, not merely negative scores.
No registered source, coefficients, selected config, calibration, prediction, raw
outcome or cohort was changed after observing results. No corrected run occurred.

Adaptive Persistence remains primary; the comparison champion never replaces it.
All methods receive identical admitted past histories and exact30/60/90-day targets.
Main256 cases/16 families; OOD160 cases/eight held-out families. All12 reported
methods (including an alias) have complete coverage, no runtime exceptions or
selectively omitted cases. Shared mechanisms/branches limit independence.

| Method | 30d MAE | 60d MAE | 90d MAE | 30d normalized skill | 60d normalized skill | 90d normalized skill |
| --- | --- | --- | --- | --- | --- | --- |
| persistence | 121.907 | 105.286 | 188.532 | +0.00% | +0.00% | +0.00% |
| rolling_mean | 129.688 | 114.794 | 198.620 | -22.19% | -10.44% | -6.49% |
| anchored_trend | 160.266 | 197.255 | 312.171 | -20.03% | -7.20% | -3.01% |
| trend_shrink | 121.907 | 105.286 | 188.532 | +0.00% | +0.00% | +0.00% |
| direct_delta | 113.830 | 111.828 | 164.068 | -9.53% | -4.22% | +14.61% |
| residual_blend | 113.830 | 131.012 | 148.299 | -9.53% | +0.71% | +5.43% |
| binary_adaptive | 106.363 | 238.501 | 167.904 | +22.47% | +5.88% | +21.64% |
| direction_gate | 170.146 | 316.337 | 200.951 | +42.39% | +45.83% | +40.33% |
| asymmetric_weighted | 182.911 | 243.605 | 171.250 | +25.29% | +30.16% | +28.13% |
| adaptive_persistence | 140.114 | 177.244 | 169.107 | +18.21% | +12.69% | +9.76% |
| frozen_phase6_2 | 152.017 | 268.576 | 312.171 | -189.65% | -20.37% | -3.01% |
| comparison_champion | 121.907 | 316.337 | 200.951 | +0.00% | +45.83% | +40.33% |

Thirty-day AP rows are descriptive after a detected fallback deviation. Raw
numbers across columns do not mix old cohorts. Frozen_phase6_2 uses exact ORIGINAL
state/preprocessing/selected configs/calibration on NEW inputs, no retraining.
Binary_adaptive and other new models use only NEW training labels. Their states,
request-membership hashes and model identities are distinct. Comparison_champion
is a validation-selected alias, not a separately fitted twelfth model.

| Days | Persistence MAE | Primary AP MAE | Raw skill | Normalized skill | Primary selection status |
| --- | --- | --- | --- | --- | --- |
| 30 | 121.907 | 140.114 | -14.94% | +18.21% | DEVIATION: safety not admitted |
| 60 | 105.286 | 177.244 | -68.35% | +12.69% | Validation safety-admitted |
| 90 | 188.532 | 169.107 | +10.30% | +9.76% | Validation safety-admitted |

| Days | Persistence MAE | AP MAE | Raw skill | Normalized skill |
| --- | --- | --- | --- | --- |
| 30 | 57.996 | 58.973 | -1.68% | -2.48% |
| 60 | 55.751 | 57.182 | -2.57% | -3.34% |
| 90 | 44.439 | 45.008 | -1.28% | -2.68% |

The comparison champion was persistence at30d, direction_gate at60/90d. Its main
normalized scores can be better than AP while its raw MAE is much worse. The
preregistered scale-aware objective is not permission to hide raw losses.

| Days | MAE excluding mixed scale | Raw skill excluding mixed scale | Normalized skill excluding mixed scale |
| --- | --- | --- | --- |
| 30 | 20.518 | +18.39% | +19.80% |
| 60 | 51.592 | +7.67% | +12.82% |
| 90 | 73.350 | +5.83% | +9.33% |

Main excluding-extreme-scale raw skill becomes positive at all horizons; full raw
skill remains negative at30/60d. The normalized gains are not real-world gains and
do not transfer to the deliberately shifted mechanisms.

| Partition | Days | Unchanged N / MAE | Changed N / MAE | Large decreases N / MAE / skill | Large increases N / MAE / skill |
| --- | --- | --- | --- | --- | --- |
| test | 30 | 88 / 0.001 | 168 / 213.507 | 0 / UNAVAILABLE / UNAVAILABLE | 21 / 104.174 / +14.15% |
| test | 60 | 65 / 0.002 | 191 / 237.562 | 32 / 180.970 / +1.58% | 30 / 133.813 / +12.53% |
| test | 90 | 45 / 0.003 | 211 / 205.172 | 48 / 178.387 / +0.60% | 45 / 196.627 / +8.02% |
| ood | 30 | 80 / 2.114 | 80 / 115.831 | 21 / 158.835 / -1.54% | 26 / 149.353 / +1.61% |
| ood | 60 | 80 / 3.378 | 80 / 110.986 | 24 / 138.174 / -1.55% | 32 / 128.091 / +2.20% |
| ood | 90 | 80 / 1.516 | 80 / 88.499 | 16 / 128.431 / -2.41% | 22 / 145.550 / +2.39% |

Large-decrease main30d has0 cases, so no MAE, skill or safety conclusion. OOD has
both classes:80 unchanged/40 increased/40 decreased endpoints at every horizon.
Main unchanged counts88/65/45; OOD negatives are informative here unlike Phase6.2.
A return to origin after intermediate changes is an unchanged endpoint. All return,
sign and large-change strata are exported; no future status enters prediction.

False movements are1/1/1 main and11/17/6 OOD for AP. Missed changes are109/132/152
main and72/70/74 OOD. Strong persistence retention comes at low movement recall.
The90d main unchanged budget is missed despite tiny raw error, illustrating why
zero/sub-minute and normalized diagnostics remain necessary. Undefined zero-history
normalized errors stay excluded/counted, with raw errors still present.

Paired comparisons use identical case IDs and whole-family resampling (500 draws,
seed620). There are16 main/eight OOD clusters, not416 real repositories. Exported
intervals are synthetic mechanism resampling diagnostics, not real-world significance
or universal power. Counterexamples are the largest model-scale excess per family,
selected after scoring solely for explanation, not for tuning or population changes.

See aggregate_metrics.csv, per_family_metrics.csv, paired_comparisons.csv and
counterexamples.json under examples/phase6_3. Full RMSE, family/case MAE, median,
bias, changed/unchanged, zero-denominator and scale counts remain available.
The scientific robustness target is NOT met. No model is promoted to a real default.
