# Matched Adaptive Persistence comparison

**PARTIAL. Implementation, numerical verification and preservation passed. The
user's consistent-improvement criterion was NOT demonstrated. Some OOD large-
increase groups also fail the registered support minimum, limiting those safety
claims. Negative results alone are not software failures. No model is promoted.
All numerical results are SYNTHETIC_ENGINEERING_TEST, in simulated estimated
maintainability remediation minutes; they are not real repository performance.


Raw MAE below uses identical eligible case IDs, exact30/60/90 targets and seven
methods. All34272 attempted forecasts are accounted for, with zero runtime failures
or exclusions. Frozen Phase6.3 uses exact saved state/preprocessing/configs, no refit;
its30d policy-deviating selection remains marked descriptive. Its feature normalizers
remain original even with the new256-position histories, an explicit transfer shift.
No ranking here changes validation selection.

| Replication | Partition | Method | 30d MAE | 60d MAE | 90d MAE |
| --- | --- | --- | --- | --- | --- |
| R1 | test | persistence | 1,459.037 | 2,227.941 | 3,096.897 |
| R1 | test | rolling_mean | 1,543.521 | 2,320.340 | 3,346.694 |
| R1 | test | anchored_trend | 1,290.670 | 1,608.117 | 2,555.689 |
| R1 | test | direct_delta | 1,329.469 | 1,889.106 | 3,269.593 |
| R1 | test | local_median | 1,050.742 | 1,267.469 | 1,756.714 |
| R1 | test | adaptive_persistence | 1,418.058 | 2,052.231 | 2,869.683 |
| R1 | test | frozen_phase6_3 | 1,719.704 | 2,805.754 | 3,813.786 |
| R1 | ood | persistence | 1,023.680 | 1,630.140 | 1,459.156 |
| R1 | ood | rolling_mean | 867.506 | 1,488.131 | 1,307.669 |
| R1 | ood | anchored_trend | 1,614.792 | 2,902.943 | 3,403.427 |
| R1 | ood | direct_delta | 1,710.667 | 3,384.954 | 4,723.245 |
| R1 | ood | local_median | 1,462.081 | 2,777.435 | 3,658.698 |
| R1 | ood | adaptive_persistence | 1,023.680 | 1,799.447 | 1,755.951 |
| R1 | ood | frozen_phase6_3 | 1,034.812 | 1,737.446 | 1,651.619 |
| R2 | test | persistence | 1,335.462 | 2,104.052 | 3,001.444 |
| R2 | test | rolling_mean | 1,468.822 | 2,282.155 | 3,203.332 |
| R2 | test | anchored_trend | 1,222.452 | 1,631.296 | 2,462.279 |
| R2 | test | direct_delta | 1,058.252 | 2,224.638 | 3,672.956 |
| R2 | test | local_median | 947.483 | 1,187.287 | 1,808.234 |
| R2 | test | adaptive_persistence | 1,335.462 | 2,104.052 | 3,001.444 |
| R2 | test | frozen_phase6_3 | 1,606.188 | 2,889.022 | 3,763.636 |
| R2 | ood | persistence | 857.339 | 1,307.291 | 1,393.812 |
| R2 | ood | rolling_mean | 880.429 | 1,369.094 | 1,364.643 |
| R2 | ood | anchored_trend | 1,455.704 | 2,651.729 | 3,449.194 |
| R2 | ood | direct_delta | 1,589.003 | 3,085.093 | 4,550.803 |
| R2 | ood | local_median | 1,290.497 | 2,445.431 | 3,545.046 |
| R2 | ood | adaptive_persistence | 857.339 | 1,307.291 | 1,393.812 |
| R2 | ood | frozen_phase6_3 | 815.037 | 1,249.763 | 1,592.985 |


The ungated local median wins main raw MAE in both replications and all horizons,
but loses badly on unseen mechanisms. This diagnoses the reliability/accuracy tradeoff,
not a replacement winner to promote. Rolling mean has some OOD gains but loses main
performance, and its raw gains are not consistent inR2. Historical and current cohort
scores are not mixed into one leaderboard.

## Scale sensitivity

| Replication | Partition | Days | Raw skill without extreme scales | Normalized skill without extreme scales | Unfloored full skill |
| --- | --- | --- | --- | --- | --- |
| R1 | test | 30 | +4.10% | +5.19% | +5.83% |
| R1 | test | 60 | +5.83% | +1.81% | +1.52% |
| R1 | test | 90 | +5.23% | +1.63% | +1.35% |
| R1 | ood | 30 | +0.00% | +0.00% | +0.00% |
| R1 | ood | 60 | -10.21% | -15.57% | -14.30% |
| R1 | ood | 90 | -17.51% | -23.21% | -21.04% |
| R2 | test | 30 | +0.00% | +0.00% | +0.00% |
| R2 | test | 60 | +0.00% | +0.00% | +0.00% |
| R2 | test | 90 | +0.00% | +0.00% | +0.00% |
| R2 | ood | 30 | +0.00% | +0.00% | +0.00% |
| R2 | ood | 60 | +0.00% | +0.00% | +0.00% |
| R2 | ood | 90 | +0.00% | +0.00% | +0.00% |


MainR1 gains survive both scale checks. R1 OOD60/90 losses also survive them.
R2 AP equals persistence under every scale policy. Primary normalization is explicitly
max(1minute,past mean); the unfloored variant excludes/counts exact zero denominators.
Near-zero histories are not silently given observed zeros. Actual full-cohort zero
historical-mean denominator count is0; exact-zero handling has separate tests.

## Safety subgroups

| Replication | Partition | Days | Stratum | N | MAE | Raw skill | Normalized skill |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | ood | 30 | unchanged | 120 | 0.000 | UNAVAILABLE | UNAVAILABLE |
| R1 | ood | 30 | large_increase | 13 | 6,352.300 | +0.00% | +0.00% |
| R1 | ood | 30 | large_decrease | 34 | 4,242.886 | +0.00% | +0.00% |
| R1 | ood | 60 | unchanged | 114 | 133.013 | UNAVAILABLE | UNAVAILABLE |
| R1 | ood | 60 | large_increase | 29 | 7,664.660 | +0.00% | +0.00% |
| R1 | ood | 60 | large_decrease | 44 | 5,296.250 | -16.85% | -14.69% |
| R1 | ood | 90 | unchanged | 111 | 239.474 | UNAVAILABLE | UNAVAILABLE |
| R1 | ood | 90 | large_increase | 16 | 5,294.341 | +0.00% | +0.00% |
| R1 | ood | 90 | large_decrease | 37 | 8,290.021 | -23.76% | -23.02% |
| R1 | test | 30 | unchanged | 147 | 37.266 | UNAVAILABLE | UNAVAILABLE |
| R1 | test | 30 | large_increase | 42 | 4,466.832 | +7.20% | +6.86% |
| R1 | test | 30 | large_decrease | 51 | 5,959.784 | +2.14% | +0.78% |
| R1 | test | 60 | unchanged | 144 | 1.178 | UNAVAILABLE | UNAVAILABLE |
| R1 | test | 60 | large_increase | 49 | 8,335.559 | +0.87% | +1.19% |
| R1 | test | 60 | large_decrease | 65 | 5,047.298 | +16.34% | +4.44% |
| R1 | test | 90 | unchanged | 144 | 1.493 | UNAVAILABLE | UNAVAILABLE |
| R1 | test | 90 | large_increase | 46 | 14,382.751 | +0.94% | +1.24% |
| R1 | test | 90 | large_decrease | 63 | 6,128.026 | +17.38% | +5.12% |
| R2 | ood | 30 | unchanged | 118 | 0.000 | UNAVAILABLE | UNAVAILABLE |
| R2 | ood | 30 | large_increase | 9 | 5,191.625 | +0.00% | +0.00% |
| R2 | ood | 30 | large_decrease | 38 | 3,183.101 | +0.00% | +0.00% |
| R2 | ood | 60 | unchanged | 119 | 0.000 | UNAVAILABLE | UNAVAILABLE |
| R2 | ood | 60 | large_increase | 18 | 3,265.217 | +0.00% | +0.00% |
| R2 | ood | 60 | large_decrease | 48 | 5,669.342 | +0.00% | +0.00% |
| R2 | ood | 90 | unchanged | 115 | 0.000 | UNAVAILABLE | UNAVAILABLE |
| R2 | ood | 90 | large_increase | 15 | 4,202.726 | +0.00% | +0.00% |
| R2 | ood | 90 | large_decrease | 40 | 7,038.974 | +0.00% | +0.00% |
| R2 | test | 30 | unchanged | 168 | 0.000 | UNAVAILABLE | UNAVAILABLE |
| R2 | test | 30 | large_increase | 40 | 5,692.735 | +0.00% | +0.00% |
| R2 | test | 30 | large_decrease | 48 | 5,030.092 | +0.00% | +0.00% |
| R2 | test | 60 | unchanged | 164 | 0.000 | UNAVAILABLE | UNAVAILABLE |
| R2 | test | 60 | large_increase | 43 | 9,067.396 | +0.00% | +0.00% |
| R2 | test | 60 | large_decrease | 60 | 6,447.152 | +0.00% | +0.00% |
| R2 | test | 90 | unchanged | 164 | 0.000 | UNAVAILABLE | UNAVAILABLE |
| R2 | test | 90 | large_increase | 45 | 14,823.040 | +0.00% | +0.00% |
| R2 | test | 90 | large_decrease | 64 | 6,979.937 | +0.00% | +0.00% |


Positive/negative target status is for scoring only. Some OOD large-up groups are
underpowered by the registered>=24 rule. Case counts are not independent repository
counts. Paired whole-family bootstrap records are exploratory; no real-world
significance claim. Counterexamples retain cases where persistence wins.
