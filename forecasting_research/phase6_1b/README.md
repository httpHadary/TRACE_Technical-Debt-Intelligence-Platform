# Phase 6.1B synthetic comparison

`SYNTHETIC_ENGINEERING_TEST` only. This package has no real-data loader,
training command, installer, scanner or external service. Persistence remains
the reference. These results cannot establish real technical-debt accuracy.

The published result is **PARTIAL**: native Chronos and TTM completed; TimesFM
was stopped during loading by the conservative RSS guard, before forecasting.

## Reproduce published arithmetic without models

From the repository root, using the existing forecast environment:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python \
  -m forecasting_research.phase6_1b reproduce
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python \
  -m pytest -q -p no:cacheprovider tests/test_phase6_1b_comparison.py
```

This parses only the published synthetic endpoint table, independently regenerates
its exact truth/normalization, and recalculates all metrics. No inference replays.
The six separate native-adapter unit tests use fake backends and require the
existing CPU Torch/NumPy dependencies; they are not native inference evidence.

## Registered experiment

Population v1 has 42 cases: 14 generator families × three seeds/scales, with
512 generated daily past positions and an independent future random stream.
Six sparse/irregular cases retain missingness and are excluded for every method;
36 eligible cases share origins and exact 30/60/90-day outcomes. Phase 6.1A is
exposed development evidence. New seeds/equations do not create a confirmatory
real-repository sample. See `population.py` and the frozen registration.

All methods receive the same 512 observations. Persistence uses the origin,
rolling mean the final seven, and anchored OLS the final 90. Chronos uses 512→90,
TTM 512→96 with its first 90 native steps, and TimesFM was registered for a direct
90-step API request. Native TimesFM patch rounding to 128 is documented, not a
weekly conversion or recursive extension. Its forecast was never reached here.

The original Chronos adapter/environment are unchanged. New Chronos composition
reuses the Phase 6.1A observed-forward adapter. TTM loads the exact original
configuration/model source modules in a task namespace, avoiding the upstream
package initializer's unrelated data/training imports. Source bytes, model
classes, forward/scaling code and checkpoint tensors are unchanged. Daily token
8 comes from the pinned upstream frequency mapping, inspected as data. This is
a minimal source installation, not certification of the full Granite toolkit.

Two private virtual environments install the pinned source trees through `.pth`
files and reuse the original dependencies read-only, with all 22,397 dependency
files hash-locked before execution. No dependency upgrade/download was needed.
The exact lock, checkpoint identities, license/API evidence and source hashes are
in `model_admission.json`; actual runtime statuses are in the examples matrix.
Private weights, source trees and environments are outside Git.

## Execution policy

The CLI exposes `prepare --out NEW_PRIVATE_DIRECTORY` and
`run --study REGISTERED_DIRECTORY`, with exclusive attempt files. Outputs must
be fresh descendants of the private `phase6_1b` task root. Already consumed
directories refuse execution. Running inference again requires a new authorized
research step; the example receipts are not permission to replay the study.

Workers run sequentially, CPU float32/eval, seed 42, deterministic Torch algorithms,
two numerical threads, local-only loading and verified kernel network denial.
The 900-second and 2 GiB ceilings are unchanged. A 1.75 GiB sampled stop threshold
leaves headroom below the ceiling; this is a 20 ms RSS guard, not a hard cgroup
quota. Completed workers also report kernel `ru_maxrss`. Logs/artifacts are bounded.
TimesFM's abrupt kill has no final kernel peak; it is marked unavailable.

Each worker seals predictions before scoring. Root seals bind registration and
combined predictions before evaluator-only truth access. Native crossings retain
invalid raw outputs and fail the case; unexpected errors abort the worker. There
is no fallback, quantile sorting, calibration or interval fabrication. Raw values
and the `max(0, raw)` stock policy are both retained.

Initial TTM startup failures are preserved in two sealed engineering receipts.
The final continuation repaired only import setup, reused the original sealed
Chronos predictions and TimesFM resource failure, and ran TTM natively once.
No model setting or metric policy was selected from numerical outcomes. The
`--reuse-prior` preparation option verifies the complete earlier seal, records
the prior identities and requires identical generated requests.

Metrics include all registered/blocked counts, identical-success pairs, the
available-model intersection and the empty all-six intersection. Normalization
divides absolute error by mean absolute past stock across 512 positions; zero
denominators remain null and counted. It is not MASE. Per-scenario, equal-scenario,
mixed-scale exclusion and unchanged/changing tables are all published.

No original study, rights decision, Java build record or analyzer dataset is
modified. Further models, real-data evaluation and SonarQube collection remain
separate authorization and admission decisions.
