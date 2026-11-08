# Milestone 1 implementation — October 11, 2026

## Outcome and scope

Implemented an additive module forecasting package with verified collector
ingestion, causal module/file lineage, historical graph extraction, versioned
model datasets, and shared M0–M2 training/evaluation. The original file-level
pipeline, module mart, shared collector, scanner/export contracts and repair
report were not edited. Existing datasets, V3 workspaces and models were not
migrated or overwritten. No real scanner submission or real-data training was
performed during this implementation.

The repaired collector already supplied strict missingness, source inventories,
task/export provenance, analyzer compatibility checks, frozen module mapping,
preserved generations and offline regression tests. Those repairs were reused,
not reimplemented. The new forecast contract and its historical module definition
are separate from the old 3/4/12-week marts and fixed-root mapping.

## Delivered implementation

| File | Responsibility |
|---|---|
| `forecasting/schema.py` | UTC observation identities, exact90/approx91 contracts, growth threshold, feature allowlists and cutoff checks |
| `forecasting/collector_bridge.py` | Isolated read-only collector ingestion; explicit supplemental endpoint planning/collection bindings and recovery |
| `forecasting/git.py` | Immutable Git reads, source lexical helpers, exact rename evidence and ancestry/time-bounded history |
| `forecasting/identity.py` | Separate build/package configurations, causal roots, stable IDs, first presence, lineage, ambiguous splits/merges and deletion events |
| `forecasting/graphs.py` | Source/build dependencies, co-change, contributor overlap, cycles/coupling/PageRank and extraction diagnostics |
| `forecasting/dataset.py` | Weekly state, identity/membership, graphs, labels, 26-week masked sequences, audits and immutable checksummed publication |
| `forecasting/evaluation.py` | Identical M0–M2 cohorts, timestamp purging, rolling and repository-held-out folds, actual CatBoost regression/classification, metrics/models/predictions/reports |
| `forecasting/interfaces.py` | M3/M4 sequence/graph windows with analyzer masks; F2 origin-membership aggregation and strict external cohort matching |
| `forecasting/__main__.py` | Public build, endpoint-plan and evaluate commands |
| `tests/test_forecasting.py` | Synthetic Git, collector and actual CatBoost software verification |
| `requirements-forecast.txt`, `requirements-forecast-lock.txt` | Separate pinned forecasting dependencies and the complete tested environment |
| `FORECASTING.md` | Commands, schemas, major feature definitions, model/evaluation policy and limitations |
| `M3_M4_DESIGN.md` | Exact GraphSAGE frame -> causal TCN -> metrics fusion -> prediction-head specification |

Only `.gitignore` and the README were changed among previously tracked files, to
exclude runtime folders and link the new documentation. No commit or deployment
was requested or performed.

Supplemental 90-day snapshots are stored in `forecast_endpoints/data/`, outside
legacy `data/` registries. Their bridge uses the same scanner/export functions
inside the isolated adapter and restores evidence paths on exit. The original
weekly generation remains valid after supplemental collection; tests verify its
complete input/output manifest before and after collection and interrupted
sidecar recovery. Original raw proofs are never moved or rewritten to pretend
they came from another scanner directory. Identical supplemental commits reuse
the first supplemental analysis. A real first supplemental commit requires a
scan unless that supplemental namespace already contains valid evidence.

## Validation evidence

The final test result and exact environment are recorded in
`validation/milestone1/verification.json` and `validation/milestone1/pytest.xml`.
**166 tests passed, zero failures/errors/skips**: 137 existing tests and 29 new
forecasting cases. Compilation, dependency consistency, CLI help checks and
`git diff --check` passed as well.
The full suite is run in `.venv-forecast` on Python 3.12 with all pinned
dependencies, including CatBoost. The original suite was also run before changes:
136 passed and one optional-dependency test skipped in the host environment.
The isolated forecasting environment supplies that optional dependency.

New coverage includes:

- Actual temporary Git repositories with births, deletions, complete renames,
  package/build strategies, ambiguous splits/merges, file movement and orphan roots.
- Known Maven/import dependency graphs, directed cycles, co-change and contributor
  weights, partial Gradle/malformed-descriptor coverage, external/unresolved imports.
- Earlier state/graphs remaining identical after a later merge of a backdated branch.
- Exact 90-day endpoints, explicit 91-day approximation, rejection of 84-day
  substitution, missing target preservation and intermediate analyzer changes.
- Debt decomposition into retained, added and removed file populations; deletion
  and ambiguous lineage never becoming observed zero-debt targets.
- Repeated dataset builds producing identical artifact hashes/data versions;
  checksum failures, failed publication and unverified real-input rejection.
- Short-history feature/snapshot masks, unknown complexity preservation, graph
  windows and incompatible analyzer-frame masking.
- Train-label maturity before validation, validation-label maturity before testing,
  whole-repository holdout and common model prediction cohorts.
- Actual M1/M2 CatBoost fitting on synthetic data, deterministic repeated predictions,
  constant/insufficient-data behavior, classification metric eligibility and unbiased
  inclusion of zero-positive snapshot blocks in Precision@K.
- File forecast aggregation using only origin membership and exact external cohort
  matching without dropping missing predictions.
- Public CLI build/evaluate, verified collector subprocess ingestion, separate
  endpoint storage/reuse/recovery, unchanged legacy generations and namespace/lock
  restoration after failure.

All synthetic results prove software execution and contract behavior only.
They are not evidence of real-world predictive accuracy. Synthetic metric values
are not promoted as a model comparison for your Java repositories.

## Available artifacts and commands

Follow the install/build/evaluate/endpoint commands in `FORECASTING.md`.
New output directories are mandatory. Dataset generation never initiates scans.
Only the explicit endpoint-collection command can submit a real scanner task.
Training produces per-fold M1/M2 CBM models or explicitly identified constant
fallback metadata, exact fold cohorts, JSON/Markdown comparisons and CSV predictions.
Insufficient data produces a retained report with no fabricated model results.

No `module_generation.json` or `complete_week_01.json` was found in the project
workspace during the real-data inventory. Consequently there was no verified,
eligible real collector dataset available for a scientifically meaningful M0–M2
run. No real model comparison or real prediction export is claimed. Dependencies
were successfully installed locally; external dependencies did not block software
verification.

## Limits and remaining gates

1. **Real collection:** run a representative Sonar integration pilot, validate
   repository production scope and analyzer behavior, and collect enough history
   and endpoint snapshots. Compiled Java build/runtime evidence still requires
   the collector's original independent verification.
2. **Semantic lineage:** identity is conservative membership/Git evidence, not a
   semantic rename/refactoring oracle. Birth means first observed presence; an
   unobserved intermediate deletion/recreation cannot be proved absent. Ambiguous
   target windows are excluded rather than guessed.
3. **Graph resolution:** import parsing is lexical. Effective Maven models,
   executable Gradle logic, calls, reflection, implicit same-package uses and full
   compiler resolution remain outside this milestone. Partial extraction and
   unresolved references are recorded; source coverage is not resolution recall.
4. **Labels and sampling:** review sampled real debt labels and membership
   decomposition. Compatibility covers retained observations; it cannot prove
   analyzer stability during unobserved intervals. Confirm enough growth events
   and future windows; row counts are not independent sample counts. Effective
   independent sample size remains explicitly unknown.
5. **Model assessment:** review real future-period and repository-held-out results,
   cohort granularity, learning curves and statistical uncertainty before choosing
   a production model. Fixed parameters in this milestone avoid test-driven tuning.
6. **F1/F2:** aggregation/matched-evaluation interfaces are implemented; file-model
   fitting and calibrated aggregate growth probabilities are deferred. Scope-changing
   targets require explicit interpretation when using current-file forecasts.
7. **M3/M4:** executable data/evaluation interfaces and the architecture specification
   are delivered. Neural dependencies/training are intentionally deferred until
   real data sufficiency passes. A finding-count head requires reliable finding
   identity/arrival-label evidence and is also deferred.

These are unvalidated scientific/integration gates, separate from the locally
verified implementation. This milestone grants no automatic production-model
approval or predictive-performance claim.
