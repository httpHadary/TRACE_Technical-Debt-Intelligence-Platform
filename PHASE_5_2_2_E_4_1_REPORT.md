# Phase 5.2.2-E.4.1 — Single T+60 offline Java compilation

**COMPILE_PASS.** Exactly one genuine offline Maven compilation ran for the frozen
Apache Commons CLI T+60 revision. The entire original lifecycle through compile
completed with Maven and Docker exit 0. All 36 registered production Java sources
match actual compiler inputs. All 55 created-file entries match independently
parsed Java 8 classes. All 25 independent output acceptance checks pass.

The task-owned container was removed after retaining complete bounded evidence.
No retry, artifact acquisition, preliminary Maven goal, other revision, SonarQube,
scanner, forecasting, debt measurement, dataset admission or Phase 5.3 occurred.
Analyzer licensing and derived-data rights remain UNRESOLVED_UNCHANGED.

Starting main: `93ed9d27f38800fd3064d3c28b4b9490c979ac01`.
Execution: **2026-10-19 00:40:20 EEST** to
**2026-10-19 00:40:32 EEST**. Raw timestamps retain UTC.

## Frozen inputs and registration

| Input | Verified identity |
| --- | --- |
| Repository / offset | apache/commons-cli / T+60 |
| Commit | `aad30eff27ac5c9a13194125226653c6c2826c58` |
| Tree | `d7434665397c8dd8156fff7ecaed29a14feeb951` |
| Historical POM SHA256 | `1c82171f91da0f4aa2994bb367e4c9ef8e65414940100be081715605739d9e0b` |
| Source population | 138 tracked files / 36 production Java sources |
| Parent chain | Commons Parent 78 → Apache Parent 33 |
| Runtime | Maven 3.9.11 / Temurin 17.0.17+10 / Java release 8 |
| Properties | maven.test.skip=true; user.home=/tmp; no explicit profiles |
| Artifact population | 753 verified files |
| Artifact manifest SHA256 | `396219aa616a8724f4a1d00285e04b4ad4f19bc8921e67e0ef6bc79c69c474d7` |
| Canonical cache SHA256 | `ce62e9b970dfeeaf397f8ec67774c4c4d2a16a216d89075023e1ac944477a2cf` |
| Actual effective-POM identity | UNAVAILABLE, null |

All 138 paths, source SHA256 values, Git blob IDs and executable modes were verified
directly against frozen commit/tree objects and registry entries. The original
read-only source export and historical POM were preserved. Independent copies use
different inodes; no `.git` metadata was manufactured. The runtime working-copy
modes match original Git modes; the read-only source-export modes remain unchanged.

All 753 artifacts passed exact-path/coordinate/version, local SHA256, recorded
Central checksum provenance, POM XML or JAR ZIP/CRC checks. The cache contains no
unregistered artifact. All 20 target build-plan descriptors, parent/import metadata,
project test closure and 318 historical compile-candidate references were rechecked.
The static target model, plan, closure and candidate records match E.4's corrected
published evidence. These are static declarations, not imported runtime profiles
or a compiler classpath. E.4's metadata-path correction receipt remains unchanged.

The 14 changed production Java files relative to T+30 retain their own frozen bytes.
The target's 138th tracked file is the existing GitHub PR template; production Java
count remains 36. No previous class count or binary hash served as an acceptance
condition. No T+90 source export, readiness preparation or build occurred.

New `tools/build_compile_e41.py` and `tools/verify_compile_e41.py` reuse the proven
sandbox/capture and corrected independent class parser, with their own mode,
owner label, exclusive claim, 138-file/753-artifact registration and explicit
36-source compiler list. No consumed runner was called and no archived adapter
was modified. Mode: `--e41-offline-compile`. Both executed adapter and independent
verifier remain byte-identical to their saved pre-attempt copies and published code.

Pre-attempt tests verify UID/GID, mounts, ownership/path boundaries, one-attempt
accounting, resource gates, output expectations and failure capture. The new adapter
also confines fatal SCM classification to error evidence, so a nonfatal original
SCM fallback cannot hide a later compiler failure. Exit 137 retains its original
resource-failure meaning, independently of the source-file count. These policy
checks and changes occurred before the single build, with no preliminary Maven goal.

The existing local image was
`sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82`.
Four binary hashes—Maven launcher/core and Java launcher/release file—match Task B.
Verification copied files from the one stopped owned container; it launched no
extra JVM, version probe or container. Shared hash-pinned settings are tooling,
not T+30 model evidence. Executed wrapper SHA256:
`b7bf5e2daa8c113a94ea0be0ef659d94a598b81f073e817b039d655fb77da45d`.

## Original lifecycle execution

The sole Maven command was:

```bash
/usr/share/maven/bin/mvn --offline --batch-mode --no-transfer-progress --errors \
  -s /inspection/settings.xml -gs /inspection/settings.xml \
  -Dmaven.repo.local=/runtime-repository -Duser.home=/tmp \
  -Dmaven.test.skip=true -Dmaven.compiler.release=8 compile
```

`MAVEN_OPTS=-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp`.
HOME=/tmp, MAVEN_CONFIG=/tmp/.m2 and MAVEN_SKIP_RC=true; MAVEN_ARGS,
JAVA_TOOL_OPTIONS and JDK_JAVA_OPTIONS are empty. No added skip, version,
profile, build-plan task, SCM or compiler workaround was supplied.

| Order | Actual executed goal banner | Execution | Result |
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

Both original Enforcer version checks passed. RAT reported 127 approved licenses
and zero unapproved, unknown or generated entries. Check-buildplan completed and
checked 20 deploy-plan descriptors. Later plugin mentions are descriptor checks,
not executions of Surefire, Felix, CycloneDX, SPDX, Moditect, install or deploy.
The actual banner sequence exactly matches target compile-bound identities and
phase order. No test compilation or other unauthorized lifecycle phase occurred.

Remote-resources executed its original bound goal and reported the inherited
configuration's skip; no agent skip property was introduced. Antrun copied two
javadoc resource files. Resources copied two files to target/classes/META-INF.
The actual compiler reported `Compiling 36 source files with javac [debug release 8]`
and BUILD SUCCESS.

Buildnumber 3.2.1 attempted its original Git commands, then used the configured
`??????` revision and `UNKNOWN_BRANCH` fallbacks in the detached export. This was
nonfatal and required no workaround. Scientific lineage remains the independently
verified commit/tree; fallback placeholders must not replace those identities.

Three POM warnings occurred during successful RAT metadata collection:
log4j:log4j:1.2.12, logkit:logkit:1.0.1 and
avalon-framework:avalon-framework:4.1.3. Both analyzers attribute them to observed
RAT context and mark them nonfatal. There was no fatal offline resolution failure.
No corresponding JAR requirement or acquisition is inferred. Jansi's native
library could not execute from noexec `/tmp`; the warning was nonfatal and all
isolation controls stayed enabled. RAT's header result does not clear rights gates.

## Independent class verification

The actual output population is **55 classes**: 34 named top-level,
11 named nested, 7 synthetic helpers,
1 anonymous and 2 package-info classes.
Every class has valid magic, parsed structure/constant-pool metadata, matching
internal/output path identity, owning SourceFile and Java 8 major version 52.
All named top-level identities derive from original T+60 declarations. Nested,
synthetic and anonymous ownership is checked against that source population.

The corrected independent classifier uses ACC_SYNTHETIC and the own InnerClasses /
EnclosingMethod attributes to distinguish numbered synthetic helpers from the
true anonymous TableDefinition$1 class. Package-info remains separately accounted
for, including synthetic access flags where present. The adapter's preliminary
numeric-name category is retained as `adapter_kind`; it is not used to claim that
all numbered classes are anonymous. Structural parsing is not a separately
executed JVM bytecode verifier.

All 36 actual compiler inputs match the target registration, including all ten
help-package source files. The compiler's createdFiles.lst exactly matches the 55
parsed class paths, with no duplicate list identity. The measured count happens to
match T+30's aggregate count; no code requires that equality or identical binary
hashes. LICENSE.txt and NOTICE.txt are the two nonclass resources, separately hashed.

All 138 original source/POM bytes and modes and all 753 artifact bytes are preserved.
Maven added zero repository metadata files. No test-classes directory was produced.
Complete Maven stdout is 5164 bytes and stderr 569 bytes;
neither stream was truncated. Setup streams remain separate. Setup-stage/EXIT-trap,
Maven/Docker exits, post-run hashes, cgroup metrics, owned container events and cleanup
were captured. No required acceptance evidence is missing.

Actual active-profile enumeration, effective-POM SHA256, compiler argument vector
and exact runtime classpath remain **UNAVAILABLE** because the registered command
did not export/log them. E.4's 24 static project-profile records retain their
UNKNOWN runtime decisions. No earlier revision's missing observation was substituted.
This proves compile success for this exact context, not every later Maven goal or
FULL_OFFLINE_BUILD_READY for another revision.

See [output audit](examples/phase5_2_2_e_4_1/output_verification.json),
[class manifest](examples/phase5_2_2_e_4_1/class_output_manifest.json),
[lifecycle receipt](examples/phase5_2_2_e_4_1/lifecycle_evidence.json) and
[execution evidence](examples/phase5_2_2_e_4_1/build_execution_evidence.json).

## Resources and security

| Measurement | Actual result |
| --- | ---: |
| Host RAM available immediately before start | 9,319,227,392 bytes |
| Minimum sampled available host RAM | 8,970,928,128 bytes |
| Free disk immediately before start | 15,346,892,800 bytes |
| Admission / host headroom requirement | 4 GiB / 2 GiB |
| Container RAM / JVM heap limits | 2 GiB / 768 MiB |
| Cgroup peak memory | 351,166,464 bytes (334.90 MiB) |
| OOM / OOM-kill / memory-max events | 0 / 0 / 0 |
| CPU usage | 10.373318 CPU-seconds |
| Maven wrapper / internal time | 9.78s / 7.624s |
| Host monitor duration | 11.61s |
| Artifact payload | 80,688,146 bytes |
| Actual repository allocation before / after | 82,227,200 / 82,227,200 bytes |
| Actual repository capacity remaining | 51,990,528 bytes |
| Conservative estimate, including 16 MiB reserve | 102,371,328 bytes |
| Repository tmpfs cap | 134,217,728 bytes (128 MiB) |
| Containers / Maven invocations / retries / artifact requests | 1 / 1 / 0 / 0 |

Live admission confirmed no prohibited workloads/running containers, sufficient
memory/headroom/disk, exact verified inputs and the pinned local image. Cache
capacity was recalculated from all 753 files with 4 KiB allocation rounding,
directory overhead and the unchanged 16 MiB reserve. Actual df/du/filesystem
counters are recorded separately from the estimate; no cap was raised.

The sandbox retained one CPU, 64 PIDs, no extra swap, UID/GID1000:1000, dropped ALL
capabilities, no-new-privileges, read-only root, network none and image pull-never.
Only task-owned read-only input and inspection binds were provided; no credentials,
Docker socket or user Maven cache. Owned noexec/nosuid/nodev tmpfs remains 128 MiB
for source/repository/tmp and 32 MiB for output. Shm is 8 MiB; file cap 8 MiB,
archive cap 32 MiB, nofile1024, Maven timeout240s, monitor265s and outer330s.
Controller address space was capped at1 GiB on CPU0; separate controller RSS was
not measured and is not inferred from container cgroup memory. Only the owned
container was removed. No unrelated service was stopped or restored.

## Regression and preservation

**980 tests passed in each checkout**, zero failures/errors/skips:
23.966s canonical and
24.274s original project. The suite contains
912 prior relevant tests and 68 new E.4.1 tests. Before the build, all166 focused
policy, integrity, class-mapping and capture tests passed without a real Maven or
container launch. New tests cover exact138/753 identities, the separate claim/mode,
resource/path/ownership gates, original command and lifecycle, rejected unsafe
sandbox settings, fatal-versus-nonfatal SCM evidence, exit137, missing artifacts,
missing measurements and the corrected independent class classifications.

Preservation PASS includes all four previous COMPILE_PASS receipts/class archives,
all earlier private caches/source exports/ledgers and consumed claims, E.4's static
tracking correction, all18 frozen source states, 56 research bundles/322 artifacts,
two Phase5.1 bundles, SQLite/model hashes, 6,262 user-cache entries and75 rehashed
reference artifacts. Old SonarQube state/volumes and unrelated containers/files
are unchanged. Four preexisting untracked remediation files remain untouched.
No independent shared-container inventory change was observed.

Prior ledgers remain D=2000, D.1=400, D.2=52, D.3=112, E.0.3=56, E.0.5=12,
E.0.5.1=52, E.1=32, E.2=67, E.3=46 and E.4=8. All four earlier successful builds
were verified with their separate read-only auditors before and after this attempt;
no consumed compilation runner was invoked. The original project HEAD stays
unchanged; new files are mirrored there and published from the canonical checkout
as a normal main descendant commit.

See [regressions](examples/phase5_2_2_e_4_1/verification.json),
[preservation](examples/phase5_2_2_e_4_1/preservation.json),
[source states](examples/phase5_2_2_e_4_1/all_source_states_preservation.json) and
[earlier builds](examples/phase5_2_2_e_4_1/successful_builds_preservation.json).

## Files, reproduction and stop

New files: `tools/build_compile_e41.py`, `tools/verify_compile_e41.py`,
`tests/test_build_compile_e41.py`, `tests/test_verify_compile_e41.py`, this report
and `examples/phase5_2_2_e_4_1/` sanitized receipts and NEXT_REVISION_HANDOFF.md.
No production feature, old runner/report, historical POM/source, previous cache,
research data, model or experiment was rewritten.

Private attempt: `/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_4_1/2026-10-19/attempt-1`.
Its exclusive claim is consumed. **Do not repeat the compile adapter.** Dependencies,
source exports, class archives and raw execution logs remain outside Git. Public
inventories expose hashes and sanitized observations rather than binary payloads.

Read-only audit from the original project:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -c 'import json; from tools.verify_compile_e41 import audit; print(json.dumps(audit("/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_4_1/2026-10-19/attempt-1")["checks"],indent=2))'
```

Focused deterministic tests:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_build_compile_e41.py tests/test_verify_compile_e41.py
```

The verification receipt lists the full30-file regression invocation. These checks
grant no new build attempt. **STOP after E.4.1 publication.** No correction is
required for this successful compile. The
[handoff](examples/phase5_2_2_e_4_1/NEXT_REVISION_HANDOFF.md) requires separate
authorization for any subsequent work. No retry, acquisition, T+90 preparation,
SonarQube/scanner, debt measurement, forecasting, dataset admission or Phase5.3 follows.
Analyzer licensing and derived-data rights remain UNRESOLVED_UNCHANGED.
