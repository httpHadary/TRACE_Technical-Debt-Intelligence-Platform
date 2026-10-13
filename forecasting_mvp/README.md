# Forecasting MVP — verification and historical ingestion

This package implements **Phase 0 verification, Phase 1 ingestion and Phase 2 exact-target datasets**.
No model loaders, training, forecasts, API or dashboard are implemented. The legacy
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
commands alongside the limited `audit-v2`. Training and prediction commands are
**not implemented**. `audit-v2`
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
no COMPLETE bundle is published. Phase 1 alone creates no future labels or models.

See [Phase 1 report](../PHASE_1_IMPLEMENTATION_REPORT.md) and [GitHub sync
instructions](../GITHUB_SYNC.md).

## Phase 2 — exact forecasting dataset, no models

Copy `study.phase2.example.json` to a private local configuration and adjust the
verified Phase 1 bundle and output root. The output directory must be new.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp build-forecasting-dataset \
  --config forecasting_mvp/study.phase2.example.json \
  --out /home/hp/tst/research/forecasting_mvp/phase2/2026-10-14/run-003
```

Artifacts: required `forecasting_dataset.csv`, `forecasting_splits.json`,
`forecasting_feasibility.json`; separate past-only `forecasting_features.csv` and
`forecasting_contexts.jsonl.gz`; evaluator-only `forecasting_labels.csv`; small
sample and checksummed manifest. Gzip has a fixed zero timestamp for deterministic
publication. Local full artifacts are ignored by Git; audit, hashes, split summary
and small samples are published under `examples/phase2/`.

Origins are Mondays at 00:00 UTC. Targets are exact 30/60/90 elapsed UTC days. Last
reachable first-parent state selects the **revision**, then only its matching
measurement supplies debt. No nearest scan, interpolation or carry across an
unmeasured change. Same-state reuse requires an identical selected revision and
known observed metadata with archived coverage through the endpoint. Imported
history still does not prove historical online availability or complete analyzer
invariance. Missing/changed profiles are barriers even between daily grid points.

Ambiguous-tip and nonmonotonic repositories are excluded with reasons, preserving
Phase 1 evidence for possible later recovery. Complete 90-day contexts define
`core90`; separate `masked90` preserves missing values and requires at least 80%
known values plus observed origin/endpoint. TTM 60/90 require complete 180/512-day
contexts and separate matched cohorts; TTM 30 uses the complete 90-day track.

The split builder freezes the largest metadata/eligibility-only shared calendar
cohort with at least 630 days of coverage, following the planned 60%/80% chronological
boundaries and 90-day validation/test embargo. Training labels crossing validation
start are purged; held repositories never enter train/validation. Core is primary
only when the six-repository/all-phase/all-horizon gate passes; otherwise the same
data-only gate tests masked contexts. Sparse shared cohorts are reported as blocked
or partial without random splits. These thresholds are project protocol choices,
not guarantees of statistical power.

Later prediction runners must receive **only an origin-filtered past context and
feature projection**. The combined dataset/labels and other origins must not be
mounted or passed as covariates. Separate artifacts enforce a reproducible data
boundary; no trainer/runner is implemented here. Any future transformations must
fit training data only, and the test cohort remains untuned.

See [Phase 2 report](../PHASE_2_IMPLEMENTATION_REPORT.md). Stop before Phase 3 until
explicit authorization. Exit 2 reflects imported-history limitations even if the
data-cohort gate passes; exit 3 rejects invalid/corrupt inputs or changed code/data.
