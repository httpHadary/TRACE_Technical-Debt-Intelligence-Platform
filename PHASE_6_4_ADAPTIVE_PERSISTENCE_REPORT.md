# Adaptive Persistence improvement — Phase 6.4

**PARTIAL.** Implementation, numerical verification and preservation passed. The
user's consistent-improvement criterion was NOT demonstrated. Some OOD large-
increase groups also fail the registered support minimum, limiting those safety
claims. Negative results alone are not software failures. No model is promoted.
All numerical results are SYNTHETIC_ENGINEERING_TEST, in simulated estimated
maintainability remediation minutes; they are not real repository performance.


The new user request authorized a successor to the frozen Phase6.3 PARTIAL study.
Date:2026-10-20 Africa/Cairo. Starting main3b351552818a3eaf87307612dbc1023904b8182a.
Implementation/protocol/registration published in3f0731f BEFORE fitting. Registration
SHA256 `b927909f1b8bf63e8d4ff258a6e84f4f744430b6efe7670e7b32f363f6fef655`. Prior phase stops/results remain unchanged.

## What was repaired and why this architecture

The new selector never uses `eligible or candidates`: when evidence is insufficient,
safety fails, or active normalized validation improvement is <=2%, it returns the
explicit zero-adjustment AP action. Phase6.3's source, flawed30d selection and outputs
are untouched. The second new replication exercised the corrected fallback at all
three horizons with adequate validation support. Analytical tests also verify the
insufficient-support path. There is no silent unsafe selection or test-based change.

Primary AP = max(0,current+confidence-gated shrunk signed median). A local empirical
training distribution retains zero change, increase and decrease mass. The median
minimizes local empirical absolute loss, not guaranteed future MAE. Direction
proportions, positive/negative medians, local predicted benefit and history novelty
are separate diagnostics. No future family, direction, branch or event is a feature.
Training-only preprocessing, exclusion of absolute log-scale, a fixed novelty test,
gap reliability and conservative validation admission aim to avoid unnecessary moves.
The complete rationale,19 configs per horizon and safety tolerances are preregistered.

## Independent data and evaluation boundaries

Two fixed streams R1=64120261020, R2=64120261021;3936 new cases total. Each has
576 train,288 validation,288 calibration,384 main test,288 unseen-mechanism OOD,
144 separate identifiability-stress cases. Twelve development families and six
unseen mechanisms; main families share generating assumptions with training.
These are artificial cases, not independent software repositories. OOD triples are
ONLY in the separate identifiability partition: eight histories/family with stable,
upward-surprise and downward-surprise branches and identical origin observations.
OOD itself evolves reversal/chirp/damped/renewal/volatility/hidden-switch mechanisms.

All observations are generated before their role is used, with missingness retained;
the origin is measured. Cross-role duplicates and old1184 history hashes are checked.
Two random-stream replications are limited evidence of repeatability, not broad
external validation. Training labels fit; validation selects; calibration alone
sets residual intervals. All three final populations' forecasts/state/selection/
calibration are sealed before opening labels. This is a tested logical interface
boundary, not an OS security sandbox. Full data/predictions remain outside Git.

## Primary results

| Replication | Days | Persistence MAE | AP MAE | Raw skill | Normalized skill |
| --- | --- | --- | --- | --- | --- |
| R1 | 30 | 1,459.037 | 1,418.058 | +2.81% | +4.95% |
| R1 | 60 | 2,227.941 | 2,052.231 | +7.89% | +1.99% |
| R1 | 90 | 3,096.897 | 2,869.683 | +7.34% | +1.81% |
| R2 | 30 | 1,335.462 | 1,335.462 | +0.00% | +0.00% |
| R2 | 60 | 2,104.052 | 2,104.052 | +0.00% | +0.00% |
| R2 | 90 | 3,001.444 | 3,001.444 | +0.00% | +0.00% |


| Replication | Days | Selected AP configuration | Admission |
| --- | --- | --- | --- |
| R1 | 30 | {'confidence': 0.8, 'k': 16, 'shrink': 0.25} | VALIDATION_ADMITTED |
| R1 | 60 | {'confidence': 0.6, 'k': 96, 'shrink': 0.5} | VALIDATION_ADMITTED |
| R1 | 90 | {'confidence': 0.6, 'k': 96, 'shrink': 0.5} | VALIDATION_ADMITTED |
| R2 | 30 | {'confidence': 1.0, 'k': 16, 'shrink': 0.0} | PROTECTED_FALLBACK |
| R2 | 60 | {'confidence': 1.0, 'k': 16, 'shrink': 0.0} | PROTECTED_FALLBACK |
| R2 | 90 | {'confidence': 1.0, 'k': 16, 'shrink': 0.0} | PROTECTED_FALLBACK |


R1 improves main raw MAE by2.81/7.89/7.34% and normalized error by4.95/1.99/1.81%.
R2 admits no active setting under the full registered rule and equals persistence everywhere. Its best safety-eligible30d setting improves normalized validation error only1.33%, below the fixed2% minimum; safety-eligible60/90d settings provide no gain. More aggressive candidates improve validation error but violate the unchanged-case protection budget.
That is correct conservative behavior, not successful change anticipation. The more
aggressive ungated local median improves familiar-family tests, but deteriorates
strongly on OOD; it is not promoted after seeing test results. Comparison baselines
never replace the primary AP objective.

| Replication | Days | Persistence MAE | AP MAE | Raw skill | Normalized skill |
| --- | --- | --- | --- | --- | --- |
| R1 | 30 | 1,023.680 | 1,023.680 | +0.00% | +0.00% |
| R1 | 60 | 1,630.140 | 1,799.447 | -10.39% | -17.15% |
| R1 | 90 | 1,459.156 | 1,755.951 | -20.34% | -25.75% |
| R2 | 30 | 857.339 | 857.339 | +0.00% | +0.00% |
| R2 | 60 | 1,307.291 | 1,307.291 | +0.00% | +0.00% |
| R2 | 90 | 1,393.812 | 1,393.812 | +0.00% | +0.00% |


R1 OOD30 equals persistence; OOD60/90 raw error worsens10.39/20.34%, normalized
error17.15/25.75%. The deterioration comes from the reversal family: apparently
similar historical trends precede the opposite future direction. The distance-based
novelty gate cannot certify stability of the conditional future distribution.
R2 equals persistence, giving no consistent positive independent improvement.

On identical-history hidden-future triples, persistence is the empirical conditional
median. No past-only deterministic predictor can strictly reduce total MAE on the
balanced triples. R1 adds normalized regret0/5.85/10.25%; R2 ties persistence.
This stress test exposes unjustified movement; it is not evidence of a hidden-event
predictive feature. Its balanced construction is not a natural-event prevalence claim.

## Reliability, signs and uncertainty

R1 main large-decrease skill improves2.14/16.34/17.38%, but unseen decreases worsen
16.85/23.76% at60/90d. Main large-increase skill is+7.20/+0.87/+0.94%; OOD increase
forecasts mostly persist. R1 unchanged main MAE is37.266/1.178/1.493 and OOD
0/133.013/239.474. Thus gains do not satisfy all registered reliability targets.
R2 unchanged error is zero and changed forecasts equal persistence.

Main decrease support is now51/65/63 inR1 and sufficient inR2, rather than the old
empty30d group. Validation has36–47 large decreases from5+ families and adequate
unchanged/increase strata. However five OOD horizon/replication cells have fewer
than24 large increases (see decision.json). No labels were replaced or cases added;
those safety conclusions are exploratory. No claim of general large-decrease repair.

| Replication | Partition | Days | Direction macro-F1 | Multiclass Brier | Action F1 |
| --- | --- | --- | --- | --- | --- |
| R1 | ood | 30 | 0.540 | 0.690 | 0.000 |
| R1 | ood | 60 | 0.390 | 0.645 | 0.267 |
| R1 | ood | 90 | 0.416 | 0.656 | 0.263 |
| R1 | test | 30 | 0.724 | 0.409 | 0.224 |
| R1 | test | 60 | 0.533 | 0.505 | 0.231 |
| R1 | test | 90 | 0.553 | 0.502 | 0.231 |
| R2 | ood | 30 | 0.480 | 0.722 | 0.000 |
| R2 | ood | 60 | 0.490 | 0.722 | 0.000 |
| R2 | ood | 90 | 0.420 | 0.767 | 0.000 |
| R2 | test | 30 | 0.664 | 0.434 | 0.000 |
| R2 | test | 60 | 0.642 | 0.468 | 0.000 |
| R2 | test | 90 | 0.637 | 0.454 | 0.000 |


Direction scores are empirical frequencies; classification F1 is not forecasting
accuracy. Movement recall is low. R2 can have informative raw direction scores while
its validation-protected final action remains persistence. Full confusion/AUC/Brier
and action diagnostics are published; undefined precision stays null.

80% calibration-only residual intervals achieve79.43–81.77% main coverage across
replications. OOD coverage is71.53–83.33%, and hidden-future stress only41.67–62.5%.
Intervals therefore do not establish reliable shift coverage. No test-driven widening,
quantile repair or conformal guarantee. Width/score and local-distribution ablations
are in the uncertainty report and machine tables.

## Verification and scope

One bounded worker: wall143.511s; sampled RSS/HWM
302,977,024bytes (288.94MiB),
final kernel high-water302,759,936bytes.
CPU user/system143.155/
0.461s; two threads; exit0.
Original2GiB RSS/900s bounds held. Task storage cap128MiB was explicitly registered
for the larger population, not raised after execution. No retries, downloads,
installations, native pretrained calls or real-data use. RSS is sampled, not cgroup
enforcement; OOM counters unavailable. Socket denial is not a network namespace.

Independent audit verified34,272 forecasts and
7,884 arithmetic identities, complete matched
populations, timestamp/source/state seals, protected fallback and hidden-branch
prediction equality. Repeated predictions are exact. Runtime NumPy2.4.4 RECORD
hashes revalidated; this is local consistency, not publisher-signature proof.
The first audit invocation lacked package import path; module invocation corrected
that read-only tooling launch. The experiment was not rerun.

See examples/phase6_4/verification.json for exact regression commands/counts and
publication_manifest.json for safe artifacts. The63 new tests include56 model/
policy cases and7 independent-auditor cases. Prior tracked/untracked files, private
studies,56 research bundles/322 artifacts, database/checkpoints, six compilation
archives/claims and user caches passed preservation checks. No service/volume
operations occurred; live SonarQube volume bytes are not certified. All24 Phase C
permissions remain NOT_APPROVED. No old historical label cohort was reopened.

## Conclusion

The implementation defect is fixed in an isolated version. Familiar-family synthetic
forecasting gains are measurable in one replication, but do not recur as positive
skill in the second, and do not transfer reliably to unfamiliar mechanisms. The
requested consistent, reliable improvement is NOT achieved. Ordinary persistence
remains the defensible default. No claim is made about real technical-debt gains.
Further research should test mechanism-held-out validation, reversal/hazard controls
and legitimately origin-known change signals under a NEW registration; hidden
future events cannot be recovered by threshold tuning. No test-informed correction
or additional experiment is included in this phase.

Final regression verification: **1,721 tests passed in the working checkout and
1,659 in the publication checkout**, including63 new cases; zero failures/errors/
skips. Fourteen cases in each total are existing tiny tensor/fake-backend contracts,
not pretrained model construction/loading/inference. Preflight repetitions are not
counted as extra independent tests. Both read-only numerical auditors agree exactly.
