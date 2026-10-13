# Module forecasting — Milestone 1

This is an additive forecasting layer. It reads the repaired collector's verified
snapshots; it does not replace `run_pipeline.py`, alter file-level targets, migrate
legacy data, or change scanner/export rules. Read `MODULE_LEVEL_README.md` for the
collector's existing evidence contract and `MILESTONE1_REPORT.md` for validation.

## Install and reproduce

From `td_pipeline_module_level/td_pipeline`, use Python 3.12 and Git:

```bash
python3 -m venv .venv-forecast
.venv-forecast/bin/python -m pip install -r requirements-forecast-lock.txt
.venv-forecast/bin/python -m pytest -q
.venv-forecast/bin/python -m pip check
```

`requirements-forecast.txt` pins direct dependencies and includes the unchanged
collector requirements. The lock file pins the complete tested Linux environment.
No PyTorch, neural training dependency, database, or graph server is required.

Run commands from this source directory. Replace `/absolute/workspace/...` with
**existing repaired-collector workspaces**, each containing `repo_context.json`,
complete snapshot evidence and a full Git repository. The CLI verifies every
snapshot and exact cutoff commit in a separate process with workspace-local
configuration. It takes the collector's workspace lock while reading; it never
checks out, clones, fetches, or scans during `build`.

```bash
.venv-forecast/bin/python -m forecasting build \
  --workspace /absolute/workspace/commons-io \
  --workspace /absolute/workspace/commons-lang \
  --output forecast_runs/dataset-001 \
  --horizon approx91 --strategy auto --growth-threshold-minutes 30

.venv-forecast/bin/python -m forecasting evaluate \
  --dataset forecast_runs/dataset-001 \
  --output forecast_runs/evaluation-001 \
  --first-validation-cutoff 2022-01-06T00:00:00Z \
  --validation-weeks 8 --test-weeks 8 --folds 2 --step-weeks 32 \
  --iterations 200 --precision-k 5
```

The validation date above is an example, not an inferred split for your data.
Choose the calendar boundaries **before looking at model results**. All output
directories must be new. Failed generations are retained with `status=FAILED`;
they cannot be consumed. An evaluation with insufficient purged training,
validation, or test observations writes an honest report and exits with code 2.
It does not fabricate results or silently fall back to random splitting.

## Prediction contract

One observation is `(repository_id, stable_module_id, prediction_timestamp)`;
`observation_id` is its deterministic SHA-256 identity. Timestamps are UTC cutoffs,
not the selected commit's timestamp. Source features are reconstructed as of the
cutoff under the recorded analyzer; this does not prove the analyzer output was
available at that historical time.

The primary target is future minus current `sqale_index`, in minutes. Combined
bug/vulnerability/code-smell effort remains a separate predictor. Growth means
`debt_delta_minutes > growth_threshold_minutes`; the threshold is predefined in
the dataset manifest and defaults to 30 minutes. Negative deltas are allowed.

- `approx91` means exactly **91 calendar days / 13 weeks**, never 90 or 84 days.
- `exact90` requires a verified snapshot bound to **T0 + 90 calendar days**.
  An 84- or 91-day snapshot cannot satisfy that target. There is no automatic
  per-row substitution between horizon definitions.
- Missing endpoints, missing SQALE, deletion/unresolved lineage, or incompatible
  analyzer/profile/image/mode observations produce explicit status/reason fields
  and blank labels. Missing future values are never zero-filled.
- Compatibility is checked over all retained observations within the target
  interval, not just its endpoints. Unobserved intervals cannot establish that
  an analyzer never changed between retained observations.
- Changed membership is label-side diagnostic information. File identities
  decompose net change as **retained-file debt change + added-file future debt
  − removed-file current debt**. This describes observed composition; it does not
  establish a causal reason for deterioration or movement.

### Exact 90-day endpoint collection

The existing weekly collector need not be modified. First produce explicit
requests from verified weekly origins:

```bash
.venv-forecast/bin/python -m forecasting endpoint-plan \
  --workspace /absolute/workspace/commons-io \
  --output /absolute/endpoint-requests.json
```

This is read-only planning. To obtain those endpoints, run the additive bridge
inside the corresponding collector workspace with the original pinned scanner,
Sonar environment and credentials. This command **can submit real scans**:

```bash
cd /absolute/workspace/commons-io
PYTHONPATH=/absolute/source/td_pipeline \
  /absolute/source/td_pipeline/.venv-forecast/bin/python \
  -m forecasting.collector_bridge --collect-endpoints /absolute/endpoint-requests.json
```

Supplemental scans are isolated in `forecast_endpoints/data/`, keeping the legacy
weekly `data/snapshots.csv`, normalized exports and generation inputs unchanged.
The adapter calls the original scanner/export functions in its isolated process
with that evidence namespace, restoring their settings on exit. It holds the
parent workspace lock to prevent concurrent weekly scans against the project.
The first supplemental source commit needs its own scanner evidence; subsequent
identical supplemental commits reuse that evidence without rewriting original
proof paths. Pending exports resume without scanner resubmission.

It rejects future calendar endpoints and mismatched requests. The
`forecast_endpoints/data/forecast_endpoint_cutoffs.json` sidecar binds endpoint
labels to exact UTC cutoffs. If completion preceded this sidecar during an interruption, repeating
the command verifies the complete snapshot and recovers the binding. It never
pretends an unbound snapshot has a known cutoff. `build` verifies and merges the
separate endpoint namespace automatically. Then run `build --horizon exact90`.

## Causal identity and lineage

The new module-definition configuration is separate from the legacy mart's
frozen-root mapper. `auto` chooses build modules when the first observed tree has
at least two production-bearing build roots, otherwise package groups. The
strategy, earliest commit, package base/depth, production scope and repository
identity are recorded in `module_config_id`.

Build roots are discovered from **each historical tree**, enabling later module
births without redefining earlier snapshots. Package groups use actual package
declarations and the base/depth frozen from the earliest observation. Build and
package outputs carry distinct configuration identifiers; performance is also
reported by strategy. Models may pool their numeric features, so a heterogeneous
cohort must not be interpreted as evidence for either granularity alone.

Continuing modules preserve IDs when there is membership continuity. A complete
one-to-one transfer of members supports `RENAMED_MEMBERSHIP`; Git's exact-content
rename evidence preserves file IDs. Partial overlaps, splits, merges and fully
disjoint replacements are recorded conservatively. Ambiguous lineage anywhere
in a target interval excludes that label. Birth is **first observed presence**,
not a claim of the module's real creation date. Deletions are recorded as dated
lineage events; no zero-debt tombstone is synthesized. No semantic refactoring
oracle or heuristic similarity matcher is claimed.

## Graphs and features

Each snapshot reads immutable Git objects, not the working tree. It extracts:

| Relation / feature | Definition |
|---|---|
| Source dependency | Directed module edges from Java imports resolved to repository classes/packages; static imports supported |
| Build dependency | Directed literal Maven coordinates or Gradle project paths resolved to owned modules |
| Co-change | Undirected weight = number of ancestral commits touching both modules in the trailing 182 days |
| Contributor overlap | Undirected Jaccard overlap of contributor email sets in that same window |
| Degree / coupling | Dependency in/out degree and normalized distinct-neighbor count |
| Cycles | Membership in a directed dependency strongly connected component of size > 1 |
| Centrality | PageRank with alpha 0.85 on the directed dependency graph |
| Current metrics | Maintainability and combined effort, size, complexity, findings, file count |
| Temporal metrics | Observed-point count, mean and slope per week over 26-week histories |
| Activity | Commit count, churn and authors from historical module mapping |

Only the selected commit's ancestors with committer timestamps <= cutoff can
enter Git features. Later merges of backdated commits cannot alter an earlier
graph. Historical module names are mapped through the lineage known at the
current cutoff; new or recreated identities cannot inherit older unrelated
history. Merge commits themselves are excluded from co-change/churn.

Java parsing is a lexical import approximation: it masks comments and literals,
but does not resolve calls, reflection, same-package uses without imports, or
full compiler semantics. Maven profiles, properties, effective-POM resolution,
dependency-management inference, and executable Gradle logic are not evaluated.
External dependencies and unresolved imports are retained as diagnostics.
Malformed descriptors and dynamic Gradle coverage are explicitly recorded.

`source_coverage` measures eligible files lexically processed, **not semantic
resolution recall**. Build coverage measures descriptor completeness; literal
Gradle edges can exist while its descriptor completeness is unknown/partial.
`graph_status`, extraction counts, coverage and availability fields distinguish
an observed source graph with zero edges from missing historical snapshots or
partial build extraction. Mandatory Git/source failures fail the generation
instead of publishing an apparently healthy empty graph.

## Dataset artifacts

| Artifact | Contents |
|---|---|
| `manifest.json` | COMPLETE/FAILED state, schema/data version, prediction contract, module configurations, environment, implementation/input/output hashes, allowlists |
| `module_identity.csv` | Active module identities at observed cutoffs, first presence, lineage status, parent IDs and membership hashes |
| `module_membership.csv` | Module/file membership at each verified weekly or endpoint snapshot, stable file IDs, blob IDs, SQALE and separate combined effort |
| `module_weekly_state.csv` | All weekly module observations, including incomplete history and unknown numeric metrics |
| `module_edges_weekly.csv` | Snapshot-stamped typed directed/undirected edges; endpoint graphs are retained too |
| `module_graph_features.csv` | Snapshot graph statistics, availability and extraction coverage |
| `module_lineage.json` | Dated renames, file movements, ambiguous restructuring and deletion events |
| `unresolved_dependencies.json` | References and extraction failures with module, path, cutoff and reason |
| `module_sequences.npz` | `[observations, 26, features]` values/feature masks, `[observations, 26]` snapshot masks and timestamps; no pickle |
| `module_labels.csv` | 90/91-day net SQALE deltas, growth labels, status/reasons and future membership decomposition |
| `dataset_audit.json` | Counts, missingness, target distribution, growth events, changed-debt counts and history coverage |

CSV blanks mean unknown. NPZ zero placeholders have **false masks** and are not
observed healthy values or model imputations. Historical observations with
incompatible analyzer metadata are masked. M3/M4 must fit imputation/scaling using
training data only. `max_feature_timestamp` and explicit predictor allowlists
are checked when consuming the artifacts. Label fields never enter matrices.

Bundle readers check publication state, checksums, version and prediction/feature
contracts. Training checks target algebra and growth thresholds. Raw source
inputs are rehashed before and after transformation. Input evidence hashes are
retained for audit; a portable completed bundle can be evaluated without its
original absolute workspace paths. Hashes establish consistency, not authenticity.

## M0–M2 evaluation

M0 predicts zero debt change and zero probability of growth. M1 uses the explicit
current/temporal numeric allowlist. M2 uses exactly M1 plus graph statistics.
CatBoost fits a MAE regressor and Logloss classifier with fixed parameters, seed
42, CPU and one thread. Numeric missing predictors use CatBoost's native NaN
handling; no future or global imputation is fitted. Constant labels/features
produce explicitly recorded constant-training fallbacks.

All models use the **same observed-label population and folds**. Calendar folds
are independent of surviving rows and keep every repository snapshot together.
Training requires `label_end_timestamp < validation_start`. The test origin
period starts after validation end plus the horizon, ensuring validation labels
mature before testing. Multiple rolling windows must not overlap. At least three
eligible repositories enable leave-one-repository-out variants, with temporal
purging retained. Their fixed-parameter models never train on the held-out repo.

Reports include MAE, RMSE, absolute/relative gain versus persistence, changed-debt
MAE, unchanged-membership MAE, average precision (the reported growth PR-AUC),
and macro Precision@K across repository snapshots. Classification metrics require
at least two positive and two negative labels. Precision@K includes zero-positive
snapshot blocks rather than selecting only favorable blocks. If a block has fewer
than K modules it uses all available modules. Ties use deterministic observation IDs.

`folds.json` exports exact train/validation/test observation IDs, counts and
calendar boundaries. Reports expose row counts, modules, repository snapshot
blocks and disjoint label windows. Effective independent sample size is **unknown**;
these proxies are not asserted to be statistically independent samples.
`predictions.csv`, `model_comparison.json`, `MODEL_COMPARISON.md`, per-fold CBM
models/fallback metadata and the experiment manifest form the reproducible result.
Synthetic evaluations are explicitly marked `SOFTWARE_VALIDATION_ONLY`.

No tuning, test-driven model selection, production approval, confidence interval
claim, or deployment occurs automatically. Before drawing scientific conclusions,
review repository scope, sample size, label validity and uncertainty across
independent repositories/windows.

## Interfaces for future comparisons

`ForecastDataset.sequence(observation_id)` exposes causal values and masks.
`graph_window(observation_id)` supplies complete historical repository graphs
with stable node ordering, features/masks, typed weighted relations and the
origin module's node index. It returns no neighboring targets.

`aggregate_file_predictions()` implements the F2 aggregation boundary over
**origin-time membership only**; missing file predictions fail rather than change
the population. Its sum predicts changes for the current file population, so
scope-changing module targets require explicit interpretation. File probabilities
are not summed; a later calibrated aggregation model is needed for growth risk.
`align_external_predictions()` requires F1/F2/M3/M4 forecasts to match exported
fold cohorts exactly, with matching IDs and causal feature cutoffs. Use the shared
`evaluation.metrics()` on these aligned cohorts. F1/F2 fitting is deferred.

See `M3_M4_DESIGN.md` for the neural architecture contract.
