# Compatibility and rollback

## Readers/writers and ownership

`scan_snapshot.py` owns append-only attempt/source/report-task evidence. `sonar_evidence.py` and
the `pull_*` entrypoints own complete normalized exports plus the final completion marker.
`validate_snapshots.py` and `build_module_mart.py` require that proof. The module builder owns
generation-specific outputs and their final manifest. `run_all_repos.py` consumes only verified
complete module generations when combining.

New columns expose metric/effort observation coverage, mapping/source identity and per-target
availability. Missing numeric cells remain blank. Existing names/horizons are retained; consumers
must support the added columns, missing values and generation status. Do not mix schemas, feature
policies or old/new code versions in a single active workspace.

## Forward path

1. Preserve the old code and data; do not overwrite an execution directory.
2. Install the repaired source and run its offline tests in a separate environment.
3. Existing exports may be reused only if their genuine source/task/profile/coverage evidence
   meets the new contract. No converter fabricates absent proof or silently turns blanks into zero.
4. If that evidence is unavailable, stop and report the missing prerequisites. A new collection
   requires explicit operator authorization and a fresh workspace; this repair did not launch one.
5. Export interruptions are resumable against the same CE/analysis identity while it remains the
   project's exact current analysis. A conflicting current analysis stops recovery rather than
   substituting newer measures. A crash leaves incomplete state visibly uncommitted.
6. Require COMPLETE generation manifests/checksums before consuming outputs. Keep failed/old
   generations for diagnosis. A stale `data/run.lock` must be investigated; never remove a lock
   while its process is active.

## Rollback

Original source is preserved in local baseline commit `cf726ca`. Export it to a separate directory
if needed, without checking out over repaired code or altering data:

```bash
git archive --format=zip --prefix=td_pipeline_original/ \
  --output=../td_pipeline_original_baseline.zip cf726ca
```

This recovers the old implementation, including its documented bugs. It does not make legacy
outputs scientifically valid. Keep old and repaired results clearly labeled and separate.
No destructive data migration, cache deletion, automatic admission or rescan is part of the repair.
