# Phase 5.2.1 evidence

Status: **implementation PASS; overall PARTIAL; later runtime/collection BLOCKED**.
No scans, historical builds, actual measurements/targets or model runs.

| File | Evidence |
| --- | --- |
| `scope_contracts.json` | Implemented versioned roots, exclusions and new scope/feature/target IDs |
| `registrations.json` | Three development-only families, still quarantined pending rights/domain evidence |
| `source_inventory.json.gz` | Deterministic full source-only inventory:18 unchanged pinned states,2,046 path-state records,342 production path-state records; no source contents/debt values |
| `readiness_manifest.json` | Gates, unchanged resource limits,18 source-state identities and exact remaining blockers |
| `resource_observation.json` | Timestamped RAM/disk/CPU/container state and Docker limit capabilities |
| `runtime_artifact_inspection.json` | Offline pinned image/JDK/Maven/scanner/plugin/Node identities; static bytes, not successful runtime/build execution |
| `dependency_inspection.json` | Six pinned Java POMs;75 cached artifact identities; missing parent POMs71/76/78; no dependency resolution |
| `preservation.json` | Frozen file/bundle/database/checkpoint and old-container preservation receipt |
| `verification.json` | Final tests, deterministic source publication and source hashes |
| `manifest.json` | SHA256 of every other evidence file |

No third-party source archives, binaries, proprietary rule text, credentials,
full experimental datasets or model weights are included. Synthetic tests are
software fixtures only. No synthetic fixture is published as real pilot data.

See [implementation report](../../PHASE_5_2_1_IMPLEMENTATION_REPORT.md),
[interface contract](../../forecasting_multilanguage/production_scope/README.md)
and [future isolated inspection](../../FUTURE_ISOLATED_SERVER_INSPECTION.md).
