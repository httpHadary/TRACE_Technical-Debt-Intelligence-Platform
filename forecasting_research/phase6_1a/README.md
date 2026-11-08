# Controlled Chronos context study v1

Synthetic engineering only. This is a **new** population and adapter, not a replay
of Phase 6.0 or the Java benchmark. All original implementations/results remain
unchanged. No other model, training, scanner or real-data loader is included.

From `/home/hp/tst/td_pipeline_module_level/td_pipeline`, using existing environments:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_phase6_1a_context.py
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_research.phase6_1a prepare \
  --out /home/hp/tst/research/forecasting_mvp/phase6_1a/2026-10-19/new-registered-study
# Review registration.json and its seal before explicitly running the study.
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_research.phase6_1a run \
  --study /home/hp/tst/research/forecasting_mvp/phase6_1a/2026-10-19/new-registered-study
# Recompute published paired metrics using only packaged synthetic endpoints:
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_research.phase6_1a reproduce
```

A fresh path is mandatory; attempts are exclusive and consumed even on resource
rejection. The prepared registration binds sources, installed API files, checkpoint,
runtime, all 42 generated cases, six exclusions, requests, horizons and policies.
No parameter grid, automatic retry, outcome-dependent selection or download exists.
The `run` command starts exactly one offline CPU worker. A missing pinned runtime,
insufficient resources or failed worker yields a typed blocked receipt, not new
limits or a fallback. A new run still requires authorization; these commands do
not authorize subsequent phases.

`population.py` defines 512 generated daily historical observations and separate
future and observation-mask RNG streams. Sparse/irregular cases retain their
original observations and are excluded from **all five methods**. Eligible short
contexts are exact final90 suffixes of long contexts; origins and future targets
are shared. Case IDs are opaque. Prediction functions receive only immutable
past-only `Request` values using the existing synthetic display-independent
contract, estimated-remediation-minute unit and SYNTHETIC_ENGINEERING_TEST status.
Scenario names/seeds/future generation are not model payloads. This boundary
protects against accidental leakage, not hostile Python introspection.

`ContextAdapter` is a new adapter accepting only90/512 complete regular daily
histories and producing90 native future steps. It uses the unchanged pinned loader,
CPU float32, q10/q50/q90, native q50 point, exact UTC endpoints and raw-plus-clipped
nonnegative stock. One full-path crossing rejects that whole native path; raw
invalid paths and steps remain explicit. Later identity/finiteness errors are
fatal and cannot be hidden by an early crossing. No sorting, tolerance, repair,
interval recalibration or persistence fallback is allowed.

A read-only forward hook requires the actual model context to match all90/512
registered float32 observations exactly and forbids future targets. Native location/
scale are observed without changing the result. UTC-naive nanosecond conversion
is confined to the pandas/model edge. Native instance normalization and arcsinh
are unchanged, but their statistics naturally differ by supplied context. Internal
masked patch alignment is not fabricated observed history. No external zero padding,
upsampling, interpolation, normalization fitting or future covariate is added.

Baselines use the common final90 history: persistence, fixed7-day mean, and fixed
90-day anchored OLS. Their parameters and eligible populations are frozen before
inference. This study does not compare an arbitrary512-day baseline window against
90-day model outputs.

The label-free worker writes and seals every attempted prediction before the
controller generates numerical future targets. Evaluation verifies identical
origin/target/denominator identities. Both full attempted coverage and success-
matched populations remain visible. The primary comparison uses all-five-method
successful IDs; a separate native-pair comparison reports its exact ID intersection.
No metric on a filtered subset is labeled full-population native performance.
Scale-normalized absolute error divides by the **common final90 past mean absolute
first difference**. A zero denominator remains null and is counted as undefined,
never given an arbitrary epsilon. Bootstrap bounds describe designed synthetic
case resampling, not independent real repository evidence.

Resource limits remain2GiB worker RSS,900s wall/CPU and two numerical threads.
Seccomp denies networking; checkpoint loading is local-only with no CUDA. Host
admission requires4GiB available memory and512MiB free disk. Logs and individual
artifacts are bounded16MiB; total study output is bounded64MiB. RSS monitoring
samples every20ms and checks final kernel `ru_maxrss`; this is not a cgroup hard
quota. Only study-owned outputs are written. No shared service is stopped.

See [report](../../PHASE_6_1A_CHRONOS_CONTEXT_REPORT.md) and
[conditional handoff](../../PHASE_6_1B_HANDOFF.md). Full paths/invalid paths/logs stay
outside Git; only synthetic endpoint summaries, registration and receipts publish.
