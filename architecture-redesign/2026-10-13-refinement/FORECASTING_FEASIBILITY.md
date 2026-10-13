# Forecasting feasibility: 30, 60 and 90 days

Date: 2026-10-13. **Conclusion: repository-level forecasting on existing V2 histories is a serious, promising research candidate. Reliable 30/60/90-day production forecasts have not been established. Module-level readiness is unsupported in the current workspace; file-level evidence is limited and imperfect.** This is a data-readiness finding, not evidence that pretrained forecasters fail. Experiment A must precede a forecasting pivot or a production forecast claim.

Evidence classes: **VERIFIED ARTIFACT** means a fresh read-only count or inspected public contract; **PRIOR VERIFIED INVENTORY** means an earlier direct count retained in the session, not recounted during this refinement; **RETAINED RESULT** means an earlier saved experiment, not a run reproduced now; **PROPOSED** means a future experiment or design; **ASSUMPTION** is explicitly conditional. No labels, datasets, model results or scans were newly constructed. Detailed fresh evidence is in the [data re-audit](digests/data-reaudit.md).

## Fresh quantitative evidence

| Population | Evidence findings | Consequence |
|---|---|---|
| V2 repository history | Fresh recount: 31 projects; 67,550 analysis records; 66,711 uniquely joined project measures; 839 blank analysis keys; no missing `SQALE_INDEX`. Prior verified inventory: 1,024,614 issue rows, not recounted during this refinement | Strong imported numerical starting point; measurement records are not independent repositories or calibrated ground truth |
| V2 Git coverage | 153,994 retained main-flag commits; 87,283 unmeasured overall; 19,954 unmeasured of 86,665 commits within project measured spans | Latest measured commit is not necessarily the actual branch state; endpoints need source-state validation |
| V2 clocks | All 66,711 joined analysis dates match author and committer timestamps to the second; Git offsets and timezone fields are zero; analysis `DATE` lacks an explicit offset | Stronger timestamp consistency than the earlier day-only audit; historical execution and branch availability cannot be inferred |
| V2 profiles and metrics | 26 missing profiles; 79 serialized metadata segments and 48 transitions; Java profile tuple constant on 66,683 rows; `NCLOC`: 26 nulls; cognitive complexity: 28; coverage: 34 | Serialized changes are not proven Java rule changes; profile ID does not replace full analyzer, rule and remediation metadata |
| Local source-only history | 180 monthly exports; 10 repositories × 18 dates, January 2023–June 2024; 144 distinct repository/revision states; 23,981 raw file observations | Real retained sensitivity exports with substantial dependence and repeated states; compiled-domain equivalence is unproven |
| Retained file mart | 15,981 rows; 1,374 file clusters; 120 repo-origin clusters; 1,361/5,371/9,249 rows at 90/91/92 days; 96.52% unchanged raw-minute pairs | Mixed-horizon proxy cohort; strong persistence control required; row counts do not establish independent backtests |
| Own module collector | No real `complete_*.json` cohort found outside excluded test, runtime, vendor, cache and design areas | Module counts, history and usable future labels are not established; source code supports collection, but does not demonstrate real accuracy |
| V3 recovery | Original operator environment still missing; 0 real CE tasks queried; recovered count unknown | The previously reported 72 submissions cannot be counted as valid observations; recovery may save work if original evidence and server become available |
| Kafka download | 8 manifest entries; one paired repository case; T0/T90 analysis times 35 minutes 50 seconds apart on 2026-09-06; historical cutoff metadata missing | Execution times cannot be used as historical horizons; commit, cutoff and effort aggregation need an audit |

V2 measured-day gaps are irregular: median 2 days, 90th percentile 16 days, maximum 1,651 days across project histories. Coverage, actual target variation, domain consistency and missing selected revisions matter more than the roughly 67,000-row headline. The 31 Apache projects also share ecosystem conventions; they are not a random sample of 31 independent software domains.

## Exact endpoints: correction to the earlier interpretation

An exact 90-day target is the **measured repository state as of T0 + 90 × 24 hours**, under a registered UTC cutoff convention. It does not require a commit or scan at that exact second. A local calendar convention, if preferred, must be registered separately. Select the branch state at the cutoff using ancestry and as-of availability. If its exact revision and domain were measured with complete target coverage, reuse that observation; if no code changed, reusing the same measured state is legitimate. If an unmeasured commit changed the branch, an older measured state is not a valid substitute.

Therefore the following are only calendar diagnostics, **neither upper nor lower bounds on usable as-of labels**:

| Horizon | Local raw exact-date repo pairs | V2 distinct-day pairs | V2 exact-second timestamp pairs |
|---:|---:|---:|---:|
| 30 days | 60 | 5,840 | 0 |
| 60 days | 20 | 5,356 | 2 |
| 90 days | 10 | 5,513 | 3 |
| 91 days, comparison only | 50 | 5,694 | 1 |

The retained mart's 1,361 exact-date file rows do not prove that all possible exact 90-day forecasts have only ten usable origins. They describe ten observed repository/date pairs in the retained monthly mart. The proposed as-of eligibility audit must consider measured selected source states; no such new label construction was run during this design task.

### Admission by granularity and horizon

| Granularity/data | 30 days | 60 days | 90 days | Current decision |
|---|---|---|---|---|
| V2 repository | Promising pending state, domain and grid audit | Promising pending the same audit and separated evaluation blocks | Promising pending the same audit, sufficient context and precision | Admit to Experiment A preparation; product capability remains unvalidated |
| Own repository scans | Recovery and coverage unknown | Recovery and coverage unknown | Three V3 slots cannot establish long histories | Recover or pilot before a numerical study |
| Own module | No admitted real history | No admitted real history | No admitted real history | Collect a trusted cohort; do not invent module totals from V2 aggregates |
| Local file sensitivity corpus | Candidate endpoint states exist | Limited cohort and cadence | Prior labels mix 90/91/92 days and show strong persistence | Secondary sensitivity study with explicit scope and domain, plus repeated-file clustering |
| Public NPF mart | Existing target is 28 days, not 30 | No verified 60-day target | Existing target is 91 days, not 90 | Research quarantine until license and provenance are resolved; do not relabel targets |

“Promising” assesses available inputs, not measured forecast accuracy. A horizon can pass for selected repositories while failing for others.

## Three requested public resources

- [Technical Debt Dataset V2](https://github.com/clowee/The-Technical-Debt-Dataset): public SQLite release 2.0.1, 31 master-branch histories, CC BY-NC-SA 4.0. The V1 timeline warning does not establish the same defect in V2. The local schema supports repository measures, Git revision links and issue lifecycle records; it has no direct module measure table. Preserve imported-domain limitations and licensing terms.
- [NPFDataSet](https://huggingface.co/datasets/MaramAllah/NPFDataSet): public CSV, card and API; license unknown; six repositories and 60 weekly scans claimed. Targets are 21/28/91 days and sum active bug, vulnerability and code-smell effort. Modern source-only scans are retrospectively associated with older commits. Full usable counts, lineage, provenance and reuse rights remain unverified. Resolve the license before reuse; missing terms do not demonstrate scientific failure.
- [SDK4ED forecaster toolbox](https://github.com/XAI-toolkit/forecaster-toolbox): MIT code, bundled example data and historical forecasting methods. Its source constructs targets by shifting observations; inspected temporal splitting lacks an explicit horizon purge. Reuse methodological ideas after an audit; do not count toolbox examples as an independent real-label population.

The previously inspected [Zenodo forecasting series](https://zenodo.org/records/4534110) remains a useful weekly or irregular external replication lead under its original license and separate domain. The weekly series can support 13-week/91-day comparisons; the irregular series require their own elapsed-time audit. Neither silently certifies 90 days. Separate data and checkpoint licenses; a repository code license does not automatically license every fine-tuned weight or embedded dataset.

## Historical integrity and lineage gate

Proof for an own observation requires an immutable revision, tree and source scope; intended cutoff; actual execution and export time; CE task, analysis, project and revision binding; complete pagination and coverage; domain and settings hashes; and checksummed raw manifests. A successful CE task alone does not prove measurements were collected. Recovery without submitting a new scan must bind the original task and its exports before any new scan request.

Imported V2 domains must retain known source, version and quality metadata, with missing settings explicitly marked. Do not fabricate compiled mode, exact plugin versions or rule hashes. Profile stability provides evidence, not complete equivalence. Evaluate imported segments and sensitivity policies separately; restrict conclusions to them. Retrospective default-branch reconstruction lacks actual historical observation logs and must state its ancestral branch and availability assumptions rather than claim online deployment conditions.

Module and file identities are causal and policy-versioned. Renames and moves need evidence; ambiguous splits, merges and deleted populations are censored or separately defined. Current module code reports stock delta with membership decomposition; targets for fixed origin members require a distinct adapter. No missing endpoint becomes zero, and no future lineage information enters features. New findings present at the endpoint and findings introduced at any time are different targets.

## Actual observation spacing and TTM eligibility

Use a registered regular grid only when the actual selected branch states have compatible measured values. Valid reuse of the same unchanged state is distinct from forward-filling across unmeasured changes and from padding. Report observed, reused and missing points, plus distinct revisions. Models consume grid steps; the remediation-minute target unit does not define the time interval.

- Daily grid: 30/60/90 native steps map exactly to the requested durations under the UTC convention. Missing inputs use documented masks or a separately evaluated past-only treatment; missing endpoint labels remain missing.
- Weekly grid: 13 steps equal 91 days, a separate comparison. Neither 3 weeks nor 4 weeks equals a calendar 30-day target.
- Irregular observations: name the next-k-state task separately and report its elapsed-time distribution; it cannot appear as a calendar forecast.

Fresh R3 branch inspection overturns a family-wide 512-point requirement. Branch-specific candidates:

| TTM R3 task | Context and native output | Planned use |
|---|---|---|
| Weekly 91 days | 52 → 16 | Crop the first 13 forecast steps; requires a valid 52-step context grid and measured endpoint state |
| Daily 30 days | 90 → 30 | Exact 30-step output with a valid 90-point input grid |
| Daily 60 days | 180 → 60 | Exact 60-step output with a valid 180-point input grid |
| Daily 90 days | 512 → 96 | First 90 steps; shortest inspected branch supporting native output ≥ 90 |

Cropping a valid native horizon is not recursive extension or label interpolation. Padding does not create measured history. A short weekly branch opens a real study option for longer weekly series; it does not establish adequate origins or splits in the claimed 60-week NPF corpus when 52 past points and 13 future steps are needed. Use the exact branch SHA and decomposed prediction class; the loader's default frequency and revision inference can select a different contract. See the [model strategy](PRETRAINED_MODEL_STRATEGY.md).

## Serious benchmark and fallback plan

Experiment A first compares persistence or zero-delta, training mean, bounded trend, Ridge, CatBoost and LightGBM on identical targets and cohorts. Then test Chronos-small and eligible TTM branches, plus full Chronos and TimesFM 2.5 if the preregistered resource budget fits. Keep target-only and covariate or fine-tuned variants separate. No future Git activity is a known-future covariate. Transfer learning is a later training-only variant if enough independent series and a zero-shot baseline justify it; it cannot replace absent future labels.

Use rolling origins and untouched repository tests; purge label windows crossing splits; group repeated revisions and lineages; report independent repository/time blocks as well as rows. Metrics are macro and per-repository MAE/RMSE, baseline skill where denominators are valid, changing and constant subsets, quantile pinball loss, and native 80% interval coverage and width. A 90% interval requires separate validation-only calibration. Proposed product gate: ≥ 10% macro MAE improvement over the strongest simple baseline, a paired clustered confidence interval above zero, benefit in ≥ 70% of eligible repositories, and adequate coverage, calibration and runtime. This is a project preference, not a universal law or a claim that the existing study has sufficient power.

If foundation models lose but a conventional model wins, use that predictor and report the pretrained negative result. If data supports only short horizons, publish 30 days separately and retain 60/90 days as unsupported. If exact-calendar data is insufficient, pilot acquisition before pivoting. If forecasting remains unsupported or inconclusive after that gate, Experiment B can lead the thesis; pretrained detection, context retrieval and verified repair remain central. A positive repair result is not assumed.

## Acquisition before abandonment

1. Audit the already-local V2 database and small public assets: lowest new collection cost.
2. Recover originally submitted V3 tasks in the actual operator environment; do not count them until exports pass proof.
3. Plan exact selected revisions for history and 30/60/90-day cutoffs; deduplicate by repository, revision and domain. Count missing measurements before committing build or scan work.
4. Later, pilot six representative repositories at three historical states each; measure compiled build, scan, CE/export, validity and failures. Expand only on recorded throughput, licensing and precision supported by independent samples.

Cost formula: let trusted reusable states be a subset of the distinct required repository/revision/domain states. Then `new_jobs = distinct_required_states − trusted_reusable_states`, and machine-hours = `new_jobs × mean_job_minutes × (1 + retry_fraction) / 60`, with engineering, review and storage costs accounted for separately. At an assumed 5–20 minutes per job, 18 jobs require 1.5–6 sequential hours before retries and setup; 360 new states require 30–120 hours. These are scenarios, not measured current runtimes. Exact-cutoff state scans can be cheaper than daily rescanning. A retrospective collection creates new measurements under a current domain, not proof those measurements were available historically.

Freeze a later bounded effort budget and stop if compatible-state coverage, clock and domain integrity, or uncertainty precision cannot support the declared study. The final primary thesis is chosen after the paired experiments; current architecture preference cannot substitute for them.
