# TechDebt360 MVP — Phase 4.2: Chronos Forecast Evaluation

Date: 2026-10-15. Working project: `/home/hp/tst/td_pipeline_module_level/td_pipeline`.

**Phase 4.2 PARTIAL.** Implementation, complete frozen-ID evaluation and reproducibility verification are complete. Native inference is partial: 12 of 1,512 validation/test contexts failed the unchanged strict quantile-path contract. Every one of the 4,536 registered endpoint IDs is represented; 4,500 are native predictions and 36 are explicitly marked persistence fallback points with no fabricated intervals. Chronos did not improve repository-macro MAE over persistence at any tested horizon. The validation-selected default remains persistence for all horizons. Native intervals are under-covered at longer horizons and collapse on constant histories. These findings are actual measurements, not proposed benchmarks or a reason to claim the entire pretrained forecasting family is ineffective.

## Scope and implementation

Only Phase 4.2 was implemented. No installation, model download, fine-tuning, dataset rebuilding, Granite, CatBoost, SonarQube scans or dashboard work occurred. Existing Phase 3 baseline predictions and metrics were reused unchanged. SonarQube `SQALE_INDEX` is estimated remediation stock in minutes, **not actual developer repair time**.

- New `forecasting_mvp/chronos_run.py`: immutable input admission, registered study, metadata-only request routing, bounded pilot/full workers, validation freeze, test sealing, paired evaluation, audit and small sample.
- New `forecasting_mvp/chronos_eval_worker.py`: offline label-free worker reusing the Phase 4.1 adapter and Phase 2.1 input boundary; exact horizon identities, status/error reporting, pilot repetition and explicit failure policy.
- New `forecasting_mvp/chronos_evaluation.py`: four-model paired comparison, validation-only selection, successful-native interval metrics, collapsed intervals, cluster bootstrap and comparison plot.
- `forecasting_mvp/baseline_evaluation.py`: optional keyword-only model list; default original three-model behavior preserved. All reused baseline metric fields were checked against the original values, without tolerance changes.
- `forecasting_mvp/cli.py`: additive `evaluate-chronos` command.
- New `tests/test_forecasting_mvp_phase4_2.py`: 13 software checks including negative leakage/identity tests, analytical metrics, fallback pairing, seal-before-label access, nondeterminism stop and full orchestration ordering.
- `.gitignore`: excludes full generated `chronos_predictions.csv`; root/package README and `GITHUB_SYNC.md` document Phase 4.2 scope.
- This report and `examples/phase4_2/`: numerical comparison tables, plot, 45-row deterministic sample, study/config/seals, resource/failure evidence, regression XML and reproducibility receipts. Weights, environments, full context datasets and full prediction exports remain local.

## Frozen data and experimental protocol

Primary track remains `core90`: 90 verified daily past states, one native 90-step path, endpoints at origin + **exactly 30, 60 or 90 days**. This is not 13 weeks/91 days. Original unchanged-state admission and unmeasured-revision exclusions were inherited; no debt interpolation, additional carry-forward, nearest-date labels or synthetic targets were introduced.

| Role | Repositories | Contexts | IDs per horizon | Native IDs per horizon | Fallback IDs per horizon |
| --- | --- | --- | --- | --- | --- |
| Validation | 15 | 735 | 735 | 729 | 6 |
| Temporal test | 15 | 555 | 555 | 551 | 4 |
| Held-out repository test | 6 | 222 | 222 | 220 | 2 |

The fixed 12-context pilot uses validation only: context-hash ordering within past-value constant/increasing/decreasing/other patterns, then deterministic hash fill. Eleven contexts produced identical repeated native paths; one failed quantile crossing. The complete validation cohort then predicted and sealed before validation numerical label parsing. No inference-parameter search occurred. A registered validation-only minimum repository-macro MAE policy, with a 1% preference for simpler models, selects the default. The unchanged Phase 3 rolling/trend windows were reused, not selected again on test data.

After `selection.json` was frozen, a fresh worker produced all temporal and held-out test rows together. Their prediction file and worker manifest were sealed, linked to the selection digest, and the two cohort ID digests were checked against Phase 3. **Only then** did the evaluator parse numerical test labels. Tests enforce this control-flow order and reject target/label fields at the worker interface. Bundle verification hashes label files as opaque bytes; it does not parse their numerical values. Workers receive only routed past-context bundles, past measurement references and identity metadata. This is a software isolation boundary, not an OS permission sandbox.

Earlier phases already reported baseline test outcomes; this is not a never-seen external holdout. This phase performed no test-informed configuration or selection and does not claim a fresh external test set. The exact repeat after evaluation verifies reproducibility without changing any decisions.

**Development corrections:** the first local attempt stopped at the pilot before any label parsing because an overly strict orchestration guard rejected an explicitly recoverable native-path failure. The guard was corrected to honor the registered persistence-failure policy; model parameters, adapter, pilot sample and cohorts stayed unchanged. Later regression inspection moved pilot repeat mismatch rejection outside recoverable inference handling, so nondeterministic valid repeats now stop the process. Real repeats were identical before and after this control-flow fix. Final source hashes and both final complete runs are recorded; no thresholds were chosen using test accuracy.

## Checkpoint and fixed inference

Reused `autogluon/chronos-2-small@ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a`, model-card Apache-2.0 license, previously admitted Phase 4.1 weights. Model safetensors SHA-256 `492290ae82bb89f9769e3479ce90b3179de1f33e600c34daa0352531538b23cd`, 111,749,048 bytes; config SHA-256 `f2780468adc8b16322aa0b6e28b26476c9401ecf64ab53292b6d2b0d3f423722`.

Python 3.12.3; Chronos 2.3.2; Torch 2.11.0+cpu; Transformers 4.57.6; NumPy 2.4.4; pandas 3.0.2. Existing isolated `.venv-chronos-cpu` and both existing CPU requirements files are unchanged. CPU float32/eval mode, batch 1, 2 intra-op threads/1 inter-op thread, seed 42, deterministic Torch algorithms, no cross-series learning. Context 90, output 90, native q10/q50/q90; q50 is the point. UTC-naive nanosecond conversion exists only at the model edge; returned endpoints are checked against exact UTC identities. Every quantile retains raw and max(0, value) debt-stock values. No post-hoc sorting, interval calibration, interval widening or residual-model tuning was applied.

A crossing at **any** native daily step rejects the whole path conservatively, even if its selected endpoints might be ordered. All 12 failed contexts reported `ValueError: Native quantile crossing; do not manufacture sorted quantiles`. The unchanged adapter did not emit invalid native intervals. The registered policy preserves each ID with a typed `PERSISTENCE_FALLBACK` point and null native interval; it never silently drops a failure or labels fallback output as a successful pretrained prediction.

## Actual point results

MAE/RMSE are in estimated debt minutes. Repository-macro MAE averages per-repository MAE; repository-macro RMSE averages per-repository RMSE. They are distinct from pooled metrics, which are also exported. Positive skill is better: `100 * (MAE_persistence - MAE_model) / MAE_persistence`. Full assigned-cohort Chronos rows below include explicitly labeled failure-policy points. Failure-free paired metrics are reported separately.

| Role | Days | Persistence MAE | Rolling mean MAE | Trend MAE | Chronos policy MAE | Chronos policy RMSE | Skill vs persistence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Validation | 30 | 53.654 | 56.170 | 87.019 | 57.215 | 130.272 | -6.64% |
| Validation | 60 | 93.210 | 94.168 | 167.507 | 101.268 | 177.850 | -8.65% |
| Validation | 90 | 131.868 | 132.374 | 243.354 | 147.520 | 223.432 | -11.87% |
| Temporal test | 30 | 50.326 | 52.421 | 82.530 | 58.889 | 110.298 | -17.01% |
| Temporal test | 60 | 98.710 | 100.877 | 149.871 | 108.426 | 157.756 | -9.84% |
| Temporal test | 90 | 148.708 | 150.829 | 189.166 | 157.478 | 194.030 | -5.90% |
| Held-out repositories | 30 | 179.599 | 186.347 | 280.616 | 227.886 | 418.015 | -26.89% |
| Held-out repositories | 60 | 327.941 | 332.544 | 520.099 | 392.762 | 576.617 | -19.77% |
| Held-out repositories | 90 | 470.252 | 474.380 | 775.956 | 541.636 | 732.360 | -15.18% |

Persistence won validation at 30/60/90 days; `selection.json` retains those decisions regardless of test outcomes. Chronos is retained as a measured pretrained research candidate, not promoted as the default predictor. The pinned 90-context zero-shot configuration performs worse than persistence on this archive. This does not establish the ranking of alternative contexts, adaptation strategies or checkpoints, which would require new preregistered experiments and separate authorization.

Uncertainty uses 2,000 **paired repository-bootstrap** draws with replacement, seed 42, equal repository weighting, percentile 95% bounds. Bounds condition on the frozen cohort and do not account for source-label ambiguity or future domain shift. No row-wise bootstrap treats overlapping daily origins as independent. Only six held-out clusters make those intervals exploratory; a single repository gets no row-derived CI. Paired gain CIs are absolute debt minutes, not percentages.

| Test cohort | Days | Chronos macro-MAE 95% CI | Paired MAE gain 95% CI (persistence − Chronos) |
| --- | --- | --- | --- |
| Temporal test | 30 | 22.155 to 104.357 | -18.028 to -1.777 |
| Temporal test | 60 | 44.598 to 187.080 | -18.384 to -3.560 |
| Temporal test | 90 | 62.760 to 277.338 | -19.081 to 0.155 |
| Held-out repositories | 30 | 49.257 to 438.541 | -103.032 to -7.912 |
| Held-out repositories | 60 | 111.137 to 705.362 | -108.128 to -21.074 |
| Held-out repositories | 90 | 150.723 to 951.820 | -121.063 to -20.337 |

Unchanged and changing-debt strata use the actual signed endpoint delta only during scoring. They are never prediction inputs. Macro statistics within a stratum average only repositories represented in that stratum, so stratum macro values must not be row-weighted to reconstruct the aggregate. Persistence is exactly zero-error on unchanged cases; its relative skill denominator is zero and is exported as null.

| Test cohort | Days | Stratum | IDs | Chronos MAE | Chronos RMSE | Persistence MAE |
| --- | --- | --- | --- | --- | --- | --- |
| Temporal test | 30 | unchanged_debt | 410 | 20.524 | 31.357 | 0.000 |
| Temporal test | 30 | changing_debt | 145 | 195.154 | 253.893 | 188.779 |
| Temporal test | 60 | unchanged_debt | 330 | 23.358 | 32.793 | 0.000 |
| Temporal test | 60 | changing_debt | 225 | 227.409 | 271.986 | 219.126 |
| Temporal test | 90 | unchanged_debt | 287 | 50.698 | 62.476 | 0.000 |
| Temporal test | 90 | changing_debt | 268 | 266.093 | 299.384 | 261.422 |
| Held-out repositories | 30 | unchanged_debt | 130 | 31.791 | 76.559 | 0.000 |
| Held-out repositories | 30 | changing_debt | 92 | 649.323 | 843.785 | 587.643 |
| Held-out repositories | 60 | unchanged_debt | 98 | 17.780 | 58.285 | 0.000 |
| Held-out repositories | 60 | changing_debt | 124 | 690.164 | 806.964 | 600.412 |
| Held-out repositories | 90 | unchanged_debt | 82 | 31.062 | 96.532 | 0.000 |
| Held-out repositories | 90 | changing_debt | 140 | 795.377 | 912.296 | 717.061 |

Native-success-only comparison pairs **all four models on the same retained IDs**. These numbers are conditional and cannot replace the full assigned-cohort failure-policy comparison. Full success-matched baseline/model metrics are published.

| Test cohort | Days | Native-success IDs | Native Chronos MAE | Matched persistence MAE |
| --- | --- | --- | --- | --- |
| Temporal test | 30 | 551 | 59.199 | 50.621 |
| Temporal test | 60 | 551 | 107.549 | 97.775 |
| Temporal test | 90 | 551 | 157.010 | 148.140 |
| Held-out repositories | 30 | 220 | 229.658 | 181.095 |
| Held-out repositories | 60 | 220 | 396.335 | 330.716 |
| Held-out repositories | 90 | 220 | 547.006 | 474.753 |

## Native 80% interval results and constant histories

Only successful q10–q90 intervals contribute to coverage/width. Failure denominators stay visible; fallback points have no interval. Coverage means inclusive `q10 <= actual <= q90`; widths are q90 − q10. Macro coverage/width give equal weight to repositories with successful intervals. Exported pooled metrics are distinct. Nominal 80% does not guarantee empirical 80%. Bootstrap coverage bounds describe sampling uncertainty, not calibrated prediction intervals.

| Role | Days | Attempt/native/fallback | Macro coverage | Macro width (minutes) | Coverage 95% CI | Collapsed | Collapsed misses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Validation | 30 | 735/729/6 | 81.93% | 169.945 | 73.81–89.71% | 360 | 50 |
| Validation | 60 | 735/729/6 | 71.84% | 206.953 | 59.49–84.28% | 360 | 69 |
| Validation | 90 | 735/729/6 | 66.31% | 229.171 | 51.31–81.20% | 360 | 69 |
| Temporal test | 30 | 555/551/4 | 79.32% | 135.200 | 69.62–89.05% | 286 | 31 |
| Temporal test | 60 | 555/551/4 | 69.30% | 166.850 | 56.91–82.24% | 286 | 53 |
| Temporal test | 90 | 555/551/4 | 62.37% | 189.417 | 47.70–76.80% | 286 | 65 |
| Held-out repositories | 30 | 222/220/2 | 78.59% | 579.561 | 63.51–93.67% | 94 | 2 |
| Held-out repositories | 60 | 222/220/2 | 67.20% | 802.361 | 50.25–84.53% | 94 | 12 |
| Held-out repositories | 90 | 222/220/2 | 60.90% | 906.714 | 47.38–74.87% | 94 | 25 |

All exactly constant past histories produced **raw and clipped zero-width native intervals** at the selected endpoints: 360 validation, 286 temporal and 94 held-out contexts per horizon. Constant history does not guarantee constant future debt. The table shows direct misses; intervals were not artificially widened or replaced after outcomes.

| Role | Days | Constant-context intervals | Macro width | Macro coverage | Collapsed misses |
| --- | --- | --- | --- | --- | --- |
| Validation | 30 | 360 | 0.000 | 55.75% | 50 |
| Validation | 60 | 360 | 0.000 | 43.63% | 69 |
| Validation | 90 | 360 | 0.000 | 43.63% | 69 |
| Temporal test | 30 | 286 | 0.000 | 66.30% | 31 |
| Temporal test | 60 | 286 | 0.000 | 54.09% | 53 |
| Temporal test | 90 | 286 | 0.000 | 50.75% | 65 |
| Held-out repositories | 30 | 94 | 0.000 | 98.20% | 2 |
| Held-out repositories | 60 | 94 | 0.000 | 86.13% | 12 |
| Held-out repositories | 90 | 94 | 0.000 | 70.59% | 25 |

There is one additional near-collapsed validation interval at 30 days under the predeclared tolerance `width <= 1e-6 * max(1, current_minutes)`. Exact collapse, near-collapse and raw collapse are separately exported. Native interval-score80 (`width + 10*lower_miss + 10*upper_miss`) and q10/q50/q90 pinball losses are included in `chronos_interval_metrics.csv`, including changing/unchanged cases, constant/nonconstant histories and per-repository diagnostics. No available-interval coverage claim is made for failed contexts.

## Context diversity and per-repository diagnostics

Ninety calendar positions are **not 90 independent scans**. Repeated states, overlapping origin/endpoint windows and overlapping horizons remain. These are inherited frozen design limitations; no cohort was altered after observing outcomes. Distinct IDs count source measurements, while distinct value-sequence digests count model-input patterns. Equal-valued sequences can arise from multiple distinct scans. These measures describe diversity, not a corrected effective sample size.

| Test cohort | Days | IDs | Distinct origin scans | Distinct endpoint scans | Distinct value contexts | Scans/context min/median/max |
| --- | --- | --- | --- | --- | --- | --- |
| Temporal test | 30 | 555 | 119 | 132 | 286 | 1/3/22 |
| Temporal test | 60 | 555 | 119 | 142 | 286 | 1/3/22 |
| Temporal test | 90 | 555 | 119 | 149 | 286 | 1/3/22 |
| Held-out repositories | 30 | 222 | 73 | 75 | 131 | 1/8/28 |
| Held-out repositories | 60 | 222 | 73 | 88 | 131 | 1/8/28 |
| Held-out repositories | 90 | 222 | 73 | 87 | 131 | 1/8/28 |

Individual repository 90-day results follow; machine-readable files contain every horizon, stratum, baseline and interval diagnostic. Repository IDs are the immutable Phase 1 lineage identifiers, avoiding name/rename ambiguity.

| Cohort | Repository ID | IDs | Chronos MAE | Chronos RMSE | Persistence MAE |
| --- | --- | --- | --- | --- | --- |
| Temporal test | v2-0d4a1de0cc1e1cb6f28a9db6 | 37 | 778.038 | 865.486 | 713.568 |
| Temporal test | v2-0ff64367ee1c3d488a880a51 | 37 | 404.499 | 473.857 | 430.297 |
| Temporal test | v2-23449eb60ab6ff083e4b7af2 | 37 | 1.970 | 4.292 | 0.811 |
| Temporal test | v2-3fee202c3b42dffa623a2b4e | 37 | 402.708 | 511.581 | 375.865 |
| Temporal test | v2-46ae23a54214d989ff07551b | 37 | 0.000 | 0.000 | 0.000 |
| Temporal test | v2-5a156039ebb55f29ae7a9601 | 37 | 179.034 | 216.842 | 150.865 |
| Temporal test | v2-6e8bf5660f0d3e6cb729d4e5 | 37 | 88.935 | 104.319 | 91.054 |
| Temporal test | v2-91429c566e7c1a0cbb0fd178 | 37 | 21.189 | 45.569 | 21.189 |
| Temporal test | v2-a9818ca385b16b2e846a8228 | 37 | 0.000 | 0.000 | 0.000 |
| Temporal test | v2-b3197a1f57f5eea93c094868 | 37 | 113.141 | 167.785 | 94.162 |
| Temporal test | v2-dbf56f245864a6282bf22bca | 37 | 178.576 | 246.595 | 181.135 |
| Temporal test | v2-dd7a6301f6577ed0b245eec3 | 37 | 0.000 | 0.000 | 0.000 |
| Temporal test | v2-ef6e6b7896649c5d7b494c6f | 37 | 97.600 | 129.583 | 90.162 |
| Temporal test | v2-f923881aac8e9e82528717b5 | 37 | 96.480 | 144.535 | 81.514 |
| Temporal test | v2-ffa9f174c149662d62016404 | 37 | 0.000 | 0.000 | 0.000 |
| Held-out repositories | v2-11eb4c34daf05c37fa6838da | 37 | 785.095 | 1360.916 | 669.378 |
| Held-out repositories | v2-2fd0e784f917563f1f08d008 | 37 | 36.486 | 99.254 | 36.486 |
| Held-out repositories | v2-be00cc678f41e66832ccd8eb | 37 | 577.146 | 744.612 | 516.135 |
| Held-out repositories | v2-c5586b674469c147cfada344 | 37 | 4.892 | 9.374 | 4.892 |
| Held-out repositories | v2-c7c657acd5ed716b76c47c1f | 37 | 1441.383 | 1721.254 | 1261.919 |
| Held-out repositories | v2-f07bbb56c8cc56591ba77bae | 37 | 404.812 | 458.748 | 332.703 |

## Runtime, resource bounds and reproducibility

Hardware: AMD Ryzen 5 PRO 5650U, 6 cores/12 logical CPUs, 16,036,016,128 bytes RAM. Observed approximately 8.6 GB available RAM and 21.0 GB free disk during verification. CPU only. Each stage uses an external supervisor with 2 GiB RSS limit; pilot timeout 900 seconds, complete validation/test timeout 1,800 seconds each. All supervisor exits were successful; data-level inference failures are recorded separately as PARTIAL.

- `pilot`: 4.348 s worker elapsed, 3.364 s model load, 0.826 s total context inference; worker high-water RSS 468.66 MiB. External resource measurements: `examples/phase4_2/pilot/resources.json`.
- `validation`: 29.726 s worker elapsed, 3.028 s model load, 26.142 s total context inference; worker high-water RSS 493.21 MiB. External resource measurements: `examples/phase4_2/validation/resources.json`.
- `test`: 31.175 s worker elapsed, 2.958 s model load, 27.639 s total context inference; worker high-water RSS 495.00 MiB. External resource measurements: `examples/phase4_2/test/resources.json`.

Canonical full evaluation elapsed 79.77 seconds (124.60 user CPU seconds, 2.52 system seconds); the full repeat elapsed 77.85 seconds. Observed external worker peak RSS reached 519,544,832 bytes, below the 2-GiB cap.

Both final full CPU runs use identical final source. All 20 checked deterministic artifacts are byte-identical, including complete native/fallback predictions, stage prediction CSVs, all metric tables, plot, selection, study and all three past-only request bundles. `determinism.json` lists individual SHA-256 checks. Timings/RSS and manifests/seals incorporating timed summaries legitimately differ and are not claimed byte-identical. Each run independently checks its seals, frozen inputs, checkpoint/code snapshots and original baseline values. The pilot repeats valid paths twice; full stages run one prediction per context. No repeat was used to choose parameters.

The final local canonical output is `research/forecasting_mvp/phase4_2/2026-10-15/run-004`; fresh full repeat is `run-005`. Earlier `run-002`/`run-003` used the pre-fix repeat-gate control flow and are not the published canonical result. Their numerical results are unchanged. `run-001` is an incomplete pilot-only development attempt. No old output directories were overwritten.

### Reproduce with existing admitted artifacts

Run from the working project; output must be a new path. Source DB is not needed for this evaluation: use the existing COMPLETE Phase 1/2/3/4.1 bundles. For another host, reproduce those bundles from the separately attributed dataset using prior reports and keep hashes/IDs identical; adjust only filesystem paths. Weights and runtime were prepared in Phase 4.1; do not silently upgrade them.

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp evaluate-chronos \
  --bundle /home/hp/tst/research/forecasting_mvp/phase2/2026-10-14/run-003 \
  --history-bundle /home/hp/tst/research/forecasting_mvp/phase1/2026-10-14/run-002 \
  --baseline-bundle /home/hp/tst/research/forecasting_mvp/phase3/2026-10-14/run-002 \
  --smoke-bundle /home/hp/tst/research/forecasting_mvp/phase4_1/2026-10-14/run-003 \
  --runtime-python /home/hp/tst/td_pipeline_module_level/td_pipeline/.venv-chronos-cpu/bin/python \
  --checkpoint /home/hp/tst/research/forecasting_mvp/model_cache/chronos-2-small/ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a \
  --out /absolute/new-phase4_2-run
```

Expected exit **2**, status PARTIAL, COMPLETE checksummed output bundle and explicit recovered failures. This is different from exit 3/BLOCKED (no valid pilot, nondeterminism, input/seal mismatch or process/resource failure). Exit 0 requires complete native success. Hashes and manifest checks are not proof that the source labels are unbiased; inherited historical-scan limitations still apply.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp verify-bundle \
  --bundle /absolute/new-phase4_2-run
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp verify-bundle \
  --bundle examples/phase4_2
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_forecasting_mvp_phase4_2.py
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests \
  -k 'not test_actual_catboost_models_shared_folds_predictions_and_purging'
```

### Verification results

- Focused Phase 4.2: **13 passed**; synthetic engines verify software contracts and analytical cases only. Real pretrained results are the separate complete CPU evaluations.
- Complete permitted regression suite in publication checkout: **310 passed, 1 deselected**. The deselected legacy test trains actual CatBoost models, prohibited in this phase. No test failed.
- Working checkout regression: **310 passed, 1 deselected** after explicit source synchronization; see `working_regression_tests.xml`.
- Identity, exact timestamps, target-free inputs, holdout/phase rejection, duplicate/count rejection, intervals, fallback pairing, validation-only selection, frozen selection seal, label-open order, original-baseline preservation and full workflow ordering are tested.
- Original Phase 1/2/3/4.1 manifests, original dataset/split IDs, Phase 3 prediction/metric bytes, adapter/input-boundary bytes, checkpoint weights/config, old dependency files and the unrelated original working main are preserved. See `preservation.json` and `study.json`.

### Outputs and integrity

Full local output includes `chronos_predictions.csv` (4,536 rows), `chronos_comparison_metrics.csv` (1,404 rows), `chronos_success_matched_metrics.csv`, `chronos_interval_metrics.csv` (585 rows), `chronos_comparison.png`, 45-row sample, `study.json`, `selection.json`, validation/test prediction seals, all three request bundles, worker resources/summaries, `run_audit.json` and COMPLETE manifest. `examples/phase4_2/full_local_output_hashes.json` is a receipt for the **local full run**, not a bundle containing unpublished datasets. `examples/phase4_2/manifest.json` covers only the actually published small evidence files. Source dataset attribution and noncommercial share-alike terms are retained in its README.

## Decision and stop condition

| Gate | Result |
| --- | --- |
| Complete registered ID coverage; no cohort changes | PASS, including explicit failure-policy points |
| Native q10/q50/q90 for every context | PARTIAL: 12 rejected paths, 36 endpoints without native intervals |
| Validation-only configuration/selection; test seal before labels | PASS |
| Exact old baseline/ID/input preservation | PASS |
| Deterministic final prediction/metric outputs and allowed regression | PASS |
| Improved Chronos macro MAE vs persistence | Not demonstrated; worse in all six test comparisons |
| Reliable nominal 80% native intervals | Not established; long-horizon undercoverage and constant-history collapse |
| Overall Phase 4.2 | **PARTIAL**, completed evaluation with documented model limitations |

Retain persistence as the frozen validation-selected point default. Preserve Chronos predictions as a reproducible negative-result research artifact and do not present the native intervals as calibrated technical-debt uncertainty. A future authorized study could investigate longer independent contexts, conservative path-rejection behavior or validation-only uncertainty calibration with fresh evaluation protection; none was implemented or tuned here. No readiness claim is made for pretrained production deployment.

Publish only verified Phase 4.2 source, tests, report, plot and small evidence through a normal descendant commit on central GitHub `main`. Remote history was refreshed: its unrelated `acda0c5` deletion of `OK` was safely fast-forwarded and preserved; no Phase 4.2 files overlapped that change. Preserve the working project's unrelated history/changes. Stop after publication; no next model, training or dashboard phase is authorized.
