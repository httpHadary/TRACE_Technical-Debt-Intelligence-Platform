# TechDebt360 MVP — Phase 2.1 Dataset Hardening

Date: 2026-10-14. Working project: `/home/hp/tst/td_pipeline_module_level/td_pipeline`.

**Phase 2.1 implementation and integrity validation: PASS. Phase 3 readiness: PARTIAL.**
The frozen data supports a bounded, separately authorized research comparison.
Imported analyzer/availability provenance and pretrained runtime/resource admission
remain unresolved. No model was loaded, trained or run; no predictions were made.

## Scope and changes

- `forecasting_mvp/hardening.py`: read-only raw-SQL state oracle, deterministic
  stratified sampling, exhaustive artifact/split checks, per-split/repository
  measurement reuse and overlap diagnostics, checksummed evidence publication.
- `forecasting_mvp/prediction_input.py`: strict allowlisted past-context admission,
  external cutoff binding, measurement-time checks, immutable model-facing payload.
- `forecasting_mvp/cli.py`: additive `validate-frozen-dataset` command only.
- `tests/test_forecasting_mvp_phase2_1.py`: 29 new checks, including adversarial
  future/target/label inputs, frozen-cohort tampering and deterministic publication.
- Root/package README, `GITHUB_SYNC.md`, this report, attributed small evidence
  under `examples/phase2_1/`.

No confirmed frozen target, ancestry or split defect was found. **No dataset
rebuild, label correction, cohort reassignment or outcome-driven selection occurred.**
Existing collectors, SonarQube integration, legacy forecasting and Phase 0–2
contracts remain intact. The missing enforced prediction-input boundary was
hardened; no prediction runner was implemented.

## Frozen input identity

Final Phase 2 bundle remains:
`/home/hp/tst/research/forecasting_mvp/phase2/2026-10-14/run-003`.
All seven artifact hashes and the original manifest hash are recorded in
`examples/phase2_1/dataset_validation.json`, checked before and after each audit.

- Original database: `/home/hp/TECH_DEBT/td_V2.db`, opened SQLite `mode=ro`,
  `query_only=ON`; source hash remains
  `8eb329e5e5690b884b98df824c4b94fc7582c5d610fa3bd12784b1e417b2684e`.
- Dataset: **121,569 forecast rows**, **59,819 contexts**, **22 admitted repositories**.
- Dataset SHA-256:
  `97c6ea0fa6560e28fce72bc128047827980f028528c99aab1b5ad84c6b5552ac`.
- Split file SHA-256:
  `6a695e05403b89bd74d9560a3fe9f3900727d8782c4f4f048fb7abc98927a6e1`.
- Frozen split ID:
  `8b72cb6a93c47f84e6907bd180345c51f005257f5b10b18893fc791d3d0c0208`.

The four ambiguous mainlines and five repositories containing the 34 first-parent
inversions remain excluded exactly as documented in Phase 2. Unmeasured revisions
remain unknown; no interpolation, nearest-time actuals, zero filling or carrying
older scans across unmeasured changes was introduced.

## Independent raw-SQL validation

**559/559 examples passed**, spanning all 22 repositories, all four tracks,
30/60/90-day horizons and every populated split-assignment category.
The sample includes 157 negative, 145 positive and 257 zero deltas; 136 unchanged
revision endpoints and 423 measured changed endpoints. **87,202 past context
points** were independently checked against raw selected revisions and SQALE.

The sampling policy chooses the smallest immutable forecast hash in every
repository/horizon, repository/split and track/horizon/split/state/delta cell,
then includes earliest/latest origins, lowest debt/delta, greatest missingness
and fewest underlying measurements in each track/horizon/split. All available
cells are represented. It is deterministic under row reordering and deliberately
overrepresents rare cases; sample frequencies are not population estimates.
Empty strata are not fabricated. There are no zero-valued origin/endpoint debt
stocks in the frozen eligible examples, although zero **deltas** are common.

The SQL oracle reads the three original tables directly. It independently
reconstructs unique-tip first-parent chains, rejects unresolved/nonmonotonic
chains, selects the latest chain state at each exact UTC cutoff, joins the exact
revision to its unique analysis/measurement, and checks numeric SQALE, signed
deltas, observation IDs and compatible profile segments. Equal commit timestamps
use chain order. It independently decodes semicolon-delimited profile JSON while
preserving quoted text. It does not call Phase 1 extraction or `RepositoryStates`.

Unchanged-state targets require identical selected origin/endpoint SHA and
archived chain extent beyond the exact endpoint. Intermediate measured profile
barriers are checked even between daily cutoffs. Masked context nulls must match
unmeasured raw revisions; valid values must match their own selected measurement.
SQL text and per-example analysis IDs/chain indices are published with the sample.
This is substantial stratified validation, **not exhaustive independent SQL proof
of all 121,569 labels**.

## Exhaustive integrity, leakage and split checks

All 121,569 rows passed exact horizon/target/forecast identity checks, signed delta
checks and unique semantic `(repository, track, origin, horizon)` identity checks.
Every row has exactly one frozen assignment. Pure policy recomputation reproduced
all boundaries, held repositories, counts, assignments and split digest identically.

The 21-repository shared calendar retains six repository holdouts and fifteen
familiar repositories. Train labels end strictly before 2014-06-09; validation
origins end before 2015-05-18; test origins start 2015-08-17 after the registered
90-day minimum embargo, rounded to Monday. Purged/embargo/excluded rows remain
explicit assignments, not training rows. Targets remain exact origin+30/60/90
calendar days; 91-day weekly targets are not substituted. All cross-split
forecast-label window overlap counts are zero.

Every serialized context passed:

- Exact length/daily UTC grid, timestamps at or before its externally bound origin.
- Past historical measurement references at or before each individual grid point.
- Registered complete/masked policy, known endpoint, null/reference consistency.
- Content hash, context summary and dataset/feature binding.

All 59,819 feature rows were recomputed from their past contexts and matched
exactly, including feature availability flags; all 121,569 separate label rows
matched the combined audit table. Model-facing feature schemas reject added target
or evaluation columns. The admission function rejects combined rows, target IDs,
actuals, endpoint information, evaluation labels, unknown fields, future-dated
measurement references and later-origin contexts. A returned payload has only
past values/timestamps and horizon and cannot expose the measurement/label store.

This contract is a data admission boundary, **not an OS sandbox**. A later runner
must call it, isolate label files until predictions are sealed, bind the caller's
origin to the registered request and fit any preprocessing on training rows only.
Those runtime obligations were not implemented because Phase 3 is unauthorized.

## Quality and independence diagnostics

`dataset_quality.json` contains all **64 track/horizon/split cells**, **870
repository/track/horizon/split cells**, and cross-split measurement reuse counts.
It separates unchanged revisions, changed revisions with equal debt, positive/
negative changes, distinct origin/endpoint measures, repeated context measurement
and value sequences, missing slots and overlapping windows. Alternative tracks
are never pooled into an independent-sample claim.

Primary complete 90-day-context track:

| Horizon | Split | Rows | Zero debt change | Changing debt | Zero fraction | Distinct origin measures | Disjoint windows |
|---:|---|---:|---:|---:|---:|---:|---:|
| 30 | train | 2145 | 1378 | 767 | 64.2% | 589 | 435 |
| 30 | validation | 735 | 541 | 194 | 73.6% | 167 | 150 |
| 30 | test_temporal | 555 | 410 | 145 | 73.9% | 119 | 120 |
| 30 | test_repository | 222 | 130 | 92 | 58.6% | 73 | 48 |
| 60 | train | 2085 | 1054 | 1031 | 50.6% | 578 | 240 |
| 60 | validation | 735 | 440 | 295 | 59.9% | 167 | 90 |
| 60 | test_temporal | 555 | 330 | 225 | 59.5% | 119 | 75 |
| 60 | test_repository | 222 | 98 | 124 | 44.1% | 73 | 30 |
| 90 | train | 2025 | 878 | 1147 | 43.4% | 573 | 165 |
| 90 | validation | 735 | 378 | 357 | 51.4% | 167 | 60 |
| 90 | test_temporal | 555 | 287 | 268 | 51.7% | 119 | 45 |
| 90 | test_repository | 222 | 82 | 140 | 36.9% | 73 | 18 |

Weekly origins cause **every adjacent within-repository label window** in these
primary train/validation/test cells to overlap. The disjoint-window count uses
half-open `[origin, endpoint)` intervals; touching boundaries are allowed.
Neither it nor distinct measurement counts estimates effective independent N.

At 90 days, temporal-test rows comprise 64 unchanged revisions and 223 changed
revisions with equal debt (287 zero deltas), plus 268 changing-debt cases.
Held-test rows comprise 12 unchanged revisions, 70 changed revisions with equal
debt and 140 changing-debt cases. Median distinct scans per 90-day context is
3 in temporal test, 8 in held test and 5 in training; some contexts contain only
one underlying measurement. Daily length therefore does not establish temporal
information content. Overall MAE alone may obscure the changing-debt problem.

For core90/90, train↔validation share 15 context measurements and 3 endpoint
measurements; validation↔temporal-test share 13 and 5; train↔temporal-test share 1
and 1. This reflects legitimately repeated measured states across archived
cutoffs. There is no forecast-window overlap across these splits. Repository
holdouts share zero context/endpoint measurement IDs with familiar repositories.
Identical values or repeated observations do not prove independent evaluation.

Repository coverage for the primary 90-day tests:

| Project | Test group | Rows | Changing debt | Distinct origin scans | Median context scans |
|---|---|---:|---:|---:|---:|
| org.apache:bcel | test_repository | 37 | 13 | 10 | 5 |
| org.apache:beanutils | test_temporal | 37 | 8 | 4 | 2 |
| org.apache:codec | test_temporal | 37 | 27 | 6 | 3 |
| org.apache:commons-cli | test_repository | 37 | 5 | 3 | 2 |
| org.apache:commons-exec | test_temporal | 37 | 14 | 5 | 2 |
| org.apache:commons-fileupload | test_repository | 37 | 11 | 5 | 2 |
| org.apache:commons-io | test_temporal | 37 | 35 | 15 | 11 |
| org.apache:commons-jelly | test_temporal | 37 | 0 | 3 | 1 |
| org.apache:commons-jexl | test_temporal | 37 | 37 | 17 | 9 |
| org.apache:configuration | test_temporal | 37 | 36 | 15 | 8 |
| org.apache:daemon | test_temporal | 37 | 3 | 6 | 3 |
| org.apache:dbcp | test_repository | 37 | 37 | 11 | 9 |
| org.apache:dbutils | test_temporal | 37 | 0 | 3 | 1 |
| org.apache:digester | test_temporal | 37 | 0 | 3 | 1 |
| org.apache:httpclient | test_repository | 37 | 37 | 21 | 16 |
| org.apache:httpcore | test_repository | 37 | 37 | 23 | 17 |
| org.apache:jxpath | test_temporal | 37 | 13 | 5 | 2 |
| org.apache:net | test_temporal | 37 | 29 | 11 | 5 |
| org.apache:ognl | test_temporal | 37 | 0 | 3 | 1 |
| org.apache:validator | test_temporal | 37 | 36 | 14 | 8 |
| org.apache:vfs | test_temporal | 37 | 30 | 9 | 6 |

These are descriptive diagnostics from fixed cohorts, not measured model outcomes.
No test rows were removed due to repetition, zero change or small context diversity.
A later authorized comparison must retain persistence, report overall and
changing/unchanged-debt metrics on the original IDs, repository-level results and
cluster-aware uncertainty. Do not use these diagnostics to tune on test outcomes.
Six held repositories provide limited evidence for cross-project generalization.

## Tests and deterministic reproduction

Final relevant regression suite: **268 passed, 0 failed, 1 deselected**. The single
excluded test actually trains CatBoost and remains unauthorized. The same suite
also passed in the original working project (268 passed, 1 deselected). The 29 new
Phase 2.1 tests and all allowed existing tests passed; no real model inference,
SonarQube scan, package install or dataset/model download occurred.

Final local evidence is `research/forecasting_mvp/phase2_1/2026-10-14/run-003`.
A second full audit of the same frozen input is run into `run-004`; exact output
byte/hash comparison is recorded in `examples/phase2_1/determinism.json`.
Development `run-001` was incomplete and is not the final evidence bundle.
The code/source/input hashes bind reproduction, and the audit fails if they change
while running. The original database and every frozen input artifact remain equal
to their registered pre-audit hashes.

From the project root, with the existing environment (use a **new** output path):

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp validate-frozen-dataset \
  --bundle /home/hp/tst/research/forecasting_mvp/phase2/2026-10-14/run-003 \
  --source-db /home/hp/TECH_DEBT/td_V2.db \
  --out /home/hp/tst/research/forecasting_mvp/phase2_1/2026-10-14/new-run

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp verify-bundle \
  --bundle /home/hp/tst/research/forecasting_mvp/phase2_1/2026-10-14/new-run

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests \
  -k 'not test_actual_catboost_models_shared_folds_predictions_and_purging'
```

The publication checkout uses the working project's same `.venv-forecast/bin/python`
by absolute path. No environment or legacy requirement lock was modified.

## Readiness decision and publication

**PASS for Phase 2.1 hardening; PARTIAL for Phase 3 readiness.** No demonstrated
data-integrity blocker requires rebuilding frozen cohorts. A separately authorized
bounded benchmark can proceed only after admitting the pretrained runtime and
resource plan, with imported-domain limitations disclosed. Historical scan dates
still do not prove online availability, and observed profiles do not prove complete
analyzer/rules/build invariance. No forecast performance, superiority or effective
sample-size claim is supported yet.

Safe small attributed artifacts, source, tests and report are committed to
`FadyYosry77/TechDebt360-MVP/main` through its existing descendant history.
Push SHA and remote accessibility are verified and reported at completion.
Full datasets/contexts/splits, SQLite binaries, caches and credentials remain local.
Original working history and unrelated changes are preserved.

**STOP after verification and publication. No Phase 3 authorization is assumed.**
