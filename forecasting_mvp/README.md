# Forecasting MVP — verification and historical ingestion

This package implements **Phases 0–2.1 data verification and Phase 3 statistical baseline forecasting**.
Pretrained model loaders, supervised training, APIs and dashboards are not implemented. The legacy
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

## Phase 2.1: hardening a frozen bundle

```bash
python3 -m forecasting_mvp validate-frozen-dataset \
  --bundle /absolute/phase2/frozen-run \
  --source-db /absolute/td_V2.db \
  --out /absolute/phase2_1/new-run
```

The read-only audit requires the original checksummed SQLite database, a COMPLETE
Phase 2 bundle and a new separate output directory. It validates every forecast
identity/split, every serialized context/feature/label projection and at least
100 deterministic stratified examples against independently reconstructed raw-SQL
first-parent states. It preserves all frozen cohorts, labels and input bytes.
The default study ID is `phase-2-v2-calendar-v1`; pass `--study-id` if a different
registered study produced the frozen splits. Failures return exit 3 without a
COMPLETE evidence manifest. Integrity PASS returns exit 0; the result separately
records PARTIAL Phase 3 readiness due to imported provenance and unverified runtimes.

`admit_prediction_input` requires one allowlisted context, an externally bound
origin and historical timestamps for referenced measurements. Its immutable
request exposes only past values/timestamps and horizon through `model_payload`.
It rejects targets, split labels, unknown fields, future references, incorrect
daily grids and tampered context identities. A future authorized runner must use
this boundary and must not receive label files, combined rows or the full context
store. It is an admission contract, not an operating-system sandbox or a model
runner. Train-only fitting and final evaluation isolation remain Phase 3 obligations.

See [Phase 2.1 report](../PHASE_2_1_VALIDATION_REPORT.md). No forecasting or training
commands were added. Original module forecasting functionality remains unchanged.

## Phase 3: real statistical baseline replay

```bash
python3 -m forecasting_mvp run-baselines \
  --bundle /absolute/phase2/frozen-run \
  --history-bundle /absolute/phase1/frozen-run \
  --hardening-bundle /absolute/phase2_1/complete-audit \
  --out /absolute/phase3/new-run
```

Requires verified Phase 1/2/2.1 bundles bound to the same database, the PASS frozen
primary `core90` cohort and existing NumPy/Matplotlib. No dependencies or weights
are installed by the command. It retains the original 30/60/90-day identities,
train/validation/test/held-repository assignments and ignored full local datasets.

The protocol registers mean windows 7/30/90 and anchored OLS trend windows 30/90,
plus persistence. All candidates use `admit_prediction_input` and only past
values; raw and nonnegative-clipped estimates are saved. Every candidate prediction
is checksummed before any numerical labels are opened. Only validation labels
select each model's window and the simplicity-preferring validation champion.
Selected predictions are then sealed before final test scoring. The label reader
scans CSV IDs for routing but retains/converts only explicitly allowed labels.
Prediction functions receive neither files, evaluation labels nor measurement stores.

Output: `baseline_predictions.csv`, `baseline_metrics.csv`, `baseline_comparison.png`,
study/selection/seal/audit manifests and a small fixed-ID prediction sample.
Metrics separate all/unchanged/changing debt, repositories and split groups; both
repository-macro and pooled MAE/RMSE are explicit. Confidence bounds use 2,000 paired
repository-bootstrap replicates (seed 42), not rows; one-repository bounds and
relative skill with zero persistence error are undefined. These are uncertainty
bounds on observed errors, not future predictive intervals.

See [Phase 3 report](../PHASE_3_IMPLEMENTATION_REPORT.md). Further pretrained,
CatBoost or dashboard work requires another authorization. Older phase statements
above record their authorization boundaries when those phases were completed.
