# TechDebt360 — Phase 4.2.1: Chronos Diagnostics & Hardening

Date: 2026-10-15. Project: `/home/hp/tst/td_pipeline_module_level/td_pipeline`.

**Phase 4.2.1 PASS.** All 12 published quantile-crossing failures were audited with paired, bounded diagnostic inference. Error handling now recovers only a typed native quantile-ordering failure after complete output identity/finiteness checks; unexpected software/runtime errors abort. Published Phase 4.2 forecasts, metrics, configuration, cohorts and source-data artifacts remain byte-identical. **Phase 4.2 remains PARTIAL**; this diagnostic pass does not promote Chronos or change its reported performance.

## Scope and preservation

Publication base: `187dcc1df247a88c95acaf56482da239c67059a8`. Original experiment study ID: `70b372e32c7292aca8b260b1a44c28787c3f03b7c11277159a53dd18cc22c958`.

Only 12 already-failed contexts were inferred, twice each: **24 diagnostic calls**, each using the same 90 past points and 90-step native path. No other validation/test context was inferred. No benchmark rerun, new accuracy evaluation, replacement predictions, recalibration, tuning, model installation/download, training, new model or dashboard occurred. The new diagnostic output has its own folder and COMPLETE manifest; it never writes into protected experiment folders. Descriptive interval arithmetic reads existing published metrics only, without opening future-label files.

The original Phase 4.2 worker discarded the invalid native paths. Their raw crossing magnitudes therefore could not be recovered from saved fallback CSVs alone. The scoped replay uses the pinned checkpoint and unchanged inference arguments, with a transparent wrapper observing the native `predict_df` output. It neither changes model inputs nor sorts/adjusts outputs. Raw values are labeled **diagnostic evidence**, not new forecasts replacing original fallback points. The adapter's new exception classification/full-path validation precedence is recorded in the diagnostic source hashes; it does not change model weights, quantile levels, context, horizon, normalization, clipping or inference settings.

`preservation.json` checks original Phase 1/2/3/4.1/4.2 manifests, both final Phase 4.2 runs, checkpoint artifacts, dependency files, the original Phase 4.2 report and every published Phase 4.2 evidence file. The original experiment implementation is retained at the above Git commit; its frozen study/code hashes are not rewritten to describe the hardening. Fresh use of hardened code is a distinct execution, not a reproduction of the original source snapshot.

## Audit of every failure

All 12 failures reproduced on both calls with exactly equal raw daily q10/q50/q90 values and crossing locations. There are **14 crossed steps across 1,080 unique diagnostic path steps** (two calls repeat each path): 11 lower crossings (`q10 > q50`) and 3 upper crossings (`q50 > q90`). Maximum positive inversion ranges from **0.000244140625 to 2.8369140625 estimated debt minutes**. These units are SonarQube estimated remediation stock, not actual developer repair effort. No arbitrary tolerance was introduced.

All selected **36 endpoints** at exact 30/60/90 days are ordered and finite. Crossings occur only at steps 1, 17, 18, 19 or 64. The published adapter rejected the whole path for any crossing, so its 12-context/36-endpoint failure policy was conservative relative to the selected endpoints. This diagnosis does **not** authorize an endpoint-only policy, quantile sorting, reclassification of old fallbacks or recomputing published metrics.

Lower/upper columns list all affected step indices. Full context hashes, origin timestamps, forecast IDs, raw paths and repeated values are in the linked diagnostic JSON/CSV.

| Context prefix | Role | Repository ID | Lower steps | Upper steps | Max inversion (minutes) | Selected endpoints |
| --- | --- | --- | --- | --- | --- | --- |
| 014354a62291 | Validation | v2-3fee202c3b42dffa623a2b4e | 1 | — | 0.125000000 | 30/60/90 ordered |
| 26d9eef4ab6b | Validation | v2-3fee202c3b42dffa623a2b4e | — | 18,19 | 0.499023438 | 30/60/90 ordered |
| 43b671bd5ff2 | Held-out test | v2-f07bbb56c8cc56591ba77bae | — | 64 | 2.836914062 | 30/60/90 ordered |
| 8e8e669e6ec8 | Validation | v2-dd7a6301f6577ed0b245eec3 | 19 | — | 0.042968750 | 30/60/90 ordered |
| 9c7f04426286 | Temporal test | v2-b3197a1f57f5eea93c094868 | 1 | — | 0.180664062 | 30/60/90 ordered |
| a2d6203eedf0 | Validation | v2-5a156039ebb55f29ae7a9601 | 1 | — | 0.003906250 | 30/60/90 ordered |
| afc786a598f7 | Validation | v2-6e8bf5660f0d3e6cb729d4e5 | 19 | — | 0.044921875 | 30/60/90 ordered |
| d27815ccdf70 | Held-out test | v2-11eb4c34daf05c37fa6838da | 1 | — | 0.218750000 | 30/60/90 ordered |
| d61c04ee72fb | Temporal test | v2-3fee202c3b42dffa623a2b4e | 1 | — | 0.155273438 | 30/60/90 ordered |
| d8b4815cf5ef | Temporal test | v2-ef6e6b7896649c5d7b494c6f | 1 | — | 0.005859375 | 30/60/90 ordered |
| f4792a9a64a7 | Validation | v2-0ff64367ee1c3d488a880a51 | 17,19 | — | 0.003906250 | 30/60/90 ordered |
| fc438e6b9898 | Temporal test | v2-23449eb60ab6ff083e4b7af2 | 19 | — | 0.000244141 | 30/60/90 ordered |

### Historical input characteristics

All failed histories are **nonconstant**, with 2–15 distinct source measurements, 2–5 distinct debt values and 1–4 observed value transitions across 90 daily states. None contains a zero debt value. Repeated daily positions are not independent SonarQube scans. Full past-only request records and reference times are published as `failed_context_inputs.json`; no future labels are included.

| Context prefix | Source scans | Distinct debt values | Value transitions | Population SD (minutes) | Current stock (minutes) | Past net change (minutes) |
| --- | --- | --- | --- | --- | --- | --- |
| 014354a62291 | 15 | 4 | 3 | 214.537 | 15245 | 594 |
| 26d9eef4ab6b | 15 | 4 | 3 | 290.319 | 15245 | 594 |
| 43b671bd5ff2 | 12 | 3 | 2 | 204.772 | 15087 | -400 |
| 8e8e669e6ec8 | 4 | 2 | 1 | 4.999 | 6705 | -10 |
| 9c7f04426286 | 7 | 5 | 4 | 99.456 | 5307 | 268 |
| a2d6203eedf0 | 7 | 2 | 1 | 0.998 | 38759 | 4 |
| afc786a598f7 | 6 | 2 | 1 | 8.980 | 14700 | -18 |
| d27815ccdf70 | 6 | 4 | 3 | 143.361 | 58602 | 473 |
| d61c04ee72fb | 2 | 2 | 1 | 99.029 | 15716 | 397 |
| d8b4815cf5ef | 4 | 3 | 2 | 50.284 | 28645 | 199 |
| f4792a9a64a7 | 2 | 2 | 1 | 1.000 | 11659 | -2 |
| fc438e6b9898 | 4 | 2 | 1 | 4.969 | 3847 | -10 |

### Raw selected endpoints

These are captured diagnostic values only. They do not replace any original persistence fallback or create a new scored cohort. No endpoint labels were used in collecting them. All 12 original failures still remain failures in the published experiment.

| Context prefix | Days | Native q10 | Native q50 | Native q90 | Ordered |
| --- | --- | --- | --- | --- | --- |
| 014354a62291 | 30 | 15090.755859375 | 15243.475585938 | 15246.716796875 | True |
| 014354a62291 | 60 | 14743.487304688 | 15243.185546875 | 15248.594726562 | True |
| 014354a62291 | 90 | 14782.638671875 | 15243.928710938 | 15250.126953125 | True |
| 26d9eef4ab6b | 30 | 14576.254882812 | 15181.532226562 | 15260.974609375 | True |
| 26d9eef4ab6b | 60 | 14637.625976562 | 14957.445312500 | 15298.852539062 | True |
| 26d9eef4ab6b | 90 | 14626.165039062 | 15138.347656250 | 15288.893554688 | True |
| 43b671bd5ff2 | 30 | 15069.815429688 | 15103.464843750 | 15599.273437500 | True |
| 43b671bd5ff2 | 60 | 15022.583007812 | 15561.988281250 | 15581.868164062 | True |
| 43b671bd5ff2 | 90 | 15077.752929688 | 15572.712890625 | 15580.887695312 | True |
| 8e8e669e6ec8 | 30 | 6704.868652344 | 6705.497558594 | 6715.728027344 | True |
| 8e8e669e6ec8 | 60 | 6704.691894531 | 6704.984863281 | 6715.192871094 | True |
| 8e8e669e6ec8 | 90 | 6704.780761719 | 6704.984375000 | 6715.161621094 | True |
| 9c7f04426286 | 30 | 5294.075195312 | 5306.428222656 | 5307.854492188 | True |
| 9c7f04426286 | 60 | 5289.469726562 | 5306.968261719 | 5308.632812500 | True |
| 9c7f04426286 | 90 | 5300.665527344 | 5306.607421875 | 5308.356445312 | True |
| a2d6203eedf0 | 30 | 38758.515625000 | 38758.996093750 | 38759.011718750 | True |
| a2d6203eedf0 | 60 | 38757.503906250 | 38759.000000000 | 38759.019531250 | True |
| a2d6203eedf0 | 90 | 38757.777343750 | 38759.003906250 | 38759.019531250 | True |
| afc786a598f7 | 30 | 14699.458007812 | 14701.006835938 | 14718.766601562 | True |
| afc786a598f7 | 60 | 14699.392578125 | 14703.068359375 | 14718.577148438 | True |
| afc786a598f7 | 90 | 14699.347656250 | 14699.844726562 | 14718.597656250 | True |
| d27815ccdf70 | 30 | 58491.625000000 | 58601.292968750 | 58603.601562500 | True |
| d27815ccdf70 | 60 | 58336.691406250 | 58601.929687500 | 58604.839843750 | True |
| d27815ccdf70 | 90 | 58414.523437500 | 58602.367187500 | 58604.968750000 | True |
| d61c04ee72fb | 30 | 15667.302734375 | 15715.661132812 | 15717.260742188 | True |
| d61c04ee72fb | 60 | 15567.083984375 | 15716.059570312 | 15717.994140625 | True |
| d61c04ee72fb | 90 | 15593.947265625 | 15716.432617188 | 15717.953125000 | True |
| d8b4815cf5ef | 30 | 28621.164062500 | 28644.826171875 | 28645.642578125 | True |
| d8b4815cf5ef | 60 | 28572.355468750 | 28645.046875000 | 28646.007812500 | True |
| d8b4815cf5ef | 90 | 28586.294921875 | 28645.226562500 | 28645.980468750 | True |
| f4792a9a64a7 | 30 | 11658.951171875 | 11659.107421875 | 11661.092773438 | True |
| f4792a9a64a7 | 60 | 11658.935546875 | 11659.041015625 | 11661.083007812 | True |
| f4792a9a64a7 | 90 | 11658.938476562 | 11658.996093750 | 11661.066406250 | True |
| fc438e6b9898 | 30 | 3846.747802734 | 3847.582275391 | 3857.562011719 | True |
| fc438e6b9898 | 60 | 3846.553466797 | 3850.052734375 | 3857.158935547 | True |
| fc438e6b9898 | 90 | 3846.577148438 | 3847.792236328 | 3857.475341797 | True |

The observed sparse crossing of independently returned native quantiles is evidence of output-order violation, not a proven unique training/numerical cause. The largest inversion exceeds a one-ULP stock rounding difference; it must not be dismissed universally as floating-point noise. Scope was diagnostic only; no tolerance, isotonic rearrangement or selected-step exception was evaluated for predictive performance.

## Narrow error handling and identity protection

Confirmed defect: `infer_records` previously caught `Exception`, silently turning `MemoryError`, runtime failures, malformed output and software bugs into persistence fallback. It could also recover a crossing during a repeat after an already valid first path, hiding a reproducibility failure.

The smallest responsible changes are:

- `forecasting_mvp/chronos_adapter.py`: adds `NativeQuantileCrossingError(ValueError)`. The **entire** 90-step output is checked for identity, target name, exact UTC daily timestamps and finite quantiles/generic output before a typed crossing can be raised. An early crossing must not mask a later identity or numerical defect. Crossing detection still has zero tolerance; all raw/native/clipped path calculations remain unchanged.
- `forecasting_mvp/chronos_eval_worker.py`: catches **only** `NativeQuantileCrossingError` from the first attempt. It emits the existing explicit persistence point and null interval under the existing failure policy. Generic `ValueError`, runtime/memory/IO/assertion/type/key failures propagate and abort before a COMPLETE worker result is published. Error **type**, never error-message matching, authorizes recovery.
- The pilot repeat executes outside the recovery block. A differing valid repeat or **any** repeat failure (including a typed crossing after a successful first path) aborts. No partial successful rows are published on a fatal failure.
- The broad catch in worker `main` is intentionally retained only as a **fatal process boundary**: it emits `BLOCKED`, returns exit 3 and performs no fallback. The parent supervisor blocks on that nonzero exit. It is distinct from per-context recovery.

| Condition | Hardened action |
| --- | --- |
| Typed native crossing; all output identities/finite values valid | Explicit persistence fallback, no invented interval |
| Plain ValueError with the exact crossing error message | Fatal; string equality never grants recovery |
| Malformed shape/columns, wrong identity/timestamp or nonfinite values | Fatal |
| Crossing at an early step plus wrong identity/timestamp/nonfinite later | Fatal; full-path contract takes precedence |
| RuntimeError, MemoryError, AssertionError, TypeError, KeyError, OSError | Fatal |
| Valid first path followed by crossing/runtime failure on repeat | Fatal reproducibility failure |
| Two valid but unequal repeat paths | Fatal reproducibility failure |
| Two identical valid paths | Same native points/quantiles and explicit repeat equality |

These are prospective code safeguards. The original experiment's error strings/types, forecast CSVs and status summaries are preserved; no error records were retroactively edited.

## Constant-history interval collapse

The published native intervals, including **raw** q10/q50/q90, already collapse before nonnegative clipping. Among 740 distinct constant-history contexts (360 validation, 286 temporal, 94 held-out), the saved raw median equals the current debt stock; q10 equals q50 equals q90. Their selected widths are zero. This conclusion comes from saved outputs, not new inference on constant histories.

The installed Chronos 2.3.2 source provides a plausible numerical explanation: `chronos/chronos_bolt.py`, `InstanceNorm.forward`, lines 95–133, substitutes epsilon `1e-5` for zero standard deviation. Its inverse computes in float32 `normalized_output * scale + loc`; `chronos2/model.py` imports and calls that normalizer/inverse. At the observed constant stock values (3,847–58,602 minutes), float32 adjacent-value spacing is **0.000244140625–0.00390625**, always larger than epsilon. Tiny normalized quantile differences can therefore round to the same original-scale value.

`constant_precision_evidence.json` records the installed source SHA-256, source paths, saved prediction hash and per-role spacing/range counts. Arithmetic uses `np.spacing(np.float32(current_minutes))` for each constant context, selecting one 30-day row per context to avoid triple-counting horizons. This supports a scale/rounding explanation; no hidden normalized activations or precision ablation were captured, so it is **not proof of a unique causal mechanism**. No model normalization, dtype, epsilon or interval policy was changed.

Constant-history diagnostics below reproduce published aggregates. The macro and pooled columns differ because equal repository weighting differs from equal row weighting, particularly within strata. Constant past does not guarantee unchanged future debt.

| Role | Days | Constant contexts | Raw collapsed | Macro coverage | Pooled coverage | Collapsed misses |
| --- | --- | --- | --- | --- | --- | --- |
| Validation | 30 | 360 | 360 | 55.75% | 86.11% | 50 |
| Validation | 60 | 360 | 360 | 43.63% | 80.83% | 69 |
| Validation | 90 | 360 | 360 | 43.63% | 80.83% | 69 |
| Temporal test | 30 | 286 | 286 | 66.30% | 89.16% | 31 |
| Temporal test | 60 | 286 | 286 | 54.09% | 81.47% | 53 |
| Temporal test | 90 | 286 | 286 | 50.75% | 77.27% | 65 |
| Held-out test | 30 | 94 | 94 | 98.20% | 97.87% | 2 |
| Held-out test | 60 | 94 | 94 | 86.13% | 87.23% | 12 |
| Held-out test | 90 | 94 | 94 | 70.59% | 73.40% | 25 |

## Long-horizon undercoverage: published measurements only

Nominal q10–q90 coverage is 80%. The following numbers retain the original successful-native interval denominators; fallback points have no interval. The pooled miss counts are descriptive integer arithmetic: `successful_intervals − round(pooled_coverage * successful_intervals)`. Noncollapsed misses subtract the published collapsed miss count. No predictions, original metrics, test cohorts or uncertainty estimates were recomputed.

| Role | Days | Attempted | Native | Fallback | Macro coverage | Macro width (minutes) | Pooled misses | Collapsed misses | Noncollapsed misses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Validation | 30 | 735 | 729 | 6 | 81.93% | 169.945 | 131 | 50 | 81 |
| Validation | 60 | 735 | 729 | 6 | 71.84% | 206.953 | 204 | 69 | 135 |
| Validation | 90 | 735 | 729 | 6 | 66.31% | 229.171 | 244 | 69 | 175 |
| Temporal test | 30 | 555 | 551 | 4 | 79.32% | 135.200 | 114 | 31 | 83 |
| Temporal test | 60 | 555 | 551 | 4 | 69.30% | 166.850 | 169 | 53 | 116 |
| Temporal test | 90 | 555 | 551 | 4 | 62.37% | 189.417 | 207 | 65 | 142 |
| Held-out test | 30 | 222 | 220 | 2 | 78.59% | 579.561 | 47 | 2 | 45 |
| Held-out test | 60 | 222 | 220 | 2 | 67.20% | 802.361 | 72 | 12 | 60 |
| Held-out test | 90 | 222 | 220 | 2 | 60.90% | 906.714 | 86 | 25 | 61 |

Collapse is not the sole undercoverage mechanism. Nonconstant histories have positive native widths but poor longer-horizon coverage:

| Role | Days | Nonconstant native contexts | Macro coverage | Pooled coverage | Macro width (minutes) | Pooled misses |
| --- | --- | --- | --- | --- | --- | --- |
| Validation | 30 | 369 | 80.42% | 78.05% | 309.811 | 81 |
| Validation | 60 | 369 | 66.98% | 63.41% | 375.339 | 135 |
| Validation | 90 | 369 | 56.65% | 52.57% | 414.544 | 175 |
| Temporal test | 30 | 265 | 75.76% | 68.68% | 249.712 | 83 |
| Temporal test | 60 | 265 | 65.41% | 56.23% | 299.977 | 116 |
| Temporal test | 90 | 265 | 56.53% | 46.42% | 336.785 | 142 |
| Held-out test | 30 | 126 | 67.50% | 64.29% | 1199.903 | 45 |
| Held-out test | 60 | 126 | 57.25% | 52.38% | 1655.804 | 60 |
| Held-out test | 90 | 126 | 56.67% | 51.59% | 1906.675 | 61 |

At 90 days, the temporal cohort has 207 native misses: 65 collapsed and **142 noncollapsed**; held-out repositories have 86: 25 collapsed and **61 noncollapsed**. These latter counts dominate total misses. Wide or nonzero intervals do not establish calibration. The table is a descriptive decomposition, not a causal estimate of what widening collapsed intervals would achieve. Context reuse, overlapping windows and few independent repository clusters remain inherited limitations; held-out uncertainty is exploratory with six repositories. The existing paired repository-bootstrap bounds and point-error comparisons stay unchanged in Phase 4.2 evidence.

Changing/unchanged debt and constant/nonconstant past are separate concepts. Diagnostic evidence includes every published macro stratum, interval score and pinball loss. No test-driven threshold, residual fitting, model selection, calibration or promotion decision was made. Persistence remains the original validation-selected point default; native Chronos intervals remain uncalibrated.

## Bounded diagnostic runtime and reproducibility

Actual bounded worker/supervisor execution: **5.716 seconds** wall time, peak observed RSS **493,850,624 bytes** (470.97 MiB), within 300 seconds and 2 GiB. Worker own elapsed time was 4.835 seconds. All 24 calls completed; raw pairs and crossing diagnostics match exactly. No process/runtime error occurred during real diagnostic inference. Runtime and source identities are recorded; elapsed/RSS values are measurements, not deterministic bytes.

Pinned checkpoint: `autogluon/chronos-2-small@ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a`, model-card Apache-2.0. Weights SHA-256 `492290ae82bb89f9769e3479ce90b3179de1f33e600c34daa0352531538b23cd`; config `f2780468adc8b16322aa0b6e28b26476c9401ecf64ab53292b6d2b0d3f423722`. Same CPU float32/eval/seed42, 2 intra-op and 1 inter-op thread, batch1, no cross-learning, q10/q50/q90, 90-context/90-output settings. Python 3.12.3, Chronos 2.3.2, Torch 2.11.0+cpu, Transformers 4.57.6, NumPy 2.4.4 and pandas 3.0.2; existing isolated environment and locks reused.

Reproduce **diagnostics only**, from the working project, with a new output directory. This command is pinned to the published study and exactly its 12 failure identities; it rejects other studies before model loading. The parent uses the existing external CPU/resource supervisor. It never calls `evaluate-chronos` or opens numerical label files.

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp.chronos_diagnostics \
  --benchmark /home/hp/tst/research/forecasting_mvp/phase4_2/2026-10-15/run-004 \
  --checkpoint /home/hp/tst/research/forecasting_mvp/model_cache/chronos-2-small/ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a \
  --runtime-python /home/hp/tst/td_pipeline_module_level/td_pipeline/.venv-chronos-cpu/bin/python \
  --out /absolute/new-phase4_2_1-diagnostic-run
```

The above command uses shell continuation backslashes between lines. Expected exit 0/PASS. A non-reproduced crossing, raw repeat mismatch, contract failure, changed input/checkpoint or resource violation blocks diagnostics without replacing the experiment. No full benchmark command was executed in this phase.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_forecasting_mvp_phase4_1.py tests/test_forecasting_mvp_phase4_2.py tests/test_forecasting_mvp_phase4_2_1.py
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests -k 'not test_actual_catboost_models_shared_folds_predictions_and_purging'
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp verify-bundle --bundle examples/phase4_2_1
```

## Tests, changed files and publication

- **26 new checks** cover typed recovery versus fatal exception classes, malformed output, identity/timestamp/nonfinite precedence after an earlier crossing, repeat failures, unchanged valid output calculations, fatal late failure without partial publication, top-level exit3, analytical crossing magnitudes/steps/endpoints, capture invariance, input summaries, descriptive published-metric arithmetic and diagnostic scope admission.
- Focused Phase 4.1/4.2/4.2.1 suite: **58 passed**.
- Complete permitted publication-checkout regression: **336 passed, 1 deselected**, no failures. The excluded legacy test trains actual CatBoost models and remains prohibited.
- Working checkout regression after explicit source synchronization: **336 passed, 1 deselected**, no failures; recorded in `working_regression_tests.xml`.
- Tests use synthetic engines/fixtures; the real model executed only the 24 bounded diagnostic calls above. No full test-cohort inference occurred.

Changed source: `forecasting_mvp/chronos_adapter.py`, `forecasting_mvp/chronos_eval_worker.py`; new `forecasting_mvp/chronos_diagnostics.py` and `tests/test_forecasting_mvp_phase4_2_1.py`. Root/package README and `GITHUB_SYNC.md` document the new stop boundary. This report and small attributed evidence are new files. No other implementation module, dependency file or old report/result was changed.

Local diagnostic bundle: `/home/hp/tst/research/forecasting_mvp/phase4_2_1/2026-10-15/run-001`.
Published `examples/phase4_2_1/` contains all raw diagnostic paths (2,160 rows = 12 × 2 × 90), exact past-only failed-context requests, all failure summaries with 36 endpoint values, published-interval descriptive tables, resource measurements, source/model identities, source-precision arithmetic, preservation receipts, regression XML and a published-evidence manifest. Its `diagnostic_worker_manifest.json` preserves the original worker manifest covering the four byte-identical worker result files; the evidence root gets its own manifest for all published files. Existing Phase 4.2 files and manifests are untouched.

Publication follows the existing two-checkout procedure: inspect/fetch remote history, preserve unrelated local work and remote content, normal descendant commit and push to central `main`, verify remote commit and each published changed file. The original working `main` is not reset or pushed over central history; only its `github-main` tracking reference advances. No force push, model weights, environments, full historical datasets or secrets are published.

## Decision

Diagnostic hardening **PASS**: all requested failures explained at the raw-output/contract level, targeted error recovery, fatal runtime/software failures, reproducibility and identity protections verified, interval limitations analyzed descriptively, and original experiment preserved. Underlying model crossings and empirical undercoverage remain unresolved research limitations. They are not silently corrected by this phase.

Any future change to tolerance, selected-step acceptance, precision, normalization or interval calibration requires a separately specified validation-only study with new evaluation protection. None was implemented or selected here. Stop after verified GitHub publication; no benchmark replacement, new forecasting experiment or dashboard phase is authorized.
