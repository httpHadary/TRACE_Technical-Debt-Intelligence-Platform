# Phase 5.1 — isolated multi-language data foundation

Schema **2**, single-node batch, Python standard library; no package installation,
model, inference worker, scanner, network collector or database mutation. This
package reuses only `forecasting_mvp.io` hash/path helpers and their existing pure
serialization dependencies. It does not change schema1 or published experiments.

The engineering targets are **Java-dominant, Python-dominant and genuinely mixed
Python+JS/TS**, all development-only. The third is not JS/TS-dominant. No fourth
project is included. See [the implementation report](../PHASE_5_1_IMPLEMENTATION_REPORT.md)
for actual data readiness; passing fixture tests does not establish a real pilot.

## Read-only commands

Run from the project root. Use an existing Python 3.12 environment. Outputs must be
new directories outside source archives/Git. A COMPLETE manifest seals artifacts
and records source/code hashes. Reusing an output directory is an error.

```bash
python3 -m forecasting_multilanguage --help
python3 -m forecasting_multilanguage audit-legacy \
  --db /path/to/td_V2.db \
  --sha256 8eb329e5e5690b884b98df824c4b94fc7582c5d610fa3bd12784b1e417b2684e \
  --git-sources /path/to/git_sources.local.json \
  --output /path/to/new-legacy-audit
python3 -m forecasting_multilanguage inventory-local \
  --root /approved/local/archive-root \
  --exclude /approved/local/archive-root/model-and-output-root \
  --exposure-records /path/to/prior_identity_records.json \
  --output /outside/source-roots/new-inventory
```

`git_sources.local.json` is a JSON object mapping **native V2 PROJECT_ID** to an
already available Git checkout. An empty object is valid and explicitly reports
unavailable Git proof. No fetch/clone, checkout, filter, textconv or external diff
is run. First-parent changes use pinned Myers/no-renames semantics; roots use the
empty tree, merges compare only against the first parent. Missing/binary/ambiguous
path evidence is never zero-filled. F2 is disabled regardless of sample results.

Exposure records have `identity` and `source_ref` strings. Exact URL aliases
coalesce; names and fork families without proof remain unresolved. Every prior
family is exposed, including old sealed cohorts. No new confirmatory cohort is
reserved by this package. Search limits/exclusions, inaccessible directories and
truncation are recorded. Inventory is discovery, **not automatic admission**.

## Strict archive import

```bash
python3 -m forecasting_multilanguage build-archive \
  --study /path/to/registered-study.json \
  --domain /path/to/analyzer-domain.json \
  --index /path/to/snapshot-index.json \
  --archive /path/to/immutable-archive \
  --git /path/to/existing-git-checkout \
  --cutoffs /path/to/registered-cutoffs.json \
  --output /path/to/new-schema2-bundle
```

This Phase5.1 command admits development-only registrations. Cutoffs are a JSON
list of timezone-aware UTC strings, normalized to `Z`; duplicate UTC instants are
rejected. Unknown origins are retained in `origin_admission.json`; unexpected
software/integrity failures abort publication. Labels are constructed only after
all past-only feature records are complete. No predictions are generated.

Registration fields are validated by `registry.validate_registration`; the
[template](study.schema2.example.json) is deliberately quarantined and contains
no real repository or measurements. Data reuse rights are separate from source
code licensing. `source_digest` identifies the owner's immutable source manifest.
It is not evidence of a license just because it is a valid hash.

`analyzer_domain()` requires server/edition, scanner/image digest, complete plugin
key/language/version/binary hashes, rules/settings, scope, runtime/dependency and
suppression-policy hashes, build mode, metric mode and semantic version. Unknown
fields give INCOMPLETE; malformed identities fail. The first study accepts
`STANDARD` + `native_sqale_index_minutes_v1`, not automatic MQR conversion. Java
requires `java_compiled`, C# `dotnet_begin_build_end`, C++
`cfamily_compilation_database`; entitlement/build provenance must come from the
archive owner. Mixed compiled scanner combinations and new suffix/capability
policies need a separate registered extension. The initial source policy covers
Java, Python, JS/TS, C/C++, C# and Go and excludes test/vendor/generated paths as
specified in `SCOPE_POLICY`; it is a declared production programming scope,
not a claim about unrecognized file types or every Sonar-supported language.

Each snapshot-index entry has:

```text
repository_id, family_id, commit_sha, source_tree_sha, state_utc,
analysis_id, executed_utc, available_utc (nullable), retrieved_utc,
domain_id, scope_id, native_project_key,
payload, raw_payload_sha256,
inventory_payload, inventory_sha256,
coverage_payload, coverage_sha256
```

All paths are relative, symlink-free, SHA256-verified archive paths. `payload`
is an archived envelope with native `analysis_id`, `revision` and
`component: {key, measures: [{metric, value}]}`. The envelope must preserve
authoritative analysis/revision linkage; this adapter does not infer it from a
modern mutable measures endpoint. Supply `sqale_index` and
`ncloc_language_distribution`. Keep raw exports/envelope provenance in the owner
source manifest; the importer checks consistency/integrity, not authenticity of
invented owner assertions.

`inventory_payload` has `commit_sha` and unique `production_paths`; these must
match the exact Git tree under the registered scope. `coverage_payload` has
`commit_sha`, `analysis_id`, `status: COMPLETE`, positive
`expected_source_files`, equal `analyzed_files`, and zero `failed_files` and
`unsupported_files`. Every declared language must have positive measured NCLOC,
an installed plugin and corresponding actual production files; extra analyzed
language scope is rejected. Partial analysis cannot become whole-scope debt.

Lineage is a complete, nonshallow, monotonic first-parent chain ending at the
registered immutable tip. Commit-time ties resolve by ancestry. Missing objects,
inversions, unmeasured selected revisions, tree mismatches and contradictory
same-state metrics do not admit invented states. A later revision with the same
tree does not license carry through an unmeasured change. Endpoint proofs use
the independently resolved state exactly 30/60/90×86400 seconds later. Unknown
endpoints retain null actuals/status/reason. There is no interpolation, nearest
timestamp, daily grid or 91-day substitution.

Retrospective reconstruction explicitly does not claim historical online
availability. Operational-as-of additionally requires contemporaneous branch and
measurement availability; absent proof blocks input admission. Git activity
without historical availability remains missing in operational mode. Current
local legacy data have not passed those operational requirements.

## Feature and artifact contracts

F0/F1 names are frozen in `features.py` and the [feature matrix](../FEATURE_AVAILABILITY_MATRIX.md).
Git windows are `(t0−L,t0]`; trends use actual elapsed UTC days and require at
least three distinct states and timestamps. A 30-day lag requires its own exact
state proof. Zero activity in a complete window differs from unknown history;
no-event last-commit age is censored/null, not a fabricated 90 days.

`build_features(store, cutoff)` emits values/statuses/reasons and source evidence.
`prediction_input(record, expected_cutoff=...)` returns only allowlisted F0/F1
values and past-observability missing indicators. Routing IDs, split roles,
target status, endpoint IDs and labels stay outside X. This contract is not a
sandbox for arbitrary code. Caller must use this boundary in future modeling.

Strict bundles contain snapshots, long typed measurements, language coverage,
Git event metadata, feature CSV/evidence JSONL, origin/label CSVs in separate
files, origin admissions, registry/domain/provenance/cohort/readiness JSON and a
schema2 COMPLETE manifest. Null CSV values are empty with explicit status/reason
sidecars; observed zero remains `0.0`/`0`. Debt units are Sonar **estimated
maintainability remediation minutes**, not actual developer repair effort.

`candidate_measurements()` preserves raw V2 project/analysis/revision/date
references and missingness in the **LEGACY_DOMAIN_UNVERIFIED** lane. Raw dates are
not automatically treated as UTC. It cannot produce strict model input by
assigning made-up analyzer metadata. The audit checks all exact joins and keeps
the old Phase1/2 datasets untouched.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider \
  tests/test_multilanguage_foundation.py
```

Tests use explicitly synthetic software fixtures and local temporary Git objects.
They are not real-world forecasting evidence. No real model or scan runs.

The additive [native project / persistence v2 lane](NATIVE_PROJECT.md) admits
strict offline project aggregates for Python, Java, JS/TS and mixed repositories.
It has separate SQALE and total-principal targets and preserves native language
coverage without changing the original study/adapters above.
