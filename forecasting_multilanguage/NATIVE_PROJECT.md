# Native project archives and persistence v2

This additive, offline lane admits archived native **project aggregate** values for
Python (`py`), Java (`java`), JavaScript (`js`, including JSX), TypeScript (`ts`,
including TSX), and mixtures. It does not run scanners, builds, downloads, models,
or live Sonar requests. The original study, adapters, production-root policies,
v1 source/presentation formats and historical principal import are unchanged.

Two explicit targets are available, one per bundle:

| Target | Native Standard-mode value |
| --- | --- |
| `native_sqale_index_minutes` | `sqale_index`, maintainability SQALE |
| `native_total_principal_minutes` | `sqale_index` + `reliability_remediation_effort` + `security_remediation_effort`, only when all three exist |

Every component uses `estimated_remediation_minutes`. Absent/null components stay
missing. SQALE can be forecast when security/reliability are absent; total
principal cannot. No file-debt sum, language debt attribution, NCLOC proxy,
MQR alias conversion or synthetic real-project value is admitted.

## Commands

Given an existing complete local Git repository and an operator-provided export:

```bash
python3 -m forecasting_multilanguage ingest-native-project \
  --index /exports/index.json --archive /exports/payloads \
  --git /sources/project --target native_sqale_index_minutes \
  --output /outputs/native-source.json
python3 -m forecasting_mvp persistence-build \
  --source /outputs/native-source.json --out /registry/project-sqale
# Or ingest and build in one command:
python3 -m forecasting_mvp persistence-ingest-native \
  --index /exports/index.json --archive /exports/payloads \
  --git /sources/project --target native_total_principal_minutes \
  --out /registry/project-principal
python3 -m forecasting_mvp persistence-verify --bundle /registry/project-sqale
python3 -m forecasting_mvp persistence-serve --registry /registry
```

Outputs must be new and outside archive/Git sources. The same GET-only API at
`/api/mvp/v1` serves verified v1 and v2 bundles, including target, units, full
native measured language NCLOC, scope/domain and provenance. The dashboard uses
bundle target labels and distinguishes ancillary coverage. It offers persistence
only. Native forecasts repeat the selected latest observation's stock, with zero
predicted change and null intervals. Missing latest values remain unavailable.

## Exact archive contract: `native.project.archive.v1`

All objects below require exactly the listed fields. JSON duplicate keys,
nonfinite values, invalid numbers/units, unsafe paths, conflicting identities,
partial evidence and unsupported domains are rejected. Paths are canonical
repository-relative POSIX paths. Digests are lowercase SHA-256; Git identities
are full lowercase 40- or 64-character object IDs. Clocks are canonical
`YYYY-MM-DDTHH:MM:SSZ`; no timestamps are invented or adjusted.

The index has `version`, `source`, `registration`, `domain`, `horizons`, `entries`.
`source` is the existing provenance object: `source_id` (safe API identifier),
`kind` (`SYNTHETIC` or `OPERATOR_PROVIDED`), `description`, `permission`,
`provenance`. All claims must be explicit nonempty text. Synthetic fixtures are
always labeled `SYNTHETIC`; source rights, reviewer claims and authenticity are
not permissions granted or independently authenticated by this software.

`registration` contains `repository_id`, `family_id` (safe API identifiers),
`canonical_url` (credential-free HTTPS claim), `tip_sha`, `ref_observed_utc`,
`declared_languages` (unique programming keys), `scope`. Scope contains `roots`
(directory paths, or `.`), `excluded_paths` (explicit files/directories),
`review_status` equal to
`REVIEWED_NO_UNRESOLVED_GENERATED_VENDOR_OR_NONCODE`, and nonempty `reviewer`.
Exclusions must exist in the archived tree. All tracked paths are reviewed;
programming source beneath roots must be completely analyzed unless explicitly
excluded. Generic registrations do not alter any frozen pilot registrations.

`domain` uses the foundation `analyzer_domain` contract, with all fields complete:
`server_version`, `edition`, `scanner_version`, `scanner_image_sha256`, `plugins`,
`rules_sha256`, `scope_policy_sha256`, `build_mode`, `runtime_manifest_sha256`,
`dependency_policy_sha256`, `suppression_policy_sha256`, `metric_mode`,
`metric_semantics`. Scope hash equals the foundation canonical digest of `scope`.
Mode is exactly `STANDARD`; semantics are exactly
`native_standard_remediation_minutes`. Build mode is `source_only` for
Python/JS/TS, or `java_compiled` for Java and any mixture containing Java.
A Java source-only domain is blocked. Runtime/settings/rules/dependency hashes
and matching installed analyzers are mandatory even for source languages.
Each plugin has `key`, `language`, `version`, `binary_sha256`. A plugin with
language `js` or `javascript` may cover both `js` and `ts`; all other native
languages require a matching plugin language. Complete metadata hashes bind
operator-supplied evidence; they do not prove that Java was compiled.

`horizons` registers either/both `revision_step: [3,4,12]` and
`elapsed_day: [30,60,90]`, exactly as in v1.

Each entry contains `project_key`, `analysis_id`, `revision`, `source_tree_sha`,
`state_utc`, `executed_utc`, nullable `available_utc`, `retrieved_utc`, `artifacts`.
Each revision and native analysis ID is unique, and all entries use one project.
Git first-parent ancestry must be complete, nonshallow and chronological.
Revision, tree and state time must match existing local Git objects. State time
cannot follow execution; execution cannot follow retrieval; known availability
falls between execution and retrieval. Two measured commits sharing the same UTC
second are explicitly blocked by the existing persistence observation clock;
Git lineage itself may retain equal-time unmeasured commits.

`artifacts` has exactly `measures`, `inventory`, `coverage`, `files`, `scanner`,
`ce`; each reference contains `path` and the raw UTF-8 file's `sha256`. Every
referenced object carries the same four binding fields:
`project_key`, `analysis_id`, `revision`, `source_tree_sha`.
The following additional fields are exact:

| Artifact | Additional fields and constraints |
| --- | --- |
| `measures` | `component`: exactly `key`, `qualifier: "TRK"`, `measures`. Key equals project. Measures are unique objects with exactly `metric`, `value`, `unit`. Allowed keys are the three effort keys, `ncloc` (unit `lines`), `ncloc_language_distribution` (unit `native_language_distribution`). Native effort values are null, finite nonnegative JSON numbers or unsigned decimal strings. Missing effort keys remain missing. |
| `inventory` | `git_files`: sorted unique complete tracked tree paths; `production_paths`: sorted scoped programming paths; `reviewed_paths`: exactly `git_files`. Scoped Git entries must be regular blobs, never symlinks/submodules, including paths without a recognized language suffix. |
| `files` | `pagination_complete: true`, `files`: unique `{path, language}` objects for all recognized programming/ancillary paths in the scope. No file debt metrics. |
| `coverage` | `status: "COMPLETE"`, integer `expected_source_files` and `analyzed_files` both equal nonempty programming inventory length; integer `failed_files: 0`, `unsupported_files: 0`; `analyzed_source_files` equals sorted programming `{path, language}` objects from `files`. |
| `scanner` | integer `exit_code: 0`, `sensors_complete: true`, nonempty `ce_task_id`. |
| `ce` | `task`: exactly `id` matching scanner task, `status: "SUCCESS"`, `analysisId` and `componentKey` matching binding. |

Language distribution is the native `py=123;js=45` string (comma also accepted),
with unique nonnegative integer values. Its keys exactly match analyzed file
languages and its sum equals native project `ncloc`. It is retained in full;
NCLOC is not estimated from source text. Ancillary suffixes supported here are
XML (`xml`), CSS (`css`), HTML (`web`), JSON (`json`), YAML (`yaml`), with matching
analyzers. Ancillary coverage never creates another programming family. Other
programming languages/suffixes require an explicit later capability extension.
The source inventory suffix rules are reused without changing frozen policies.

These are normalized **archive envelopes**, not a claim that Sonar REST returns
all identity/unit/completion fields in one response. The exporter must preserve
native project identity, actual analysis/revision/tree binding, complete
pagination and native scanner/CE success evidence when constructing them.
Authenticity of supplied exports remains an explicit operator claim.

## Persistence source, replay and actuals

Ingestion emits `persistence.observations.v2` with exactly `version`, `source`,
`target`, `unit`, `horizons`, `admission`, `observations`. Admission contains
`version`, `registration`, `domain`, `entries`, `evidence` (each original raw
UTF-8 artifact string, so byte hashes replay), `git_identity`,
`revision_sequence` (complete first-parent `sha`, `tree`, `timestamp`, `parents`).
Ingestion checks this sequence/inventory against local Git. Self-contained replay
validates hashes, evidence, domain, lineage structure, identities and derived
observations; it does not re-open the source repository or independently
re-authenticate operator claims.

Each derived observation has the v1 row fields plus `native`; its ID hashes its
selected target and full row. Native metadata retains typed metric statuses,
full measured languages, programming/ancillary languages, family, project and
analysis IDs, tree, scope/domain, all evidence hashes and lineage-prefix hash.
History, forecasts, evaluations and summary retain target/unit and native source
evidence. Forecast IDs are target-qualified. Publication uses
`persistence.presentation.v2`, kind `NATIVE_OBSERVATIONS`, with the same exclusive
output, manifest-last publication, prediction seal and semantic replay used by
v1. The v1 defaults and bytes remain unchanged.

Optional `--actuals` is read only after predictions are written and sealed. Native
actuals require `persistence.actuals.v2` with exactly `version`, `source`,
`target`, `unit`, `admission`, `actuals`. Admission uses the same archive proof
contract, including a Git sequence extending the sealed origin prefix. Each
actual has the v1 actual fields plus `native`, identical to its admitted
endpoint's native metadata. Target, clock, horizon, origin, repository, domain,
scope, native project, component values and revision index must match. Evaluation time must
select that exact state from the complete archived Git sequence and remain
within observed-ref evidence. An unmeasured changed state blocks evaluation;
stale/nearest measurements cannot fill it. Calendar horizons require exact UTC
cutoffs. Cross-clock chronology and unchanged-revision consistency remain
checked by the shared engine. This lane uses retrospective archived measurements;
it does not claim historical operational availability or current accuracy.

## Offline proof and real Click blocker

The executable fixture builder and negative cases are in
[`tests/test_native_project_persistence.py`](../tests/test_native_project_persistence.py).
They create tiny Git objects and invented Sonar-shaped envelopes, including
Python first, Java, JS, TS and mixed/ancillary coverage. Reproduce with:

```bash
python3 -m pytest -q tests/test_native_project_persistence.py \
  tests/test_multilanguage_foundation.py tests/test_multilanguage_preflight.py \
  tests/test_production_scope_readiness.py \
  tests/test_persistence_flow.py tests/test_persistence_api.py
```

This proves software behavior only. No real Click native export was present.
The unchanged [Phase 5.2 source audit](../examples/phase5_2/README.md) and
[Phase 5.2.1 evidence](../examples/phase5_2_1/README.md) retain source-only Click
references; both readiness manifests record zero native scans/measurements.
Click remains quarantined pending rights/content review, full analyzer/runtime
and rule/settings evidence, successful archived scanner/CE completion and complete
native project/language measurements. Those historical source inventories are
not NCLOC or debt measurements and are not converted by this feature.

Read the source-only audit without modifying evidence or contacting a service:

```bash
python3 - <<'PY'
from contracts import read_json
for name in ('phase5_2', 'phase5_2_1'):
    report = read_json('examples/' + name + '/readiness_manifest.json')
    print(name, {k: report[k] for k in report if k.startswith('actual_')})
report = read_json('examples/phase5_2_1/readiness_manifest.json')
for row in report['planned_source_states']:
    if row['repository_id'] == 'pallets/click':
        print(row['commit_sha'], row['tree_sha'], row['native_analysis_id'], row['raw_measurement'])
PY
```
