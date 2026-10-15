# Phase 5.2.2-B — Isolated runtime probes

Date: **2026-10-16**. Verified starting `main`:
`42493f8442ccd5901a2146c694b4af509506bcbb`.

**Task B PASS: all five actual version probes succeeded.** Every checked artifact
matches the published Phase5.2.1 SHA256. Maven emitted a native-console warning
under the retained noexec temporary-filesystem policy; its version command still
exited0. This warning is preserved below and in raw evidence.

No SonarQube server was started, no historical build/scan or Maven project goal
ran, and no provisioning, dependency/plugin download or model execution occurred.
Task C was not started. Task A's unresolved rights and publication decisions
remain unresolved; version success does not grant permission or admit data.

## Actual results

| Probe | Observed identity | Exit | Command wall time | Cgroup peak memory | CPU usage |
| --- | --- | ---: | ---: | ---: | ---: |
| SonarScanner CLI |8.0.1.6346|0|0.71s|86,396,928 bytes (~82.39MiB)|774,804µs|
| Scanner Java |Corretto21.0.11+10-LTS|0|0.03s|20,054,016 bytes (~19.12MiB)|89,019µs|
| Maven |3.9.11; reports Java17.0.17 / Eclipse Adoptium|0|0.44s|68,644,864 bytes (~65.46MiB)|489,239µs|
| Build Java |Temurin17.0.17+10|0|0.05s|18,116,608 bytes (~17.28MiB)|108,202µs|
| Embedded Node |v24.11.0 in pinned scanner image|0|0.01s|5,902,336 bytes (~5.63MiB)|66,716µs|

Raw [runtime evidence](examples/phase5_2_2_b/runtime_evidence.json) and the five
`.log` files retain stdout/stderr, exit codes, image IDs, exact command arrays,
resource readings and cleanup records. No timeout or OOM occurred.

Wall time comes from `/proc/uptime` sampled before/after the command, with
10ms clock granularity; host start/wait timing is recorded separately. Cgroup
`memory.peak` and `cpu.stat` are read while the wrapper remains alive after the
command. They include wrapper/helper overhead up to that reading, rather than
claiming per-JVM-only consumption or including final container shutdown.

### Maven native-console warning

Maven's Jansi2.4.2 native library could not map an executable shared-object segment
from `/tmp`, which Docker mounts noexec in this configuration. The version output
and JDK identity were successfully produced with exit0 using the console fallback.
The full warning is in [maven.log](examples/phase5_2_2_b/maven.log).

The noexec policy was retained. No library installation, writable executable
mount or permanent JVM/configuration change was used to hide the warning.
Native-console loading is therefore a **known compatibility warning**, even
though the requested version probe passed. This task does not establish that a
historical Maven lifecycle or all its plugins/classpaths will succeed.

## Binary and image identity

Existing image IDs were rechecked locally before any execution:

```text
scanner: sha256:23ca0f137965d9dff2198074043fd48d386280bc5d0ccac8c8349cea4cf096a9
build:   sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82
Node carrier image, used only as a STOPPED extraction donor:
         sha256:9026624a61cd25542a402a9e7213dd7dbb39724ac9597e331e6b85362558c079
```

The scanner launcher, CLI JAR, scanner properties, Java21 executable/release,
Maven launcher/core JAR and Java17 executable/release were copied from the new,
stopped probe containers and hashed against the published manifest before
those containers were started. Read-only image roots and pinned image IDs bind
execution to those verified artifacts. The existing user containers/volumes
were not mounted or reused.

The JS plugin JAR was copied from a **new stopped extraction donor**, with its
entrypoint overridden to `/bin/true`; that donor was never started. Its JAR hash,
embedded Node version file, compressed XZ hash and decompressed executable hash
all matched the committed evidence. The Node executable hash is:
`d918479037f14dc30c8d21df3767a010fe710685373baec7edf680ca8c3edbee`.
The binary was mounted read-only into the pinned scanner image for `--version`.
No JS analyzer was loaded or run. Full artifact identities are in the evidence.

## Isolation and bounded execution

All five probes ran **sequentially**, each in its own disposable environment:

- Network `none`, no published ports and image pulling disabled (`--pull never`).
- Cgroup memory and memory+swap limits each **1,073,741,824 bytes**; no extra swap.
- One CPU (`NanoCpus=1,000,000,000`); runtime `cpu.max=100000 100000` verified.
- User1000:1000, all capabilities dropped, no-new-privileges, read-only root.
- No source repository, credentials, Docker socket or user Maven cache mounted.
- 32MiB bounded `/tmp`,8MiB shared memory,64-process cap,1MiB single-file logs.
- 30-second command wait timeout, bounded Docker operations and600-second outer
  runner timeout. Timeout handling targets only the task-owned container.
- JVM heaps capped at128/256MiB for the temporary probes, with one active JVM CPU.
  These are temporary probe settings, not edits to registered historical builds.

The wrapper checks actual cgroup memory/CPU limits **before** invoking the
version command. Missing/mismatched limit evidence aborts the command; it is not
replaced with an assumed limit. Exact version strings and command exit codes
must match before a result can be marked PASS.

All command arrays are version-only. Maven receives only `--version`, runs in an
empty temporary directory with RC loading disabled, and bypasses the image's
Maven entrypoint. Scanner receives `--version` and explicit JRE/Node-provisioning
skip properties; no project-root properties were present. Network isolation and
absence of project inputs prevent downloads/application analysis. Node receives
only `--version`.

Host extraction storage peaked at **254,617,830 bytes (~242.82MiB)** against the
384MiB bound. The temporary Node executable, carrier JAR and wrapper were removed.
This temporary extraction is not a package installation. No third-party binary
is committed or retained in the Task B output directory.

### Initial setup incompatibility

The first disposable scanner attempt verified its files but did not execute the
version command: Docker's local log driver rejected default compression with a
one-file rotation limit. Its container was removed. The task-specific retry set
`compress=false` while retaining the one-file/1MiB log cap. No daemon setting,
original environment or resource ceiling changed. The original failed-attempt
receipt/log remains local; the public evidence includes its cause and resolution.

## Cleanup and preservation

The successful run removed five executed probe containers and one never-started
artifact donor, including the donor's four new anonymous volumes. The initial
failed-attempt container was also removed. Label/owner checks protect cleanup
from targeting an unrelated container. No Task B container or temporary binary
remains. Pre-existing containers and volumes remain present; the old
`td-target-sonar` state, image and volume mappings are unchanged.

All385 pre-existing central files,296 matching working-project files, four
unfinished untracked remediation files,56 frozen experiment bundles /322
artifacts, both Phase5.1 bundles, source SQLite and pinned checkpoint were
verified unchanged. Existing dataset/split IDs, forecasts, model parameters,
contracts, earlier reports and Task A rights decisions were preserved.

## Tests and reproduction

Targeted tests validate isolation/ownership/image checks, host-mount rejection,
conflicting identity detection, measured resource-limit failures, incomplete
resource-evidence rejection, and actual published version-only results. Existing
Task A, production-scope, preflight and schema-v2 foundation tests are included.
**204 tests passed in each checkout**, including17 new probe/evidence cases; no
failures or skips. Actual results and streamed preservation checks are in
[verification.json](examples/phase5_2_2_b/verification.json). Tests use fixtures
and completed evidence; they do not launch additional runtime probes.

Use only the existing local pinned images and a new output directory outside Git:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
TD522B_PY="$PWD/.venv-forecast/bin/python"
PYTHONDONTWRITEBYTECODE=1 timeout 600s "$TD522B_PY" \
  -m tools.probe_phase5_2_2_b --output /path/outside/git/to/new-task-b-probes
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s prlimit --as=1073741824 --cpu=120 --fsize=16777216 -- \
  "$TD522B_PY" -m pytest -q -p no:cacheprovider \
  tests/test_phase5_2_2_b_probes.py tests/test_phase5_2_2_a_review.py \
  tests/test_production_scope_readiness.py tests/test_multilanguage_preflight.py \
  tests/test_multilanguage_foundation.py
```

Publication uses a normal descendant commit on central `main`, explicit file
sync and GitHub byte verification. Only the new report, probe/test code and small
safe logs/metadata are published. The original working `main` history remains
untouched. The four unfinished broader-remediation files remain uncommitted.

**STOP after Task B verification/publication. No Task C, server startup,
historical compilation, scan, model inference or training is authorized here.**
