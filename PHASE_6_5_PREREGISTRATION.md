# Phase 6.5 — information adequacy, before fitting

Scope: SYNTHETIC_ENGINEERING_TEST. User authorization is the new request at commit
26dea4942d934d1f3325096ed1ca452b39bf3ba8. No restricted data, real feature extraction,
pretrained models, acquisition, scanner, service or previous experiment execution.
All 24 Phase C decisions stay NOT_APPROVED. Standard library only.

## Questions and falsification

1. Does added origin-known information improve exact 30/60/90-day predictions when
   its relationship to the outcome is stable? Failure to beat matched persistence
   falsifies that result for the registered synthetic channel, not all real signals.
2. Can unsigned activity identify direction? It may identify event likelihood but
   mixes increases/decreases; point-median persistence can remain optimal.
3. Can a valid timestamp or confidence gate detect a reversed conditional mapping
   with identical observed inputs? No; paired-world equality tests enforce this.
4. Does stress-aware validation protect against known mapping uncertainty? Compare
   local admission to validation stress admission; zero adjustment is a valid result.
5. Do calibration intervals transport? Measure coverage and width/score under each
   mechanism. No test-driven calibration or distribution-free guarantee.

## Fixed population and intervention

Replications: 65120261020, 65120261021, 65120261022. Unit tests use seed 11 only.
Six development history families: plateau, growth, decline, cycle, sparse, noise.
Four unseen-history families: reversed historical trend shape, damping, irregular
observations, burst shape. These are new history mechanisms, not new real projects.
96 generated daily calendar positions, null sparse records and genuinely irregular
observations. No padding or interpolation. Exact origin+30/60/90 UTC targets.
Per family: 60 train, 30 validation, 30 calibration, 40 test; unseen 60 per family.
Per replication: 360 train, 180 validation, 180 calibration, 240 main test and
240 unseen-history cases. Three additional 240-case paired interventions reuse the
main requests: hidden independent future driver, reflected/reversed future mapping,
and signals arriving one day after origin. They are paired worlds, not independent
replications. Core population has 5,760 case-role entries, including paired copies; two additional
paired validation stress stores add1,080, giving6,840 stored request entries;
3,600 final case-role entries, with only 1,440 distinct final histories/identities
before accounting for intentionally repeated all-zero histories.

Scales 0,10,100,10000 times [.8,1.2]. Zero controls are absorbing by construction;
they cannot establish that zero-debt real systems cannot accumulate debt. Report
zero denominators separately. All nonzero generated history hashes must be unique
across generation roles and replications. Origin timestamps are 2040+synthetic offsets.

Causal generation order: history → uniformly sampled origin plan {-1,0,+1} → noisy
ordinal record (90% correct, otherwise a uniform redraw) and unsigned activity
(8–10 if nonzero plan,1–3 otherwise) → future realization draws. These are artificial
information channels, not actual Git metrics or stakeholder plans. Intent is NOT
copied from the realized endpoint. Realization probabilities at 30/60/90 are
.70/.82/.90 with one shared uniform draw; independent sign reversal probability .07.
Magnitude is current×uniform(.12,.30)×(h/30)^.6. Unexecuted plans leave stock unchanged.
Hidden intervention uses independent uniform {-1,0,+1} directions and independently
sampled magnitudes. Reversed intervention reflects the base targets about current.
Do not alter seeds, strata or realization probabilities after scoring.

## Models and fixed selection

Matched methods: persistence; fixed last-seven-observed mean; fixed anchored
90-calendar-day OLS trend; history-sign conditional median; unsigned-activity
conditional median; ordinal-intent conditional median; locally admitted Adaptive
Persistence; stress-admitted Adaptive Persistence. All start at current stock and
retain raw signed adjustments before max(0,raw stock). No model identity/family,
partition, branch, outcome or future event is an input. Real data is rejected.

Training-only empirical signed-delta distributions normalized by max(1 minute,
current observed stock). History sign uses trailing30-day slope normalized by this
scale and fixed .0002/day tolerance. Unsigned activity bin threshold5. Intent bins
{-1,0,+1}. Each horizon has its own empirical distribution. Require30 training
observations per cell; absent/late/incomplete signal means protected persistence.
Zero-origin controls return persistence, an explicit synthetic-only domain assumption.
Distribution medians minimize training empirical MAE; no claim of future optimality.

Adaptive candidates are shrink {0,.5,1}; no tuning of feature thresholds/model type.
Local selection uses validation equal-family normalized MAE, requires >2% skill,
>=24 stable/up/down examples, unchanged normalized MAE<=.05 and raw MAE no more
than1.02×persistence. Choose minimum objective, then smaller shrink; otherwise0.
Stress admission additionally requires no normalized regret and the same safety
conditions on paired validation hidden and reversed worlds. It changes only the
validation uncertainty set, never test labels. Zero is an honest robust outcome.

This is an engineering information experiment, not a universal reliability claim.
The goal is to expose a useful channel's dependence on assumptions. Report positive
and negative effects for every method/seed/horizon/population without promotion.
The broader user success criterion requires positive raw AND normalized skill at
all horizons across independent and shifted conditions plus unchanged-case safety;
it must fail if these are absent. Real-world validation remains unavailable.

## Evaluation and uncertainty

Primary: equal-family normalized MAE and paired error differences to persistence.
Secondary: raw MAE/RMSE/bias/median error, changed/unchanged, large signs >=max(1min,
.1×current), false/missed movement, no-extreme-scale sensitivity, direction confusion
macro-F1/Brier, native empirical distribution support and failures. Normalize by
max(1,current) with its physical one-minute floor explicit; also report unfloored
normalization excluding/counting zero denominators. Never use a hidden epsilon.
500 family-cluster paired bootstrap draws are exploratory; families are synthetic.
Do not pool paired intervention siblings as independent experimental units.

After point selection freeze, separate calibration residuals set an empirical80th
percentile radius in normalized units per method/horizon. Retain widths,80% coverage,
interval score, changed/unchanged coverage and collapsed intervals. Desired
calibration diagnostic75–85% coverage with normalized mean width<=1; report failures
without widening or retrospective model selection. Derived intervals, not pretrained
native intervals; no distribution-free or temporal guarantee.

## Reproducibility and resource boundary

Seal input/code/protocol/test/auditor hashes before fitting. Freeze model states,
selection and calibration; write ALL final predictions before opening final labels.
Verify complete seals, repeatability and paired-request equality. Labels live in
separate files behind audited logical access boundaries, not an OS security sandbox.
Publish protocol/implementation before the scientific worker. No reruns/retuning.
One sequential worker, <=2GiB RSS, <=900s, <=2 CPU threads,128MiB task payload,
16MiB per file,8MiB logs;4GiB host availability and256MiB disk admission. `/proc`
monitoring + kernel final ru_maxrss, RLIMIT address-space/CPU/file limits and socket
connection denial. No cgroup/network-namespace guarantees. Abort on resource failure.
Preserve all old tracked/untracked files and private studies by opaque hashes; use
existing receipts for legacy caches, datasets, weights and compilation preservation.
Publish only source, safe summaries and reproducibility metadata; keep full generated
inputs, labels, states and predictions outside Git. Stop after this registered study.
