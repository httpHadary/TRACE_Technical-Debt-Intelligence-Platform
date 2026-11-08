# Forecasting MVP — persistence-only flow

The persistence-only flow is implemented. See [run instructions](../forecasting_mvp/PERSISTENCE.md)
and the [implementation/verification report](../PERSISTENCE_IMPLEMENTATION_REPORT.md).
Use `persistence-build`, `persistence-import`, `persistence-verify` and `persistence-serve`
for the active MVP; older multi-model commands below retain their research-only scope.

For the current MVP direction, use the
[persistence-only workflow](../architecture-redesign/2026-10-13-forecasting-mvp/MVP_FORECASTING_PLAN.md)
and [repository index](../MVP_REPOSITORY_INDEX.md), updated 2026-10-30.
Chronos-2 and hybrid studies remain archived research; they are not active forecast
stages. The phase entries below retain their historical execution boundaries.

This package implements **Phases 0–2.1 verification, Phase 3 baselines and Phase 4.1 bounded Chronos CPU smoke**.
Full pretrained benchmarks, supervised training, APIs and dashboards are not implemented. The legacy
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

## Phase 4.1: isolated Chronos CPU smoke

New commands are limited to `prepare-chronos-smoke` (exactly six metadata-selected
train/validation contexts) and `chronos-smoke` (900-second / 2-GiB-RSS worker).
No general benchmark or test-cohort inference command is added. The worker has
no label file inputs and uses only the published past-only smoke request bundle.

Install the separate runtime in a new `.venv-chronos-cpu`, preserving every prior lock:

```bash
uv venv --python /usr/bin/python3 .venv-chronos-cpu
uv pip install --python .venv-chronos-cpu/bin/python --index-strategy unsafe-best-match \
  -r requirements-chronos-cpu-lock.txt
uv pip check --python .venv-chronos-cpu/bin/python
```

The registered model is `autogluon/chronos-2-small` at
`ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a`. Download only its pinned
`config.json`, `README.md`, `model.safetensors` into an ignored/local checkpoint
directory, copy `examples/phase4_1/checkpoint_admission.json` there, and verify its
SHA-256 inventory with `verify_checkpoint`. Weights are deliberately not uploaded.
The report contains the exact download and full-data preparation commands.

The small published requests are also independently reproducible without the
full historical database or evaluation labels:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-chronos-cpu/bin/python -m forecasting_mvp chronos-smoke \
  --requests-bundle examples/phase4_1/requests \
  --checkpoint /absolute/local/pinned-checkpoint \
  --out /absolute/new-smoke-run
```

The adapter sends only target values on a 90-point daily grid, uses CPU float32,
two intra-op/one inter-op threads, native q10/q50/q90, no future covariates or
cross-learning, and saves a 90-step path. Indices 29/59/89 preserve exact original
forecast identities. Native q50 is the point; all quantiles retain raw values and
use the same nonnegative stock clipping policy as baselines.

Chronos 2.3.2 needs UTC-naive `datetime64[ns]` at its DataFrame edge; the adapter
converts already verified UTC times without changing their values, then restores
explicit UTC and verifies all returned daily timestamps. Shape, identity,
nonfinite outputs and quantile crossings fail closed. Each of the six contexts
is repeated twice in the same pinned CPU worker; this is runtime/determinism
evidence, not model accuracy or interval calibration.

See [Phase 4.1 report](../PHASE_4_1_IMPLEMENTATION_REPORT.md). Phase 4.1 stopped
after its smoke test; the separately authorized Phase 4.2 evaluation follows.

## Phase 4.2: frozen-cohort Chronos evaluation

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp evaluate-chronos \
  --bundle /absolute/phase2/frozen-run \
  --history-bundle /absolute/phase1/frozen-run \
  --baseline-bundle /absolute/phase3/frozen-results \
  --smoke-bundle /absolute/phase4_1/complete-smoke \
  --runtime-python /absolute/.venv-chronos-cpu/bin/python \
  --checkpoint /absolute/pinned-checkpoint \
  --out /absolute/new-phase4_2-run
```

Requires the original verified Phase 1/2/3/4.1 bundles and pinned CPU checkpoint.
The registered primary track remains `core90`. A metadata-only fixed 12-context
validation pilot repeats successful predictions, then complete validation predicts
before its numerical labels are loaded. Validation macro MAE selects a default
among unchanged baselines and Chronos (within 1% prefer simpler models). No
inference parameters, native quantiles or interval calibration are tuned.

Only after `selection.json` is frozen does a label-free worker infer all original
temporal-test and held-repository IDs. Both test cohorts are sealed together and
their identity digests checked against Phase 3 before the evaluator opens numeric
test labels. The worker receives one past-only request bundle and no label files.

The original strict adapter rejects native quantile crossings and invalid paths.
Every such failure emits a typed status and an explicitly labeled persistence
fallback point; it never fabricates a native interval. Reports separate the full
assigned failure-policy comparison from all-model paired success-only metrics.
Interval coverage/width are conditional on successful native intervals and retain
attempted/success/failure denominators. A pilot with valid deterministic successes
and explicit recoverable failures may continue under the registered fallback;
zero valid native contexts, non-determinism or process/resource failures stop it.

Workers have external 2-GiB RSS caps, a 900-second pilot cap and 1800-second caps
for each full cohort stage. No new installation or weights are required. Original
baseline prediction/metric bytes, datasets, splits and legacy functionality are
preserved. Point metrics use the existing evaluator with its default behavior
unchanged and an explicit four-model comparison option for this phase.

Outputs include `chronos_predictions.csv`, full and success-matched comparison
metrics, native interval metrics, a comparison PNG, source/code/config manifests,
stage seals, failures, resources and a small prediction sample. Interval checks
include constant past histories, exact collapsed and near-collapsed ranges,
collapsed misses, quantile pinball and nominal 80% interval score. No row bootstrap
or invented intervals: 2,000 paired repository replicates, seed 42; held-out bounds
remain exploratory with only six clusters.

Exit 0 means complete native success; exit 2/PARTIAL explicitly reports recovered
inference failures; exit 3 blocks corrupt inputs, missing coverage, code changes,
invalid seals or runtime/resource failures. See [Phase 4.2 report](../PHASE_4_2_IMPLEMENTATION_REPORT.md).
Stop after publication. No Granite, CatBoost, training or dashboard work is added.

## Phase 4.2.1: diagnostic-only hardening

The original Phase 4.2 source snapshot is Git commit `187dcc1`; its predictions,
metrics, study/config, failure records and evidence remain unchanged. Hardened
workers recover only `NativeQuantileCrossingError` raised after complete output
identity, timestamp and finiteness validation. Unexpected runtime/software/shape
errors abort. Any failure after a valid first pilot path, including a repeat
crossing, is fatal. Whole-path rejection and zero ordering tolerance are retained.

`python -m forecasting_mvp.chronos_diagnostics --benchmark ORIGINAL_RUN
--checkpoint PINNED_CHECKPOINT --runtime-python CPU_PYTHON --out NEW_DIAGNOSTIC_RUN`
is a separate bounded diagnostic entry point. Supply the arguments on one shell
line or use continuations as in the report. It admits only the original published
study and exactly its 12 failed contexts, with two raw-path captures each, under
300 seconds and 2 GiB. It does not invoke the benchmark, inspect numerical labels,
infer other contexts, replace forecasts or recalibrate intervals. Saved interval
metrics provide descriptive undercoverage/collapse diagnostics only.

See [Phase 4.2.1 report](../PHASE_4_2_1_DIAGNOSTIC_REPORT.md) for exact commands,
typed/fatal recovery tests, raw magnitudes/endpoints and immutable artifact proofs.
Stop after diagnostic verification and publication; later experiments remain
unauthorized.
