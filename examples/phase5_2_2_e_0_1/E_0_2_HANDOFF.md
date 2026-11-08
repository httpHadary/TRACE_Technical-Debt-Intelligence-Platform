# E.0.2 single-compilation handoff — authorization required

E.0.1 status: **SETUP_AND_CAPTURE_PASS**. Original E.0 stays BLOCKED.
No Maven lifecycle or dependency-runtime closure was exercised by this smoke test.

Before any real build, obtain explicit E.0.2 authorization. Keep E.0/E.0.1 attempt
claims and evidence intact; use one new versioned task directory and one container.
Do not use the archived `compile_phase5_2_2_e_0.execute_once` recipe.

1. Reverify T0 commit/tree/POM and all117 source/653 artifact hashes from the sealed
   manifests. Use independent copies and immutable read-only seed mounts. Recheck
   D.3 model identity and all original cache/ledger preservation references.
2. Reuse the owned tmpfs, archive validation, stage/EXIT-trap capture, terminal-log/
   daemon-event capture and ownership-checked cleanup helpers in `tools/build_sandbox.py`
   and `build_sandbox_setup.sh`. The current shell intentionally permits only
   `--no-maven-smoke`; E.0.2 needs a separately reviewed adapter after setup. Do not
   silently pass Maven to smoke mode or remove its expected-failure sentinel.
3. E.0.2's authorized adapter must agree on2GiB cgroup guard/host limit, heap768MiB,
   one CPU,64PIDs, zero extra swap and240second compile timeout. Preserve owned
   UID/GID1000 tmpfs, noexec/nosuid/nodev, bounded storage/files/logs, read-only image
   and seed mounts, no capabilities/new privileges/network/credentials/socket.
   Require at least2GiB host headroom beyond the admitted container budget.
4. Only the registered offline Maven lifecycle through `compile` may follow setup:
   Maven3.9.11 / Temurin17.0.17+10 in the same pinned image; release8,
   `maven.test.skip=true`, `user.home=/tmp`, no selected profiles or lifecycle skips.
   Retain original enforcers, RAT, buildnumber and resource executions. Do not add
   Git metadata, edit historical POMs or substitute dependency versions.
5. Capture setup and Maven stdout/stderr separately with stage-specific real exit
   codes. Extend the archive allowlist explicitly for bounded approved Maven and
   class metadata. Snapshot logs/state/OOM/events before cleanup even on early exit;
   mark missing cgroup evidence unavailable rather than estimating it.
6. Stop after one attempt. Missing artifacts must be reported at exact coordinates
   without enabling networking. Distinguish SCM-context failures from dependency
   failures. Claim COMPILE_PASS only after actual original lifecycle success,
   production-class completeness, hashes and Java8 bytecode checks.

No other revision, Sonar operation, scan, model, dataset admission or later phase
is authorized by this handoff. Old licensing/derived-dataset approvals are unchanged.
