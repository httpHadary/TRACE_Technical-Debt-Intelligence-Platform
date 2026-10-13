# Forecasting MVP — Phase 0 foundation

This package implements **verification and contracts only**. No histories/labels,
model loaders, training, forecasts, API or dashboard are implemented. The legacy
`forecasting/` and collector remain unchanged.

From the project root, using the existing dependency-checked environment:

```bash
.venv-forecast/bin/python -m forecasting_mvp validate-config --config forecasting_mvp/study.phase0.json
.venv-forecast/bin/python -m forecasting_mvp environment --disk-path /home/hp/tst
```

Read-only SQLite integrity/schema/coverage/measurement audit (requires a **new**
output filename inside the config's output root):

```bash
.venv-forecast/bin/python -m forecasting_mvp audit-v2 \
  --config forecasting_mvp/study.phase0.json \
  --output /home/hp/tst/research/forecasting_mvp/phase0/2026-10-13/v2_audit-recheck.json
```

Phase 0 adds verification-only `validate-config`, `environment`, `verify-bundle`
commands alongside the limited `audit-v2`. The planning document's later import,
grid, split and prediction command contracts are **not implemented**. `audit-v2`
returns a JSON audit file, not a forecasting dataset or certified historical scan.
Exit 0 means verification passed, 2 means partial/data insufficiency, 3 means an
invalid configuration/artifact or I/O/database error.

`contracts.py` defines native-project SQALE observations and exact elapsed UTC
30/60/90-day target contracts; missing values remain null and derived deltas may
be negative. It cannot certify own scans. Configuration is separate from legacy
module horizons/units. `io.py` reuses strict legacy JSON/atomic publication/path
checks, adding streaming SHA-256 for large inputs and COMPLETE-bundle validation.
No package installation or model import occurs on config load.

`study.phase0.json` records this machine's explicit source/output locations,
research-use license, immutable checkpoint candidates and future resource budgets.
Model candidates are metadata records, not loaded or validated predictors. Make a
new config/study ID when moving paths or changing contracts; preserve this record.

See [Phase 0 report](../PHASE_0_IMPLEMENTATION_REPORT.md) for measured environment,
dataset evidence, tests, limitations and the authorization boundary.
