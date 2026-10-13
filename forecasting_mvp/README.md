# Forecasting MVP — verification and historical ingestion

This package implements **Phase 0 verification and Phase 1 historical ingestion**.
No future labels, model loaders, training, forecasts, API or dashboard are implemented. The legacy
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
commands alongside the limited `audit-v2`. The planning document's later grid,
split and prediction command contracts are **not implemented**. `audit-v2`
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

## Phase 1 — ingest archived repository measurements

Copy `study.phase1.example.json` to a new local configuration and adjust its
absolute database/output paths. The expected database hash pins release 2.0.1;
keep it for that release. Set it to null only for explicitly registered alternate
inputs such as test fixtures. No database or model download is performed.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp ingest-history \
  --config forecasting_mvp/study.phase1.example.json \
  --out /home/hp/tst/research/forecasting_mvp/phase1/2026-10-14/run-002
```

The output directory must be new and contained in the configured output root.
Artifacts: `historical_debt.csv`, `git_history.csv`, `historical_data_audit.json`,
`excluded_records.json`,12-row historical sample and checksummed COMPLETE manifest.
Raw history files are local-only; GitHub contains a small sample, audit and byte
hashes with reproduction instructions under `examples/phase1/`.

`AUDITED_IMPORTED` certifies exact record linkage, validated numeric values and
timestamp provenance; it does not certify a complete historical analyzer domain.
Naive imported analysis timestamps are assigned UTC only after matching an aware
Git committer timestamp to the second. Blank debt remains blank, observed zero
remains0. Mainline/profile/chronology defects are explicit flags, not secretly
repaired rows. First-parent indices require a unique archived tip and acyclic
graph. Missing parent boundaries and time inversions remain separate diagnostics.
Profile/chronology segments describe observed metadata only.

Exit 2/PARTIAL means usable measurements were published with documented source
limitations/exclusions. It does not mean the CSV should be mistaken for a ready
forecast dataset. Exit 3 means an invalid source/configuration/publication input;
no COMPLETE bundle is published. Future labels and models remain out of scope.

See [Phase 1 report](../PHASE_1_IMPLEMENTATION_REPORT.md) and [GitHub sync
instructions](../GITHUB_SYNC.md). Stop before Phase 2 without authorization.
