# Code reuse evidence for the forecasting MVP

Read-only source audit: 2026-10-13. No scripts, CLI commands, tests, scanners, builds, model loads or training were executed. Paths below are relative to `/home/hp/tst`. The existing audit and refinement architecture/roadmap/data digest were read as prior evidence; this note reconciles those documents against actual source. Counts in the previous data audit were not recalculated here.

## What exists and what must be new

The application checkout is `td_pipeline_module_level/td_pipeline`; it contains Python collection, Git features, module/file marts, and an additive `forecasting/` package. The actual entry points are `run_pipeline.py` and `forecasting/__main__.py`; there is no project-owned `run.py` or `git_history.py` in the inspected source inventory. The matching Git implementation is `forecasting/git.py`.

There is useful forecasting software, but no selected Hugging Face forecaster adapter, repository-level exact 30/60/90-day forecasting runner, or implemented application API/dashboard in this checkout. Frontend/API/server filename and dependency-manifest searches returned no project-owned app source. The earlier workspace audit also distinguishes HTML reports/architecture drawings from an application. Thus backend/dashboard work must be estimated as new, small implementation work, not an existing platform migration.

The latest standalone `techdebt360_v3_analyzer_domain_v152` is a domain-validation and scan-recovery research package, not another backend to deploy. Prefer direct, bounded reuse of its evidence policies when needed; do not make the entire 36-pair compiled/source admission study an MVP prerequisite.

## Critical semantic traps

1. `forecasting/schema.py:54` accepts only `exact90` and `approx91`, fixes history at 26 weeks, and defines a future-minus-current **module SQALE delta**. Existing `forecasting/__main__.py:50` exposes those two horizons only. It cannot accept 30/60-day or repository-level records without a new adapter/schema.
2. `build_project_dataset.py:19` uses `[1,2,4,12]` **week/row shifts**, after intersecting available week rows at line 35. Missing weeks can therefore change elapsed calendar time. Replace this target-building path for the new exact-calendar experiment. Old module/file targets in `config.py:57` are 3/4/12 weeks; 12 weeks is 84 days, not 90 days.
3. `compute_project_sonar_features.py:70` does implement a paginated native project-history API reader. Its `nearest_value` at line 98 chooses the absolute nearest scan timestamp, while lines 141–146 turn missing values into zero and sum SQALE, reliability and security remediation estimates. Retain only the API/pagination concept. Replace unrestricted nearest-date matching, missing-to-zero conversion and mixed burden target construction. Historical scan execution time does not prove the logical Git cutoff. Native repository SQALE needs an archived revision/analysis binding.
4. `sonar_evidence.py:169` exports file-component measures; lines 192–197 verify coverage of production Java source. Summing these files creates a **production-Java repository aggregate**, not necessarily the same whole-project target scope as imported V2 project SQALE or Sonar's native repository component. Distinguish target scope IDs and domains; never pool these as interchangeable ground truth.
5. `build_module_mart.py:28` documents SQALE as code-smell remediation estimates. Its broader `technical_debt_minutes` also adds bug/vulnerability effort at line 31. Neither quantity is observed developer repair labor. Use SQALE minutes alone as the initial forecasting target; retain other burdens as explicitly named auxiliary metrics.
6. `research/cmr90_v2_experiment/config/label_policy.yaml:6` defines corrective fix events in `(T0,T0+90 days]`. `src/build_event_evidence.py:256` defines a binary artifact label from those events. `src/build_origins.py:383` includes debt minutes as an origin feature. This is corrective-maintenance risk, not future SQALE stock, and its model results do not establish forecasting MAE/RMSE.
7. `V3_v0152_Repair/Live_Recovery_Availability.json:2` still records `NOT_RUN_MISSING_ORIGINAL_ENVIRONMENT`, zero real CE tasks queried at line 5 and unknown recovered real scans at line 6. It does not provide 72 verified historical observations. Source recovery machinery is reusable, but scientific data availability remains unresolved.

## Existing component decisions

All changes below are future implementation recommendations, not changes made during this audit. Reuse means reuse relevant verified logic, preserving old artifacts and schema semantics.

| Component and exact evidence | Decision | MVP boundary / required adjustment |
|---|---|---|
| `run_all_repos.py:111,127,235,386`; `repos.csv`; `run_pipeline.py:78` | Simplify | Reuse repository registry validation and owned clone paths; one operator, one repository task at a time. Freeze clone/ref before analysis; avoid running broad default collection as experiment setup. |
| `config.py:14,28,47,57` | Modify through a new context adapter | Keep secrets in environment/private files. Do not globally change legacy horizons or workspace settings. Explicit per-run context and target policy replace hidden current-working-directory assumptions for new work. |
| `forecasting/git.py:10,21,24,53,77`; `weekly_commits.py:57` | Reuse/modify | Immutable Git tree/blob reads, complete-history check, first-parent resolver and origin-ancestry activity. Add explicit frozen branch tip, historical availability assumptions and logical cutoff to provenance. Do not infer actual historical branch publication solely from commit date. |
| `contracts.py:13,27,38,48,57,88,93` | Reuse | Numeric missingness, no fabricated ratios, checksums, safe paths, unique keys/JSON, atomic publication. These are essential data integrity, not enterprise infrastructure. |
| `scan_snapshot.py:39,57,89,101`; `sonar_evidence.py:51,77,151,246` | Reuse/modify | Immutable snapshot materialization, pinned compiled/source mode, exact CE/analysis/revision, complete pagination, raw archive, final proof. Current scan acquisition remains serial, isolated and bounded. Add native project SQALE collection if choosing that scope. |
| `pull_metrics.py:3`; `pull_issues.py`; `pull_analysis_metadata.py`; `validate_snapshots.py:9` | Reuse | Retain collector metric normalization, issue pagination and evidence checks. Absence stays unknown. Legacy validation alone does not reconstruct archived missing history. |
| `scan_weekly_snapshots.py:13,28`; `weekly_update.py` | Simplify/defer automatic operation | Retain complete-export recovery before rescan, and identical-revision reuse with provenance. Reused states are grid support, not new independent analyses. Defer autonomous weekly scheduling. New historical acquisition may use a finite deduplicated manifest. |
| `compute_project_sonar_features.py:70,98,127`; `build_project_dataset.py:19,35,62` | Replace target/matching path | API pagination is reusable; new observation/target builders enforce exact cutoffs, complete revision/domain mapping, no nearest-future lookup, no row-shift calendar approximation and no missing-to-zero conversion. |
| `compute_project_git_features.py:62,99,127` | Reuse/modify | Trailing origin-only process features for CatBoost/LightGBM; future features disallowed. Match the selected repository origin and ancestry. Keep target-only forecasters separate from covariate variants. |
| `modules.py:93,116,172`; `build_module_mart.py:149,291,398,706`; `forecasting/identity.py:22,62` | Preserve/reuse selectively | Retain module grouping, causal identity, file aggregation and checksum concepts. Current/last-snapshot module evidence can support priorities. Module forecast science awaits compatible real history; do not force module lineage into repository-level imported data. |
| `build_td_mart.py:159,169,186`; `compute_label.py:42` | Preserve, replace new forecast labels | Keep legacy file-level evidence and prior results. Do not use its 3/4/12-week label scheme for exact 30/60/90. |
| `compute_lineage.py:88`; `compute_git_window_features.py:70,107`; `compute_ownership_entropy.py:45,88` | Reuse selectively | Useful causal source/process features. Repository MVP avoids expensive file lineage unless needed for present module views. |
| `compute_sonar_trend_features.py:53,88,114`; `compute_issue_persistence.py:39,54`; `compute_finding_lifecycle.py:48,61` | Preserve, optional reuse | Explicit observed histories and issue lifecycle descriptors only. Issue-key resets are not new debt. Optional current prioritization explanations; not a dependency for initial pretrained predictions. |
| `merge_measures_issues.py:66,94`; `merge_weekly_features.py:64`; `compute_features.py:73`; `add_weekly_commits_churn.py:54`; `pipeline_g3.py:202`; `pipeline_total_line.py:6` | Preserve/simplify | Reuse individual normalization/trailing-feature routines if needed; avoid executing the entire redundant file-feature chain for repository forecasting. |
| `clean_stale_weeks.py:24` | Defer | No deletion/cleanup as data repair. New runs use a fresh output namespace and explicit excluded-record manifest. |
| `forecasting/schema.py:54,80`; `forecasting/dataset.py:65,236,292` | Reuse concepts, new repository schema | Preserve old exact90/approx91 contracts unchanged. Reuse exact endpoint checks, censoring, analyzer compatibility and immutable checksummed generations. New schema handles repository target scope and all three horizons. |
| `forecasting/collector_bridge.py:43,121,138` | Reuse/modify | Isolated workspace ingestion of verified snapshots and explicit supplemental endpoints. Current endpoint acquisition is exact90-only (line 163); adding 30/60 needs its own new request contract, never silently relabel endpoints. |
| `forecasting/evaluation.py:88,142,180,216` | Reuse concepts, modify evaluator | Existing purged time/repository folds, MAE/RMSE, M0 zero-delta persistence and actual CatBoost M1/M2. Adapt new repository stock/delta outputs, exact horizons, matched common cohort, cluster reporting, latency and interval metrics. LightGBM and HF interfaces are new. |
| `forecasting/interfaces.py:12,100,128` | Reuse cohort validation only | Existing module sequences are 26-week masked tensors; cannot feed unchanged into a daily TTM branch. Preserve exact external-cohort identity and prohibition on probability summation. New target-only model arrays have explicit cadence/masks. |
| `forecasting/graphs.py:15`; `M3_M4_DESIGN.md`; GraphSAGE/TCN interfaces | Defer | Lexical import/co-change evidence can remain archived. Neural graph/temporal training is unnecessary for a pretrained repository forecasting MVP. |
| `requirements-forecast.txt`, `requirements-forecast-lock.txt`, `requirements-dev.txt`; `tests/test_forecasting.py`, `test_collection.py`, `test_missingness.py`, `test_contracts.py` | Reuse safeguards; new isolated model environments | Existing lock does not prove Chronos/TTM compatibility. Future tests retain old behavior and add precise new target/cohort/adaptor checks; no tests ran in this task. |
| Old package copies, ZIPs, synthetic workspaces, prior target-selection/NPF outputs | Preserve, defer active dependencies | Evidence and reproducibility only. Never count duplicate package copies or synthetic scans as new history. |

## CMR90 research reuse

| Source | Decision and evidence |
|---|---|
| `src/inspect_database.py:43,345`, `src/build_event_evidence.py:45` | Reuse read-only source connection, schema audit and source identity patterns. Do not run scripts that write legacy outputs. |
| `src/build_lineage.py:328`, `src/build_origins.py:66,175,288` | Reuse only Git/blob and linkage concepts if required. CMR artifact lineage and active-issue interval construction are not the new repository SQALE target builder. |
| `src/build_features.py:91,101,143` | Reuse trailing-window/process feature concepts, explicit source read-only access. New predictor allowlist excludes future corrective labels and future SQALE. |
| `src/build_splits.py:66`, `config/split_policy.yaml:4`, `src/leakage_checks.py:35` | Reuse purged chronological/held-repository checks and manifest ideas; new exact-horizon/cohort tests must replace dataset-specific CMR joins. |
| `src/train_baselines.py:53,64,75,143`, `src/evaluate.py:195,205` | Defer binary Logistic/RandomForest/XGBoost estimators and classification results. They answer observed corrective activity, not stock forecasts; existing report itself limits its claims. |
| `config/feature_registry.yaml`, `label_policy.yaml`, `repositories.yaml`, `experiment.yaml`; existing outputs/reports | Preserve repository metadata and audit trail as evidence; new scope and forecasting manifests must have different IDs/output roots. |

## V3 package decisions, without a second platform

| Named module(s) and evidence | Decision |
|---|---|
| `cli.py:16`; `manifest.py:17,67`; `gitmeta.py:27,50` | Reuse freeze/source scope concepts; **modify** the fixed-pair manifest for a bounded new acquisition only if necessary. Current branch resolution is not historical publication proof. |
| `preflight.py:11`; `domain.py:26`; `evidence_policy.py:11,57` | Reuse pinned server/runtime/rule/remediation semantics and genuine class checks. **Simplify** fixed reference assumptions: domain.py:42 hard-codes 571 rules and a frozen study reference; do not copy this as a universal domain definition. |
| `build.py:61,100,136`; `execute.py:78,102,208`; `sonar_api.py:9,16`; `sonar_parse.py:4,14` | Reuse isolated source materialization, build/scanner evidence directories and raw paginated exports for compiled current measurement or strictly bounded backfill. Build candidate code without privileged host mounts or scanner credentials. |
| `scan_recovery.py:207,233,336` | Reuse existing CE-task recovery **if original environment/evidence is obtained**. Zero currently queried tasks, unknown valid count; never schedule rescans merely to hide failed export recovery. |
| `admission.py:67`; `admission_merge.py:269,431`; `scan_only.py:76,228` | Defer the full compiled/source cohort admission/merge study. Minimal MVP validates one accepted current build and finite data acquisitions instead. |
| `analyze.py:19,277,687`; `gate.py:196,440`; `compare.py:19` | Preserve comparison/audit logic. Do not make compiled-versus-source equivalence research a mandatory forecasting MVP dependency; maintain separate imported/compiled/source domains. |
| `matching.py:30,64`; `npf.py:145,214` | Defer NPF/issue-introduction identity studies from core stock forecast MVP. Current evidence views may reuse normalization; no issue matching needed for imported repository SQALE forecasts. |
| `util.py:15,26,42`; `__init__.py` | Reuse compatible hash/serialization concepts; avoid duplicate platform utility modules. |

## Existing CLI contracts: source inspected, commands not executed

- `python run_pipeline.py START [--branch BRANCH] [--weeks N] [--level module|file|both] [--skip-scan]`, from `run_pipeline.py:78`. Default broad collection can submit scans; not an initial imported-data experiment command.
- `python run_all_repos.py REPOS_CSV [--holdout-repos IDS] [--skip-scan] [--level module|file|both] [--output-dir DIR]`, from `run_all_repos.py:386`. Clone/update and scan behavior must be authorized in implementation; not called here.
- `python -m forecasting build --workspace W --output D --horizon exact90|approx91`, `endpoint-plan --workspace W --output JSON`, and `evaluate --dataset D --output R --first-validation-cutoff UTC ...`, from `forecasting/__main__.py:44`. Module-only legacy contract; not the new repository experiment runner.
- `python -m forecasting.collector_bridge ...` is a lower-level endpoint/ingestion bridge; exact90 acquisition is a separate mutation, not inference.
- V3 `recover-scan-only --admission-workspace W --failed-scan-workspace F --recovery-workspace R --token-file PATH --sonar-url URL`, from `cli.py:23`, requires original operator context. Other V3 commands (`freeze-manifest`, `preflight`, `execute`, `smoke-execute`, `build-admission`, `merge-admission`, `scan-only`, `analyze`, `gate`) exist in source at `cli.py:16–25`; they are not prerequisites to obtaining initial V2 pretrained forecasts.

## Additive implementation module proposal

Parent architecture may finalize the package name; none of these files currently exists. Use one additive `forecasting_mvp/` package within the active checkout rather than rewriting legacy `forecasting/` artifacts:

- `contracts.py`, `observations.py`, `v2_import.py`, `targets.py`, `splits.py`: new repository observation, exact-calendar target and leakage-free cohort contracts.
- `adapters/base.py`, `adapters/chronos.py`, `adapters/ttm.py`, `adapters/baselines.py`: uniform target-only forecast output, runtime identity, failure and common-cohort handling.
- `evaluate.py`, `cli.py`, `__main__.py`: first real ground-truth predictions, metrics, manifests and errors before any UI.
- `current_analysis.py`, `detection.py`, `prioritization.py`: thin collector adapter, gated GraphCodeBERT Java annotations, deterministic evidence ordering. Classifier probabilities remain separate from SQALE minutes and never manufacture historical labels.
- `api.py`, `templates/dashboard.html`, `static/dashboard.js`: small local application after metric artifacts exist; do not create a separate frontend build pipeline unless required.
- `tests/test_targets.py`, `test_v2_import.py`, `test_splits.py`, `test_model_contracts.py`, `test_evaluation.py`, `test_api.py`: future tests of meaningful failure/identity/target behavior, plus regression tests for old supported paths.

New input/output namespaces and versioned IDs are required. No change to old data files, scanner configuration, production code or existing research outputs was made while preparing this digest.
