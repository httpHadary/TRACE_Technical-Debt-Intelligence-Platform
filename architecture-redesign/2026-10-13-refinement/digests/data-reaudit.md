# Data re-audit for exact 30/60/90-day forecasting

Audit date: 2026-10-13. Fresh reads of source files, retained CSV/JSON and SQLite opened with `file:/home/hp/TECH_DEBT/td_V2.db?mode=ro`. Public primary resources retrieved this date. Old design documents supplied locations only; counts below were independently recomputed. No source/config/database changes, installs, builds, tests, inference, training, Sonar scans, label generation or access to sealed NPF outcome artifacts occurred. This digest is the only written artifact.

## Decision supported by present data

Forecasting is a substantive research option at repository, module and file levels; existing evidence does not yet support reliable exact 30/60/90-day production accuracy. The strongest immediate exact-cutoff reconstruction lead is the local V2 repository-level history. The monthly source-only collection supports file-level proxy exploration, with substantial persistence and only ten independent repositories. Module-level collection code exists, but this workspace does not demonstrate a real cohort admitted through its proof contract. These are feasibility judgments, not model results.

Do not claim that exact-date observation pairs enumerate or bound the eligible cohort. An exact cutoff labels **the branch state as of that cutoff**, which may legitimately reuse an earlier measured revision. Conversely, a measurement on a matching date can be invalid if it is not the selected reachable branch state or belongs to a different analyzer domain.

## Independently recounted local populations

| Source and unit | Fresh result | What it supports / limits |
|---|---:|---|
| [Raw snapshots](/home/hp/tst/research/td_target_selection/raw) | 180 snapshots; 10 repositories × 18 month-end dates, Jan 2023–Jun 2024; 23,981 file observations; 144 distinct repository/revision states | Snapshot/revision audit input; repeated revision scans are not independent history |
| Raw analyzer metadata | All 180: Sonar `26.8.0.126808`, domain `source-only-empty-binaries-sensitivity`, pinned scanner image digest | One declared sensitivity domain, not compiled Java evidence or frozen rule-hash proof |
| [Same_Data_Target_Mart.csv](/home/hp/tst/research/td_target_selection/outputs/Same_Data_Target_Mart.csv) | 15,981 rows; 1,374 repository/file clusters; 120 repository/origin clusters | Retained file proxy cohort; no new labels were made |
| Mart endpoint elapsed dates | 90d: 1,361; 91d: 5,371; 92d: 9,249 | Existing “90” population mixes horizons; 90d rows are date-level candidate pairs, not a certified exact-time cohort |
| Mart stock dynamics | 15,425 unchanged raw-minute pairs (96.52%); 8,470 zero origin stocks (53.00%) | Strong persistence baseline required; do not let zero stock dominate error summaries |
| [V2 database](/home/hp/TECH_DEBT/td_V2.db): `SONAR_ANALYSIS` | 67,550 rows; 31 projects; 839 blank analysis keys; no blank revisions | Blank-key rows excluded from measured join audit |
| V2 `SONAR_MEASURES` | 66,711 rows; 31 projects; no missing `SQALE_INDEX`; 31 explicit zeros | Project-level static-analysis remediation proxy, not realized labor |
| V2 `GIT_COMMITS` | 153,994 unique project/revision records in audited mapping; all main-branch flag `True`; parent field present | Historical commit reconstruction lead; branch availability/reachability still requires graph validation |
| Module collection proofs | 0 `complete_*.json` found outside test/runtime/vendor/cache/design exclusions | No real admitted module cohort demonstrated by this bounded inventory |
| [V3 availability](/home/hp/tst/V3_v0152_Repair/Live_Recovery_Availability.json:2) | Missing original environment; zero real CE tasks queried; recovered scans unknown; scientific gate not evaluated | Existing repaired code/synthetic validation cannot be counted as live real data |

The source checkout remains [td_pipeline](/home/hp/tst/td_pipeline_module_level/td_pipeline), HEAD `2e7999e`, dated 2026-10-10. It has existing README/.gitignore modifications and untracked forecasting files. No changes were made to this checkout.

### V2 joins, time and measurement-domain audit

Every one of the 66,711 nonblank-key analyses joins **uniquely** on `(PROJECT_ID, REVISION)` to `GIT_COMMITS` and on `(PROJECT_ID, ANALYSIS_KEY)` to `SONAR_MEASURES`; no duplicated measure keys were found. All joined Git records have `IN_MAIN_BRANCH=True`.

Fresh exact-second comparison corrects the weaker previous day-only statement: for **all 66,711 joined rows**, `SONAR_ANALYSIS.DATE` equals both `AUTHOR_DATE` and `COMMITTER_DATE` to the second after parsing; both Git timestamp offsets are `+00:00`, and timezone fields are zero. No seconds or timezone mismatch was observed. Analysis `DATE` is nevertheless a naive string without an explicit offset. Its equality to historical Git time is evidence of imported/reassigned historical timing, **not proof of actual analyzer execution time or historical branch availability**. Repository min/max dates are 2000-10-10–2018-10-15; this is historical data, not contemporary repository state.

Coverage is incomplete: 87,283 of 153,994 retained main-flag commits lack a nonblank-key measurement. Even restricting each project to its first/last measured timestamp leaves **19,954 unmeasured of 86,665 commits**. Therefore choosing the last *measured* revision before a cutoff is not equivalent to choosing the actual branch state; intervening unmeasured commits can invalidate that shortcut. Missing revisions must be resolved or the pair marked unavailable.

`QUALITY_PROFILES` is absent/blank on 26 rows. There are 14 distinct non-null serialized values; ordering analyses by project/time yields 79 contiguous serialized-profile segments across 31 projects, with 48 transitions. These are **metadata/language-set segments**, not proven changes to Java rules: parsed Java profile key `java-sonar-way-04122` and `rulesUpdatedAt=2017-03-16T16:05:56+0000` occur unchanged on 66,683 rows. Seven language/profile tuples were observed and all nonblank strings parsed after the dataset's semicolon-to-comma normalization. Full active-rule hashes, scanner/plugin versions and compiled/source-only mode are not supplied by these three tables, so profile-key equality alone does not certify immutable analyzer semantics.

Feature missingness is modest but real: `NCLOC` 26 nulls, `COGNITIVE_COMPLEXITY` 28, `COVERAGE` 34. Reliability/security remediation fields have zero nulls; these remain separate target channels rather than automatically being added to SQALE debt. Distinct measured-day gaps across project histories have median 2 days, 90th percentile 16 days, and maximum 1,651 days. Commit cadence is irregular; no fixed observation-step horizon is interchangeable with calendar days.

### Candidate pair counts and the correct eligibility contract

| Horizon | Raw exact-date repository pairs / same-path intersections | V2 distinct-day pairs | V2 exact-second measured timestamp pairs |
|---|---:|---:|---:|
| 30 days | 60 / 7,972 | 5,840 | 0 |
| 60 days | 20 / 2,719 | 5,356 | 2 |
| 90 days | 10 / 1,361 | 5,513 | 3 |
| 91 days (comparison only) | 50 / 6,651 | 5,694 | 1 |

All counts are observation-calendar diagnostics, **not training-label counts and neither upper nor lower bounds on the final eligible as-of cohort**. Raw same-path intersections additionally omit additions/deletions/renames, and provide no origin-defined complete repository aggregation.

For an origin `t0` and `h ∈ {30,60,90}`, declare UTC cutoffs (or explicitly choose a local calendar convention), the historical branch identity, and a deterministic reachable-state policy. At `t0+h`, select the last reachable branch state available at/before that cutoff; validate parent/branch history and timestamp semantics instead of globally sorting arbitrary commit timestamps. Reuse a retained measurement when its **revision and immutable domain** match that state and its inventory/target coverage is complete. The same revision may validly label several cutoffs, including an unchanged branch. If the selected state has no matching trusted measurement, mark missing or plan a scan of that revision. Never carry an older measured stock across a changed branch merely because the latest commit is unmeasured. Future branch head knowledge and post-origin feature events cannot enter predictors.

File and module targets also require origin-defined membership/lineage and explicit deletion, move, copy and new-file handling; zero means observed zero, not absent measurement. Repository SQALE measurements cannot establish module or file totals without complete attributable component evidence. The [collector proof publication](/home/hp/tst/td_pipeline_module_level/td_pipeline/sonar_evidence.py:192) checks complete source coverage, records metadata/artifact hashes, and writes the final `complete_{label}.json` marker at [line 218](/home/hp/tst/td_pipeline_module_level/td_pipeline/sonar_evidence.py:218). This contract is available code, not a newly executed audit of historical raw scans.

### Kafka retained bundle

The [bundle](/home/hp/tst/data/drive-download-20260909T114653Z-1-001) has 8 snapshot rows (`m6`…`m1`, `t0`, `t90`), 3,718 origin feature/measure rows, 3,752 endpoint measure rows and 3,736 label rows. All analysis timestamps are execution-time observations on **2026-09-06**, with `t0=18:10:16Z` and `t90=18:46:06Z`; those are **35m50s apart**, not 90 days. Commit hashes distinguish revisions, but historical commit cutoffs are absent from the supplied snapshot CSV. The bundle is one repository paired case, not eight independent forecast trajectories. No raw-minute endpoint target column is present in the measure CSV; issues would need an audited aggregation. Origin cognitive complexity is blank on 1,604/3,718 rows and duplicated-lines density on 3,344/3,718; origin debt minutes have zero blanks. Do not impute these missing metrics to zero.

## Three requested public resources, freshly accessed

| Resource | Exact access / provenance / license | Calendar and target implications |
|---|---|---|
| [Technical Debt Dataset](https://github.com/clowee/The-Technical-Debt-Dataset) | Public README and [release API](https://api.github.com/repos/clowee/The-Technical-Debt-Dataset/releases) accessible; 2.0.1 dated 2021-11-04, `td_V2.db` 1,542,533,120 bytes, matching local size; CC BY-NC-SA 4.0. README distinguishes v2: 31 projects, master only; warns v1 has Sonar timeline problems | Commit measurements, no ready exact-30/60/90 mart. Strongest local reconstruction input; independent branch/provenance/completeness audit required |
| [MaramAllah/NPFDataSet](https://huggingface.co/datasets/MaramAllah/NPFDataSet) | Browser-page retrieval failed in web tool; public [API](https://huggingface.co/api/datasets/MaramAllah/NPFDataSet), [raw card](https://huggingface.co/datasets/MaramAllah/NPFDataSet/raw/main/README.md), [tree](https://huggingface.co/api/datasets/MaramAllah/NPFDataSet/tree/main) and HTTP 206 bounded CSV read succeeded. Public, ungated; uploaded/modified 2026-09-15; CSV 332,837,236 bytes; license `unknown`; custom pipeline claim, no linked reproducible pipeline/paper | Six repositories claimed; 60 weekly scans from 2015-01-01. `TD_3w=21d`, `TD_1m=28d`, `TD_3m=91d`, sum of active bug/vulnerability/smell effort. Not exact 30/60/90. First bounded row is source-only modern Sonar 26.8, historical `t0` with `+10:00`, ineligible and unknown 3m target. Whole usable cohort/provenance unverified |
| [Forecaster toolbox](https://github.com/XAI-toolkit/forecaster-toolbox) | Public SDK4ED backend source, MIT code license, bundled example data. [Model source](https://github.com/XAI-toolkit/forecaster-toolbox/blob/master/model_training.py) freshly retrieved; no installation/execution | Uses target `.shift(-intermediate_horizon)` and version counters; observation-step rather than guaranteed day horizon. `TimeSeriesSplit` in inspected source lacks explicit horizon purge. Useful baseline code lead, not an independent exact-cutoff ground-truth corpus |

These resources must not be summed into one independent sample count: repeated revisions, files in one repository, bundled examples, reused upstream data and alternative target constructions all share dependence. NPF's claimed chronological partitions are documentation, not validated leakage safeguards. Its six-repository/full-coverage/usable-target counts and reuse rights remain unresolved; the first-row sample cannot resolve them.

## Effective independence and acquisition cost

Report each horizon separately with repositories, origin cutoffs, distinct selected revisions, domain segments, usable lineage clusters and available non-overlapping label windows. Raw rows greatly overstate sample independence: the monthly source-only set has ten repositories, 144 distinct states and 120 retained repo/origins; V2 has 31 historical Apache projects sharing ecosystem/analyzer conventions. Splits must hold out repositories and time, purge every label window intersecting an evaluation boundary, and group related clones/lineages. Missingness and unchanged-stock prevalence must be reported per repository/horizon; no claim about confidence intervals or learned superiority follows from the counts alone.

Planning cost formula: let `D` be distinct required `(repository, branch-state revision, analyzer-domain)` states across history and all 30/60/90 cutoffs, and `V` the subset with trusted reusable measurements. New jobs `J=|D \ V|`; shared revisions/cutoffs are scanned once per domain. Expected compute-hours `≈ J × mean job minutes × (1+retry overhead) / 60`; add checkout/build/dependency repair, CE/export validation, storage, licensing and human provenance/lineage labor separately. Cost in currency is compute-hours × chosen infrastructure hourly price plus engineer-hours × chosen labor rate. None of these future rates/job times are measured here.

Illustration only: six repositories × 60 weekly origins × up to four distinct states (origin plus three cutoffs) gives **at most 1,440 nominal state slots** before history windows, reuse/deduplication and failures. With all 1,440 requiring scans, assumed 10–60 min/job implies 240–1,440 compute-hours before retries/engineering. This is not a prediction; calendar fixed-state design can be far cheaper than daily scanning. The retained raw source-only scanner elapsed values sum to 4,367.59 seconds for 180 jobs (median 18.12s, range 12.36–189.09s), but exclude compiled build/domain repair and do not forecast current production cost. A pilot timing manifest would be required before committing a budget.

No numerical forecasting direction should be rejected solely because only ten raw exact-date 90d repository pairs were counted. Equally, no serious accuracy claim should precede the horizon/domain/branch-state eligibility audit and a clean persistence comparison. This planning audit establishes usable inputs and unresolved conditions; it creates no new scientific outcomes.
