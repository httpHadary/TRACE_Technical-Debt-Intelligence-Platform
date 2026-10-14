# TechDebt360 MVP — Phase 4.1 Chronos-2 CPU Runtime & Smoke Test

Date: 2026-10-14. Project: `/home/hp/tst/td_pipeline_module_level/td_pipeline`.

**Phase 4.1 PASS: successful bounded real CPU inference.** The pinned runtime and
adapter are ready for a separately authorized full evaluation. Predictive accuracy,
interval calibration and technical-debt generalization remain **unmeasured**.
No final benchmark, test-cohort inference, CatBoost, Granite or dashboard ran.

## Completed work and changed files

- `forecasting_mvp/chronos_adapter.py`: immutable checkpoint/config hash admission,
  CPU float32 loading, strict admitted past-only input, native daily quantile path,
  exact UTC timestamp/shape checks, q50 point and raw/nonnegative stock outputs.
- `forecasting_mvp/chronos_smoke.py`: deterministic six-cell training/validation
  selection, frozen request publication and fixed-process timeout/RSS supervisor.
- `forecasting_mvp/chronos_smoke_worker.py`: offline worker, all-input validation
  before loading, pinned version checks, duplicate inference and small sealed results.
- `forecasting_mvp/cli.py`: additive `prepare-chronos-smoke` and `chronos-smoke` only.
- `requirements-chronos-cpu.txt`, `requirements-chronos-cpu-lock.txt`: new standalone
  direct requirements and complete 32-package runtime freeze. All old locks preserved.
- `tests/test_forecasting_mvp_phase4_1.py`: 19 new checks with fake engines and
  software-only child processes. Real checkpoint execution is the separate smoke.
- Root/package README, `GITHUB_SYNC.md`, this report and small evidence under
  `examples/phase4_1/`. No unrelated source or Phase 3 baseline algorithm changed.

## Checkpoint, license and runtime admission

The existing Phase 0 registration selects
`autogluon/chronos-2-small@ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a`.
The official pinned model metadata resolves exactly that revision and declares
**Apache-2.0**; this is model-card licensing evidence. The adapter accepts only
that registered revision, its pinned config and pinned safetensors digest.
[Official pinned checkpoint](https://huggingface.co/autogluon/chronos-2-small/tree/ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a).

- Safetensors: **111,749,048 bytes**, SHA-256
  `492290ae82bb89f9769e3479ce90b3179de1f33e600c34daa0352531538b23cd`.
- Config SHA-256:
  `f2780468adc8b16322aa0b6e28b26476c9401ecf64ab53292b6d2b0d3f423722`.
- Actual loaded parameter count: **27,934,624**.
- Native config context capacity 8192; native output capacity 1024 (64×16).
  This study supplies only 90 past points and requests 90 daily steps.
- q10/q50/q90 are native configured quantiles. The median, not a renamed generic
  mean, supplies point forecasts. Nominal q10–q90 coverage is not measured here.

Chronos 2.3.2 metadata admits Python≥3.10, Torch≥2.2,<3, Transformers≥4.41,<6,
NumPy≥1.21,<3 and pandas≥2,<4. We installed the **base** package without extras.
[Release metadata](https://pypi.org/project/chronos-forecasting/2.3.2/),
[upstream package requirements](https://github.com/amazon-science/chronos-forecasting/blob/1224fafa91e1ecd6674f5204066b159e40b5e4a1/pyproject.toml).
The downloaded package wheel SHA-256 was
`0f0d9a1972f252d6cf584b9fa749bd1b389b3c1cf05a889c4130cb10652c2117`.

Isolated environment:
`/home/hp/tst/td_pipeline_module_level/td_pipeline/.venv-chronos-cpu`.
Python 3.12.3, Torch **2.11.0+cpu**, Chronos **2.3.2**, Transformers **4.57.6**,
NumPy **2.4.4**, pandas **3.0.2**; accelerate 1.15.0. `uv pip check` passes.
`pyvenv.cfg` records `include-system-site-packages = false`; no user/system package
inheritance. Torch reports no compiled CUDA version and no available CUDA device.
All five numerical/model versions are checked before model loading.

Only the new venv and local model cache were installed. Existing `.venv-forecast`,
all four prior requirements files, dataset/split manifests and Phase 3 result bytes
remain unchanged. Existing tests run using the original environment.

## Hardware and bounded resource results

Host: AMD Ryzen 5 PRO 5650U, 12 logical CPUs, about 14.9 GiB physical RAM.
A verification snapshot recorded 6.94 GiB available RAM,
23.24 GiB free disk and only
315 MiB free swap. These are snapshots,
not guaranteed ongoing capacity. New venv footprint is about 940 MiB; checkpoint
weights about 107 MiB. No GPU is needed for the demonstrated smoke.

Fixed admission limits: **900 seconds** whole worker wall clock and **2 GiB RSS**.
The supervisor samples Linux `/proc` every 0.1 second and kills the worker process
group on a limit breach. Its worker has offline HF/Transformers settings, empty
CUDA visibility and 2-thread OMP/MKL/OpenBLAS limits. Torch uses two intra-op and
one inter-op thread. The current worker creates no data-loader child processes;
RSS observation is of that worker, not a hardened container memory quota.

Final successful run:

| Measurement | Actual |
|---|---:|
| Supervisor wall time | 5.219 seconds |
| Worker model-load time | 3.623 seconds |
| Worker elapsed before final serialization | 4.333 seconds |
| Supervisor sampled peak RSS | 467.58 MiB |
| Worker reported peak RSS | 477,764 KiB |
| Contexts / unique endpoints | 6 / 18 |
| Inference requests (including repeat checks) | 12 |
| Saved native daily path rows | 540 |
| Limit breaches / model failures | 0 / 0 |

These timings include a small cold-loaded CPU smoke, not measured full-cohort
throughput, deployment latency, or a forecast accuracy benchmark.

## Predefined sample and no test access

Selection was frozen before successful inference in
`research/forecasting_mvp/phase4_1/2026-10-14/requests-001`, under `/home/hp/tst/`.
The policy has six fixed cells: train/validation × constant/positive-past-trend/
negative-past-trend. Constant means zero past standard deviation; increasing or
decreasing refers to the **past 90-day OLS slope**, not strict monotonicity or any
future outcome. Constants choose fewest distinct scans; moving cells choose most;
ties use the original context hash. All three horizon IDs must exist in the same
allowed phase. No thresholds or samples were revised after model outputs.

| Phase | Past pattern | Source project | Origin UTC | Distinct scans | Distinct debt values | Current minutes |
|---|---|---|---|---:|---:|---:|
| train | constant | org.apache:beanutils | 2012-01-02T00:00:00Z | 1 | 1 | 52416 |
| train | decreasing | org.apache:configuration | 2013-04-15T00:00:00Z | 38 | 29 | 33580 |
| train | increasing | org.apache:configuration | 2013-02-04T00:00:00Z | 50 | 38 | 37490 |
| validation | constant | org.apache:commons-jelly | 2015-03-09T00:00:00Z | 1 | 1 | 42212 |
| validation | decreasing | org.apache:configuration | 2014-10-06T00:00:00Z | 22 | 12 | 38729 |
| validation | increasing | org.apache:net | 2015-02-16T00:00:00Z | 28 | 16 | 28375 |

Source names are recovered from Git metadata only. The six smoke contexts contain
only measured past stock and timestamps; all pass `admit_prediction_input` before
model loading. Known measurement times must be at or before each daily point.
The worker receives a standalone request bundle, not any history, combined dataset,
evaluation-label file or complete context store. It rejects held repositories,
test/unknown roles, unregistered IDs, future references, target columns and 91-day
horizons. Original source, context, forecast and split identities remain intact.

Preparing requests hashes original label files for integrity but never loads
numerical evaluation labels. Only past feature summaries and frozen assignments
route the sample. **Zero test IDs inferred, zero labels opened, no accuracy scored.**
Previously reported Phase 3 errors were reviewed but did not change the registered
checkpoint, sample selection, quantiles or inference options.

## Output, units, nonnegative policy and determinism

Each single-series DataFrame has only ID, timestamp and target stock. There are
no future covariates, repository/classifier scores or other origins in model input;
`cross_learning=False`, batch size 1, context length 90. Stock values are raw
Sonar `SQALE_INDEX` estimated maintainability remediation minutes. The model's
internal scaling is undone by its pipeline; this adapter adds no unit conversion.
These are not actual developer repair hours or classification probabilities.

Every returned frame must have **90 rows × 7 columns**, one series/target, finite
native q10/q50/q90, ordered quantiles and exact daily timestamps from origin+1 to
origin+90. Endpoint indices **29/59/89** map to exact 30/60/90-day targets. No
weekly 91-day substitution, interpolation or renamed quantile levels occurs.

All three quantiles keep raw outputs and apply the preregistered `max(0, raw)`
stock policy. The actual sample produced no negative path quantiles and no
crossings; negative-output clipping is proven by fake-engine unit tests, not
claimed as observed in these six positive-stock cases. Native q10/q90 constitute
an uncalibrated nominal 80% range, not a validated prediction interval.

The model is eval-mode CPU float32, seed 42, deterministic Torch algorithms.
Two predictions per context in one worker matched **exactly**, maximum difference
0.0. After completing the five-package version guard, a fresh worker reproduced
both CSVs byte-for-byte on the identical frozen sample. This is evidence for this
pinned CPU/host; no cross-hardware or future-version determinism guarantee.
Request preparation was also repeated with all three request files byte-identical.
Resource timings/summaries naturally differ and are not asserted byte-identical.

## Confirmed compatibility fix and failure handling

The first attempt (`run-001`) loaded the checkpoint but stopped before model
forward execution. Chronos 2.3.2 `df_utils.normalize_df` uses
`df[timestamp_column].to_numpy().view("int64")`; timezone-aware pandas timestamps
produce an object array, raising `TypeError: Cannot change data-type for array of
references`. A preprocessing-only reproducer proved the failure with aware UTC
and reached the model-call boundary with UTC-naive nanosecond timestamps.

The adapter now converts **already verified UTC times** to UTC-naive
`datetime64[ns]` only at the model DataFrame edge, preserving wall-clock values.
It explicitly restores UTC on output and checks every returned cutoff. No stored
historical timestamp, dataset label or split changed. The final runtime retains
pandas 3.0.2; this is a narrow adapter fix, not a dependency downgrade or profile
repair. The dtype argument also uses the supported `dtype` spelling.

Failures produce typed worker/resource JSON and logs, exit 3 and no COMPLETE
success manifest. Missing patterns fail without reselection. Wrong checkpoints,
package drift, malformed shape/identity/times, nonfinite values, quantile crossings
and changed inputs/code fail closed. Timeout, memory breach and child failure have
explicit software tests. No silent fallback forecasts or fabricated outputs.

## Tests, artifacts and commands

Publication-checkout regression suite: **297 passed, 0 failed, 1 deselected**.
The single excluded legacy test trains CatBoost. Nineteen new software checks
cover exact horizons, UTC conversion, point quantile choice, shapes, clipping,
future/target rejection, test/held roles, runtime drift, pins and supervisor failure
paths. Existing Phases 0–3 functionality remains compatible. The original project
also passed the full allowed suite: 297 passed, 1 deselected in 31.91 seconds.

Final complete smoke:
`/home/hp/tst/research/forecasting_mvp/phase4_1/2026-10-14/run-003`.
Earlier successful `run-002` supplies the fresh-worker numerical comparison;
`run-001` is blocked diagnostic evidence, not a successful forecast result.
Published small evidence mirrors `requests/` and `results/` bundles plus runtime,
checkpoint, preservation, resource and test receipts. No weights, environments,
full datasets, secrets or full benchmark results are uploaded.

Actual initial installation command used uv 0.11.29:

```bash
uv venv --python /usr/bin/python3 .venv-chronos-cpu
uv pip install --python .venv-chronos-cpu/bin/python \
  --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match \
  'torch==2.11.0+cpu' 'chronos-forecasting==2.3.2' 'transformers==4.57.6' \
  'numpy==2.4.4' 'pandas==3.0.2'
uv pip check --python .venv-chronos-cpu/bin/python
```

The new full lock recreates the observed transitive versions on compatible Linux
Python 3.12; use it in a **new** isolated environment instead of changing old locks:

```bash
uv pip install --python .venv-chronos-cpu/bin/python --index-strategy unsafe-best-match \
  -r requirements-chronos-cpu-lock.txt
```

Download only the registered model files and verify them (choose a local ignored
cache path; there is no download during offline inference):

```bash
HF_HUB_DISABLE_XET=1 .venv-chronos-cpu/bin/python - <<'PY_DOWNLOAD'
from pathlib import Path
import shutil
from huggingface_hub import snapshot_download
from forecasting_mvp.chronos_adapter import MODEL_ID, REVISION, verify_checkpoint
checkpoint = Path('model_cache/chronos-2-small') / REVISION
snapshot_download(MODEL_ID, revision=REVISION, local_dir=checkpoint,
                  allow_patterns=['README.md', 'config.json', 'model.safetensors'],
                  token=False, max_workers=1)
shutil.copy2('examples/phase4_1/checkpoint_admission.json', checkpoint / 'checkpoint_admission.json')
verify_checkpoint(checkpoint)
PY_DOWNLOAD
```

To reproduce the actual full-data selection, use **new** output paths:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp prepare-chronos-smoke \
  --bundle /home/hp/tst/research/forecasting_mvp/phase2/2026-10-14/run-003 \
  --history-bundle /home/hp/tst/research/forecasting_mvp/phase1/2026-10-14/run-002 \
  --baseline-bundle /home/hp/tst/research/forecasting_mvp/phase3/2026-10-14/run-002 \
  --out /home/hp/tst/research/forecasting_mvp/phase4_1/2026-10-14/new-requests

PYTHONDONTWRITEBYTECODE=1 .venv-chronos-cpu/bin/python -m forecasting_mvp chronos-smoke \
  --requests-bundle /home/hp/tst/research/forecasting_mvp/phase4_1/2026-10-14/new-requests \
  --checkpoint /home/hp/tst/research/forecasting_mvp/model_cache/chronos-2-small/ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a \
  --out /home/hp/tst/research/forecasting_mvp/phase4_1/2026-10-14/new-smoke

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests \
  -k 'not test_actual_catboost_models_shared_folds_predictions_and_purging'
```

For a small independent smoke replay, replace `--requests-bundle` with the
published `examples/phase4_1/requests`; no database, test labels or complete
history is needed. This does not authorize new phases or a benchmark.

## Readiness and stop decision

**Runtime readiness PASS.** No remaining installation, checkpoint loading, shape,
CPU resource or deterministic-repeat blocker was found in the registered smoke.
A full model evaluation still needs separate authorization and its own sealed
validation/test prediction workflow. Runtime success does not prove Chronos
outperforms persistence or supports calibrated technical-debt uncertainty.

Existing scientific limitations persist: incomplete analyzer/rules/build history,
imported branch/measurement availability approximation, repeated observations,
overlapping horizons, selected old Java cohorts and only six held repositories.
No such evidence is repaired or made stronger by loading a foundation model.
Preserve all frozen IDs, Phase 3 results and native quantile/raw-clipping semantics
in any later authorized comparison. Do not tune using test outcomes.

Normal descendant GitHub publication preserves prior remote content and original
working history; final commit SHA/file accessibility are verified at completion.

**STOP after Phase 4.1 verification and publication.**
