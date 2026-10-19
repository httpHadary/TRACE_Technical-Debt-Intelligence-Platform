# TimesFM 2.5 low-memory feasibility

Final result: **PARTIAL**. The separately approved single attempt loaded the
full model and returned one finite native path at approximately1.19GiB observed
peak RSS. All90 steps failed full-decile ordering, so the smoke gate stopped the
worker. No remaining35-case benchmark, quantile repair or retry occurred.

Phase 6.1C is isolated from the published Phase 6.1B experiment. No new weights,
dependency installation, model substitution, source patch or quantile repair is
part of this package. Native TimesFM loading/forecasting requires **separate
explicit operator approval after the static audit**.

The static inspector never imports or constructs TimesFM. It reads the pinned
source's literal architecture configuration, independently derives all 232 state
keys/shapes and compares them to the safetensors header. Streaming 1 MiB reads
verify the entire checkpoint, every tensor hash and float32 finiteness without
loading the model. The original source/runtime manifests are reverified.

The proposed loader constructs the unchanged architecture on `torch.device('meta')`,
loads CPU safetensors through the installed `backend='mmap'`, then calls strict
`load_state_dict(assign=True)`. It rejects missing/unexpected tensors, shape/type
changes, unexpected buffers and storage copies. Assigned tensor hashes and pointer
identity must match the mapped tensors. The original native forecast code and
Phase 6.1B adapter are reused unchanged. Tiny toy tests prove these generic API
mechanics; they do not certify TimesFM behavior or actual model RSS.

Static commands, using fresh paths under the private task root:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python \
  -m forecasting_research.phase6_1c audit --out NEW_STATIC_AUDIT.json
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python \
  -m forecasting_research.phase6_1c prepare \
  --out NEW_STUDY_DIRECTORY --audit NEW_STATIC_AUDIT.json
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q \
  -p no:cacheprovider tests/test_phase6_1c_memory.py
```

The eight tiny assignment tests require the existing CPU Torch/safetensors
environment. They never import/instantiate TimesFM or open its checkpoint.

The `run --study ... --approval ...` entry point validates a separate
approval bound to the exact registration SHA256 before creating an attempt claim
or launching a subprocess. There is no approval-writing or automatic retry
command. The initial user prompt, old Phase 6.1B acquisition approval and the
registration itself do not authorize native execution. This phase's one explicit
approval and attempt are consumed; the archived command is not permission to rerun.

An approved attempt uses one CPU-only worker, two numerical threads, 900 seconds,
a 2 GiB RSS ceiling and the unchanged conservative 1.75 GiB stop threshold.
The monitor samples RSS and high-water values every 5 ms; this is not a hard
cgroup quota. Host admission, kernel network denial, bounded logs/outputs,
fresh exclusive claims and final kernel peak checks remain required.

The smoke case is the preregistered increasing-history case from Phase 6.1B:
512 genuine generated daily values, 90 native future daily steps. Only if that
case succeeds, and the separate approval includes the conditional comparison,
may the same loaded worker forecast the other 35 cases. It reuses the smoke
prediction as that case's primary forecast. No repeat call, reloading or retry.

All native outputs are sealed before scoring. The conditional evaluator reuses
the original sealed baseline/Chronos/TTM predictions without executing them.
This is the exposed Phase 6.1B synthetic development cohort, never a new
confirmatory real-data test. Native crossings retain invalid raw outputs with
no sorting or fallback. No original artifact or rights decision is modified.
