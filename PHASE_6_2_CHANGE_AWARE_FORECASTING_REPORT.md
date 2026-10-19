# Phase 6.2 — change-aware forecasting

**PASS — SYNTHETIC_ENGINEERING_TEST only.** A complete lightweight synthetic study
ran under the approved limits. A positive real technical-debt forecasting result
has not been established. No pretrained model was executed. All 24 Phase C
permission decisions remain NOT_APPROVED.

Date: 2026-10-20, Africa/Cairo. Starting main:
`500bbf80014359832cb41103fb28dec1e9129dd9`.
Registration SHA256: `7bf143612bf2eebb011e90e29630ea5572562d8b94eec9e1a25bffcf775947f4`.

## Frozen evidence and scope

The required Phase3/4.2, persistence analysis, change-aware design, Phase6.0/6.1A/
6.1B/6.1C, Phase6.2 handoff, accuracy summary and Phase C reports and actual
contracts/adapters were audited; exact hashes are in
[prior_research_audit.json](examples/phase6_2/prior_research_audit.json).
The original 90-day historical repository-macro MAEs remain persistence148.708
versus Chronos157.478 temporally, and470.252 versus541.636 held-out. Those old,
already exposed test cohorts were not reopened, retuned or relabeled. No historical
numerical label file or original model benchmark was executed.

Persistence is exact when endpoint stock is unchanged; observed unchanged
fractions in the published Java summaries are51.7% temporal and36.9% held-out at90d.
Those facts motivate research but do not prove that change is predictable. Phase4's
constant-history interval collapse/long-horizon undercoverage and Phase6.1's scale
sensitivity remain limitations, not licenses to retune exposed tests. The Phase6.1C
TimesFM quantile failure stays PARTIAL. This phase neither repairs nor reruns it.

## New population and label boundaries

New `phase6_2.change-aware.v1`: 384 training,128 validation,128 calibration,
192 test cases from16 mechanisms;48 additional OOD cases from two wholly held-out
mechanisms (damped oscillation and saturating recovery). Each case has one origin,
up to180 genuinely generated past calendar positions and exact30/60/90-day targets.
Irregular histories omit observation times; sparse histories retain explicit nulls.
No padding, interpolation or observed zero fabrication occurs.

The16 development mechanisms include constants, plateaus, both gradual trends,
both jump directions, multiple changes, stationary noise, changing volatility,
irregular/sparse observations, near-zero values, extreme scales, unobservable
future changes, distribution shifts and nonlinear reversals. Random streams,
mechanisms, counts, fixed windows and search settings were registered before fitting.
All880 history hashes, case identities and full generator-parameter hashes are
unique. Shared generating families remain related; these are not880 real repositories.
The old synthetic populations were not reused as new test evidence.

The target is **endpoint inequality**, not any interim event followed by reversal.
Only synthetic training labels enter fitting. Validation chooses configs once.
Separate calibration labels produce residual interval radii. Models, requests,
selection, calibration and all6480 endpoint predictions were sealed before either
test/OOD numerical target file was read for scoring. Events/seals and the independent
[verification](examples/phase6_2/numerical_verification.json) prove the implemented
logical chronology. This is a tested role/file/contract boundary, not OS isolation
against malicious Python code or a claim that generator truth is inaccessible to
an author deliberately bypassing the interface.

## Implementation and selection

New package [forecasting_research/phase6_2](forecasting_research/phase6_2/README.md)
reuses immutable synthetic requests, UTC/finite/hash utilities and signed-stock
reconstruction/gate/blend arithmetic. Existing experiments and adapters are unchanged.
Pure predictors receive only request/state/config/horizon, never split, scenario,
future labels or generator parameters.24 past-feature definitions, training-only
median/missing-indicator preprocessing, deterministic logistic heads and direct/
changed-only ridge heads are documented in the two component reports.

Regularization candidates are1 and10; hard thresholds0.1/0.25/0.5/0.75/0.9;
blend weights0/0.25/0.5/0.75/1. Both intercepts are unpenalized. No class reweighting.
Logistic uses40 deterministic half-step Newton updates. No refit follows validation.
The selected policy minimizes equal-family normalized **validation** MAE with an
explicit one-minute training/selection scale floor; fixed grid order resolves ties.
Reported normalized metrics use unfloored past mean absolute stock, excluding and
counting the one all-zero-history test denominator. These denominators are different
by design and must not be interchanged. No epsilon is silently assigned to metrics.

## Main test results

All methods score the same192 test cases at all three exact horizons, no failures.
One origin per case makes case-macro MAE equal pooled case MAE; equal-family MAE
is separately exported and here equals raw MAE because every family has12 cases.
RMSE is pooled-case RMSE. Units are simulated estimated maintainability remediation
minutes, never measured analyzer debt or actual repair labor.

| Days | Validation-selected method | Persistence MAE | Selected MAE | Raw MAE skill | Normalized skill |
| --- | --- | --- | --- | --- | --- |
| 30 | hard_gate | 1,942.398 | 688.603 | +64.55% | +37.43% |
| 60 | mixture_median | 3,311.420 | 595.005 | +82.03% | +62.90% |
| 90 | anchored_trend | 5,393.460 | 459.493 | +91.48% | +64.94% |

These are validation-selected policies, **not** post-test winners. Descriptively,
raw test MAE is lowest for blend at30d(373.800), anchored trend at60d(132.787),
and anchored trend at90d(459.493). The normalized test ranking favors the frozen
selected methods. The raw winners were not adopted after seeing test scores.
The90d selected method is a statistical baseline, so the two-stage architecture
is not uniformly superior even within this synthetic setting.

## Scale, changes and negative results

| Days | Persistence MAE without mixed scale | Selected MAE without mixed scale | Raw skill without mixed scale | Normalized skill without mixed scale |
| --- | --- | --- | --- | --- |
| 30 | 37.904 | 27.165 | +28.33% | +36.08% |
| 60 | 64.644 | 28.580 | +55.79% | +61.92% |
| 90 | 86.854 | 42.735 | +50.80% | +63.48% |

The selected policies retain positive normalized skill with and without the
extreme-scale family. Raw improvement is much larger and scale-sensitive; it must
not be used alone to claim success. All metrics and per-family values are in
[aggregate_metrics.csv](examples/phase6_2/aggregate_metrics.csv) and
[per_family_metrics.csv](examples/phase6_2/per_family_metrics.csv).

| Days | Unchanged N / MAE | Changed N / MAE | Large increases N / MAE / skill | Large decreases N / MAE / skill |
| --- | --- | --- | --- | --- |
| 30 | 54 / 0.000 | 138 / 958.056 | 38 / 58.731 / +51.88% | 5 / 89.401 / -6.88% |
| 60 | 30 / 28.046 | 162 / 699.997 | 61 / 338.642 / +92.84% | 14 / 58.483 / +31.11% |
| 90 | 15 / 9.572 | 177 / 497.621 | 78 / 1,075.002 / +91.87% | 24 / 96.333 / -7.10% |

A large change is `abs(delta)>=max(10 minutes,0.2*current)`, preregistered.
Selected30d hard gating removes all54 unchanged-case movements, compared with
54 false movements and23.528 MAE for ungated delta regression. This is useful
engineering evidence. At60d the selected mixture still introduces10 false movements;
at90d the selected trend introduces2. Large-decrease skill is negative at30d and90d.
Improving aggregate error does not establish safety on meaningful debt reductions.

Held-out-mechanism robustness,48 cases from only two families:

| Days | Persistence MAE | Frozen selected MAE | Raw skill | Normalized skill |
| --- | --- | --- | --- | --- |
| 30 | 28.853 | 33.715 | -16.85% | +22.09% |
| 60 | 44.809 | 29.864 | +33.35% | +48.71% |
| 90 | 52.116 | 48.310 | +7.30% | +21.73% |

Raw30d error is worse than persistence. These OOD results are descriptive synthetic
stress evidence, not real-world generalization. All48 OOD targets change at every
horizon; negative-class classification/AUC diagnostics are explicitly undefined.

## Classification and uncertainty

Metrics below describe the validation-selected **hard-gate classifier**, even when
the selected stock forecast at a horizon is a different method. Classification
scores do not replace forecasting MAE or certify calibrated probabilities.

| Days | Threshold | Precision | Recall | F1 | PR-AUC (AP) | ROC-AUC | Brier | Positive prevalence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 30 | 0.75 | 1.0000 | 0.9493 | 0.9740 | 0.9974 | 0.9924 | 0.0226 | 0.7188 |
| 60 | 0.5 | 0.9401 | 0.9691 | 0.9544 | 0.9943 | 0.9677 | 0.0579 | 0.8438 |
| 90 | 0.75 | 0.9880 | 0.9322 | 0.9593 | 0.9957 | 0.9507 | 0.0436 | 0.9219 |

Full probability bins, prevalence/confusion counts and single-class nulls appear
in [classification_metrics.json](examples/phase6_2/classification_metrics.json).

Derived80% absolute-residual intervals, separate calibration partition:

| Partition | Days | Coverage80 | Mean width | Collapsed / invalid |
| --- | --- | --- | --- | --- |
| test | 30 | 82.81% | 5,771.717 | 0 / 0 |
| test | 60 | 85.42% | 6,230.620 | 0 / 0 |
| test | 90 | 77.08% | 8,313.534 | 0 / 0 |
| ood | 30 | 50.00% | 72.266 | 0 / 0 |
| ood | 60 | 58.33% | 78.030 | 0 / 0 |
| ood | 90 | 54.17% | 104.166 | 0 / 0 |

Coverage deteriorates markedly on the held-out mechanisms, and mean widths are
scale-sensitive. All selected calibrated intervals are ordered/noncollapsed, but
that is not proof of useful calibration. Raw empirical-mixture intervals have
main-test coverages80.73/88.02/78.65% and17/1/0 collapsed intervals at30/60/90d.
Native pretrained intervals are unavailable because no pretrained inference ran.
No test residuals were used for calibration. No distribution-free conformal or
conditional-coverage guarantee is claimed. Interval scores/pinball/strata are exported.

Paired comparisons preserve identical IDs and sample whole mechanism families,
500 paired bootstrap resamples with seed620. The test has16 families; OOD has2.
The two-family intervals are especially weak descriptive diagnostics. Synthetic
bootstrap intervals do not establish real-world significance or independent
repository replication. See [paired_comparisons.csv](examples/phase6_2/paired_comparisons.csv).

## Resources, reproducibility and verification

One sequential CPU worker, two numerical threads, no network calls, no downloads
or installations. Existing NumPy2.4.4's916 RECORD-hashed payload files and the
Python binary were independently verified before and after execution. RECORD is
local integrity evidence, not an independent publisher signature. No Torch or
pretrained model code was imported by the numerical worker.

Measured wall time: 147.165s supervised / 146.990s worker.
Worker user/system CPU: 147.153/0.203s.
Peak observed RSS/HWM: 103,190,528 bytes (98.41MiB);
final kernel worker high-water: 102,957,056 bytes. Exit0, no failure.
Limits remain2GiB RSS/900s/two threads,8MiB logs/64MiB task output. Monitoring is
10ms sampled RSS/HWM plus final ru_maxrss, not a hard cgroup quota. Python socket
connections are denied; this is not network-namespace isolation. Ordinary errors
retain a finally resource receipt; abrupt kill measurements remain unavailable
except captured supervisor observations. No cgroup/OOM counters are invented.

All6480 frozen predictions repeated identically without refitting. Independent
read-only auditing checks26 sealed artifacts,6480 matched forecasts and3024
separate arithmetic checks. The full private study, dataset, predictions, raw
logs and full NumPy file inventory stay outside Git at
`/home/hp/tst/research/forecasting_mvp/phase6_2/2026-10-20/study-001`.
Small original synthetic model states, configs, seals and summaries are published.
84 new deterministic tests passed. The working checkout passed1,530 main regressions
plus14 tiny-tensor/fake-contract tests (**1,544 total**); canonical main passed1,468
plus14 (**1,482 total**). Zero failures/errors/skips. The62-case difference is the
preexisting local-only demo suite. Exact commands, test lists, exclusions, log hashes
and timings are in [verification.json](examples/phase6_2/verification.json).
No real benchmark, historical labels, pretrained checkpoint inference or external
service execution was included in these tests.

Preservation verifies all prior working/canonical file bytes,19,209 earlier
private-task files, all six compilation archives/claims,18 source states,56 frozen
bundles/322 artifacts, both Phase5.1 bundles, database/checkpoint/cache/ledger hashes,
all earlier Phase6 private artifacts and22,397 original dependency files. User Maven
cache metadata and75 reference artifacts are unchanged. No Docker, SonarQube, Maven,
scanner, service or volume command was issued; live-volume bytes were not measured.
No ownership of unrelated services or preexisting changes is assumed.

## Decision and stop

PASS means valid synthetic software, fitting/selection/sealing, measured comparison,
uncertainty investigation, reproducibility and preservation. It is not a real-data
forecasting improvement or promotion of any model. Chronos is
NOT_EXECUTED_NO_SEPARATE_APPROVAL; TTM/TimesFM are NOT_EXECUTED, outside this phase's
comparison. All24 rights decisions remain NOT_APPROVED. No real data was admitted.
The [Phase6.3 handoff](PHASE_6_3_RESEARCH_HANDOFF.md) is planning only. STOP after
publication; no further model execution, real collection or Phase6.3 follows.
