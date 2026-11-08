# Phase 5.2.2-E.0 — First T0 build attempt

Date: **2026-10-16**. Starting main: `96d5f308e1b955dd53ac368c48f7b35a0e6c709c`.

**BLOCKED_BUILD_OR_RESOURCE — workspace setup failed before Maven launched.**
Exactly one disposable build container started and exited123. No Maven lifecycle,
plugin dependency resolution, enforcer, resource generator, SCM/buildnumber task
or compiler ran. Historical Java compilation readiness remains **UNKNOWN**.
No missing dependency or SCM-context failure is inferred from this setup failure.

The setup wrapper added for this task contains an ownership defect: recursive
`chmod` includes root-owned tmpfs mount directories while running as UID1000.
The exact failed setup subcommand and its stderr were not retained. The Docker
event record proves the pre-Maven setup exit; the ownership defect is established
by the executed wrapper and mount recipe, without claiming a recovered stderr line.

The user required one build container and prohibited automatic retries with changed
settings. That limit was honored. **No second build container or Maven attempt ran.**

## Prerequisites actually verified

- Commons CLI T0 commit `4ff0d4adbc2161677e71050ba23c152831f6ad83`.
- Tree `ac7521be84b2820a83f7b960d329a15521408214`.
- POM SHA256 `b75fb9813e3c06121caa7d84c31a471b646465966079cf10ec4c7a2e4aba55f2`;
  Commons Parent76. No historical POM/source/build property was changed.
- D.3 effective POM SHA256
  `bf4a9243703b32ca363232c2759c8bab4f009ac544897dafab87f4b22f42e449`
  and exact active-profile output matched published evidence. The eight active
  and17 inactive project profiles remain D.3 model observations, not new build results.
- All624 D.2 artifact POM/JAR identities were reverified against the published
  manifest, SHA256, repository checksums, coordinates and JAR CRC. All29 D.3 helper
  artifacts received the same checks. The653-file D.3 runtime-cache inventory matched.
- All653 artifacts were copied independently, with SHA256 and distinct inodes
  checked; no previous cache or request ledger was overwritten.
- All117 tracked source files were rechecked against the Git tree and D.3 export,
  including Git blob IDs/SHA256 and all26 production Java files. The fresh seed export
  has no manufactured `.git`, fake sources or marker files.
- The existing pinned Maven/JDK image was used:
  `sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82`.
  Maven launcher/core and Java executable/release hashes matched TaskB before startup;
  those assertions precede the daemon-observed startup. Maven3.9.11 and Temurin
  17.0.17+10 were preserved. No extra runtime-version command ran.

[Prerequisite metadata](examples/phase5_2_2_e_0/prerequisite_verification.json)
binds the new seed verification to the previous effective model. Helper artifacts
were kept separate from historical project dependency provenance.

## One actual container attempt

Container: `td522e0-08d92f8b4bcd`.
Daemon container ID: `3f47bf4e6c621003235b6aeb50deea4a9d7e78de2079ccbfa1d5e85715d14f19`.

| Evidence | Actual result |
| --- | --- |
| Startups |1; daemon events include create, start, die123, destroy|
| Terminal container exit |123; reserved by the executed wrapper for setup copy/chmod failure|
| Maven launches |0; all exit123 paths precede the Maven command|
| Compiler launches |0|
| Missing runtime artifact coordinates |Not assessed; dependency resolution not reached|
| Enforcers / generated resources / SCM |Not reached|
| Class outputs |Not established; no compiler or class archive capture|
| Peak cgroup RAM |Unavailable; container exited before evidence collection|
| Full setup stdout/stderr |Unavailable; cleanup removed the container before logs were retained|
| Additional dependency downloads |0|
| Retry / changed settings |0 /none|
| Cleanup |Task container removed; old containers/volumes preserved|

The controller observed the container running, then its next evidence-read `exec`
raced the very early exit and returned “container is not running”. The `finally`
cleanup removed the task-owned container. A subsequent **read-only** Docker event
query recovered the authoritative exit123 and single startup; it did not create
or execute anything. No complete Maven log is fabricated to replace missing output.

The raw original execution receipt is retained unchanged in
[build execution evidence](examples/phase5_2_2_e_0/build_execution_evidence.json).
The [failure manifest](examples/phase5_2_2_e_0/failure_manifest.json) supplements
that receipt with sanitized daemon events and explicit unavailable fields.
The private executed controller and wrapper are hash-bound by the failure manifest.

## Resource limits and admission

Immediately before startup, available host RAM was
10,135,187,456bytes
(~9.44GiB),
with 35,544,125,440bytes free disk.
No other container, Java/Maven/Sonar process was running. Minimum sampled host
available RAM was 10,122,817,536bytes
(~9.43GiB), above the2GiB headroom floor.
This is host availability evidence, **not** measured container peak RAM.

The created sandbox passed its pre-start isolation assertions:2GiB container memory,
2GiB memory+swap cap (no extra swap), one CPU,64PIDs, read-only image root,
unprivileged1000:1000, all capabilities dropped, no-new-privileges, network `none`,
image pulling disabled, no credentials or Docker socket. Only fresh task seed inputs
and inspection settings/wrapper were mounted read-only.

Writable source/repository/tmp each had128MiB tmpfs caps; output had32MiB, totaling
416MiB, plus8MiB shared memory. All used noexec/nosuid/nodev. Per-file output was
capped at8MiB and file descriptors at1024. Planned JVM heap was768MiB and one active
processor; the JVM did not start. Planned compile timeout was240seconds with a
260second host monitor; neither timeout caused exit123. No OOM event appears in the
recovered daemon stream; peak-memory/OOM-counter readings were not captured and are
not replaced with estimates. The setup exit is not a host-RAM admission failure.

## Exact planned Maven command and environment

**This command was prepared but never reached.** The wrapper failed first.

```text
/usr/share/maven/bin/mvn \
  --offline \
  --batch-mode \
  --no-transfer-progress \
  --errors \
  -s \
  /inspection/settings.xml \
  -gs \
  /inspection/settings.xml \
  -Dmaven.repo.local=/runtime-repository \
  -Duser.home=/tmp \
  -Dmaven.test.skip=true \
  -Dmaven.compiler.release=8 \
  compile
```

```text
HOME=/tmp
MAVEN_CONFIG=/tmp/.m2
MAVEN_SKIP_RC=true
MAVEN_ARGS=
MAVEN_OPTS=-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp
JAVA_TOOL_OPTIONS=
JDK_JAVA_OPTIONS=
```

Settings were identical to D.3, with no user settings/cache. No `-P`, enforcer/RAT/
buildnumber skip flag or substituted historical dependency was added. Source and
Maven cache writable working copies were intended inside disposable tmpfs; the
root ownership prevented setup from completing. No lifecycle was resumed or retried.

D.3's actual effective model contains these through-compile bindings. This table
records **expected bindings**, not observed plugin execution:

| Plugin | Expected binding(s) | E.0 result |
| --- | --- | --- |
| org.apache.maven.plugins:maven-remote-resources-plugin:3.2.0 | process → generate-resources | NOT REACHED |
| org.apache.maven.plugins:maven-enforcer-plugin:3.5.0 | enforce → validate, enforce → validate | NOT REACHED |
| org.apache.maven.plugins:maven-antrun-plugin:3.1.0 | run → generate-sources | NOT REACHED |
| org.apache.maven.plugins:maven-compiler-plugin:3.13.0 | compile → compile | NOT REACHED |
| org.apache.rat:apache-rat-plugin:0.16.1 | check → validate | NOT REACHED |
| org.apache.maven.plugins:maven-artifact-plugin:3.5.1 | check-buildplan → validate | NOT REACHED |
| org.codehaus.mojo:build-helper-maven-plugin:3.6.0 | parse-version → validate | NOT REACHED |
| org.codehaus.mojo:buildnumber-maven-plugin:3.2.1 | create → generate-resources | NOT REACHED |
| org.apache.maven.plugins:maven-resources-plugin:3.3.1 | resources → process-resources | NOT REACHED |

The lifecycle remains original. No conclusion is drawn about its eventual plugin
classpath completeness, enforcer acceptance, buildnumber fallback or missing `.git`.

## Output completeness and missing artifacts

[Class-output manifest](examples/phase5_2_2_e_0/class_output_manifest.json):
`NOT_REACHED`, completeness `NOT_ESTABLISHED`, class count unknown. There are25
named production top-level classes plus `package-info.java` among26 source files.
No bytecode-major-version52, class hash or successful release8 compilation is claimed.

The failure manifest has an empty missing-artifact list with assessment
`NOT_REACHED`; it does **not** mean the offline compile closure is complete.
No artifact recovery is justified by this attempt because Maven never requested one.
The15 unresolved transitive profile sources and final runtime classpaths remain
pending as documented in D.3. They were not overridden or assumed resolved.

## Smallest safe correction for a separately authorized continuation

1. Assign `/source` and `/runtime-repository` tmpfs ownership explicitly with
   `uid=1000,gid=1000`, retaining existing mode, noexec, size, CPU/RAM/swap/PID and
   network restrictions. Alternatively create owned subdirectories without chmod
   on mount roots, with a separately recorded source-path context. Do not add
   capabilities or run the Maven build as root.
2. Preserve stage-specific setup stderr and a terminal-state/log snapshot before
   cleanup, including a container that exits between inspect and exec. Capture
   startup/cgroup metrics from the task namespace while it is alive. No silent
   retry or synthetic peak-memory value is acceptable.
3. Test the ownership/capture correction independently before any newly authorized
   compilation. Keep the exhausted E.0 attempt claim and all existing evidence.
4. Only after separate authorization, permit one new T0 compile attempt with
   unchanged source/POM, registered properties, offline cache and lifecycle.

These are proposed corrections. **No corrected second container was executed in
this phase, and no successful correction is claimed.** The committed controller
retains the exact executed recipe, including its recorded setup defect; it is not
advertised as a working compilation path. Its exclusive attempt claim prevents
reusing this task directory. Do not automatically call it with a different directory.

## Regression and preservation

**333 tests passed in each checkout**, including20 E.0 cases; zero failures,
errors or skips. Central: 19.520s; working project:
16.017s. Tests cover exact offline command/registered properties,
no lifecycle skips, immutable one-attempt claim, resource rejection before startup,
separate dependency/SCM/setup failure categories, bounded evidence extraction and
archive traversal rejection, and the actual failure's unavailable/NOT_REACHED fields.
They do not execute Docker/Maven or validate this failed integration as successful.

The [verification receipt](examples/phase5_2_2_e_0/verification.json) records test
and source hashes. Preservation PASS:454 pre-existing central files,365 working
files and4 unrelated unfinished files;1378/615/630 D/D.1/D.2 cache files plus all842
D.3 private files; prior request counts2000/400/52/112 unchanged;5878 user-cache
entries and75 reference artifact hashes;56 frozen bundles/322 artifacts,2 Phase5.1
bundles, source database, model checkpoint, original source/POM and old Sonar
container state/mounts. New653-artifact/117-source seed copies were rehashed.
No task container remains. Original working `main` stays at
`2e7999ea436d49449652e6c52e9066ef2e514419`.

New files are this report, `tools/compile_phase5_2_2_e_0.py`, its targeted tests and
`examples/phase5_2_2_e_0/` metadata. All dependency binaries and source/build/cache
artifacts remain outside Git under:

```text
/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0/2026-10-16/
```

Reproducible regression command, without rerunning the build:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s taskset -c 0 prlimit --as=1073741824 --cpu=120 --fsize=16777216 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_phase5_2_2_e_0_compilation.py tests/test_phase5_2_2_d_3_inspection.py \
  tests/test_phase5_2_2_d_2_recovery.py tests/test_phase5_2_2_d_1_continuation.py \
  tests/test_phase5_2_2_d_recovery.py tests/test_phase5_2_2_b_probes.py \
  tests/test_phase5_2_2_a_review.py tests/test_production_scope_readiness.py \
  tests/test_multilanguage_preflight.py tests/test_multilanguage_foundation.py
```

Source/tests/sanitized metadata are published as a normal descendant commit to
GitHub main with remote byte verification. **STOP after E.0 publication.** No retry,
other revision, Sonar, scan, model, dataset admission or later task started.
