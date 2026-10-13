# Module-level pipeline: repaired evidence and missingness contract

This is the **weekly module technical-debt regression pipeline**, not the TechDebt360 V3
NPF-90 experiment. No V3 package, real execution workspace, scientific threshold, or evidence
was edited by this repair. Legacy file-level tools remain in the distribution for reference;
the validation report covers module mode and its shared collection/orchestration dependencies,
not an independent certification of the legacy file-level mart.

## Install and test without scans

Use Python 3.12, Git and a fresh environment:

```bash
cd td_pipeline
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

The tests use temporary Git repositories and synthetic Sonar responses. HTTP is forbidden in
tests and Docker is simulated. They do not scan your repositories or train a model.
On Windows use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.

## Missing is not zero

| Observation | Published module value |
|---|---|
| Every eligible file supplies the metric, including explicit zeros | Sum, status `OBSERVED` |
| One or more eligible files omit the metric | Blank, status `UNKNOWN_OBSERVATION` |
| Invalid, negative, NaN, infinite or malformed metric | Validation error |
| Complete issue export has no active issues | Observed zero findings/effort |
| Issue exists but its effort is absent | Finding counted; affected effort total blank |
| Issues export missing | Aggregation reports unknown; complete pipeline rejects incomplete evidence |
| Zero or missing denominator | Blank ratio/rating, never an invented healthy value |

For `ncloc` and each summed measure, `*_observed_files`, `*_missing_files`, `*_status` and
`*_partial_sum` describe coverage. A partial sum is **diagnostic**, not the module total.
Example: complexity values `10`, blank produce a blank `complexity_t0`, one observed file,
one missing file and partial sum `10`. Do not train on the partial sum as a substitute.
CSV blanks are missing values; readers must not fill them with zero automatically.

SQALE and code-smell effort are checked when both are observed. The existing 2% reconciliation
tolerance is retained, but a violation now stops the build. No finding severity/type is guessed.
Missing numeric predictors do not by themselves erase an otherwise observed origin/target.
TD and SQALE targets have separate statuses. Filter the particular target's `OBSERVED` rows
when fitting that target, not all horizons globally. Any predictor imputation must be fitted
on training data only; this package does not impute or train.

`issues_status` describes inventory availability, not effort completeness. `effort_status`,
`missing_effort_findings` and `observed_effort_minutes_partial` distinguish observed findings
whose remediation estimates are missing. Future membership counts, future statuses, deltas and
all per-horizon effort/TD/SQALE columns are label-side diagnostics and must never enter predictors.

The module debt ratio/rating are **derived** from `DEV_COST_PER_LINE_MIN` (default 30 minutes)
and the configured A–E bounds, not exported module ratings. Verify this choice against your server
settings before interpreting it as a Sonar-equivalent rating. Generation evidence records these
definitions and implementation hashes; combination rejects differently defined generations.

## Identity, scope and time

- Module strategy is frozen from the **earliest** observation, not future structure.
  `auto` chooses build modules only when at least two actual descriptor-backed production
  modules exist; orphan files do not manufacture a second module.
- Build roots, package base/depth, scope and repository identity are bound in
  `module_strategy.json`. Changes require a fresh workspace. Do not delete/recreate this
  file inside an existing dataset.
- Package membership comes from the Java package declaration. Deleted-file history uses
  the historical source declaration. Build IDs are frozen descriptor directory paths.
- Scope is Java under `src/main/java/` or `src/java/`, excluding test/generated/build/vendor
  source-root ancestors. A production Java package named `test` or class named `Sample`
  is not itself evidence of test/nonproduction code. Nonstandard roots require explicit
  `EXTRA_PRODUCTION_ROOTS` configuration before the run.
- Weekly T0 is the complete calendar-week endpoint in UTC. `commit_timestamp` is separate.
  The selected commit must exactly match the snapshot and be reachable on the first-parent
  history at that cutoff. Per-T0 Git features use only that commit's ancestors; later-merged
  backdated commits cannot enter earlier features. Shallow Git history is rejected.
- Horizons retain the existing 3, 4 and 12 weeks (not calendar months). Sonar trend windows
  retain 3, 4, 12 and 26 weeks. Analyzer/profile/image/mode compatibility is checked across
  the entire historical window and at each target endpoint.
- Partitions are fixed against the configured 100-origin calendar, independent of surviving
  rows. Default counts are 60 TRAIN, 12 PURGED, 8 VALIDATION, 12 PURGED, 8 TEST weeks. Later
  origins are `UNASSIGNED`, never silently moved into an existing test set.

## Source and Sonar evidence

The collector creates a new Git-archive source checkout per attempt. Scanner source scope is
explicit; the image must be an immutable `image@sha256:...`. Credentials come from environment
variables, never command-line token arguments. Captured scanner logs redact the configured token.

The scanner working directory is explicitly `/td-evidence/work`, mounted into its unique attempt
directory. Collection requires the original report-task, process return code zero, exact CE task
`SUCCESS`, matching project/analysis ID/revision, full pagination, stable analyzer/profile metadata,
and exact eligible source coverage. Raw responses, source SHA/blob records, logs and normalized
exports are checksummed. `complete_week_NN.json` is published **last**, after both exports and
the snapshot/metadata rows are durable.

An interrupted export can resume its existing task without re-scanning. If the server's current
analysis is no longer that exact analysis, recovery fails closed: current issues/measures must
not be attributed to an older analysis. Dedicated project keys are required; do not share a project
with another running scanner. `run_all_repos.py` checks workspace identity on reuse.

SOURCE_ONLY uses a clean source archive, explicit empty binaries/libraries and no build. It rejects
tracked class files and JARs in owned build-output trees. COMPILED requires an externally retained
successful build record, the exact source inventory/commit/tree, pinned build image, JDK 17 claim,
build-log hash and complete hashed class inventory; it no longer trusts a binaries directory alone.
This is integrity checking, not cryptographic authentication of whoever created the build proof.
No actual COMPILED build or real Sonar scan was exercised in this repair.

## Existing datasets: intentionally fail closed

Old exports without the required task/source/profile proof are **not automatically upgraded**.
Likewise a malformed or different `repo_context.json` is not silently reset. Preserve old data;
obtain/reconcile its genuine evidence separately, or explicitly authorize a fresh collection in a
new workspace. Do not invent proofs, re-hash contradictory evidence, or rerun scans just to make
validation pass. `--force` and destructive validator `--fix` are disabled.

For already valid evidence, run from its workspace:

```bash
/path/to/td_pipeline/.venv/bin/python /path/to/td_pipeline/validate_snapshots.py
/path/to/td_pipeline/.venv/bin/python /path/to/td_pipeline/build_module_mart.py 2020-01-02 main 138
```

Use the actual pinned start date, branch and weeks, not these example values. These two commands
do not scan. Multi-repository `--skip-scan` also does not clone, fetch, auto-repair or rescan.

For a **separately authorized new collection**, configure the repository registry, unique project
key, pinned image, Sonar URLs and secret environment first; then run `run_all_repos.py` in a fresh
output directory. No new collection was launched as part of this repair.

## Outputs and consuming them safely

| File | Meaning |
|---|---|
| `module_weekly_state.csv` | Every observed module/week, including missingness flags |
| `module_latest_snapshot.csv` | Most recent observed module state |
| `module_td_mart.csv` | Origins with history, per-horizon TD/SQALE status and fixed split |
| `module_generation.json` | Required publication status, input/output hashes, generation identity |
| `.generations/<id>/` | Preserved output generation or failure record |
| `combined_module_*.csv` | Combined verified repository generations |
| `combined_generation.json` | Required status/checksums for combined publication |

Require `module_generation.json.status == COMPLETE` and verify its hashes before using mirrored
CSVs. A failure preserves old CSVs but marks the current generation FAILED; old files must not be
mistaken for the new result. `run_all_repos.verify_generation()` performs this check. Empty outputs
have stable headers and replace stale results. Combination rejects wrong repository identities,
duplicate scientific units, incompatible schemas, failed generations and modified input/output files.
Any repository failure makes the orchestration command exit nonzero; no partial combined success
is published. Publication is atomic per file, with the final manifest as commit marker, not a single
filesystem transaction across every CSV.

## Interpretation and limits

- Missingness is honest, not a guarantee of model readiness. `training_ready` only means the
  configured train/validation/test partitions contain rows; inspect per-target statuses and sample size.
- Module membership can change. `membership_hash` and per-horizon added/removed file counts expose
  this. Fully disjoint membership is unresolved, not assumed to be the same healthy module.
- There is no general semantic module rename/split/merge tracker. Literal module IDs are not proof
  of architectural continuity. Package and build strategies are different granularities; stratify them.
- Finding arrivals/closures compare active issue-key sets at window endpoints. They are not gross
  arrivals/closures of findings that appeared and vanished between observations, nor semantic identity.
- Debt is analyzer-estimated remediation effort, not human-verified defect counts or observed cost.
  Zero findings require a complete observed population; they do not prove software is healthy.
- Snapshot data is collected later from historical commits. Features are *as-of source T0 under the
  recorded analyzer*, not proof that the same analyzer outputs were available in historical real time.
- Strict source/API contracts may reject unsupported repository layouts or newer Sonar schemas.
  A representative real-server smoke test still needs separate authorization. Offline PASS does not
  establish real analyzer equivalence, predictive performance, or permission to train/run V3.
