# TechDebt360 MVP — Phase 3 Baseline Forecasting

Date: 2026-10-14. Working project: `/home/hp/tst/td_pipeline_module_level/td_pipeline`.

**Implementation and real baseline replay: PASS. Phase 4 readiness: PARTIAL.**
Persistence was selected using validation alone at all three horizons and has the
lowest overall test repository-macro MAE among these baselines. Rolling mean has
slightly better held-out RMSE but worse MAE; linear trend has worse overall MAE.
This is a baseline result, not evidence about unrun pretrained models.

## Implemented scope and files

- `forecasting_mvp/baselines.py`: persistence, past rolling mean and anchored daily
  OLS trend. The predictor accepts only the Phase 2.1 admitted immutable request.
- `forecasting_mvp/baseline_run.py`: verified inputs, request planning from past
  features, registration, generation, seals, validation-only selection, final
  evaluation, deterministic outputs and input/code-change guards.
- `forecasting_mvp/baseline_evaluation.py`: paired macro/pooled MAE and RMSE,
  per-repository/subset metrics, repository bootstrap, diversity counts and plot.
- `tests/test_forecasting_mvp_phase3.py`: ten checks, including parameterized exact
  horizons, analytical errors, pairing, bootstrap, leakage, seals and full replay.
- Updated CLI, package description, root/package README, `.gitignore`,
  `GITHUB_SYNC.md`; new report and small attributed results in `examples/phase3/`.

Existing code and unrelated working changes were preserved. No SonarQube scan,
package/model/data download, pretrained inference, CatBoost run, dashboard or
Phase 4 feature was performed.

## Frozen study and leakage prevention

Reused unchanged:

- Phase 1: `research/forecasting_mvp/phase1/2026-10-14/run-002`.
- Phase 2: `research/forecasting_mvp/phase2/2026-10-14/run-003`.
- Phase 2.1: `research/forecasting_mvp/phase2_1/2026-10-14/run-003`.

Paths are under `/home/hp/tst/`. The original database source SHA-256 remains
`8eb329e5e5690b884b98df824c4b94fc7582c5d610fa3bd12784b1e417b2684e`.
Input manifest hashes, all frozen Phase 2 hashes, split ID, code hashes, Python /
NumPy / Matplotlib versions and policies are recorded in `study.json` **before
prediction generation**. Database values are not accessed by the predictor.
Phase 1 contributes only historical measurement ID/timestamp metadata.

The data-only primary track is still `core90`: complete 90-day daily past contexts.
All assigned train/validation/temporal-test/held-test IDs are retained. Masked and
TTM-context tracks remain untouched and were not pooled or selected using errors.
No train/global scaling, interpolation, unknown-state carry or fabricated labels.
Exact endpoints remain origin + 30/60/90 calendar days, never 91 weekly days.

Prediction routing uses past feature IDs plus frozen assignments; the combined
forecast dataset is **not parsed for predictions**. Each forecast passes through
`admit_prediction_input` with its externally bound origin and only referenced
past measurement timestamps. `baseline_predict` gets one immutable request and
reads its past-values/timestamps/horizon payload, with no files, labels or stores.
The orchestration can route by split; the prediction function receives no split
labels, actuals, endpoint measurement identities or future covariates.

Execution order, recorded and tested:

1. Freeze `study.json` and the entire candidate grid.
2. Generate **64,746 candidate rows**, six candidates on **10,791 forecast IDs**,
   including every frozen active test ID. Save and hash all candidates before
   opening any numeric labels.
3. Read only the 2,205 allowed validation labels and choose each model's window.
   The CSV reader scans routing IDs; unallowed actuals are not converted, retained
   or exposed. Tests reject test/training labels in the selector.
4. Freeze selected parameters/champions, select already sealed candidate rows,
   save **32,373 selected predictions**, and seal prediction/parameter hashes.
5. Verify the seal, then open the full allowed evaluation label view and score.
6. Recheck seals, code and every input manifest/artifact hash before publication.

No test-informed tuning occurred. Stored labels had been audited in earlier
phases, but no Phase 3 numerical test outcome was used for parameter choice.
Hashing input label bytes for integrity is distinct from loading their values.
The boundary is a data contract, not an OS sandbox. It is regression-tested for
future/target access and file-free prediction; no claim of hostile-code isolation.

## Registered baseline definitions and selection

Persistence predicts the observed current SQALE stock at every exact horizon.
Rolling mean predicts the arithmetic mean of the last W daily observed stocks;
registered W candidates are **7, 30, 90**. Trend fits OLS slope on last W daily
stocks, then predicts **current stock + h × daily slope**; W is **30 or 90**.
Raw estimates are stored, and all scored stocks use `max(0, raw)` because debt
stock cannot be negative. Daily grids reuse verified measurements; no daily scan
independence is assumed. No seasonal naive was added because no period was
registered or supported by a prior seasonality audit.

The user-authorized bounded window search extends the earlier fixed 30-day trend
proposal. This grid was registered before any Phase 3 scoring. It is unchanged
in every replay; no grid/clip/tie policy changed after test results.

Each model/horizon chooses minimum validation repository-macro MAE, exact ties
favoring the shorter window. A validation champion within 1% of the best favors
persistence, then rolling mean, then trend. No supervised cross-repository model
was trained; OLS uses only the single request's historical window.

| Horizon | Mean window | Mean validation MAE | Trend window | Trend validation MAE | Persistence validation MAE | Champion |
|---:|---:|---:|---:|---:|---:|---|
| 30 | 7 | 56.17 | 90 | 87.02 | 53.65 | persistence |
| 60 | 7 | 94.17 | 90 | 167.51 | 93.21 | persistence |
| 90 | 7 | 132.37 | 90 | 243.35 | 131.87 | persistence |

## Actual numerical performance

All errors are in SonarQube **estimated maintainability remediation minutes**, not
actual developer repair effort. Primary MAE is the unweighted mean of per-repo
MAE. Macro RMSE is the mean of per-repo RMSE; pooled RMSE is separately reported
and can differ substantially. Improvement is `1 − model macro MAE / persistence
macro MAE`; negative means worse. Undefined zero-denominator skill remains null.

Each temporal-test horizon has 555 IDs across 15 repositories; each held-test
horizon has 222 across six. All three models score identical IDs with 100% coverage
and zero failures. Full CSV also includes train/validation and every repository.

| Test | Days | Model | Macro MAE | Macro RMSE | Pooled RMSE | MAE improvement |
|---|---:|---|---:|---:|---:|---:|
| test_temporal | 30 | persistence | 50.33 | 102.96 | 167.56 | +0.00% |
| test_temporal | 30 | rolling_mean | 52.42 | 104.42 | 170.01 | -4.16% |
| test_temporal | 30 | linear_trend | 82.53 | 116.04 | 189.33 | -63.99% |
| test_temporal | 60 | persistence | 98.71 | 152.07 | 242.04 | +0.00% |
| test_temporal | 60 | rolling_mean | 100.88 | 153.22 | 243.83 | -2.20% |
| test_temporal | 60 | linear_trend | 149.87 | 181.55 | 293.74 | -51.83% |
| test_temporal | 90 | persistence | 148.71 | 193.17 | 308.57 | +0.00% |
| test_temporal | 90 | rolling_mean | 150.83 | 194.67 | 310.60 | -1.43% |
| test_temporal | 90 | linear_trend | 189.17 | 223.50 | 353.67 | -27.21% |
| test_repository | 30 | persistence | 179.60 | 378.90 | 500.89 | +0.00% |
| test_repository | 30 | rolling_mean | 186.35 | 369.70 | 488.34 | -3.76% |
| test_repository | 30 | linear_trend | 280.62 | 432.97 | 558.72 | -56.25% |
| test_repository | 60 | persistence | 327.94 | 527.86 | 690.03 | +0.00% |
| test_repository | 60 | rolling_mean | 332.54 | 519.66 | 679.98 | -1.40% |
| test_repository | 60 | linear_trend | 520.10 | 698.40 | 884.81 | -58.60% |
| test_repository | 90 | persistence | 470.25 | 680.72 | 892.33 | +0.00% |
| test_repository | 90 | rolling_mean | 474.38 | 675.04 | 884.86 | -0.88% |
| test_repository | 90 | linear_trend | 775.96 | 981.01 | 1243.80 | -65.01% |

Point MAE gains over persistence are negative for both alternatives at every
reported test horizon. The mean's held-test macro RMSE is slightly lower at all
horizons, so the conclusion is specific to the registered primary MAE objective.
Absolute scales and cohort differences must not be interpreted as actual labor
or transferable accuracy for newly scanned repositories.

### Unchanged versus changing debt

Zero delta means equal measured debt, including changed revisions with equal
stock. It does not imply unchanged Git state. Subgroup macro averages weight
repositories with at least one example in that subgroup; empty per-repository
cells are emitted with N=0 and undefined errors, never invented zeros.

| Test | Days | Subset | IDs/model | Repositories | Persistence MAE | Mean MAE | Trend MAE |
|---|---:|---|---:|---:|---:|---:|---:|
| test_temporal | 30 | unchanged_debt | 410 | 15 | 0.00 | 4.17 | 58.59 |
| test_temporal | 30 | changing_debt | 145 | 10 | 188.78 | 191.51 | 207.61 |
| test_temporal | 60 | unchanged_debt | 330 | 14 | 0.00 | 6.84 | 107.02 |
| test_temporal | 60 | changing_debt | 225 | 11 | 219.13 | 221.68 | 249.96 |
| test_temporal | 90 | unchanged_debt | 287 | 14 | 0.00 | 5.15 | 182.98 |
| test_temporal | 90 | changing_debt | 268 | 11 | 261.42 | 264.25 | 280.83 |
| test_repository | 30 | unchanged_debt | 130 | 6 | 0.00 | 9.01 | 101.17 |
| test_repository | 30 | changing_debt | 92 | 5 | 587.64 | 580.15 | 601.43 |
| test_repository | 60 | unchanged_debt | 98 | 4 | 0.00 | 2.55 | 207.17 |
| test_repository | 60 | changing_debt | 124 | 6 | 600.41 | 599.38 | 691.48 |
| test_repository | 90 | unchanged_debt | 82 | 3 | 0.00 | 3.34 | 420.74 |
| test_repository | 90 | changing_debt | 140 | 6 | 717.06 | 717.76 | 885.90 |

Persistence is exact on zero-debt-change cases by definition. Those cases are
51.7% of the 90-day temporal test (287/555) and 36.9% of held test (82/222).
Consequently overall MAE is not sufficient evidence of success on changing debt.
The subgroup metrics are diagnostics from frozen tests, not tuning criteria.

## Cluster-aware uncertainty and context diversity

Use **2,000 paired repository-bootstrap replicates, seed 42**, sampling repositories
with replacement and weighting each repository equally. All weekly observations
inside a sampled repository stay together. Bounds are 2.5/97.5 percentile values
with linear quantile interpolation. Pairing uses the same repository resamples
for model and persistence. No IID row bootstrap or effective-independent-N claim.
These bounds describe uncertainty in observed error summaries; they are **not
future prediction intervals** and have not been calibrated for future debt.

Selected 90-day error and paired improvement bounds:

| Test | Model | MAE | 95% MAE bounds | MAE reduction vs persistence | 95% paired reduction bounds |
|---|---|---:|---|---:|---|
| test_temporal | persistence | 148.71 | [57.79, 262.02] | 0.00 | [0.00, 0.00] |
| test_temporal | rolling_mean | 150.83 | [58.39, 264.71] | -2.12 | [-4.26, -0.54] |
| test_temporal | linear_trend | 189.17 | [81.71, 334.80] | -40.46 | [-79.30, -9.79] |
| test_repository | persistence | 470.25 | [129.96, 829.36] | 0.00 | [0.00, 0.00] |
| test_repository | rolling_mean | 474.38 | [131.25, 838.42] | -4.13 | [-9.52, -0.26] |
| test_repository | linear_trend | 775.96 | [241.66, 1231.53] | -305.70 | [-608.98, 14.01] |

Six held clusters are below the registered eight-cluster caution threshold;
held-out intervals are explicitly exploratory. Fifteen temporal-test clusters
also yield conditional, availability-selected archive evidence, not a universal
population guarantee. Wide bounds and repeated states limit scientific strength.
Per-repository bounds are not generated from overlapping rows; one-repo intervals
remain undefined. Full CSV includes bounds for every aggregate phase/horizon/subset.

For the 90-day tests, 555 temporal rows have only **119 distinct origin scans**,
149 endpoint scans and median **3 scans/context** (range 1–22). The 222 held rows
have **73 origin scans**, 87 endpoint scans and median **8/context** (range 1–28).
Distinct context value sequences number 286 and 131. The original Phase 2.1
quality audit remains the source for repeated states, cross-split reuse and
window overlaps; it was not altered or converted into an independent sample count.

### Individual repository results (90 days)

All 30/60/90-day repository results and subgroup rows are in `baseline_metrics.csv`.
This table shows 90-day overall MAE and context coverage; names map to the original
source project IDs, not guessed URLs.

| Source project | Test | IDs/model | Persistence MAE | Mean MAE | Trend MAE | Distinct origin scans | Median scans/context |
|---|---|---:|---:|---:|---:|---:|---:|
| org.apache:beanutils | test_temporal | 37 | 21.19 | 21.19 | 21.19 | 4 | 2 |
| org.apache:codec | test_temporal | 37 | 375.86 | 376.00 | 319.15 | 6 | 3 |
| org.apache:commons-exec | test_temporal | 37 | 94.16 | 95.75 | 185.33 | 5 | 2 |
| org.apache:commons-io | test_temporal | 37 | 713.57 | 718.23 | 964.13 | 15 | 11 |
| org.apache:commons-jelly | test_temporal | 37 | 0.00 | 0.00 | 0.00 | 3 | 1 |
| org.apache:commons-jexl | test_temporal | 37 | 430.30 | 445.12 | 480.04 | 17 | 9 |
| org.apache:configuration | test_temporal | 37 | 150.86 | 154.96 | 192.38 | 15 | 8 |
| org.apache:daemon | test_temporal | 37 | 0.81 | 0.89 | 4.29 | 6 | 3 |
| org.apache:dbutils | test_temporal | 37 | 0.00 | 0.00 | 0.00 | 3 | 1 |
| org.apache:digester | test_temporal | 37 | 0.00 | 0.00 | 0.00 | 3 | 1 |
| org.apache:jxpath | test_temporal | 37 | 81.51 | 82.41 | 161.83 | 5 | 2 |
| org.apache:net | test_temporal | 37 | 90.16 | 89.38 | 168.65 | 11 | 5 |
| org.apache:ognl | test_temporal | 37 | 0.00 | 0.00 | 0.00 | 3 | 1 |
| org.apache:validator | test_temporal | 37 | 91.05 | 95.82 | 101.08 | 14 | 8 |
| org.apache:vfs | test_temporal | 37 | 181.14 | 182.68 | 239.43 | 9 | 6 |
| org.apache:bcel | test_repository | 37 | 669.38 | 668.25 | 1486.78 | 10 | 5 |
| org.apache:commons-cli | test_repository | 37 | 36.49 | 36.49 | 36.49 | 3 | 2 |
| org.apache:commons-fileupload | test_repository | 37 | 4.89 | 4.89 | 4.89 | 5 | 2 |
| org.apache:dbcp | test_repository | 37 | 332.70 | 337.64 | 630.74 | 11 | 9 |
| org.apache:httpclient | test_repository | 37 | 516.14 | 520.91 | 1362.28 | 21 | 16 |
| org.apache:httpcore | test_repository | 37 | 1261.92 | 1278.10 | 1134.56 | 23 | 17 |

## Artifacts, tests and reproduction

Final full local result:
`/home/hp/tst/research/forecasting_mvp/phase3/2026-10-14/run-002`.

- `baseline_predictions.csv`: all 32,373 selected real forecasts, raw/clipped stock,
  exact horizon/endpoint, original forecast ID, model, chosen window and provenance.
- `baseline_metrics.csv`: 1,485 paired phase/horizon/subset/repository/model rows,
  with MAE/RMSE, persistence skill, cluster bounds and context diversity.
- `baseline_comparison.png`: visually inspected MAE/RMSE panels for both test groups.
- `study.json`, `selected_parameters.json`, `prediction_seal.json`, `run_audit.json`,
  complete manifest, small 108-row prediction sample and sealed candidate folder.

The complete repeat in `run-003` produced **11 byte-identical files**, including
both prediction tables, parameters, metrics, plot, seals and manifests. The first
smoke `run-001` differs only in subsequently corrected package-description code
registration; it is not the final source snapshot. Frozen inputs were verified
before and after each replay; no dataset/split rebuild occurred.

**278 tests passed, 0 failed, 1 deselected** in the publication checkout. The
excluded legacy test trains CatBoost and remains unauthorized. Ten new Phase 3
checks cover analytical forecasts and clipping, exact horizons, file-free prediction,
paired macro/pooled metrics, zero-denominator/null cases, repository uncertainty,
validation-only selection, seal ordering/tampering, frozen IDs and reproducibility.
The same suite also passed in the original project: 278 passed, 1 deselected
in 30.18 seconds, preserving existing functionality.

Measured full repeat: **17.65 seconds wall time**, maximum RSS **263,416 KiB**
(about 257 MiB), no swaps, exit 0. This is a single CPU-host replay including
verification, generation, bootstrap and plotting, not a model-serving benchmark.
Existing Python 3.12.3 / NumPy 2.4.4 / Matplotlib 3.11.2 were reused; no packages
or requirement locks were changed.

From the working project, choose a **new** output directory:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp run-baselines \
  --bundle /home/hp/tst/research/forecasting_mvp/phase2/2026-10-14/run-003 \
  --history-bundle /home/hp/tst/research/forecasting_mvp/phase1/2026-10-14/run-002 \
  --hardening-bundle /home/hp/tst/research/forecasting_mvp/phase2_1/2026-10-14/run-003 \
  --out /home/hp/tst/research/forecasting_mvp/phase3/2026-10-14/new-run

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp verify-bundle \
  --bundle /home/hp/tst/research/forecasting_mvp/phase3/2026-10-14/new-run

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests \
  -k 'not test_actual_catboost_models_shared_folds_predictions_and_purging'
```

The CLI returns 0/PASS for successful baseline replay, 3 for invalid inputs,
missing/incompatible cohorts, changed artifacts/code or failed seals. Incomplete
outputs lack a COMPLETE final manifest and cannot be mistaken for a verified run.

GitHub receives source/tests/report and small results under `examples/phase3/`:
full metrics, plot, 108-row prediction sample, selection, study, seals, test XML,
resource log and hashes of full local outputs. **13 MB selected predictions and
25 MB candidate predictions remain local and ignored**, as do the large frozen
datasets and SQLite database. Published seal/hash receipts refer to those original
full files; samples are not substitute evaluation cohorts. The small-results
manifest checksums only published artifacts.

## Limitations and Phase 4 decision

**Phase 3 PASS; Phase 4 PARTIAL.** There is a reproducible measured baseline and
an untouched-in-selection fixed test cohort. There is no pretrained efficacy
result or deployment-ready forecast guarantee. Current baseline outcomes do not
justify prematurely discarding pretrained forecasting.

Remaining limits: imported branch-time availability approximation; incomplete
analyzer/rules/build histories; availability-selected, old Java project cohorts;
repeated scans/states and overlapping windows; only six held repositories; no
native predictive interval coverage. Sonar minutes are rule estimates, not repair
labor. These limitations persist even though software and data integrity pass.

A separately authorized Phase 4 should first admit the pinned pretrained runtime,
license and resource budget, retain these baseline results/IDs, and evaluate any
pretrained candidate without changing the test cohort or retuning these baselines.
No such work starts here. Normal descendant GitHub publication preserves remote
content, original local history and unrelated changes; remote SHA/files are verified
at completion.

**STOP after Phase 3 verification and GitHub publication.**
