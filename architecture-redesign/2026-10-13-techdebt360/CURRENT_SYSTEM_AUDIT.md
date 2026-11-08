# TechDebt360 current-system audit

Date: 2026-10-13. Method: read-only source inspection, retained report inspection, CSV/JSON recounts, SQLite connections using `mode=ro`, Git metadata, and XLSX XML extraction. No tests, models, scanners, servers, builds or training were run. Existing validation results below are retained evidence, not results reproduced during this audit.

## What the actual project is

`/home/hp/tst` is a research workspace containing successive packages and experiments; it is not a Git application root. The active Git checkout is [td_pipeline](/home/hp/tst/td_pipeline_module_level/td_pipeline/README.md). Its latest recorded commit is `2e7999e`, dated 2026-10-10, following baseline `cf726ca`; no remote was listed. The additive forecasting package is untracked and README/.gitignore already have local modifications. Preserve that work. The latest separate analyzer-domain package is [v0.15.2](/home/hp/tst/techdebt360_v3_analyzer_domain_v152/README.md), a recovery handoff rather than a deployed platform. Versions v1–v151, extracted operator workspaces, repair trees and ZIPs are historical evidence or duplicates, not independent applications or datasets.

The workspace supplies meaningful Python collection, lineage, dataset and evaluation code. No TechDebt360 backend service, production database migrations, authentication implementation or frontend application was evidenced in the project-owned source inventory. Maven/Gradle projects inside `workspace/repos`, `admission_raw` and research mirrors are analyzed subjects. HTML architecture diagrams are planning artifacts. `Java_Backend_Roadmap.xlsx` is a personal learning roadmap; it does not establish an implemented Spring backend.

## Implementation assessment and reuse decisions

| Component | Observed implementation and limits | Decision |
|---|---|---|
| Git/source inventory | `modules.py:54`, `forecasting/git.py`; immutable-tree reads, source scopes and trailing activity | **Reuse**, add explicit branch-observation/availability time and separate snapshot clocks |
| Legacy file pipeline | `build_td_mart.py`, Git-window scripts, issue persistence and legacy labels | **Modify** through an adapter; retain evidence/missingness rules; keep legacy 3/4/12-week targets separate |
| Module mart | `build_module_mart.py`, `modules.py`; build/package strategy frozen from first observation | **Reuse** mapping concepts; do not interpret lexical package boundaries as validated architecture |
| Historical module identity | `forecasting/identity.py:62`; births, conservative membership matching, ambiguity/deletion events | **Reuse** causal identity; censor ambiguous splits/merges; preserve origin-membership target semantics |
| Sonar collector | `sonar_evidence.py:51,77,151`; complete pagination, exact CE task, current analysis revision, profile checks, source coverage, final completion proof | **Reuse** verification and raw archive; modify workspace-global configuration and locking for per-job isolation |
| Scan orchestration | `scan_snapshot.py`, weekly/all-repo runners, V3 compiled/source execution | **Modify** one runtime adapter; compiled Java is primary candidate; source-only is a separate domain |
| V3 recovery | `scan_recovery.py:207,336`; binds original source/build/invocation to existing CE tasks and isolated export | **Reuse** mechanism after real operator recovery gate; do not copy v0.15.2 as a second general pipeline |
| Finding identity | `matching.py`, NPF identity review pack; independent match policy and ambiguity strata | **Reuse/modify** with human adjudication; issue-key resets must never become new-debt labels |
| Forecast dataset | `forecasting/schema.py:54`, `dataset.py:65,236`; explicit exact90/approx91, 26-week masked tensors, checksummed publication | **Reuse** contracts conditionally; zero verified real module datasets currently discovered |
| Tabular predictors | `forecasting/evaluation.py:180`; real CatBoost classes and constant fallback, purged folds | **Retain for research**; software execution on synthetic data does not establish predictive value |
| Graph extraction | `forecasting/graphs.py:15`; imports/build literals, co-change, contributor overlap, SCC and PageRank | **Retain as optional evidence**; compiler-resolved dependencies, reflection and full Gradle semantics are missing |
| GraphSAGE/TCN | `M3_M4_DESIGN.md`, `interfaces.py`; input boundaries and design exist | **Defer** neural fitting and integration; no evidence justifies the complexity |
| Target-selection experiment | raw Sonar snapshots, same-data mart, baseline predictions and metrics | **Preserve** as prior experimental evidence; repair horizon naming and report staleness/inconsistencies |
| CMR-90 experiment | read-only source DB path, 5-repository history/mart, linked corrective-event labels, baseline results | **Preserve** as a maintenance-risk comparator; human validation absent; do not relabel as technical debt |
| Pretrained model integration | No selected HF inference adapter, frozen revisions, calibration or measured runtime evidenced | **Design new** minimal adapters; start with Qwen assistance and optional retrieval, gate classifiers |
| Prioritization and remediation | Existing plans describe them; no complete tested patch verification service evidenced | **Design new** transparent rankings and isolated before/after verification |
| Backend/dashboard | Architecture reports/HTML exist; application implementation not evidenced | **Design new** small API and dashboard over existing Python capabilities |
| Duplicate versions/repair tests | Numerous package copies and synthetic workspaces | **Remove from active build scope**, preserve all originals as provenance; no deletion during this task |

## Scan reliability: the decisive boundary

The local collector correctly distinguishes process exit, CE status, analysis revision, exports and complete source coverage. It checks the latest project analysis both before and after export. This is valuable because current issue/component endpoints must not be assumed to return a chosen historical analysis. Export immediately or isolate analyses; archive immutable raw responses. [SonarSource's transfer notes](https://github.com/SonarSource/sonar-migration-tool/blob/main/docs/TRANSFER.md) explicitly describe the limitation of reconstructing historical issue inventories; [history management](https://docs.sonarsource.com/sonarqube-server/project-administration/managing-project-history) documents retention behavior.

The v0.15.1 failure read `work/.scannerwork/report-task.txt`, whereas operator logs reportedly placed it under `/tmp/.scannerwork`. v0.15.2 binds a dedicated evidence directory and provides recovery without rescanning. The source and retained diagnosis support the failure mechanism. The operator report of 72 CE IDs is **not independently verified here**. [Live_Recovery_Availability.json](/home/hp/tst/V3_v0152_Repair/Live_Recovery_Availability.json) records zero real CE tasks queried and an unavailable original environment. Therefore:

- 72 scheduled scans or CE IDs do not establish 72 valid observations.
- Zero recorded successful exports does not establish zero successful server analyses.
- Recovered valid analysis count is **unknown**, not zero.
- No real V3 scientific pass can be claimed from package tests.

Compiled classes are required by the supported Java analysis workflow, per [current Java documentation](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/languages/java). An empty-binaries workaround cannot be silently promoted to compiled ground truth. Freeze scope, JDK, binaries/libraries, analyzer, profile, rule parameters and remediation configuration; compare identical source populations.

## Existing datasets and prior experiments

1. **Kafka bundle:** 8 snapshot entries, 3,718 T0 measures, 3,752 endpoint measures and 3,736 label rows. Snapshot `analysis_date` entries all occur on 2026-09-06 during roughly two hours; these are execution times, not eight monthly observation dates. Commit ancestry and calendar cutoffs must be reconstructed before temporal use. Missing metric cells exist. It is not a certified longitudinal series.
2. **Target-selection corpus:** 180 source-only JSON snapshots, ten repositories, 18 monthly dates per repository (2023-01 through 2024-06); 15,981 retained file origins, 1,374 unique repository/file clusters, 120 repository-origin clusters. The mart now has 510 NPF positives. Its stale profile JSON still says 738. The final NPF report explains the Joda repair; consumers must bind metrics to exact dataset hashes rather than combine these versions.
3. **Public V2 source DB:** `/home/hp/TECH_DEBT/td_V2.db` actually exists. Read-only counts: 31 projects; 67,550 analysis records; 66,711 project-level measure rows; 1,024,614 issue rows. Independent read-only review also confirmed all 66,711 nonblank analysis records join Git revisions and 66,685 measure rows contain profile metadata. Analysis dates match author and committer days in those joins; this does not establish exact UTC endpoints or stable measurement settings. It offers substantial repository-level research potential, but does not directly provide file/module measure rows.
4. **CMR mart:** actual read-only table count is 110,977 origins; five repositories, 1,509 distinct repository/artifact clusters, 639 repository-origin timestamps, 461 primary positive rows, and 288 known-open future-work exclusions in the retained summary. Event validation is still pending; every row having a numerical debt feature does not make it a verified forecasting endpoint.
5. **Netty XLSX sample:** one date in its filename, 138 package metric rows, 1,133 package dependency rows, no listed parse-error rows. Metrics include external/JDK packages and test/example references. No embedded Sonar debt history or exact future labels were established. Useful schema evidence, not a longitudinal module benchmark.

The [Milestone 1 report](/home/hp/tst/td_pipeline_module_level/td_pipeline/MILESTONE1_REPORT.md) records 166 passing tests with synthetic data and no real scanner/training run. The read-only discovery found no `module_generation.json` or `complete_week_01.json` outside excluded vendor/test/runtime trees. Real-module history length, module count, graph validity and usable horizon labels are **not established**.

Retained continuous metrics show persistence MAE 3.0952 for the old **density** target; the best reported cross-repository learned density model MAE is 6.7500. These are not raw-minute results. CMR process-only Logistic mean held-repository AP is 0.04457, versus 0.03634 for process+TD, with negative mean incremental AP. Such evidence favors simple baselines and restrained claims; it cannot prove that every future forecaster or remediation model will fail.

## Gaps that change the redesign

Scientific gaps: exact endpoint semantics, analyzer-domain equivalence, dual-human finding identity, independent repository tests, calibrated probabilities, pretrained detector task validity and verified remediation outcomes. Operational gaps: original V3 recovery environment, runtime model adapters, per-job isolated configuration, an application persistence/auth boundary, and reproducible end-to-end integration. Hardware capacity and graduation deadline were not supplied; resource and schedule estimates are assumptions, not host measurements.

Recommended preservation order: collector evidence contracts → causal Git/lineage → missingness and checksummed dataset publication → grouped evaluation → optional lexical graphs. Freeze historical scientific artifacts read-only. Consolidate active adapters later; this redesign changes no source files or old protocols.

All local conclusions trace to the named files or read-only recounts; see [local digest](digests/local-audit.md) and [source preservation inventory](imports/LOCAL_SOURCE_HASHES.md). Public model/dataset facts are sourced separately in the research documents.
