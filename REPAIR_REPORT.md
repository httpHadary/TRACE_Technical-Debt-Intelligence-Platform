# Module pipeline repair — 2026-10-10

**Offline repair validation: PASS.** This result covers the repaired module path and its
collection/orchestration dependencies. It is not a guarantee that every possible defect is absent,
a real Sonar smoke result, an independent scientific review, or approval to train a model.

## Reproduced defect

The original `fnum()` was executed from baseline commit `cf726ca`, independently of the modified
implementation. The observed results were:

| Input | Before | After |
|---|---|---|
| Empty string | `0.0` | `None` (CSV blank) |
| `None` | `0.0` | `None` |
| `broken` | `0.0` | ValueError |
| Explicit `0` | `0.0` | `0.0` |

Initial missingness regressions exposed the additional missing-export, incomplete-sum,
duplicate-row and unknown-taxonomy problems. They are retained in `tests/test_missingness.py`.

## Repair coverage

| Responsibility | Repair and regression evidence |
|---|---|
| Missing metrics/effort | Unknown stays unknown; invalid numeric input rejected; partial sums and missing counts separate from totals; no invented healthy rating; fractional effort preserved |
| Issues and module totals | Missing inventory distinct from observed zero; duplicate keys/rows and unmeasured production findings rejected; explicit taxonomy; strict effort units; SQALE reconciliation is enforced |
| CSV/JSON contracts | Unique headers/identities/JSON keys, complete row widths, canonical paths; NaN and infinity rejected; atomic output writes |
| Source/module mapping | Git blob source inventories; actual Java package declarations; earliest-snapshot strategy and frozen roots/depth; config/repository-aware caches; orphan build roots do not count as modules |
| Git history/time | Exact snapshot/resolver commits; separate calendar T0 and commit time; checked Git failures; UTF-8/NUL-safe paths; per-T0 ancestry excludes later-merged history; deleted files use historical declarations |
| Targets/trends | Full-window analyzer/mode/profile compatibility; independent TD/SQALE target status; missing optional predictors retained; membership change exposed; disjoint lineage unknown |
| Splits | Fixed configured calendar, 12-week purge, no survivor-dependent or weekly-update partition movement; later origins UNASSIGNED |
| Sonar task/export | Explicit scanner work directory, original report-task, process success distinct from CE SUCCESS, exact project/analysis/revision; complete paginated exports; changed profile parameters detected |
| Scan inputs | Pinned scanner digest, clean source archive, explicit source/test/binary settings, read-only source mount, token outside argv and redacted logs; source/command/property contradictions rejected |
| Compiled/source-only distinction | Empty SOURCE_ONLY binaries and no-build evidence checked; COMPILED requires matching source/commit/tree, successful build, JDK/image/log/hash/class inventory evidence |
| Resume/preservation | Failed attempts retained; export recovery never silently launches another scan; completion marker only after all exports/metadata; force-overwrite and destructive validator disabled |
| Validation/orchestration | No empty/uncheckable PASS; every repeated-commit week checked; nonzero errors stop the pipeline; skip-scan does not fetch/clone/re-scan; workspace calendar/identity cannot silently change |
| Output/combination | Preserved generations, explicit FAILED/COMPLETE state, stable empty schemas, input/output/config/implementation checksums; wrong repository, duplicate unit, altered input and stale generation rejected |

## Validation

The clean Python 3.12 environment ran **137 tests, all passing, no skips/failures**. The suite
includes a full synthetic producer/export/validator/Git/module/target/CSV/combination roundtrip:

- 138 complete weeks from an actual temporary Git repository;
- one unchanged source commit reused without 138 repeated scanner submissions;
- 100 origin rows, with 60 TRAIN, 24 PURGED, 8 VALIDATION and 8 TEST;
- absent complexity remains blank with the expected coverage/partial-sum fields;
- zero debt is observed only with a complete empty issue inventory;
- calendar T0 differs correctly from an unchanged older commit timestamp;
- shorter collection preserves origin IDs/splits; an empty mart replaces the previous mirror;
- changed exports cannot make a failed generation eligible for combination;
- a missing effort estimate does not erase an independently observed SQALE target.

Further tests exercise rehashed source/task/report/analysis/scope contradictions, interrupted-export
resume without scanner calls, CE failure, malformed pagination, unknown metrics, duplicate CSV rows,
backdated branches, deleted source files, compiled evidence and workbook/registry validation.
Python compilation, CLI help, dependency consistency and `git diff --check` also passed.
Docker and HTTP responses are simulated; the fixture deliberately does not prove live-server behavior.

Reproduce from the delivered source directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q .
.venv/bin/python -m pip check
```

The delivered ZIP is additionally extracted and tested separately. Its external handoff verification
record and SHA-256 sidecar accompany the archive; the source report does not embed its own ZIP hash.

## Exact implementation scope

Modified production files:

`build_module_mart.py`, `config.py`, `modules.py`, `pull_analysis_metadata.py`, `pull_issues.py`,
`pull_metrics.py`, `run_all_repos.py`, `run_pipeline.py`, `scan_snapshot.py`, `scan_weekly_snapshots.py`,
`td_utils.py`, `validate_snapshots.py`, `weekly_commits.py`.

Added production helpers: `contracts.py`, `sonar_evidence.py`.

Added tests: `tests/conftest.py`, `test_missingness.py`, `test_contracts.py`, `test_collection.py`,
`test_module_integration.py`, `test_orchestration.py`, `test_binary_policy.py`.

Added/updated support: `.gitignore`, `requirements.txt`, `requirements-dev.txt`, `README.md`,
`MODULE_LEVEL_README.md`, `CHANGES.md`, `TD_Pipeline_Documentation.md`, `TESTED_ENVIRONMENT.txt`,
this report and `MIGRATION_NOTES.md`.

The implementation is confined to `td_pipeline_module_level/td_pipeline`. No existing real data,
external `combined_td_mart.csv`, TechDebt360 V3 package/workspace, admission, cohort, V2 reference,
training code or model artifact was modified. Validation artifacts are separate under
`research/module_pipeline_repair/20261010`. Neither real scans nor real cohort builds were run.

## Compatibility and remaining limits

See [MIGRATION_NOTES.md](MIGRATION_NOTES.md) before using old exports. Existing data was not
rewritten. Missing genuine provenance cannot be inferred from a CSV or made valid by re-hashing it.
The legacy file-level feature/mart implementations are retained, not claimed to have received the
same module-level missingness/identity review. Use `--level module` for this validated workflow.

General semantic module rename/split/merge matching remains a research-design limitation, not a
silently solved identity problem. Literal module IDs and dynamic membership require interpretation.
Endpoint issue-key differences are not gross finding lifecycle counts. Derived rating formulas must
be aligned with the operator's server settings. Hashes prove consistency, not an external author's
honesty. A real-server integration test, actual build/runtime verification, representative repository
scope review, label review and model suitability assessment remain separate work requiring evidence
and authorization. No predictive/scientific PASS is claimed.
