# Phase 5.2 metadata evidence

Planning only: zero scans, zero native observations, zero labels and zero model runs.
The three PRIMARY candidates are development-only. Other rows document screening,
not additional pilot targets or a new held-out cohort. Source-text line proxies
are not Sonar NCLOC or measured language strata.

- `selected_source_plans.json`: six exact cutoffs, full commit/tree identities,
  complete first-parent checks, inventories and frozen scope mismatches.
- `tracked_source_inventory.jsonl.gz`: all tracked paths/object IDs and explicit
  scope dispositions at the 18 primary cutoff states; no source file contents.
- `source_candidates.json`: metadata, license/exposure checks and alternatives.
- `capability_manifest.json`: offline binary versions/digests/licenses, resources
  and unknown live mode/profile state. No proprietary rule text or credentials.
- `scope_extension_proposal.json`: a future versioned amendment, NOT applied.
- `schema2_contract_preflight.json`: existing validators reused without bypasses.
- `historical_collection_spec.json`: future fixed settings/runtime/build/native-completion contract; no scanner runner.
- `historical_build_provenance.json`: historical license/config hashes and cache
  inventory summaries; no build success is inferred from their existence.
- `readiness_manifest.json`: all 18 planned jobs, budgets and blocking gates.
- `replay_sources.example.json`: host-specific paths; adjust to bounded immutable
  source mirrors on another machine, retain pinned tips and UTC cutoffs.
- `verification.json` and `manifest.json`: tests, preservation and integrity.

Source attribution: Apache Commons CLI, https://github.com/apache/commons-cli
(Apache-2.0; retain LICENSE/NOTICE for any later source redistribution);
Pallets Click, https://github.com/pallets/click (BSD-3-Clause);
Adam Johnson's Django Browser Reload,
https://github.com/adamchainz/django-browser-reload (MIT);
Django Debug Toolbar, https://github.com/django-commons/django-debug-toolbar
(BSD-3-Clause). No source archives, third-party binaries or rule text are included.
Source licenses do not automatically certify new dataset/model publication rights.
Those decisions remain an explicit collection gate.

See [preflight report](../../PHASE_5_2_PREFLIGHT_REPORT.md),
[candidate decision](../../REAL_PILOT_REPOSITORY_CANDIDATES.md) and
[future execution plan](../../HISTORICAL_SCAN_EXECUTION_PLAN.md).
