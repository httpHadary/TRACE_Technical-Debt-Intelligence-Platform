# Task B runtime evidence

All five actual offline version probes passed. Maven retained a Jansi native
console warning caused by noexec `/tmp`; that limitation is explicitly recorded.
No server/build/scan/model execution. Task C was not started.

- `runtime_evidence.json`: image/artifact hashes, actual outputs/versions,
  exit codes, cgroup memory/CPU readings, limits, setup warning and cleanup.
- Five runtime `.log` files: complete small version/measurement logs.
- `verification.json`: tests, preservation and cleanup proof.
- `manifest.json`: artifact integrity hashes.

No binaries, private exports, secrets, dependencies or datasets are included.
Task A rights approvals and all frozen experiments remain unchanged.
See [Task B report](../../PHASE_5_2_2_B_REPORT.md).
