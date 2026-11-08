# Phase 6.1B — comparative pretrained forecasting

**PARTIAL.** Genuine local Chronos-2 Small and Granite TTM inference completed on
the same 36 eligible synthetic cases. TimesFM 2.5 was acquired and hash-verified,
but stopped during loading by the conservative memory guard; it produced **zero
forecasts**. Its forecasting behavior and accuracy remain unmeasured. This is
synthetic engineering evidence, not demonstrated real technical-debt improvement
or a reason to change the real-world default.

Date: 2026-10-19, Africa/Cairo. Starting main:
`9d2972eda3c94efbeeec0427080ac0d15e3949f5`.

## Audit, approval and admission

Reviewed Phase 6.0 research/compatibility evidence, Phase 6.1A report and full
published numerical summaries, its conditional handoff, the original Chronos
contracts, and Phase C rights dossier. Existing experiments were not rerun.
The exposed Phase 6.1A population remains development evidence. Its mixed-scale
dominance motivated preregistered sensitivity analyses, not outcome-driven tuning.

The operator first kept acquisition blocked, then explicitly authorized the exact
TTM and TimesFM downloads/installations in this session. Both decisions remain
in the evidence chronology. No analyzer/data-use permission was inferred.
All 24 Phase C decisions remain NOT_APPROVED.

| Candidate | Exact checkpoint revision | Result |
| --- | --- | --- |
| autogluon/chronos-2-small | ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a | 36/36 native successes |
| ibm-granite/granite-timeseries-ttm-r2, 512-96-ft-r2.1 | 3442406f106122f414a11f72b4ebfe4878bec89d | 36/36 native successes |
| google/timesfm-2.5-200m-pytorch | 1d952420fba87f3c6dee4f240de0f1a0fbc790e3 | BLOCKED_RESOURCE, no forecasts |

TTM source commit is `3d92535ca4138648b9d1e2f3f1421b5dec4dc3aa`;
TimesFM source commit is `e51928e27119cb17bebc005be2696b75e0a9e688`.
Pinned code licenses and model-card Apache-2.0 metadata were inspected separately.
TimesFM code's package version is 3.0.2, but the selected class and weights are
explicitly **2.5**; no TimesFM 3.0 weights/API were substituted.
Sources: [TTM pinned card](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2/blob/3442406f106122f414a11f72b4ebfe4878bec89d/README.md),
[TimesFM pinned card](https://huggingface.co/google/timesfm-2.5-200m-pytorch/blob/1d952420fba87f3c6dee4f240de0f1a0fbc790e3/README.md),
[TTM pinned code](https://github.com/ibm-granite/granite-tsfm/tree/3d92535ca4138648b9d1e2f3f1421b5dec4dc3aa),
[TimesFM pinned code](https://github.com/google-research/timesfm/tree/e51928e27119cb17bebc005be2696b75e0a9e688).

TTM's 3,440,416-byte weights match SHA256
`37fa184887f260cda022d3ae9f1c642fdba579d0aefeabdf751f83f45383a761`;
TimesFM's 925,181,104-byte weights match
`2f776efe6245e42b24bc4153ffdf61810140210e4bd3b01fb21f7aa779ab6ce8`.
Config hashes, exact source Git blob/SHA256 identities, metadata URLs and license
hashes are in the admission matrix. Same-origin TLS/LFS checksums and Git object
identities pin bytes; they are not independent publisher signatures.

Fourteen primary metadata requests and 31 exact source-file requests were recorded.
Weight acquisition preserved an initially rejected CDN redirect and a near-complete
TimesFM read timeout. A single validated HTTP 206 range request recovered the last
337,072 bytes, then the entire file was hashed. Recorded top-level requests and
the extra redirect-inspection HEAD are distinguished from automatic redirect hops.
Final new weight payload is 928,621,520 bytes. No replacement version was selected.

Two isolated source installations reuse an unchanged, hash-locked CPU dependency
tree read-only. No new dependency bytes, package upgrade or change to Chronos's
environment occurred. The minimal TTM inference modules need Torch/Transformers,
not the full dataset/training toolkit. This is not a full Granite toolkit install.
The exact lock remains Python 3.12.3, Torch 2.11.0+cpu, Transformers 4.57.6,
NumPy 2.4.4, pandas 3.0.2, with all other dependency versions and hashes recorded.

## Frozen population and fair comparison

New version `phase6.1b.comparison.v1`: 14 families × three seeded scale variants,
42 registered cases. Six sparse/irregular cases are ineligible for **every**
method; no fill, interpolation or padding creates measured history. The remaining
36 cases have 512 genuinely generated daily past positions, 32 distinct numerical
histories, one common origin 2026-10-01T00:00:00Z, and independently generated
future noise. Exact endpoints are October 31, November 30 and December 30, 2026.
Cases and repeats are not independent real repositories.

Scenarios cover constants, plateaus, both trends and jump directions, multiple
steps, noise, quiet then change, near/zero debt, distribution shift and mixed
scales. Seeds, equations, windows, normalization, horizons, failures and settings
were frozen before native inference. All methods receive identical historical
observations: persistence uses origin stock, mean uses final seven values, anchored
OLS uses final 90. These fixed windows were not tuned on evaluation outcomes.

Chronos uses native 512→90, median q50 and q10/q90. TTM uses native 512→96,
`prediction_outputs` from its MSE point head, daily frequency token **8** verified
from pinned source, and endpoints at indices 29/59/89. Its other six native steps
are retained privately; it has **no admitted native intervals**. Native context
scaling is past-only. Different model point estimands are explicit, not disguised.

TimesFM was configured for direct `forecast(horizon=90)` with max_context=512,
continuous quantile head, normalization enabled, flip invariance disabled,
native positivity clipping disabled and `fix_quantile_crossing=False`.
Its pinned implementation rounds internal horizon capacity to a patch boundary;
only 90 daily outputs would be accepted. Source inspection shows its returned
point is q50; the separate mean head and all deciles would also be retained.
None of those forecast outputs was reached or claimed as measured.

Both successful models' 72 input traces match **exactly the same flattened
float32 bytes**, shapes [1,512] and [1,512,1], with no future values. Both made
72 native calls: 36 primary cases and 36 exact repeats. All repeat pairs were
identical. There were no native path crossings, nonfinite outputs or fallbacks.
Native TimesFM quantile repair is disabled in code and unit-tested, without
claiming a successful TimesFM native path.

## Setup failures, sealing and continuation

The first TTM worker failed before model loading because the upstream package
initializer eagerly imports unrelated toolkit modules. The next setup worker
caught an import-name collision in our repair. Both had **zero native calls**;
their complete failure receipts remain preserved. The corrected adapter loads
the original model/config modules in a private Python namespace, preserving
their exact source bytes, native class/forward/scaling logic and checkpoint.
Strict loading rejected missing, unexpected or mismatched state keys; none occurred.

There were five sequential model workers in total: one successful Chronos worker,
three TTM workers (two startup failures, one successful native run), and one
resource-blocked TimesFM worker. No Chronos or TimesFM inference was retried.
Earlier registrations, partial outcomes and seals remain immutable. Later
registrations reuse the original sealed Chronos predictions and TimesFM failure
verbatim and bind identical requests. No native forecast settings, population,
normalization or metric policy changed after numerical outcomes.

Each registered attempt sealed its predictions/failures before evaluator scoring.
The final joined predictions were sealed before final truth generation/scoring.
Earlier engineering receipts had already scored the same synthetic Chronos-only
population while TTM startup was blocked; this is explicitly development evidence,
not a fresh blind confirmatory study. TTM's prediction function received only past
requests, never earlier scores or numerical future labels. This is a strict typed
data interface, not hostile-code filesystem isolation from Python introspection.

## Actual numerical results

Units are **synthetic estimated maintainability remediation minutes**. The five
completed methods share all 36 eligible cases and 108 exact endpoints each.
TimesFM has zero successful endpoints; the all-six intersection is empty.
No persistence substitute or guessed TimesFM score is included.

| Method | MAE 30d | MAE 60d | MAE 90d |
| --- | ---: | ---: | ---: |
| Persistence | 98.9198 | 171.6310 | 239.2241 |
| Rolling mean | 120.8121 | 193.3373 | 261.1164 |
| Anchored trend | 13.4655 | 39.5518 | 65.5506 |
| Chronos 512 | 22.5695 | 34.2076 | 54.2687 |
| TTM 512 | 212.1957 | 344.3387 | 434.3861 |

Relative raw-MAE skill `1−MAE_model/MAE_persistence` for Chronos is
0.771840/0.800691/0.773147; for TTM −1.145130/−1.006274/−0.815813.
These are engineering-population comparisons, not real-world accuracy estimates.
Anchored trend has the lowest raw 30-day error here. No model/default was selected.

| Method | RMSE 30d | RMSE 60d | RMSE 90d |
| --- | ---: | ---: | ---: |
| Persistence | 527.2231 | 880.5708 | 1251.3042 |
| Anchored trend | 32.5808 | 128.8130 | 259.3601 |
| Chronos 512 | 83.5115 | 92.6372 | 188.4618 |
| TTM 512 | 1183.9252 | 1880.8368 | 2377.5821 |

All 12 eligible families have three cases, so equal-scenario macro MAE equals
equal-case MAE in these complete rows. It does not itself remove within-family
scale dominance. Removing the three mixed-scale cases gives:

| Method | MAE 30d | MAE 60d | MAE 90d |
| --- | ---: | ---: | ---: |
| Persistence | 11.7303 | 26.3809 | 32.5958 |
| Anchored trend | 10.1400 | 20.3822 | 24.9884 |
| Chronos 512 | 9.9045 | 21.5366 | 25.8099 |
| TTM 512 | 15.4326 | 32.2192 | 39.9549 |

The preregistered normalized error divides absolute error by mean absolute past
stock over all 512 positions. This is relative-level error, **not MASE**. Two
all-zero histories per horizon have undefined denominators and remain null/countable;
all 36 remain in minute-based metrics. Normalized MAE on the 34 defined cases:

| Method | 30d | 60d | 90d |
| --- | ---: | ---: | ---: |
| Persistence | 0.089419 | 0.184211 | 0.221021 |
| Anchored trend | 0.080576 | 0.148321 | 0.176008 |
| Chronos 512 | 0.076452 | 0.151354 | 0.176946 |
| TTM 512 | 0.112028 | 0.220845 | 0.267873 |

Paired TTM-minus-Chronos absolute-error differences, on identical successful IDs,
are +189.6262/+310.1311/+380.1174 minutes; excluding mixed scales they are
+5.5282/+10.6826/+14.1450. The normalized paired differences are
+0.035577/+0.069491/+0.090927. These results show why unnormalized aggregate
MAE alone is insufficient. Tables retain every scenario and pair, not selected wins.

At 90 days, five cases have unchanged truth: persistence MAE 0, Chronos about
2.23e−10, TTM 0.000073. The 31 changing cases have MAE 277.8086, 63.0218 and
504.4484 respectively. Median absolute error, signed bias, clipping counts,
per-scenario metrics, strata and all attempted/blocked populations are in the files.

Chronos's nominal 80% q10–q90 coverage is 69.44%/52.78%/50.00%; mean interval
width is 70.5918/77.1634/81.3135 minutes, with six collapsed intervals per horizon.
These uncalibrated designed-data results do not establish reliable risk calibration.
TTM/TimesFM interval coverage and widths are **unavailable**, not zero-width.

## CPU feasibility and limitations

| Native worker | Calls | Worker time | Mean call | Sampled peak RSS |
| --- | ---: | ---: | ---: | ---: |
| Chronos | 72 | 16.966s | 82.774ms | 496.625 MiB |
| TTM | 72 | 13.878s | 24.465ms | 349.988 MiB |
| TimesFM | 0 | 6.551s to guard stop | unavailable | 1834.539 MiB |

Completed kernel peaks were 512,790,528 bytes for Chronos and 355,905,536 for
TTM. Every successful worker verified CPU float32, deterministic algorithms,
two numerical threads/one inter-op thread, two-CPU affinity and kernel socket
denial. Host resources were checked immediately before every worker.

The approved ceiling stayed 2 GiB RSS/900 seconds. Because this host offers no
writable task cgroup, the reused monitor samples RSS every 20 ms; a stricter
1.75 GiB stop threshold provides headroom. TimesFM crossed that guard during
loading and was killed, sampled at 1,923,653,632 bytes, below 2 GiB. Its final
kernel peak is unavailable. This establishes **non-admission under this conservative
guard**, not proof that every implementation must exceed 2 GiB. No higher limit,
loader modification or second TimesFM worker was tried. Weight size alone did
not establish CPU memory eligibility. Timing order was fixed, not randomized.

## Verification, preservation and next step

The published 540 endpoint rows independently reproduce all aggregate, scenario,
stratum and paired metrics through regenerated synthetic truth and denominators,
without inference replay. The [package README](forecasting_research/phase6_1b/README.md)
documents setup, exact interface and reproduction. Small evidence is under
`examples/phase6_1b/`; raw paths, models, installed source trees, logs and environments
remain outside Git under the private Phase 6.1B directory.

**53 new tests passed**: 47 software/evidence tests and six fake-native adapter
contract tests. The complete allowlisted regression run passed **1,412 + 6 tests
in the working checkout and 1,350 + 6 in canonical main**, with zero failures,
errors or skips. The 62-test difference is the pre-existing local synthetic demo.
Non-allowlisted legacy training, real-data benchmark and historical execution
suites were excluded. Regression and preservation receipts give exact commands
and timings. They cover
leakage, identities, daily horizons, missingness, native point/quantile semantics,
all-nine TimesFM decile crossings, raw/clipped outputs, blocked populations,
scale normalization, source loading, path guards and numerical reproduction.
Fake-backend tests are explicitly separated from the 144 genuine native calls.

Preservation verifies 887 original-project files, 975 earlier canonical files,
19,209 earlier private-task files, 150 Phase 6.0 and 34 Phase 6.1A private files,
56 frozen bundles/322 artifacts, both Phase 5.1 bundles, database/checkpoint hashes,
old cache/ledger/claim evidence and 22,397 original dependency files. Payloads are
stream-hashed as opaque bytes; no historical labels are reopened. User-cache
metadata/reference hashes are checked. No SonarQube/container/volume operation
occurred; live-volume byte preservation is not claimed. Previous compilation
archives, studies, working HEAD and unrelated changes remain preserved.

Next research decision: review this synthetic-only result and the TimesFM loader
memory evidence. Any alternative low-memory loading route requires a separately
reviewed, pinned compatibility/resource plan; no limit increase or new execution
is implied. Broader synthetic scenarios and independent replications also require
new preregistration. Real-data claims additionally require rights-cleared new
measurements, consistent domains and an independent held-out cohort.

**STOP after Phase 6.1B publication.** No real-data benchmark, fine-tuning,
SonarQube/Maven/scanning, debt collection, dataset admission or dashboard work
occurred. Analyzer licensing and derived-data rights remain UNRESOLVED_UNCHANGED.
