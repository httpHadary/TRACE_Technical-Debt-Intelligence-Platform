# Adaptive Persistence improvement — new Phase 6.4 registration

SYNTHETIC_ENGINEERING_TEST. This successor is authorized by the user's new
Adaptive Persistence Improvement request. Earlier phase stop conditions and their
results remain historical records; no old result is corrected or overwritten.
All 24 analyzer/data permissions remain NOT_APPROVED. No real data, pretrained
execution, model acquisition, scanner, Maven, service or interface work is included.

## Evidence and design decision, before fitting

Phase 6.3 had a real selector defect (`eligible or candidates`) and inadequate
30-day decrease support. Main normalized gains did not survive unseen mechanisms;
raw 30/60-day losses and poor uncertainty transfer forbid claiming a reliable model.
Phase 6.2's selected 90-day model was a trend baseline, not learned Adaptive
Persistence. Old Java persistence advantages are contextual, not a fresh holdout.

The primary proposal is a local empirical signed-change distribution. It directly
retains zero mass, increase/decrease proportions and signed magnitudes. Its inverse
CDF median minimizes empirical absolute loss; this is a property of the local
training sample, not a guarantee about a new case. Conditional means and hard
class decisions can exaggerate movement under uncertain change. A distribution
median, novelty rejection, shrinkage and an explicit protected action address
that mechanism with no new dependency or pretrained model.

The predictor always starts from observed current debt. A training-normalized
origin-only neighborhood estimates the three endpoint-direction proportions and
signed median. If the median is zero, history lacks similarity support, direction
confidence is insufficient, or empirical local MAE gain is below .01 model-scale
units, retain persistence. Otherwise apply a validation-selected shrinkage times
the audited historical gap reliability, then clip final stock to zero. Raw delta,
negative magnitude, median, direction scores and gate reason remain observable.
Scores are empirical neighbor frequencies, not certified posterior probabilities.
Unobserved future events may be inherently unpredictable from the admitted past.

## Population fixed before numerical fitting

Two independently seeded replications: 64120261020 and 64120261021. Each has
576 training, 288 validation, 288 calibration, 384 test, 288 unseen-mechanism
and 144 identifiability-stress cases. Total 3,936 cases; 1,632 final evaluation cases. Histories have 256 generated
calendar positions with genuinely missing or irregular observations when specified.
Exact endpoint timestamps are origin +30/+60/+90 days; units are simulated
estimated maintainability remediation minutes. No imputed observations or labels.

Twelve development families: constant, growth, decay, stairs up/down, cycle,
mean reversion, stationary noise, quiet jump, trend stopping, sparse and irregular.
Scales are 1,30,300,30000 times independently sampled [.8,1.2] factors. Near-zero
histories reach zero and remain there; exact all-zero behavior is a unit fixture.
Development futures independently cease movement with probability .25; visible
trends are not assumed to continue. All parameters/noise streams are registered
in source. No rejection sampling or outcome-dependent replacement is permitted.

Six OOD mechanisms absent from development: reversal, chirp, damped cycles,
renewal events, volatility shift and hidden switches. The OOD evaluation continues
their registered trajectories, with the same independently hidden .25 cessation
probability. A SEPARATE identifiability-stress partition has eight independent
histories per family with three branches: unchanged exact endpoints after interim
excursions, upward surprise, downward surprise. The triple shares history and receives identical
predictions, but separate hidden future labels. These are an explicit information
limit stress test, not three independent observations. Family/group dependence must
remain visible. It cannot support claims that an algorithm can foresee hidden
branches. Test families overlapping training still share generator semantics.

Cross-role history duplicates are prohibited. Within the identifiability stress set, duplicates must belong
to the registered triple. All generator identities, request/label file hashes and
code are sealed before fitting. The previous published history inventory is checked
for overlap. No old label is used for fitting or validation.

## Fixed model search and selection

Use the existing audited 24 past-only features and training-only median/missing-flag
standardization. Exclude absolute log-scale from the new model; use 19 registered
features plus their missing indicators for distances. Euclidean squared distances
are averaged across those dimensions. Neighbors are selected with deterministic
ties; no family/partition/seed/future feature enters prediction.

Primary grid: one zero-adjustment option, plus k={16,48,96}, direction confidence
{.6,.8}, shrinkage {.25,.5,1}: 19 configurations/horizon/replication, 114 total.
Training leave-one-out k-neighbor distances establish the 95th-percentile novelty
threshold. No test distance sets that threshold. A .01 local expected normalized
MAE reduction is required. Gap multiplier is 1/(1+max_observed_gap_days/30).

Validation safety requires at least24 examples from at least2 families in each of
unchanged, large increase and large decrease strata. Large means |delta| >=
max(10 minutes,.2*current). Insufficient evidence forces protected persistence.
Active candidates must satisfy unchanged equal-family normalized MAE<=.01,
full raw MAE<=1.01*persistence, and both raw/normalized large increase/decrease
MAE<=1.02*persistence. Require >2% normalized validation improvement overall.
Among eligible candidates within1% of minimum normalized error, choose first in
registered order. No eligible candidate ALWAYS yields shrinkage0, never the best
unsafe candidate. Sample inadequacy is explicitly distinct from demonstrated safety.

Primary selection objective is equal-family MAE divided by max(1 minute, mean
observed historical debt). This explicit one-minute scale is used consistently
in modeling, selection and primary normalized reporting. Also report unfloored
historical-mean normalized skill, excluding/counting exact zero denominators, and
full raw errors. No hidden epsilon. Extreme-scale exclusion is a secondary analysis.

Matched baselines: persistence, last7 actual observations mean, original90-calendar
day anchored trend, direct ridge delta (fixed L2=10), ungated local median (k48),
and original frozen Phase6.3 AP state/configs (30d marked historical policy deviation).
Frozen transfer is applied to new requests only. No archived fit or cohort is rerun.
Adaptive Persistence stays primary even when a baseline wins. No post-test promotion.

## Calibration, sealing and evidence

Freeze point state/selection before opening separate calibration labels. Default
80% intervals use empirical80th percentile absolute residual / model-scale on that
partition, centered on frozen point and truncated at zero. Also report uncalibrated
local10/90 empirical stock intervals as an ablation. No test calibration, widened
interval search, quantile sorting or distribution-free coverage claim.

Complete test, OOD and identifiability predictions, models, calibration and selection must be sealed
before their target files open. This is a logical audited interface/filesystem
boundary, not a malicious-code security sandbox. Replications are predetermined;
no intermediate score changes any later replication/configuration. Predictions
repeat exactly, and hidden-branch triples must get equal forecasts.

Report every method/horizon/replication/partition, including raw MAE/RMSE/median/bias,
equal-family normalized skill, unfloored sensitivity, extreme-scale exclusion,
changed/unchanged/large-up/large-down counts and errors, false/missed changes,
direction/action F1 and Brier,80% coverage/width/score, failures and eligibility.
500 paired family-cluster bootstrap draws are exploratory synthetic diagnostics.
They do not establish real-repository independence or scientific significance.

Performance success is deliberately stringent: strictly positive raw and normalized
AP skill at every horizon in BOTH replications and BOTH evaluation populations,
unchanged normalized error<=.01, no worse than−2% large-sign raw/normalized skill,
and informative final safety strata (>=24 examples, >=2 families). The balanced
identical-history stress set makes persistence the conditional empirical median;
strict improvement there is mathematically unattainable. Its separate reliability
target is raw/normalized regret <=1%, with no claims to foresee a hidden branch.
Interval success
is separate:75–85% coverage and normalized mean width<=2 throughout. Any failure
rejects that combined research claim; a correct negative experiment can still PASS
implementation/evaluation validity. No seed swaps, retuning or retries to force success.

One sequential CPU worker:2GiB RSS,2 numerical threads,900s,8MiB logs,16MiB per
artifact,128MiB total task payload (larger input population than Phase6.3). Use existing
Python/NumPy, verify installed NumPy RECORD hashes, no downloads or installation.
Sampled RSS/HWM and final kernel ru_maxrss are observations, not cgroup guarantees.
Python network connections denied; no network-namespace claim. Exclusive attempt,
fresh outside-Git directory, ordinary-exception receipts and owned-process cleanup.

Preserve old code/reports/states/data/claims/rights as opaque-byte hashes. Publish
only original source, small synthetic summaries and receipts. Full inputs/predictions
remain private. Report the outcome transparently and stop this registered study.
