# Phase 6.3 — Adaptive Persistence robustness

**PARTIAL — SYNTHETIC_ENGINEERING_TEST.** Numerical execution, identity/seal
checks and arithmetic verification passed. Overall phase validity is PARTIAL:
the30-day primary AP selection violated the preregistered protected fallback when
validation safety support was inadequate, and main30-day large-decrease evaluation
has no cases. These are validity/support limitations, not merely negative scores.
No registered source, coefficients, selected config, calibration, prediction, raw
outcome or cohort was changed after observing results. No corrected run occurred.

Date:2026-10-20, Africa/Cairo. Starting main4f8cfa60514632f71462769ac8adb0bd7ac09611.
The failure audit was published first in d116343; implementation/protocol/registration
were published in c76f6ec **before** fitting the registered population.
Registration SHA256 `4baa04cc4f60b9887b84cd045f55d653b4efb951b048b986ca37a0cf00647493`.

## Primary architecture and immutable protocol

Adaptive Persistence stays primary at every horizon. It starts from current stock,
learns three-way endpoint direction, predicts separate positive/negative signed
magnitudes, and uses validation-selected confidence, minimum magnitude, volatility
and measurement-gap-aware shrinkage. Final stock is max(0,current+adjustment).
Raw components, sign projections, intentional shrinkage and stock clipping remain
distinct. Weak evidence should preserve persistence. There is a protected zero-
adjustment candidate. Trend/direct regression are comparisons, never replacements
for this research objective. The comparison champion is an explicitly separate alias.

The [preregistration](PHASE_6_3_PREREGISTRATION.md) fixes73 configurations per horizon,
219 total, L2 1/10,40 deterministic Newton half-steps, unpenalized intercepts,
none/balanced training class weights, fixed thresholds/blends, scale policies and
quantitative safety/interval targets. Only new training data fit models/transforms;
validation selects point and interval algorithms; separate calibration fits final
residual distributions. No refit follows selection. Full state and configs are
small original synthetic JSON artifacts in examples/phase6_3.

Selection minimizes equal-family validation MAE / max(1 minute,past observed mean),
with unchanged error<=0.02 and raw plus normalized large-decrease MAE<=1.05 times
persistence, requiring at least8 examples per safety stratum. A1% tie band prefers
registered simpler methods/configs. Reported normalized metrics use the **unfloored**
past mean, excluding/counting one all-zero-history test denominator; raw metrics
retain every case. The different training/selection scale is explicit, not a hidden
epsilon. It also limits conclusions for sub-minute/zero-debt series.

## Protocol defect and unsupported essential comparison

At30d validation had only3 large-decrease cases, so no candidate was safety-admitted.
The generic `selection.choose` used `eligible or candidates`, selecting the minimum
unconstrained-error active AP configuration instead of the registered protected
zero-adjustment fallback. The comparison champion correctly fell back to ordinary
persistence, but that does not fix the primary AP policy deviation. This is a
selector implementation defect. It was found after test scoring; no post-test
correction, replacement forecast or new cohort was generated. The original
`selection.json` already records safety_eligible=false and sample_adequate=false.

Main30d has0 large-decrease cases; MAE/skill are null, not invented zeros. Thus the
requested30d decrease-robustness conclusion is unavailable. At60/90d validation
safety was admitted with18/30 large-decrease examples; those recorded configs
retain their validation meaning. Every30d primary result below is descriptive of
this actual noncompliant selection, not an approved safe-model result.

[Protocol audit](examples/phase6_3/protocol_audit.json) and six documentary regression
checks reproduce/detect the deviation without fitting or forecasting. Numerical
PASS receipts mean arithmetic/lineage correctness only; they do not override this
PARTIAL phase decision. The original preregistered source remains unchanged;
README now appends a warning rather than concealing the original design promise.

## New population, boundaries and exact coverage

1184 original synthetic cases:384 train,192 validation,192 calibration,256 main
test,160 OOD. Sixteen development mechanisms and eight entirely held-out mechanisms
cover plateaus, increases, reductions, recovery/regression, interim returns,
reversals, unobservable future jumps, sparse/irregular histories, noise and scales.
180 generated calendar positions precede each origin. Nulls/timestamps stay intact;
no padding, interpolation, zero fabrication or Git/process features. Common admission
requires measured origin and at least2 actual observations in the final90 days.
All cases pass; no outcome-based exclusions or population edits occurred.

All1184 history/parameter identities are unique, with zero history-hash overlap
against Phase6.2. Independent hash-derived seeds use root63020261020. OOD has8
families x20 cases; at every horizon each family has10 unchanged,5 increased and5
decreased endpoints. Interim excursions returning to origin count as unchanged.
The shared OOD balancing scaffold still creates dependence; these are not independent
software repositories. Some future branches are intentionally unidentifiable from
past observations, making persistence a particularly strong reference.

Requests expose only past values/timestamps and opaque IDs. Future class, family,
partition, seed and changepoints never enter prediction features. Role/file guards
and complete prediction/config/model/calibration seals precede main/OOD/diagnostic
label access. This is a logical tested interface boundary, not an OS adversarial
sandbox. All14976 forecasts (12 methods incl alias x416 cases x3 horizons) are
represented, zero runtime exceptions/dropped/ineligible cases. Protocol defects are
separate from forecast failure accounting. Old6.2 workload/labels were not rerun.

## Primary measured results

Units are simulated remediation minutes. Case-macro MAE equals pooled case MAE
because each case has one origin; family macro is separately reported. RMSE is
pooled across cases. These are not the original Java repository-macro statistics.

| Days | Persistence MAE | Primary AP MAE | Raw skill | Normalized skill | Primary selection status |
| --- | --- | --- | --- | --- | --- |
| 30 | 121.907 | 140.114 | -14.94% | +18.21% | DEVIATION: safety not admitted |
| 60 | 105.286 | 177.244 | -68.35% | +12.69% | Validation safety-admitted |
| 90 | 188.532 | 169.107 | +10.30% | +9.76% | Validation safety-admitted |

The comparison champion was persistence30d and direction_gate60/90d. It is not
substituted into the primary results. Main normalized error improves, but raw MAE
worsens substantially at30/60d. This does not establish uniform forecasting success.

| Days | MAE excluding mixed scale | Raw skill excluding mixed scale | Normalized skill excluding mixed scale |
| --- | --- | --- | --- |
| 30 | 20.518 | +18.39% | +19.80% |
| 60 | 51.592 | +7.67% | +12.82% |
| 90 | 73.350 | +5.83% | +9.33% |

Gains survive main-test scale normalization/excluding mixed scales. The raw ranking
changes because a few extreme-scale cases dominate errors. Complete methods,
per-family errors, RMSE/median/bias and paired tables are published; no favorable
subset replaces the full population.

## Unseen mechanisms and changes

| Days | Persistence MAE | AP MAE | Raw skill | Normalized skill |
| --- | --- | --- | --- | --- |
| 30 | 57.996 | 58.973 | -1.68% | -2.48% |
| 60 | 55.751 | 57.182 | -2.57% | -3.34% |
| 90 | 44.439 | 45.008 | -1.28% | -2.68% |

All OOD normalized skills are negative. AP is closer to persistence than the frozen
Phase6.2 transfer, but that is not improvement over the required reference. Direction
and magnitude confidence do not transfer reliably to hidden future branches.

| Partition | Days | Unchanged N / MAE | Changed N / MAE | Large decreases N / MAE / skill | Large increases N / MAE / skill |
| --- | --- | --- | --- | --- | --- |
| test | 30 | 88 / 0.001 | 168 / 213.507 | 0 / UNAVAILABLE / UNAVAILABLE | 21 / 104.174 / +14.15% |
| test | 60 | 65 / 0.002 | 191 / 237.562 | 32 / 180.970 / +1.58% | 30 / 133.813 / +12.53% |
| test | 90 | 45 / 0.003 | 211 / 205.172 | 48 / 178.387 / +0.60% | 45 / 196.627 / +8.02% |
| ood | 30 | 80 / 2.114 | 80 / 115.831 | 21 / 158.835 / -1.54% | 26 / 149.353 / +1.61% |
| ood | 60 | 80 / 3.378 | 80 / 110.986 | 24 / 138.174 / -1.55% | 32 / 128.091 / +2.20% |
| ood | 90 | 80 / 1.516 | 80 / 88.499 | 16 / 128.431 / -2.41% | 22 / 145.550 / +2.39% |

Main unchanged forecasts make only1 false movement at each horizon, but the90d
model-scale unchanged error0.021758 exceeds its0.02 tolerance. Most actual changes
are missed. Main60/90 large-decrease raw skill is+1.58/+0.60%; OOD decrease skill
is−1.54/−1.55/−2.41%, within the−5% tolerance but still worse than persistence.
The30d main decrease question remains untestable. These results do not repair or
relabel Phase6.2's exposed test. Compare the frozen model on NEW matched cases only.

## Classification and derived uncertainty

| Partition | Days | Direction macro-F1 | Multiclass Brier | Action precision | Action recall | Action F1 | False moves / misses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test | 30 | 0.813 | 0.263 | 0.983 | 0.351 | 0.518 | 1 / 109 |
| test | 60 | 0.756 | 0.346 | 0.983 | 0.309 | 0.470 | 1 / 132 |
| test | 90 | 0.745 | 0.365 | 0.983 | 0.280 | 0.435 | 1 / 152 |
| ood | 30 | 0.261 | 1.023 | 0.421 | 0.100 | 0.162 | 11 / 72 |
| ood | 60 | 0.198 | 1.011 | 0.370 | 0.125 | 0.187 | 17 / 70 |
| ood | 90 | 0.199 | 1.007 | 0.500 | 0.075 | 0.130 | 6 / 74 |

Direction macro-F1 measures three-way raw-head decisions; action F1 measures actual
stock movement after gates/shrinkage/clipping. Multiclass Brier ranges0–2. Confidence
scores are normalized OVR estimates, not certified posteriors. High main head F1
coexists with low movement recall and poor OOD direction/forecasting. Auxiliary
binary probability diagnostics and bins are separate from action metrics.

| Partition | Days | Selected coverage | Mean / median width | Shared coverage | Frozen-transfer coverage |
| --- | --- | --- | --- | --- | --- |
| test | 30 | 80.47% | 767.212 / 59.647 | 77.73% | 67.58% |
| test | 60 | 83.20% | 921.076 / 176.436 | 82.81% | 80.08% |
| test | 90 | 78.12% | 1,470.123 / 205.133 | 81.25% | 77.34% |
| ood | 30 | 44.38% | 55.954 / 56.715 | 52.50% | 61.25% |
| ood | 60 | 62.50% | 192.054 / 186.111 | 76.25% | 73.12% |
| ood | 90 | 81.25% | 235.276 / 225.715 | 86.88% | 88.75% |

Intervals use training residual prototypes for validation-only choice, then192
independent calibration cases. All horizons selected predicted-direction-stratified
signed residuals with widening1.0. No test-based widening occurred. Quantile ordering
is valid, with0 collapsed/invalid selected intervals, but OOD coverage still fails.
All main selected interval scores beat same-point shared symmetric scores; all OOD
selected scores are worse. Only90d OOD coverage enters75–85%, and even there interval
score fails the comparator criterion. Widths are not arbitrarily increased; raw
mean/median and normalized widths are reported. Frozen-transfer intervals use a
different frozen point model and are not a calibration-only ablation.

## Runtime, verification and preservation

One CPU-only lightweight worker; two numerical threads; no foundation-model loading,
networking, downloads, installation, fine-tuning or service operations. Existing
Python3.12.3 / NumPy2.4.4 and916 NumPy RECORD payload hashes verified before/after.
Local RECORD checksums are integrity evidence, not independent publisher signatures.
Supervised wall 50.063s; worker wall 49.892s;
user/system CPU 50.298/0.222s.
Peak observed RSS/HWM 171,233,280bytes
(163.30MiB); final kernel high-water
170,979,328bytes. Exit0; no resource-triggered termination.
Limits unchanged:2GiB RSS,900s,two threads,8MiB logs,64MiB outputs. Actual private
payload36,981,752bytes; stdout/stderr empty. Monitoring uses sampled /proc and final
ru_maxrss, not hard cgroup enforcement; cgroup/OOM counters are unavailable. Python
socket connections are denied, not network-namespace isolation. Finally receipts
cover ordinary errors; abrupt-kill missing fields remain unavailable.

All14976 predictions repeat exactly without refitting. Independent auditing checks
29 sealed files and10152 arithmetic identities, complete
matched populations and original transfer hashes. New tests:108 architecture tests
plus6 protocol diagnostics. Broad regressions passed1652 working/1590 canonical;
with six later diagnostic checks1658/1596 respectively. The final108 targeted checks
also passed in both checkouts after protocol clarifications. Repeated executions of
the same test are not counted as independent cases. Zero pytest failures/errors/skips;
passing deviation-detection tests do NOT mean the selector defect is fixed.

Preservation verifies1008 prior working/1086 canonical file hashes,19,209 earlier
private-task files, Phase6.0/6.1/6.2 private outputs,56 bundles/322 frozen artifacts,
both Phase5.1 bundles, database/checkpoints, all six compilation archives,18 source
states, request ledgers/claims and original dependencies/user-cache reference hashes.
No Docker, SonarQube, Maven, scanner, database query or live-volume command occurred;
no live-volume byte preservation is claimed. All24 permission decisions stay
NOT_APPROVED. No real data or production service was admitted/modified.

Full dataset/predictions/raw receipts remain outside Git in
`/home/hp/tst/research/forecasting_mvp/phase6_3/2026-10-20/study-001`.
Only original source, small synthetic model states, summaries and reproducibility
metadata are published. Source/config seals and the PARTIAL protocol gate remain
separate authoritative records. No post-test correction or automatic retry occurred.

## Explicit conclusions and stop

1. Synthetic forecasting: main normalized gains, but raw gains only90d; not uniform,
   and30d primary selection is noncompliant.
2. Unseen-mechanism robustness: NOT demonstrated versus persistence; skill negative
   at all three horizons, despite improvement over frozen transfer.
3. Large-decrease failure: narrower main60/90 gains, no30d main evidence, small OOD
   deterioration. No general reduction claim is justified.
4. Uncertainty: main calibration metrics improve; reliable OOD calibration does not.
5. Independent rights-cleared real-data verification remains essential and blocked.

Smallest next step is a separately authorized versioned no-safe-AP selector fix,
its regression, and a new preregistration with adequate decrease strata planned
from development evidence. Do not reuse these exposed scores as fresh tests.
The [handoff](PHASE_6_4_RESEARCH_HANDOFF.md) is planning only. STOP after publication;
no Phase6.4 execution, real-data study, pretrained run or collection is authorized.
