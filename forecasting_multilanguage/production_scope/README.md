# Production-root study v1

Opt-in entry point: `forecasting_multilanguage.production_scope`. The existing
`registry`, `admission`, `GitArchive`, `features`, `targets`, adapters and old CLI
remain byte-identical. Outer serialization retains schema2; **scope and study
semantics are versioned separately** as `production-root-study-v1`. No source is
implicitly migrated from the frozen study.

`scope.policy(repository_id)` defines only these three development populations:
Commons CLI `src/main` (.java), Click `src/click` (.py), Browser Reload
`src/django_browser_reload` (.py/.js). Each has a different scope hash, and new
scope-bound F0/F1 and exact30/60/90 target IDs. Proposal hashes from Phase5.2
are historical proposal identities, not the hashes of this implemented policy.

`ScopedGit(GitArchive(...), repository_id)` enumerates **all** tracked Git objects,
binds source/tree/blob/mode identities and records outside-root paths as well as
production files. Unknown production suffixes, nonregular in-root objects and
empty source populations block admission. Tests/docs/examples/vendor/generated
paths and minified/source-map files have explicit exclusions; `py.typed` and Java
`overview.html`/`package.html` are explicit noncode dispositions. Other in-root
assets/suffixes need another contract amendment; none is silently skipped.
Excluded-directory naming is not generated/vendor provenance proof.

The new registry adds exactly `contract_version`, `feature_contract_id` and
`target_contract_id` to the original field set. It accepts only the pinned
provider/family/URL/language combinations and development/quarantine roles.
For common shape, rights and UTC checks only, it uses a temporary **validation
projection** of the frozen registry shape. That projection is never published
or admitted. Real source registrations remain quarantined until reuse-policy
acceptance; these three families can never become confirmatory holdouts here.

`archive.read_archive(root, index, scoped_lineage)` reuses the hash-checked native
metric parser and returns `(observations, coverage_proofs)`. Each index entry
retains the old payload/coverage/inventory hashes and adds:

- `review_payload`, `review_sha256`: bound inventory ID, reviewer, all in-root
  reviewed paths and `REVIEWED_NO_UNRESOLVED_GENERATED_VENDOR_OR_NONCODE` status.
- `file_components_payload`: complete paginated export envelope with project,
  revision, analysis ID, exact `files=[{path, language}]` and completion flag;
  its bytes are bound by coverage `raw_file_components_sha256`.
- `scanner_completion_payload`: sanitized completion envelope with exit0,
  complete sensors, revision/project, analysis ID and CE task identity; coverage
  binds its `scanner_completion_sha256`.
- `ce_success_payload`: native task SUCCESS, matching task/project/analysis IDs;
  coverage binds its `ce_success_sha256`.

The inventory payload must equal the recomputed **full Git inventory object**,
including its identity and production paths. Coverage also carries version,
repository/scope/commit/tree/analysis/inventory identities, counts and exact
`analyzed_source_files`. Equal counts with different, duplicate, missing, extra
or misclassified files fail. Each normalized envelope must be backed by local
raw scanner/API/page evidence and ordered hashes; it is not proof merely because
someone wrote `COMPLETE` in JSON. A future collector must retain those originals,
check pagination totals and bind the scanner task/native revision before invoking
this importer. This phase does not implement that collector.

`admission.PastStore(registration, domain, scoped_lineage, observations,
coverage_proofs)` checks the new registry and exact coverage proof, then retains
all original state/time/domain/missingness/availability invariants. Native Standard
`sqale_index` minutes only; Java requires `java_compiled`; all declared analyzers
and measured languages must match. Actual native NCLOC must confirm the registered
language stratum, including both mixed programming families≥10%. Proxy line/file
counts never substitute. State lookup/window/proof methods reuse the frozen base
class; its old constructor is not used for new scopes.

`interfaces.build_features`, `prediction_input`, `origin_identity` and
`target_status` preserve the pure existing F0/F1 and exact-duration algorithms
through explicit identity projections and return new public contract/context/forecast
IDs. Git source-path activity now uses the scoped lineage. The model boundary
accepts only the frozen feature allowlist, checks source times and online
availability, and returns values/missingness flags without store handles, labels
or split metadata. Missing/unmeasured endpoint states stay UNKNOWN. F2 remains
disabled. No real features/targets/predictions have been materialized here.

Source-only evidence reproduction, using existing local objects:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python \
  -m forecasting_multilanguage.production_scope.readiness \
  --config examples/phase5_2/replay_sources.example.json \
  --pinned-readiness examples/phase5_2/readiness_manifest.json \
  --output /path/outside/git/to/new-scope-evidence
```

Use a new output directory; publication refuses overwrite. Source paths may be
adjusted to the same existing objects; source identity excludes the local path.
All18 original cutoffs/commits/trees/project keys must still match. This CLI
has no server startup, dependency fetch, build, scan, model or measurement path.
