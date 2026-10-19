# Change-aware comparison — Phase 6.2

**SYNTHETIC_ENGINEERING_TEST; no real-world ranking.** Main test192 new cases,
16 shared mechanisms,12 cases per mechanism, three exact endpoints. OOD48 cases,
two wholly held-out mechanisms. Every method has complete matched coverage.
Persistence remains mandatory. Fixed mean uses last7 **observed** values, and trend
uses actual time coordinates in the last90 calendar days anchored at the origin.
For complete daily histories these reproduce the existing baseline mathematics;
the sparse extension is newly registered and does not change older baseline results.

| Method | 30d MAE | 60d MAE | 90d MAE | 30d normalized skill | 60d normalized skill | 90d normalized skill |
| --- | --- | --- | --- | --- | --- | --- |
| persistence | 1,942.398 | 3,311.420 | 5,393.460 | +0.00% | +0.00% | +0.00% |
| rolling_mean | 2,092.514 | 3,461.232 | 5,543.109 | -29.71% | -14.10% | -11.03% |
| anchored_trend | 504.666 | 132.787 | 459.493 | +11.26% | +56.79% | +64.94% |
| direct_delta | 882.398 | 780.400 | 1,268.018 | +8.52% | +59.89% | +60.27% |
| hard_gate | 688.603 | 564.238 | 1,245.053 | +37.43% | +62.41% | +60.32% |
| probability_weighted | 687.818 | 514.970 | 1,272.038 | +30.79% | +60.48% | +60.67% |
| mixture_median | 710.706 | 595.005 | 981.150 | +36.96% | +62.90% | +61.38% |
| blend | 373.800 | 780.400 | 1,268.018 | +14.33% | +59.89% | +60.27% |
| selected | 688.603 | 595.005 | 459.493 | +37.43% | +62.90% | +64.94% |

Raw MAE/RMSE, case macro, family macro, bias, median absolute error and skill are
in [aggregate_metrics.csv](examples/phase6_2/aggregate_metrics.csv). All per-family
results are in [per_family_metrics.csv](examples/phase6_2/per_family_metrics.csv).
Equal-family normalized metrics use each history's unfloored mean absolute stock;
the all-zero-history case is excluded and counted, never assigned epsilon.

Validation-selected methods and their main test results:

| Days | Validation-selected method | Persistence MAE | Selected MAE | Raw MAE skill | Normalized skill |
| --- | --- | --- | --- | --- | --- |
| 30 | hard_gate | 1,942.398 | 688.603 | +64.55% | +37.43% |
| 60 | mixture_median | 3,311.420 | 595.005 | +82.03% | +62.90% |
| 90 | anchored_trend | 5,393.460 | 459.493 | +91.48% | +64.94% |

These choices were frozen before test targets opened. Descriptive raw test MAE
winners are blend30d, trend60d and trend90d; they are not a new test-selected policy.
Reporting that ranking does not overwrite the validation selection. By normalized
main-test error, the frozen selected methods are also the best among this grid.

| Days | Persistence MAE without mixed scale | Selected MAE without mixed scale | Raw skill without mixed scale | Normalized skill without mixed scale |
| --- | --- | --- | --- | --- |
| 30 | 37.904 | 27.165 | +28.33% | +36.08% |
| 60 | 64.644 | 28.580 | +55.79% | +61.92% |
| 90 | 86.854 | 42.735 | +50.80% | +63.48% |

Positive gains survive excluding the deliberately extreme-scale family; their
magnitude changes substantially. Raw results alone would favor a different30/60d
policy. No method is selected solely on raw test error or reused exposed results.

| Days | Unchanged N / MAE | Changed N / MAE | Large increases N / MAE / skill | Large decreases N / MAE / skill |
| --- | --- | --- | --- | --- |
| 30 | 54 / 0.000 | 138 / 958.056 | 38 / 58.731 / +51.88% | 5 / 89.401 / -6.88% |
| 60 | 30 / 28.046 | 162 / 699.997 | 61 / 338.642 / +92.84% | 14 / 58.483 / +31.11% |
| 90 | 15 / 9.572 | 177 / 497.621 | 78 / 1,075.002 / +91.87% | 24 / 96.333 / -7.10% |

False movements, missed movements, positive prevalence and large-change definitions
are explicitly counted. The selected30d gate preserves all unchanged stocks, but
its large-decrease error is worse than persistence. A high classifier F1 does not
remove that forecasting limitation.

| Days | Persistence MAE | Frozen selected MAE | Raw skill | Normalized skill |
| --- | --- | --- | --- | --- |
| 30 | 28.853 | 33.715 | -16.85% | +22.09% |
| 60 | 44.809 | 29.864 | +33.35% | +48.71% |
| 90 | 52.116 | 48.310 | +7.30% | +21.73% |

The raw30d OOD result is worse than persistence, while normalized error is better:
scale and family weighting answer different questions. Two held-out synthetic
mechanisms are not a rights-cleared real cohort or evidence of universal transfer.

All36 pairs of nine reported methods are compared at every horizon/partition on
identical case IDs. Error differences are `right MAE-left MAE` (negative favors
right), with500 whole-family paired bootstrap resamples, seed620. Case counts and
family counts are recorded. OOD's two-family intervals are exploratory only; no
real-world significance/power claim follows. Selected duplicates its parent by
design, so those pairs are not independent models. Full paired tables are published.

| Partition | Days | Coverage80 | Mean width | Collapsed / invalid |
| --- | --- | --- | --- | --- |
| test | 30 | 82.81% | 5,771.717 | 0 / 0 |
| test | 60 | 85.42% | 6,230.620 | 0 / 0 |
| test | 90 | 77.08% | 8,313.534 | 0 / 0 |
| ood | 30 | 50.00% | 72.266 | 0 / 0 |
| ood | 60 | 58.33% | 78.030 | 0 / 0 |
| ood | 90 | 54.17% | 104.166 | 0 / 0 |

Intervals are derived from a separate calibration partition, not native output.
Pinball loss, interval score, changed/unchanged coverage, width and collapse are in
[interval_metrics.csv](examples/phase6_2/interval_metrics.csv). No empirical mixture
or calibration assumption is promoted to a distribution-free guarantee. Zero
ordering violations and noncollapsed intervals are validity checks, not proof of
useful risk estimates. No quantile repairs, future oracle gating or population
filtering were applied.

Chronos: NOT_EXECUTED_NO_SEPARATE_APPROVAL. TTM/TimesFM: NOT_EXECUTED. Their old
exposed predictions do not belong to this new population. No incomparable score
is inserted into these tables. Original historical persistence remains the real
study reference.
