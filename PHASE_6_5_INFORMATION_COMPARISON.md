# Adaptive Persistence — information comparison

SYNTHETIC_ENGINEERING_TEST. These are artificial information channels, not real
software feature findings. Three preregistered random-stream replications. All
methods use the same case IDs/origins/endpoints in each population. Hidden and
reversed futures reuse the base requests; delayed requests change only availability.
These interventions are paired, not independent repository samples.

The following table averages replication MAEs (identical240-case population sizes)
and recomputes skill from averaged errors. Normalized skill similarly uses the
ratio of mean equal-family normalized errors. It is not the arithmetic mean of
individual replication percentages. Units: simulated estimated remediation minutes.

| Population | Days | Persistence MAE | Local AP MAE | Raw skill | Normalized skill |
| --- | --- | --- | --- | --- | --- |
| test | 30 | 271.622 | 219.667 | +19.13% | +13.30% |
| test | 60 | 474.217 | 313.835 | +33.82% | +33.27% |
| test | 90 | 622.101 | 401.000 | +35.54% | +40.66% |
| unseen | 30 | 256.796 | 225.411 | +12.22% | +10.26% |
| unseen | 60 | 440.504 | 333.534 | +24.28% | +31.06% |
| unseen | 90 | 625.942 | 403.199 | +35.59% | +41.16% |
| hidden | 30 | 392.245 | 465.747 | -18.74% | -21.53% |
| hidden | 60 | 593.902 | 777.323 | -30.88% | -34.76% |
| hidden | 90 | 733.659 | 981.054 | -33.72% | -28.87% |
| reversed | 30 | 271.622 | 484.337 | -78.31% | -88.20% |
| reversed | 60 | 474.217 | 863.827 | -82.16% | -90.49% |
| reversed | 90 | 622.101 | 1132.104 | -81.98% | -84.65% |
| delayed | 30 | 271.622 | 271.622 | +0.00% | +0.00% |
| delayed | 60 | 474.217 | 474.217 | +0.00% | +0.00% |
| delayed | 90 | 622.101 | 622.101 | +0.00% | +0.00% |

All9 base and9 unseen-history cells improve raw AND normalized error with the
engineered intent relationship held fixed. Unseen histories have new shapes but
the SAME plan-to-outcome semantics: this is not independent evidence about transport
of the signal relationship. Every hidden and reversed local AP cell worsens.
Every stress-selected policy chooses shrink0 and exactly matches persistence;
this is protection without anticipation. Delayed signals are retained as cases,
marked unavailable, and yield persistence for signal-conditioned forecasts.

## Complete main-test ablations

| Method | Days | Mean MAE | Raw skill |
| --- | --- | --- | --- |
| persistence | 30 | 271.622 | +0.00% |
| persistence | 60 | 474.217 | +0.00% |
| persistence | 90 | 622.101 | +0.00% |
| rolling_mean | 30 | 292.031 | -7.51% |
| rolling_mean | 60 | 491.338 | -3.61% |
| rolling_mean | 90 | 638.988 | -2.71% |
| anchored_trend | 30 | 308.353 | -13.52% |
| anchored_trend | 60 | 537.828 | -13.41% |
| anchored_trend | 90 | 717.173 | -15.28% |
| history_median | 30 | 271.622 | +0.00% |
| history_median | 60 | 474.217 | +0.00% |
| history_median | 90 | 622.101 | +0.00% |
| activity_median | 30 | 271.622 | +0.00% |
| activity_median | 60 | 474.217 | +0.00% |
| activity_median | 90 | 668.743 | -7.50% |
| intent_median | 30 | 219.667 | +19.13% |
| intent_median | 60 | 313.835 | +33.82% |
| intent_median | 90 | 401.000 | +35.54% |
| adaptive_local | 30 | 219.667 | +19.13% |
| adaptive_local | 60 | 313.835 | +33.82% |
| adaptive_local | 90 | 401.000 | +35.54% |
| adaptive_stress | 30 | 271.622 | +0.00% |
| adaptive_stress | 60 | 474.217 | +0.00% |
| adaptive_stress | 90 | 622.101 | +0.00% |

History-sign medians equal persistence in this construction because plans/future
realizations are independent of history. This is NOT a real-world finding that
history is useless. Activity is unsigned; its empirical median mostly remains
zero. R2's activity90 estimator moves in one direction and worsens base MAE19.39%
(normalized19.49%); finite cell imbalance does not establish causal direction.
Intent medians and local AP coincide because every local validation selected
shrink1; this equality is observed, not assumed. No test-driven promotion occurs.

## Per-replication local AP and reliability

| Seed suffix | Population | Days | AP MAE | Raw skill | Normalized skill | Unchanged MAE | Large-up skill | Large-down skill |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | test | 30 | 211.854 | +23.32% | +18.93% | 139.742 | +54.82% | +60.79% |
| 20 | test | 60 | 339.465 | +26.01% | +38.92% | 185.672 | +47.26% | +53.07% |
| 20 | test | 90 | 425.603 | +29.10% | +45.89% | 234.948 | +46.83% | +55.83% |
| 20 | unseen | 30 | 228.855 | +21.36% | +11.86% | 150.573 | +76.21% | +31.36% |
| 20 | unseen | 60 | 323.802 | +34.22% | +32.30% | 197.771 | +77.83% | +30.68% |
| 20 | unseen | 90 | 350.676 | +50.43% | +43.55% | 142.725 | +78.27% | +39.88% |
| 21 | test | 30 | 260.182 | +9.16% | +6.34% | 46.091 | -14.84% | +64.14% |
| 21 | test | 60 | 322.781 | +39.93% | +28.53% | 91.709 | +44.50% | +57.54% |
| 21 | test | 90 | 421.981 | +41.52% | +34.56% | 77.780 | +40.51% | +57.94% |
| 21 | unseen | 30 | 215.278 | +4.01% | +3.79% | 102.906 | -0.09% | +61.13% |
| 21 | unseen | 60 | 314.511 | +23.93% | +30.23% | 248.675 | +69.00% | +48.22% |
| 21 | unseen | 90 | 371.570 | +34.78% | +43.44% | 286.268 | +72.02% | +50.62% |
| 22 | test | 30 | 186.966 | +25.85% | +14.99% | 121.291 | +61.22% | +54.59% |
| 22 | test | 60 | 279.260 | +34.52% | +32.67% | 173.231 | +60.12% | +58.25% |
| 22 | test | 90 | 355.415 | +34.72% | +42.35% | 244.710 | +62.18% | +58.79% |
| 22 | unseen | 30 | 232.100 | +9.01% | +15.49% | 149.940 | +30.33% | +61.83% |
| 22 | unseen | 60 | 362.288 | +12.87% | +30.77% | 226.084 | +22.16% | +64.94% |
| 22 | unseen | 90 | 487.352 | +18.87% | +36.37% | 218.993 | +18.82% | +57.52% |

Persistence has zero unchanged-case error. Local AP introduces unnecessary moves
when plans fail/reverse or records are wrong. Main unchanged MAE ranges46.091–244.710
minutes, unseen102.906–286.268. Validation's normalized protection budget is not a
zero-loss guarantee, and is not claimed to certify all final subgroups. All main
and unseen large-sign cells have at least35 cases, unlike earlier empty strata;
counts and per-family support remain in the machine tables. All-zero controls
are absorbing by design and cannot certify zero-debt real-world behavior.

Scale sensitivity is in aggregate_metrics.csv (explicit current-stock one-minute
floor, unfloored zero exclusion and extreme-scale removal). Do not read raw scale-
dominated MAE alone. No interval or point setting was changed after these results.
Full matched all-method/per-seed/per-family and subgroup tables are published.
