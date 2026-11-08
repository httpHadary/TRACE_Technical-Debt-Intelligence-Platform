# Phase 5.2.2-E.5.1 — Final T+90 offline Java compilation

**COMPILE_PASS. COMMONS_CLI_SIX_REVISION_COMPILE_GATE_PASS.** Exactly one genuine
offline T+90 Maven compilation completed its complete original lifecycle through
compile. Maven and Docker exited 0. The independent verifier matched all 36
registered production sources and parsed all 55 created Java 8 class files;
all 25 output acceptance checks passed. The five previous successes revalidate.

This completes only the six-revision Commons CLI compilation gate. It does not
establish test/package/deploy success, SonarQube/scanner compatibility, historical
debt collection, forecast evaluation, dataset admission or MVP completion.
Analyzer licensing and derived-data rights remain **UNRESOLVED_UNCHANGED**.

Starting main: `840645edbcb26bb06e186f870133c0a26f228191`.
Execution: 2026-10-19 01:13:31 EEST to
2026-10-19 01:13:46 EEST; raw timestamps retain UTC.
The exclusive attempt is consumed and the task-owned container has been removed.
No retry, acquisition, other revision or additional Maven goal occurred.

## Frozen target and inputs

| Input | Verified identity |
| --- | --- |
| Repository / offset | apache/commons-cli / T+90 |
| Commit | `af2b3e72a552cfb2a902556469868763ddea3638` |
| Tree | `0d773516c1c7bb0a371b2af6e084b62ef2d36546` |
| Original POM SHA256 | `87c8ed93cb21deedb52b826d520931bc175e24e5ee48643c6a21ed154c62324b` |
| Original tracked / production Java population | 138 / 36 |
| Parent chain | Commons Parent 78 → Apache Parent 33 |
| Runtime | Maven 3.9.11 / Temurin 17.0.17+10 / Java release 8 |
| Properties | maven.test.skip=true; no explicitly selected profiles |
| Artifact count | 758 |
| Manifest SHA256 | `eb471e18cca6828bb2abbe2273184faaa693298807363b0280630cb180a6adba` |
| Canonical cache SHA256 | `df9f176ceeea2f165cbf463dd3eb43675741b0932d1134c756386f0f7259462d` |
| T+90 effective-POM SHA256 | UNAVAILABLE, null |

Every source path, Git blob, SHA256 and mode was verified directly against frozen
Git objects and the registry. All 758 artifact coordinates/paths/hashes, recorded
Central checksum provenance, POM structures and JAR ZIP/CRC integrity were
reverified. Recorded same-origin checksums over TLS are not independent publisher
signatures. No network acquisition occurred during this task.

The new independently copied input repository has no unregistered artifact. The
new detached source export contains no manufactured .git metadata; no historical
POM, source byte, mode or plugin version changed. The two Java files differing
from T+60, CommandLine.java and Option.java, retain their own T+90 identities.
The ten help-package files remain part of the independently verified 36-source
population. No previous class count/hash or effective model was substituted.

Static reinspection reproduces E.5's target, 20 descriptors, project dependency
closure and 318 registered compile-candidate references. All known required paths
remain present. These references are repeated static candidates, not independent
artifacts or a mediated runtime classpath. E.5's initial PARTIAL, final scoped
static PASS, original acquisition-source snapshot, profile scope proof, raw audits
and sealed17-request ledger are unchanged. Commons Text's own-test profile proof
still makes no claim about actual activation.

New files tools/build_compile_e51.py and tools/verify_compile_e51.py reuse the
proven E.4.1 sandbox and independent class parser, with their own mode
`--e51-offline-compile`, owner label, exclusive one-attempt claim, 138-file,
758-artifact and36-Java-source registration. No consumed runner was invoked and
no archived adapter was modified. Executed adapter and verifier hashes match
saved pre-attempt copies and published source.

The only sandbox addition checks actual mounted repository capacity after the
verified copy, before Maven: capacity must equal128MiB and free space must retain
at least16MiB metadata reserve. The real REPOSITORY_CAPACITY setup stage passed;
actual before/after df, du and filesystem counters are retained. This does not
increase any cap or replace the independent static block-allocation estimate.

The pinned local image is `sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82`. Four binary hashes (Maven launcher/core,
Java launcher/release file) match Task B. They were copied from the single stopped
owned container for hash verification; no preliminary JVM or version probe ran.

## Actual original lifecycle

Exactly one command ran:

```bash
/usr/share/maven/bin/mvn --offline --batch-mode --no-transfer-progress --errors \
  -s /inspection/settings.xml -gs /inspection/settings.xml \
  -Dmaven.repo.local=/runtime-repository -Duser.home=/tmp \
  -Dmaven.test.skip=true -Dmaven.compiler.release=8 compile
```

MAVEN_OPTS=`-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp`.
HOME=/tmp, MAVEN_CONFIG=/tmp/.m2, MAVEN_SKIP_RC=true. MAVEN_ARGS,
JAVA_TOOL_OPTIONS and JDK_JAVA_OPTIONS were empty. No additional skip/property,
profile, SCM workaround or build-plan override was supplied.

| Order | Actual goal banner | Execution | Outcome |
| --- | --- | --- | --- |
| 1 | enforcer:3.5.0:enforce | enforce-maven-version | Completed |
| 2 | enforcer:3.5.0:enforce | enforce-java-version | Completed |
| 3 | apache-rat:0.16.1:check | rat-check | Completed |
| 4 | artifact:3.5.1:check-buildplan | check-buildplan | Completed |
| 5 | build-helper:3.6.0:parse-version | parse-version | Completed |
| 6 | antrun:3.1.0:run | javadoc.resources | Completed |
| 7 | remote-resources:3.2.0:process | process-resource-bundles | Completed |
| 8 | buildnumber:3.2.1:create | default | Completed |
| 9 | resources:3.3.1:resources | default-resources | Completed |
| 10 | compiler:3.13.0:compile | default-compile | Completed |

Both original Enforcer version checks passed. RAT reported127 approved licenses,
zero unapproved, unknown or generated entries. Check-buildplan completed against
all20 original deploy-plan descriptors; later goal mentions are not executions.
The actual banner population and phase order match this target's static lifecycle
registration. No test compilation or unauthorized phase executed.

Antrun's original inherited property expression remains unchanged and resolved at
runtime to3.1.0. It copied two javadoc resources. Remote-resources executed its
bound goal and used the original inherited skip configuration; no agent skip was
added. Resources copied two LICENSE/NOTICE files. The actual Compiler3.13.0 goal
reported `Compiling 36 source files with javac [debug release 8]` and BUILD SUCCESS.

Buildnumber3.2.1 attempted original Git operations, then used its configured
`??????` and `UNKNOWN_BRANCH` detached-export fallbacks. These were nonfatal;
scientific lineage uses the independently verified commit/tree, never placeholders.
No SCM context or POM workaround was introduced.

RAT emitted the existing nonfatal POM warnings for log4j:log4j:1.2.12,
logkit:logkit:1.0.1 and avalon-framework:avalon-framework:4.1.3. No fatal offline
resolution failure occurred and no JAR need/acquisition is inferred from warnings.
Jansi could not map its native library from noexec /tmp; the warning remained
nonfatal and isolation was not weakened. RAT header approval clears no rights gate.

## Independent compiler and output proof

Actual output: 55 classes — 34 named top-level,11 named nested,7 synthetic helpers,
1 anonymous and2 package-info classes. Expected top-level identities derive from
T+90 declarations. Internal names match output paths and SourceFile ownership;
every class passed structural/constant-pool parsing and has Java8 major version52.

Synthetic helpers are classified using ACC_SYNTHETIC; anonymous status uses the
own InnerClasses record and EnclosingMethod. Numeric suffixes alone do not prove
anonymous status. Package-info is separately accounted, including synthetic flags.
Structural parsing is not a separately executed JVM bytecode verifier.

All36 actual compiler inputs match the original source registration. The exact
createdFiles.lst population matches the parsed class set, with unique identities.
The observed55 count happens to match T+60; no acceptance condition requires that
count or binary equivalence. Two nonclass LICENSE/NOTICE resources are separately
hashed. No test-classes directory or additional lifecycle phase was observed.

All138 original source/POM identities and modes and758 seed artifact bytes were
preserved. Maven added 0 repository metadata files.
Maven stdout was5,164 bytes; stderr569 bytes.
Both complete bounded streams are retained privately, separately from setup
stdout/stderr. Trap stage, terminal codes, post-run hashes, resource evidence,
owned container events and cleanup all passed evidence completeness checks.

Actual profile enumeration, effective-POM SHA256, compiler argument vector and
mediated classpaths remain **UNAVAILABLE**: the approved command did not export
or log them. E.5's24 actual project-profile decisions remain UNKNOWN. Runtime
compilation is not an effective-model export and does not rewrite static evidence.

See [output verification](examples/phase5_2_2_e_5_1/output_verification.json),
[class manifest](examples/phase5_2_2_e_5_1/class_output_manifest.json),
[lifecycle evidence](examples/phase5_2_2_e_5_1/lifecycle_evidence.json) and
[execution receipt](examples/phase5_2_2_e_5_1/build_execution_evidence.json).

## Actual resources and sandbox

| Item | Observation or unchanged limit |
| --- | ---: |
| Available host RAM immediately before start | 6,782,717,952 bytes |
| Minimum sampled available host RAM | 6,511,517,696 bytes |
| Free disk immediately before start | 15,227,617,280 bytes |
| Admission / minimum host headroom | 4GiB / 2GiB |
| Container RAM / maximum JVM heap | 2GiB / 768MiB |
| Cgroup peak memory | 370,491,392 bytes (353.33MiB) |
| OOM / OOM-kill / memory-max events | 0 / 0 / 0 |
| CPU usage | 13.723798 CPU-seconds |
| Maven wrapper / internal time | 12.87s /9.922s |
| Host monitor duration | 14.81s |
| Actual repository allocation before / after | 83,296,256 /83,296,256 bytes |
| Actual repository available before / after | 50,921,472 /50,921,472 bytes |
| Conservative estimate including16MiB reserve | 103,452,672 bytes |
| Unchanged repository tmpfs cap | 134,217,728 bytes |
| Containers / Maven invocations / retries / artifact requests | 1 /1 /0 /0 |

The sandbox retained CPU1, PIDs64, zero extra swap, UID/GID1000:1000, dropped ALL
capabilities, no-new-privileges, read-only image root, network none and pull-never.
Only task-owned read-only inputs/inspection were mounted; no host credential,
Docker socket or user Maven cache. Owned noexec/nosuid/nodev tmpfs caps remained
source128MiB, repository128MiB, tmp128MiB and output32MiB, with shm8MiB,
file8MiB, archive32MiB and nofile1024. Maven timeout240s, host monitor265s and
outer330s were unchanged. Host controller used1GiB address-space cap/CPU0;
its separate RSS was not measured and is not inferred from cgroup memory.
Only the owned container was removed; no unrelated service was stopped/restored.

## Regression and preservation

**1,124 tests passed in each checkout**, with zero failures, errors or skips:
37.001s canonical and36.060s original.
The suite includes1049 prior relevant tests and75 new E.5.1 tests. Before the
single build,131 focused policy/capture tests passed without Maven/Java/container
execution. Three initial fixture failures (stale copied target assertion and a
shell fixture not crossing sh -c) were fixed before execution; their original
logs remain private. They consumed no build attempt and changed no historical input.

Preservation PASS covers every prior class archive/runtime receipt/consumed claim,
old caches and ledgers, E.5 evidence, all18 source states,56 frozen research
bundles/322 artifacts, both Phase5.1 bundles, database and model hashes,
6262 user-cache metadata entries and75 rehashed reference artifacts. Old SonarQube
state/mount/volume metadata and unrelated containers/files are unchanged; this
is not a byte-level claim about live volume contents. All850 previous canonical
tracked files,761 preexisting original-project files and4 unrelated untracked
remediation files remain unchanged. The original project HEAD remains unchanged.

All old request ledgers remain sealed: D2000,D.1 400,D.2 52,D.3 112,E.0.3 56,
E.0.5 12,E.0.5.1 52,E.1 32,E.2 67,E.3 46,E.4 8,E.5 17. No recovery batch ran.

## Six-revision compilation gate

| Offset | Verification phase | Frozen commit | Actual classes | Revalidated result |
| --- | --- | --- | ---: | --- |
| T-90 | e.2.1 | `e1529b546d9696192f4de52152777403b4a01b39` | 37 | COMPILE_PASS |
| T-30 | e.1.1 | `fb6293fcd6a9b55ac8ecb550af6572daaed18fa1` | 37 | COMPILE_PASS |
| T0 | e.0.6 | `4ff0d4adbc2161677e71050ba23c152831f6ad83` | 37 | COMPILE_PASS |
| T+30 | e.3.1 | `7ddf691ac2afbda7473c0d07f1f4e7ae1e69e47b` | 55 | COMPILE_PASS |
| T+60 | e.4.1 | `aad30eff27ac5c9a13194125226653c6c2826c58` | 55 | COMPILE_PASS |
| T+90 | e.5.1 | `af2b3e72a552cfb2a902556469868763ddea3638` | 55 | COMPILE_PASS |

All six independently pass their original offline lifecycle through compile.
The five earlier runners were never reexecuted. The
[six-revision gate receipt](examples/phase5_2_2_e_5_1/six_revision_compile_gate.json)
records per-revision source/artifact registration, claim, archive, execution,
result and independent-verifier hashes. This gate is not FULL_OFFLINE_BUILD_READY
for every Maven phase, scanner admission, rights acceptance or entire MVP success.

## Deliverables, reproduction and stop

New source: tools/build_compile_e51.py and tools/verify_compile_e51.py.
New tests: tests/test_build_compile_e51.py and tests/test_verify_compile_e51.py.
New report and sanitized receipts: this file and examples/phase5_2_2_e_5_1/.
No old tracked implementation/report, source POM, dataset or model was modified.

Private attempt: `/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_5_1/2026-10-19/attempt-1`. The claim is consumed. **Do not repeat the runner.**
Build outputs, raw logs, JARs, source exports and caches remain outside Git.
New safe files are mirrored to the requested project and published from the
canonical main checkout as a normal descendant, preserving all850 prior remote
blobs and original-project unrelated work. Post-push byte/ancestry verification
is retained in the private github_publication_receipt.json.

Read-only output verification, with no new Maven attempt:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -c 'import json; from tools.verify_compile_e51 import audit; print(json.dumps(audit("/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_5_1/2026-10-19/attempt-1")["checks"],indent=2))'
```

Targeted tests:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_build_compile_e51.py tests/test_verify_compile_e51.py
```

The [verification receipt](examples/phase5_2_2_e_5_1/verification.json) lists the
complete33-file regression invocation and log/JUnit hashes. All original source,
cache, resource and output checks remain independently reproducible.

[The six-revision handoff](examples/phase5_2_2_e_5_1/SIX_REVISION_COMPILATION_HANDOFF.md)
requires separate authorization for further work. No correction is needed for this
compile. **STOP after E.5.1 publication.** No retry, acquisition, extra Maven goal,
SonarQube/scanner, debt measurement, forecasting, dataset admission or Phase5.3
follows. Analyzer licensing and derived-data rights remain UNRESOLVED_UNCHANGED.
