# Task D dependency evidence

Status: **PARTIAL**. Parent POMs71/74/76/78 and their Apache parent chains are
verified; the static compile dependency frontier remains incomplete.

- `dependency_manifest.json`:509 verified acquisition artifacts, SHA256/source
  URLs/repository checksums;433 staged candidates and76 earlier unused candidates.
- `requirements.json`:six pinned revision inventories, profile decisions,
  plugin declarations, static closures and exact unresolved frontier.
- `readiness_manifest.json`:fixed gates,22 missing frontier files, resource limits
  and explicit non-readiness for offline compilation.
- `verification.json`:regression, deterministic offline audit and preservation.
- `manifest.json`:hashes for this metadata-only bundle.

No third-party POMs/JARs, credentials, weights or datasets are published.
See [Task D report](../../PHASE_5_2_2_D_REPORT.md). Task C/E/F were not started.
