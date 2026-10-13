# Reproducible real-forecast experiment

Date: 2026-10-13. **Protocol only; no measured forecast results exist from this task.** The first experiment compares Chronos-2 Small with persistence on audited historical validation outcomes. The final experiment adds compact controls and admitted TTM variants, freezes choices, then opens untouched tests. No remediation experiment is required for this forecasting-first MVP.

## Study registration

Future study root: `/home/hp/tst/research/forecasting_mvp/studies/study-001/`. Code root: `/home/hp/tst/td_pipeline_module_level/td_pipeline/forecasting_mvp/`. **Both are proposed new implementation locations.** The source-backed existing CLI is `python3 -m forecasting`, supporting module exact90/approx91 only; the commands below are new parser contracts to implement, not working commands today. Do not run them during this planning task.

Before predictions, register `study.json`: source DB/release/hash/license; repository IDs/mainline tip/source policy; imported domain metadata and unknowns; target scope/unit/exact 30/60/90 durations; grid/context/missingness; calendar/repository splits; model/code/checkpoint/environment revisions; fixed preprocessing/features; clipping policy; search budgets; seeds; inference resource caps; metrics/coverage/denominators; useful-effect threshold; cluster uncertainty and stopping rules. Copy frozen configuration to every result manifest; changes create a new study ID and do not reopen a test for retuning.

Use the fixed protocol in [forecasting plan](MVP_FORECASTING_PLAN.md). Audit the complete 90-day core context first. If its data-only G2 gate fails, freeze the specified limited-data fallback before model outcomes. Target-only Chronos, explicit native TTM branches, UTC first-parent states, native project SQALE, metadata-selected pilot, purged chronological/repository tests and exact observed future endpoints remain binding. Runtime/eligibility checks may legitimately block execution.

## Future steps and command contracts

All paths shown below are examples of the exact proposed namespace, with new outputs required. Commands run from the code's parent directory. A supplied `--config` is the registered `study.json`; wrappers may not take arbitrary shell strings or SQL statements. Each command checks completed input manifests and rehashes sources. Test commands do not imply tests were run now.

### Step 1 — Audit source and permissions (M0/M1)

```bash
python3 -m forecasting_mvp audit-v2 \
  --db /home/hp/TECH_DEBT/td_V2.db \
  --config /home/hp/tst/research/forecasting_mvp/studies/study-001/study.json \
  --out /home/hp/tst/research/forecasting_mvp/studies/study-001/audit
```

Expected output: schema/counts/unique joins, dates/parents/tips, missing measured states, profile segments, source hashes, license status and repository selection. DB connection is read-only. No model imports or scans. Spot-check 12 raw states/endpoints and retain evidence references. Reject corrupt/ambiguous scored records. Dataset “verified” means audited linkage/integrity, not undocumented analyzer facts becoming verified.

### Step 2 — Build past grids, labels and splits (M1)

```bash
python3 -m forecasting_mvp build-dataset \
  --audit /home/hp/tst/research/forecasting_mvp/studies/study-001/audit \
  --config /home/hp/tst/research/forecasting_mvp/studies/study-001/study.json \
  --out /home/hp/tst/research/forecasting_mvp/studies/study-001/dataset

python3 -m forecasting_mvp split \
  --dataset /home/hp/tst/research/forecasting_mvp/studies/study-001/dataset \
  --config /home/hp/tst/research/forecasting_mvp/studies/study-001/study.json \
  --out /home/hp/tst/research/forecasting_mvp/studies/study-001/splits
```

Expected artifacts: separate `past_grid.csv`, `features.csv`, `labels.csv`, exact target contracts, eligibility audit and frozen phase IDs/boundaries. Test unchanged-state reuse, selected unmeasured changes, missing ancestry, cutoff seconds, 90 versus 91, source-end censorship, missing/zero distinction and all future feature timestamps. Label folder is excluded from runner request manifests and feature matrices. Duplicate revision cutoffs stay identified; report counts instead of calling them independent samples.

Choose `primary_track` using data audit only, before any model outcomes: `core90` when it admits six eligible projects, two untouched repository tests and nonempty purged phases. Otherwise preregister `masked90` with at least 80% known values on the same 90-point daily grid, a known origin stock and exact observed endpoints. Historical gaps stay missing; neither origin nor future labels are imputed. Freeze the threshold, repository selection, splits, feature/mask policy and primary-track ID before predictions. If the masked cohort also fails the data gate, stop or execute the bounded acquisition ladder; do not change thresholds after seeing forecast errors. Record strict/masked coverage and limited-data claims separately.

### Step 3 — Contract smoke test, then validation predictions (M2)

Load only Chronos-small's pinned checkpoint in the isolated recorded environment. Feed one real validation origin on the 90-point daily target-only grid, complete for `core90` or using registered missing-value masks for `masked90`; no label/status/path columns or future covariates. Known origin and exact future scoring endpoints are required in either track. Request 90 steps, verify q50 point and native deciles/endpoint times, then the pilot. Runner owns and logs peak memory, wall time, runtime locks and failures. Smoke timeout 15 minutes; pilot cap 8 machine-hours; no expensive budget escalation.

```bash
python3 -m forecasting_mvp predict \
  --dataset /home/hp/tst/research/forecasting_mvp/studies/study-001/dataset \
  --splits /home/hp/tst/research/forecasting_mvp/studies/study-001/splits \
  --model chronos-small --phase validation --track core90 \
  --out /home/hp/tst/research/forecasting_mvp/studies/study-001/chronos-validation

python3 -m forecasting_mvp predict \
  --dataset /home/hp/tst/research/forecasting_mvp/studies/study-001/dataset \
  --splits /home/hp/tst/research/forecasting_mvp/studies/study-001/splits \
  --model persistence --phase validation --track core90 \
  --out /home/hp/tst/research/forecasting_mvp/studies/study-001/persistence-validation
```

`--model` is a fixed enum, never arbitrary code; `--phase` is validation/test, `--track` core90/ttm30/ttm60/ttm90/masked90 with preregistered admissibility. The command examples show the strict case. When the data audit freezes `primary_track=masked90`, replace `--track core90` with `--track masked90` in every primary predict/fit command, use distinct track-labeled output folders and require the recorded track to match input manifests. This substitution is predetermined by data, not validation MAE. Persistence repeats the observed origin value; it does not read actuals. Every attempted forecast ID emits SUCCESS or a typed failure. Saving synthetic forecasts is permissible only in software tests under separate `SOFTWARE_VALIDATION_ONLY` fixtures, never under a real study result.

### Step 4 — Join actual future measurements and report first errors (M2)

```bash
python3 -m forecasting_mvp evaluate \
  --dataset /home/hp/tst/research/forecasting_mvp/studies/study-001/dataset \
  --splits /home/hp/tst/research/forecasting_mvp/studies/study-001/splits \
  --predictions /home/hp/tst/research/forecasting_mvp/studies/study-001/chronos-validation \
  --predictions /home/hp/tst/research/forecasting_mvp/studies/study-001/persistence-validation \
  --phase validation \
  --out /home/hp/tst/research/forecasting_mvp/studies/study-001/validation-comparison
```

The evaluator alone opens actual endpoint labels; join by exact forecast/target IDs, not nearest date or file row order. Outputs include per-prediction error/measurement IDs, MAE/RMSE per repository/horizon, pooled/macro values, skill, actual data coverage, model failure coverage, changing/constant subsets, decile pinball and 80% interval coverage/width. Undefined metrics remain null with a reason. Record raw and clipped predictions. Plot actual historical state values only where observed, without interpolating ground truth. This is the first substantive real-result milestone.

### Step 5 — Fit compact debt-specific controls and optional TTM (M3)

Implement the following proposed parser contract. Fitting reads registered training features and training-label views only, stores model and transform artifacts plus train-ID hashes, and cannot open validation/test labels. The foreground orchestrator materializes a past-only request bundle before launching an isolated prediction runner; the runner receives that bundle rather than an unrestricted dataset directory. `predict` for a fitted control requires `--fit NEWDIR`; otherwise it rejects the request. Freeze the small search grids from the forecasting plan; at most 3 Ridge and 2 CatBoost settings per horizon, seed 42, no test tuning. Trend has no trained search.

```bash
python3 -m forecasting_mvp fit \
  --dataset /home/hp/tst/research/forecasting_mvp/studies/study-001/dataset \
  --splits /home/hp/tst/research/forecasting_mvp/studies/study-001/splits \
  --model catboost --track core90 \
  --out /home/hp/tst/research/forecasting_mvp/studies/study-001/catboost-fit

python3 -m forecasting_mvp predict \
  --dataset /home/hp/tst/research/forecasting_mvp/studies/study-001/dataset \
  --splits /home/hp/tst/research/forecasting_mvp/studies/study-001/splits \
  --fit /home/hp/tst/research/forecasting_mvp/studies/study-001/catboost-fit \
  --model catboost --phase validation --track core90 \
  --out /home/hp/tst/research/forecasting_mvp/studies/study-001/catboost-validation
```

The same fixed command contract admits `ridge` and optional `lightgbm`, with distinct output folders. The fit command executes only the preregistered training settings; validation evaluation selects their candidate IDs. For a masked primary track, supervised features preserve past missingness and include the registered coverage/mask summaries; any fitted imputation/scaling uses training only. No supervised preprocessing reconstructs future actuals. TTM uses `predict --model ttm --track ttm30|ttm60|ttm90` with a branch already recorded in the study, never a free-form checkpoint override.

TTM 30 first: 90 complete daily past points and a measured 30-day endpoint. TTM 60/90 run only when 180/512 daily context and matched test cohorts exist; no padding. Direct immutable decomposed-class loader, one channel, exact native axes and mean-slot/decile semantics are load-test requirements. Generate matched Chronos/controls on precisely those IDs/contexts. Saving “TTM not admitted” with a reason is a legitimate comparator status, not an invented prediction. LightGBM optional within 4 engineering-hours. TTM remains complete-context only even when `masked90` is primary; its comparison rows cannot be pooled with masked primary results.

Select a validation champion separately within each horizon/track: lowest macro MAE on the full assigned cohort under the registered persistence-on-failure policy, with raw-model failure metrics reported separately and acceptable measured runtime; ties within 1% choose persistence, then Ridge, CatBoost, Chronos-small, TTM, LightGBM in that fixed order. This favors operational simplicity without claiming all ties equivalent. Report raw-model failure metrics and the explicitly defined persistence-on-failure variant separately. The champion on the data-audit-frozen `primary_track` (`core90` or `masked90`) supplies the default research replay for each admitted horizon. Complete-context TTM-track champions remain separately labeled comparators; do not select a global winner by comparing MAE from different tracks/cohorts. Retain one primary-track default per horizon, not every benchmark model. This registry does not authorize forecasts for an unsupported current domain or complete-history claims for masked data. Freeze the decision/model registry and any statistical claims before test labels open.

### Step 6 — Untouched final comparisons (M3)

Run the same predict/evaluate parser with `--phase test`, new result folders and frozen configs. Separate familiar-repository chronological tests from untouched-repository tests; neither is used to retune. A new tuned study needs new held-out evidence. Save every test model's predictions **before** endpoint join. Compare paired all-success IDs and full-assigned failure-fallback outcomes, denominators and coverage. No current Sonar repository performance extrapolation is authorized by V2 results.

Report macro MAE as primary; macro RMSE, absolute/minute and relative baseline improvement, native interval quality and resources as secondary. Use 2,000 paired repository-bootstrap replications (seed 42), disclose overlap/clusters and exploratory small-count bounds. No formal power is asserted. The proposed 10% MAE gain is meaningful only with positive held-out paired evidence, adequate precision/coverage and cost; poor/imprecise results are honestly negative/inconclusive. No dashboard phase can turn a failing model into a validated predictor.

### Step 7 — Current evidence and read-only platform (M4–M6)

These are proposed foreground parser contracts to implement after the forecasting-result gate. The registered local repository path/ref, allowed build/scanner invocation, Sonar URL and secret-file/environment references come from a new `current-config.json`; no command accepts arbitrary shell text. This configuration is an operator input, not an instruction to execute source files discovered in a repository.

| Future command | Required arguments | Output and completion condition |
|---|---|---|
| `register` | `--config CURRENT_CONFIG --out NEW_REGISTRY` | Frozen local repository/ref/tip/source inventory; missing or ambiguous identity fails. |
| `collect-current` | `--registry NEW_REGISTRY --config CURRENT_CONFIG --out NEW_CURRENT` | Serial restricted build/scanner/export adapter; COMPLETE only after exact revision/CE/analysis, native project stock and complete issue evidence. Missing existing evidence may require one explicitly controlled new scan; no browser trigger. |
| `annotate` | `--current NEW_CURRENT --config CURRENT_CONFIG --out NEW_ANNOTATIONS` | Gated Java function extraction/classifier annotations; blocked permission/loadability/overlength reasons are records, not fabricated scores. |
| `prioritize` | `--current NEW_CURRENT --out NEW_PRIORITIES` | Registered maintainability severity/minutes/ID ordering and separate incomplete queue; no forecast/classifier score mixing. |
| `assemble` | `--study STUDY_DIR --current NEW_CURRENT --annotations NEW_ANNOTATIONS --priorities NEW_PRIORITIES --out NEW_BUNDLE` | Validated presentation bundle with explicit imported/current domains, selected model registry, exact constituent manifest hashes and study limitations. A blocked annotation manifest is permitted and displayed. |
| `serve` | `--bundles BUNDLE_ROOT --host 127.0.0.1 --port 8000` | GET-only local FastAPI/static application; `--host` accepts only `127.0.0.1`; no scan, fit or predict from the API. |

All input directories must have compatible completed manifests; each mutating CLI stage refuses an existing output directory. `assemble` references immutable source/result bundles without silently reassigning their IDs. API startup verifies the registry and constituent hashes. M6 logs the actual commands and restores one bounded real-origin result from the frozen manifests; it does not begin another tuned experiment.

## Required result tables — schemas only

These define output **columns**, not fabricated result rows. Values remain unavailable until execution.

| Table | Columns |
|---|---|
| Data feasibility | source/domain/horizon/context, eligible repositories/origins, distinct revisions, non-overlapping blocks, missing endpoint/context counts, profile/branch exclusions |
| Point forecast | split/track/horizon/model, attempted/success/paired N, macro MAE, macro RMSE, pooled MAE/RMSE, persistence MAE, absolute skill, relative skill, changed-subset MAE |
| Uncertainty | model/track/horizon, native quantiles/point kind, pinball, 80% coverage/width/interval score, crossing count, cluster CI and precision warning |
| Operational | checkpoint/runtime/hardware, peak memory, wall time, model failures, fallback coverage, input/source/prediction hashes |
| Error analysis | repo/origin/horizon, actual revision/analysis, point/actual/error, repeated-state fraction, changing/constant stock, known scope/domain limitations |

## GraphCodeBERT demonstration side study

After forecasting results, M4 integrates the exact licensed classifier when feasible. Twenty Java functions across two repos suffice for contract/coordinate/display smoke checks; this is **not** a defensible F1 benchmark. Four independent labels DESIGN/IMPLEMENTATION/DEFECT/TEST and exact author normalization are recorded; all zero is not clean probability. Any later effectiveness claim requires an independently annotated multi-repository study with clean/OOD/rare type controls and a separate budget. Neither score nor threshold becomes predicted minutes.

## Stopping and scientific outcomes

`BLOCKED_LICENSE`, `BLOCKED_DATA`, `NOT_ADMITTED_CONTEXT`, `LOAD_FAILED`, `INSUFFICIENT_TEST_BLOCKS`, `NO_PRETRAINED_GAIN`, `GAIN_EXPLORATORY` and `GAIN_SUPPORTED` are different conclusions. Stop at registered resource/acquisition budgets. A useful persistence or CatBoost default with a documented pretrained comparison can complete the platform/research core; no pretrained forecasts means the AI forecast feature remains blocked. A missing 90-day cohort means 90-day capability remains incomplete. Maintain a journal of exact future commands, exit codes, durations and artifact hashes.

No implementations, weight downloads, scanner runs, training or expensive experiments were performed to produce this protocol. After this planning handoff, wait for explicit authorization before M0.
