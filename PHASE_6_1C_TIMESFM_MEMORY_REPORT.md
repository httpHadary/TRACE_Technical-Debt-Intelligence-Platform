# Phase 6.1C — TimesFM low-memory feasibility

**PARTIAL — low-memory loading succeeded; the native smoke path failed quantile
ordering.** After static verification and separate explicit approval, one worker
loaded all 232 exact tensors and returned one finite native 90-step forecast.
Observed peak RSS was approximately **1.19 GiB**, below the unchanged 1.75 GiB
guard and 2 GiB ceiling. However, all 90 steps had an adjacent-decile crossing.
No valid full-decile path was accepted, and the remaining 35 cases were not run.

Prepared 2026-10-19; completed/reviewed 2026-10-20, Africa/Cairo client dates.
Starting main:
`e0f3e6feb4cbe1386bc8723a4dbfd23492efeb9a`.
The Phase 6.1B report, handoff, adapters, original source/runtime manifests and
failed TimesFM receipt were reviewed. Its PARTIAL result remains unchanged.

## Allocation diagnosis

The pinned constructor creates the CPU parameter bank before loading weights.
Its `load_checkpoint` calls `safetensors.torch.load_file`, then
`load_state_dict(tensors, strict=True)` with default `assign=False`, and finally
CPU `.to()`/eval. Installed safetensors 0.8.0 **already defaults to mmap**; merely
enabling mmap would not resolve the duplicate parameter bank.

The checkpoint contains **232 float32 tensors / 231,289,280 elements /
925,157,120 parameter bytes**. Its complete file is 925,181,104 bytes. The existing
path can hold approximately 1,850,314,240 tensor-data bytes across initialized
parameters and mapped checkpoint pages while copying, before Python, Torch,
libraries, allocator overhead or activations. State-dictionary Python containers
are separate from their large backing storage. Initialization also touches the
destination pages and discards its values once checkpoint copying occurs.

This is an evidence-backed explanation, not a measured allocation trace. Phase
6.1B recorded only MODEL_LOADING, then a sampled 1,923,653,632-byte RSS peak and
guard kill; it did not identify the precise allocating operation. It produced
zero forecasts and no final kernel peak. It did not prove a universal 2 GiB
incompatibility. Inference working memory remains unmeasured for this model.

The pinned source is [TimesFM code commit e51928e](https://github.com/google-research/timesfm/blob/e51928e27119cb17bebc005be2696b75e0a9e688/src/timesfm/timesfm_2p5/timesfm_2p5_torch.py).
The selected checkpoint remains **google/timesfm-2.5-200m-pytorch** revision
`1d952420fba87f3c6dee4f240de0f1a0fbc790e3`, SHA256
`2f776efe6245e42b24bc4153ffdf61810140210e4bd3b01fb21f7aa779ab6ce8`.
Source package version 3.0.2 retains the explicit 2.5 class; no 3.0 weights/API
are substituted. Existing Apache-2.0 evidence does not grant analyzer-data rights.

## Supported loading design

Installed Torch **2.11.0+cpu** supports metadata-only initialization and strict
assignment of state tensors. The version-specific documentation explains the
[meta device](https://docs.pytorch.org/docs/2.11/meta.html) and
[`load_state_dict(assign=True)`](https://docs.pytorch.org/docs/2.11/generated/torch.nn.Module.html#torch.nn.Module.load_state_dict).
The installed implementation and docstrings were inspected and hashed rather
than assuming the latest online tutorial matches the local runtime.

New `forecasting_research/phase6_1c/loader.py` proposes:

1. Construct the original 2.5 architecture under `torch.device('meta')`.
2. Map the exact existing checkpoint using CPU float32 safetensors mmap.
3. Verify exact keys, shapes, dtypes and absence of unexpected buffers.
4. Assign mapped tensors with `strict=True, assign=True`.
5. Require matching storage pointers and per-tensor content hashes.
6. Reuse original eval/forecast code and unrepaired native quantiles.

The [safetensors API](https://huggingface.co/docs/safetensors/api/torch) is checked
against installed 0.8.0 source. No checkpoint conversion or new dependency is
needed. Assignment preserves module requires-grad properties; this inference-only
path creates no optimizer. Unexpected buffers or residual meta tensors fail closed.
No dtype reduction, quantization, dropped quantile head, architecture change,
manual value transformation or new tensor version is accepted.

`torch.load(mmap=True)` is for Torch serialization, not a reason to reinterpret
the safetensors file. `to_empty()` would allocate another destination bank and is
not selected. Changing backend, patching native forecasting, raising the guard or
altering pretrained weights is outside this proposal. The intended saving is
avoiding one approximately 882.3 MiB destination bank; actual RSS is still UNKNOWN.

## Static parameter and identity verification

The inspector performs no TimesFM import, architecture construction or forward.
It parses only allowlisted literal configuration expressions from the pinned
source and independently derives the dense/transformer parameter mapping:
six tokenizer tensors, 11 per transformer × 20 layers, and six output-head tensors.
All 232 names, shapes and F32 types match the checkpoint exactly.

Header/storage checks reject duplicate keys, missing/unexpected tensors, invalid
extents, gaps/overlaps, trailing data, symlinks and mismatched file hashes. Bounded
1 MiB streaming checks verified all stored values finite, full-file SHA256 and
per-tensor SHA256. All 16 pinned TimesFM source files and 22,397 existing dependency
files were rehashed against their unchanged manifests. The static audit reproduces
deterministically; no weights were edited, cloned, converted or downloaded.

Tiny toy Linear modules test the installed meta/mmap/assign API, exact storage
sharing, unchanged values and equal toy outputs. Negative cases reject incorrect
keys/shapes/types/hashes, real CPU destination parameters and unexpected buffers.
These tests do not validate full TimesFM construction, mapping or forecast RSS;
the native loader must independently recheck those after approval.

## Registered conditional attempt and approval boundary

The separate registration binds new source hashes, the audit, original Phase 6.1B
requests and sealed prediction identities. It is explicitly **NOT approval**.
The planned smoke case is the original increasing synthetic case, with 512 genuine
past daily positions and a direct 90-step request. Settings match Phase 6.1B:
CPU float32, normalization and continuous quantile head enabled, flip/positivity
repair disabled, `fix_quantile_crossing=False`, no training or JIT compilation.

The native entry point refuses missing, unscoped or mismatched approval before
claim creation or subprocess startup. Approval must identify this exact sealed
registration, one attempt, scope and unchanged budgets. Old acquisition approval
does not authorize this execution. No approval is synthesized by software/tests.

Limits remain **2 GiB RSS**, **1.75 GiB guard**, **900 seconds**, two numerical
threads, CPU only, no network/downloads and bounded logs/artifacts. A 5 ms RSS/HWM
monitor provides finer observations than Phase 6.1B; it is still not hard cgroup
enforcement. Immediate exit, missing memory observations, timeout and limits retain
explicit evidence. Missing memory values remain unavailable. No automatic retry.

If separately approved for the conditional comparison, the same worker first
tests the smoke case and only then the remaining 35 original cases. It reuses
the first prediction rather than repeating it. It seals outputs before evaluator
truth access, reuses original sealed Chronos/TTM/baseline forecasts, and reports
failures plus identical-success metrics. This exposed synthetic cohort is not a
fresh confirmatory test. No Chronos, TTM or historical forecasting study is rerun.

## Separately approved native attempt

The operator explicitly approved one worker and the conditional 36-case comparison
for registration SHA256
`6cde20fee48ce7f1eb940556dc7e85c90739f258c95561efda59f0e057ce47d6`.
Approval was recorded only after the static audit, toy tests and registration.
The former Phase 6.1B acquisition permission was not reused as run authorization.
The full regression and preservation checks completed before native launch.

Exactly one TimesFM worker ran, with one model load and one smoke call. No further
dependency/checkpoint acquisition, limit change, alternative loader or retry occurred.
The original Phase 6.1B attempt, all earlier forecasts and all pretrained bytes
remain unchanged.

Native loading took **1.210556 seconds**. All 232 model state tensors matched the
registered keys/shapes, CPU float32 types, checkpoint content hashes and mapped
storage pointers. The actual constructor on meta succeeded, and no unexpected
buffers or residual meta parameters were accepted. Native source files and the
original forward/configuration were not patched.

The unchanged native API accepted the generated 512-position input and returned
finite point/quantile arrays of shapes [1,90] and [1,90,10]. The recorded internal
horizon capacity was128 after original patch rounding; requested output was90.
The original adapter rejected its full native decile path without repair:

- All90 forecast steps contained a crossing among adjacent q10–q90 deciles.
- There were264 adjacent-decile violations. Largest magnitude was0.978806
  synthetic minutes at step53, between q10 and q20.
- Selected q10/q50/q90 trios at days30,60,90 were ordered, but this does not
  override the registered requirement that **all nine deciles at every step**
  be ordered. No endpoint exception or post-outcome point-only policy was added.
- The raw path, request identity and smoke seal were preserved. A small endpoint
  sample is explicitly labeled INVALID_NATIVE_PATH_DIAGNOSTIC_ONLY.

The worker then raised `NATIVE_SMOKE_INVALID; no further calls`. Its original
execution receipt remains BLOCKED_RUNTIME / exit1. The scientific overall result
is **PARTIAL**, distinguishing successful memory/loading feasibility from a failed
forecast-contract gate. This was not another loading-resource failure.

The supervisor observed RSS and `/proc` kernel high-water values up to
**1,276,624,896 bytes (1217.484MiB / 1.189GiB)**, below the unchanged guard.
Total supervised wall time was5.582101 seconds. This observed peak is lower than
Phase 6.1B's1834.539MiB guard-stop observation, but the runs terminated at
different stages; this is not a controlled measurement of exact bytes saved.

The process aborted before writing its final resource/timing receipt. Therefore
exact inference duration, final `ru_maxrss`, final runtime-thread readback and
post-inference in-memory parameter hashes are **UNAVAILABLE**. They are not
estimated by subtracting load time from total wall time. The observer's high-water
sample is reported as observed, not hard-cgroup proof. Pre-inference tensor hashes
and independent post-run checkpoint/source preservation are verified. Missing
capture and invalid native intervals prevent a full PASS.

## Outcome, verification and handoff

No full36-case TimesFM benchmark or matched comparison was executed because the
smoke condition failed. TimesFM has no accepted comparable MAE/RMSE/coverage here.
The finite median of one rejected smoke path is not promoted to a benchmark.
No historical or synthetic Chronos/TTM/baseline inference was rerun.

**42 new tests passed:**34 static/protocol/supervision tests and eight tiny
assignment tests. Full allowlisted regressions passed **1,446 +14 tests in the
working checkout and1,384 +14 in canonical main**, zero failures/errors/skips.
The fourteen toy/fake-backend tests include six pre-existing adapter checks and
eight new assignment checks; none executes TimesFM. Non-allowlisted legacy
training, real-benchmark replay and historical-execution suites were excluded.

Static audit reproduction took2.807191 seconds and36,548,608 bytes peak process
RSS under a1GiB address-space cap. Its232-tensor mapping/hash/finiteness result
was byte-deterministic. This static measurement is separate from native RSS.

Preservation verifies922 pre-existing working files,1010 canonical files,
19,209 earlier private-task files,150 Phase6.0 files,34 Phase6.1A files and198
Phase6.1B private files,56 frozen bundles/322 artifacts, both Phase5.1 bundles,
database/checkpoint identities, prior cache/ledger/claim evidence and22,397
original dependency files. Payloads were stream-hashed as opaque bytes; no raw
historical labels were reopened. No Docker/server/volume operation was performed;
live-volume byte preservation is not claimed.

The user's additional accuracy-summary request was answered from existing small
published aggregate records only. See [benchmark error tables](BENCHMARK_ACCURACY_SUMMARY.md)
and the42-row CSV/source-hash receipt. Relative skill is percentage MAE reduction
against persistence, never classification-style accuracy. Historical and synthetic
results, repository-macro and pooled statistics stay separate. This calculation
adds no new benchmark and does not change previous results.

Preservation/regression receipts and the [Phase6.2 handoff](PHASE_6_2_RESEARCH_HANDOFF.md) accompany publication.
All original studies, model files, Java compilation archives, datasets, database,
caches, claims and Phase C decisions remain protected. All 24 permission decisions
remain NOT_APPROVED. No SonarQube, Maven, historical collection, real-data training,
dashboard or dataset admission is authorized or performed. **STOP after Phase6.1C
publication.** A future point-only protocol, quantile diagnostics or new attempt
requires separate review/authorization; no guard increase or hidden repair follows.
