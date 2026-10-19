# Phase 6.0 synthetic forecasting research

This package is separate from `forecasting_mvp`, schema-v2 studies and the internal
UX demo. It accepts **SYNTHETIC_ENGINEERING_TEST** requests only. Nothing here
admits analyzer output, real repository data, historical labels or a new study.
No real-data loader, training command, external model downloader or service exists.
Synthetic values model the original estimand, estimated maintainability remediation
minutes; they are invented numbers, not actual analyzer measurements or repair labor.

## Run with existing environments

From `/home/hp/tst/td_pipeline_module_level/td_pipeline`:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_research.phase6_0 baselines \
  --out /home/hp/tst/research/forecasting_mvp/phase6_0/2026-10-19/new-synthetic-baselines

# Only the already pinned local checkpoint/environment; no installation/download.
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_research.phase6_0 chronos-synthetic \
  --out /home/hp/tst/research/forecasting_mvp/phase6_0/2026-10-19/new-synthetic-chronos

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_phase6_0_research.py
```

Choose a genuinely new output name. Paths are confined to the external Phase 6.0
research root; symlinks/existing directories are rejected. Worker execution has an
exclusive claim. There is no input-path, real-data mode, checkpoint fallback or
candidate auto-download. If runtime admission fails, receipts say BLOCKED_RUNTIME
and the command exits nonzero. Do not use this command to rerun the Java benchmark.
A checkout without the existing `.venv-chronos-cpu` cannot infer; no installation
is attempted. New environment/checkpoint acquisition requires separate authorization.

## Interfaces

- `Request.from_dict`: exact allowlisted fields, immutable copied tuples, UTC
  chronology, explicit null/reason, finite nonnegative past stock, fixed30/60/90
  horizons and synthetic status. Case IDs are opaque; scenario/mechanism/future
  truth remain in evaluator-side `Case`, never the model payload.
- `baseline`: persistence, fixed7-day rolling mean and90-day anchored OLS trend.
  Complete daily contexts reuse original baseline functions at scored endpoints.
  Sparse/irregular alternatives use actual observed timestamps, with insufficient
  windows reported as failures; no interpolation, padding, implicit measured zeros
  or last-value carry. An unknown origin cannot support persistence.
- `chronos.predict`: bridges only complete90-day synthetic requests to the original
  immutable typed request and unchanged CPU adapter. The bridge is not historical
  provenance or an admission decision. Full native-path quantile crossing is an
  explicit failure with diagnostics; no sorting or persistence fallback.
- `response`/`validate_response`:90 exact future daily timestamps, finite raw outputs,
  request/model identity, q10≤q50≤q90, nativeq50 point policy and explicit nonnegative
  stock clipping. Raw negative values remain visible. Baseline intervals are null.
- `score`: evaluator-only access to generated truth after prediction sealing.
  Complete attempted populations include identity-bound failures. Matched success
  populations are reported separately. See the benchmark report for metric meanings.
- `registry.compatible`: documented API compatibility is not runtime permission.
  Only Chronos may execute. Granite/TimesFM need separate acquisition and runtime
  admission; short-horizon or unverified branches are rejected.
- `change_features`, `reconstruct`, `blend`, `gate`: mathematical interfaces only.
  No classifier or weights were fitted. Gapped observations retain censoring.

The contract boundary prevents accidental future/label access, not arbitrary
hostile Python introspection. The actual pretrained worker also denies networking
with Linux x86_64 seccomp, verifies that a socket fails, pins runtime/checkpoint,
restricts numerical threads/CPU affinity, disables CUDA and monitors worker RSS/wall
clock. The2GiB memory guard samples every20ms plus final `ru_maxrss`; it is **not a
cgroup hard quota** and sampling cannot exclude a brief overshoot. Actual observed
runs stayed far below the ceiling. Outputs/logs are bounded; no worker children or
model-loading services are launched. Timing/RSS are measured, not byte-deterministic.

`source_identity.json`, registration, prediction seal, evaluation and final SHA256
manifest support replay. Compare predictions separately from nondeterministic
runtime fields. Historical summary arithmetic is a separate explicit function,
`summary_audit.audit(output_path)`, restricted to two published small summary CSVs;
it does not form inputs for synthetic predictors.

See [research report](../../PHASE_6_0_FORECASTING_RESEARCH_REPORT.md),
[compatibility](../../PRETRAINED_MODEL_COMPATIBILITY_MATRIX.md),
[benchmark](../../SYNTHETIC_FORECASTING_BENCHMARK_REPORT.md) and
[Phase 6.1 handoff](../../PHASE_6_1_HANDOFF.md).
