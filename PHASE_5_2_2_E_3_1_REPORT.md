# Phase 5.2.2-E.3.1 — Single T+30 offline Java compilation

**COMPILE_PASS.** Exactly one offline Maven compilation ran for the frozen Apache
Commons CLI T+30 revision. Maven and Docker exited 0. All 36 registered production
Java sources match the compiler input list, including all 10 files in the new
`org.apache.commons.cli.help` package. The compiler's 55 created-file entries match
55 independently parsed Java 8 class files. All 25 independent acceptance checks pass.

The task-owned container was removed after capture. No retry, artifact acquisition,
preliminary Maven goal, other-revision preparation/compilation, SonarQube, scanner,
forecasting, debt measurement or dataset admission occurred. Analyzer licensing
and derived-data rights remain unresolved and unchanged.

Starting main: `ab7c015649897899038835cc97dc00c75bfb1b17`.
Execution: **2026-10-19 00:07:15 EEST** to
**2026-10-19 00:07:26 EEST**. Raw machine timestamps retain UTC.

## Verified inputs

| Input | Identity |
| --- | --- |
| Repository / offset | apache/commons-cli / T+30 |
| Commit | `7ddf691ac2afbda7473c0d07f1f4e7ae1e69e47b` |
| Tree | `a2ff09febdac9da6e6ee422a9144ad09d81113bf` |
| Historical POM SHA256 | `674975083520370c7a691778fa6fcdfe2eb0ae672c48abc923ffc75688c73e8e` |
| Source inventory | 137 tracked files, 36 production Java files |
| Parent chain | Commons Parent 78 → Apache Parent 33 |
| Runtime | Maven 3.9.11 / Temurin 17.0.17+10 / release 8 |
| Artifact population | 751 verified files |
| Dependency manifest SHA256 | `2e77c1a9578231e6b9f8d6425fb6ebe45304d7905f8e91d02346e1ca0d199fa9` |
| Canonical cache SHA256 | `a6469c15e4a99fcb4b59f8c4c3a9c19892523cffa8a5a2467711cda11399b463` |
| Actual target effective-POM hash | UNAVAILABLE, null |

Commit/tree object bytes and all 137 Git blobs, file modes, paths, SHA256 hashes and
historical POM bytes were checked against frozen Git objects. Each artifact passed
exact-path/coordinate, recorded Central checksum provenance, local SHA256 and
POM XML or JAR ZIP/CRC checks. Same-origin checksums over TLS are not an independent
publisher-signature assertion. All 20 target descriptors, parent/import metadata,
project test-dependency closure and 318 registered compile-candidate references
were rechecked without network access or Maven. The target-only static model,
plan, closure and candidate records match E.3's published evidence. No T+60/T+90
model preparation or source export was performed.

Independent copies have different inodes from the original source/cache inputs.
The old E.3 cache and its sealed 46-request ledger remain unchanged. New private
inputs and execution artifacts are confined to `/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_3_1/2026-10-19/attempt-1`. No original export,
user cache, POM or Git worktree was modified. No `.git` metadata was manufactured.

The new `tools/build_compile_e31.py` and `tools/verify_compile_e31.py` reuse the
proven setup/capture and class-parser libraries, with an E.3.1-only mode, ownership
label, exclusive claim, 137-source/751-artifact registration and explicit 36-source
compiler registration. They do not invoke consumed runners. Archived adapters and
smoke sentinels are unchanged. New capture records actual repository tmpfs usage
before and after Maven, independently of the conservative capacity estimate.
Named top-level, nested, anonymous and package-info outputs are audited separately.

The pinned local image is
`sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82`.
Maven launcher/core and Java launcher/release-file hashes match Task B's evidence;
these files were copied from the single stopped owned container for verification.
No preliminary JVM or probe container ran. Shared hash-pinned settings are tooling,
not a substituted earlier revision's model/profile evidence. Executed wrapper SHA256:
`45a32267202c9daaf128689568d21114ebf19ed5fcc354279ff49bd34a39de7e`.

## Actual Maven execution

The sole command was:

```bash
/usr/share/maven/bin/mvn --offline --batch-mode --no-transfer-progress --errors \
  -s /inspection/settings.xml -gs /inspection/settings.xml \
  -Dmaven.repo.local=/runtime-repository -Duser.home=/tmp \
  -Dmaven.test.skip=true -Dmaven.compiler.release=8 compile
```

`MAVEN_OPTS=-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp`.
HOME=/tmp, MAVEN_CONFIG=/tmp/.m2, MAVEN_SKIP_RC=true; MAVEN_ARGS,
JAVA_TOOL_OPTIONS and JDK_JAVA_OPTIONS are empty. No explicit profiles, dependency
version changes, extra skip properties or build-plan task override were supplied.

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

Both original Enforcer version checks passed. RAT reported 126 approved licenses,
zero unknown, unapproved or generated entries. Check-buildplan completed and checked
20 deploy-plan descriptors. Its references to later plugins do not mean those
goals executed. Original remote-resources configuration reported its skip; no
agent-added skip flag was used. Resources copied two files. The compiler explicitly
reported `Compiling 36 source files with javac [debug release 8]` and BUILD SUCCESS.
No test compilation, test classes or unauthorized lifecycle goal was observed.

Buildnumber 3.2.1 attempted the original Git commands in the detached source export
and used its configured `??????` / `UNKNOWN_BRANCH` fallbacks without failing the
build. Scientific lineage remains the independently verified commit and tree,
never those placeholders. No SCM workaround or fake Git metadata was introduced.

Three missing-POM warnings occurred during successful RAT metadata collection:
log4j:log4j:1.2.12, logkit:logkit:1.0.1 and
avalon-framework:avalon-framework:4.1.3. The analyzer and independent auditor retain
the observed RAT context and classify them as nonfatal metadata warnings. No fatal
offline dependency failure occurred. These warnings justify no automatic JAR
acquisition. Jansi's native library could not load from noexec `/tmp`; it remained
nonfatal, and isolation was preserved. RAT's header check does not clear rights gates.

## Independent output verification

The target produced **55 classes**: 34 named top-level, 11 named nested, 7 synthetic helpers, 1 anonymous
and 2 package-info classes. All match their internal/path identities and frozen
owning source files, with valid class magic, parsed structure and major version 52.
The new help package is included. The exact class population reconciles with
`createdFiles.lst`; all 36 compiler inputs reconcile with frozen source identities.
Counts were measured for this target, not borrowed from the earlier 37-class builds.
The independent verifier corrected the adapter's preliminary numeric-name category:
seven `$1` files have ACC_SYNTHETIC; TableDefinition$1 has an own InnerClasses entry
with inner_name_index=0 and EnclosingMethod, and the original source declares
`new TableDefinition() { ... }`. Package-info retains its own category even when
its access flags include synthetic. Original raw result, execution receipt and
adapter are unchanged; `adapter_kind` and classification basis preserve this
reconciliation. The independent verifier was strengthened after the build, with
four additional tests; it only rereads existing evidence and launches no process.
Structural parsing is not a separately executed JVM bytecode verifier.

LICENSE.txt and NOTICE.txt are the two generated nonclass resources, separately
hashed. All 137 original source/POM bytes and modes and all 751 artifact bytes
remain unchanged. Maven added zero repository metadata files. Setup and Maven
streams were captured separately. Complete Maven stdout is 5164 bytes,
stderr 569 bytes; neither was truncated. EXIT-trap, setup-stage,
Maven/Docker terminal status, post-run hashes, cgroup counters and task-owned
container events were retained. All required capture evidence is present.

Actual profile enumeration, effective-POM export and exact compiler classpath or
argument vector remain **UNAVAILABLE**. The authorized command did not export/log
them. E.3's 24 project-profile records retain their static UNKNOWN classification;
no prior revision's runtime profile/model identity was transferred. This successful
compile proves this target/context, not a separate effective-model capture or
later lifecycle execution.

See [output verification](examples/phase5_2_2_e_3_1/output_verification.json),
[class manifest](examples/phase5_2_2_e_3_1/class_output_manifest.json),
[lifecycle receipt](examples/phase5_2_2_e_3_1/lifecycle_evidence.json) and
[execution evidence](examples/phase5_2_2_e_3_1/build_execution_evidence.json).
Raw logs and classes remain outside Git; capture inventories publish their hashes.

## Resource evidence

| Measurement | Actual result |
| --- | ---: |
| Available RAM immediately before start | 9,249,013,760 bytes |
| Minimum sampled available host RAM | 8,939,352,064 bytes |
| Free disk immediately before start | 15,529,373,696 bytes |
| Container memory / heap caps | 2 GiB / 768 MiB |
| Cgroup peak memory | 361,684,992 bytes (344.93 MiB) |
| OOM / OOM-kill / memory-max events | 0 / 0 / 0 |
| CPU usage | 10.495120 CPU-seconds |
| Maven wrapper / internal time | 9.89s / 7.730s |
| Host monitor duration | 11.72s |
| Artifact payload | 80,129,204 bytes |
| Actual tmpfs allocated before / after Maven | 81,666,048 / 81,666,048 bytes |
| Actual remaining repository capacity | 52,551,680 bytes |
| Conservative capacity estimate, including reserve | 101,806,080 bytes |
| Repository tmpfs cap | 134,217,728 bytes (128 MiB) |
| Containers / Maven launches / retries / artifact requests | 1 / 1 / 0 / 0 |

Live admission satisfied >=4 GiB available RAM and 2 GiB host headroom, adequate disk,
no prohibited workloads/running containers, pinned local image and verified cache
capacity. The estimate includes 4 KiB file allocation, directory overhead and the
unchanged 16 MiB metadata reserve; kernel `df`, `du` and filesystem counters record
actual allocated tmpfs usage separately. No resource ceiling was raised.

Security remained one CPU, 64 PIDs, zero extra swap, UID/GID 1000:1000, dropped ALL
capabilities, no-new-privileges, read-only root, network none and image pull-never.
Only read-only task input/inspection binds were mounted; no socket, credentials or
user-cache mount. Source/repository/tmp each retain 128 MiB owned noexec/nosuid/nodev
tmpfs; output 32 MiB, shm 8 MiB, file cap 8 MiB, archive 32 MiB, nofile 1024,
Maven timeout 240s, monitor 265s and outer 330s. Cleanup removed only the owned
container. No unrelated service was stopped. Controller address-space was capped
at 1 GiB on CPU0; its RSS was not separately measured and is not the cgroup peak.

## Regression and preservation

**857 tests passed in each checkout**, zero failures/errors/skips:
22.253s canonical and
22.057s original project. The suite includes
794 previous relevant tests plus 63 new target-specific tests. Before the build,
148 deterministic policy, identity, failure-capture and class-mapping tests passed
without Maven or a build container. New checks include the help package, anonymous
and package-info mapping, actual tmpfs capture, exact registrations, one-attempt
accounting, resource gates, prohibited goals and preservation boundaries.

Preservation PASS covers the independently reverified T0, T−30 and T−90 COMPILE_PASS
receipts/class archives, every prior private cache/report/claim/ledger, all 18
registered source states, 56 frozen research bundles and 322 artifacts, two Phase
5.1 bundles, the source database and model hashes, 6,262 user-cache entries and
75 rehashed reference artifacts. The old SonarQube container/volumes and unrelated
files/containers are unchanged; no shared-container change was observed. Four
preexisting untracked remediation files remain unchanged. Previous request ledgers
remain D=2000, D.1=400, D.2=52, D.3=112, E.0.3=56, E.0.5=12,
E.0.5.1=52, E.1=32, E.2=67, E.3=46.

The original project HEAD remains unchanged. New files are mirrored there and
published from the canonical checkout as a normal main descendant commit.
See [regression receipt](examples/phase5_2_2_e_3_1/verification.json),
[preservation](examples/phase5_2_2_e_3_1/preservation.json) and
[source-state preservation](examples/phase5_2_2_e_3_1/all_source_states_preservation.json).

## Files and reproduction

New files: `tools/build_compile_e31.py`, `tools/verify_compile_e31.py`,
`tests/test_build_compile_e31.py`, `tests/test_verify_compile_e31.py`, this report
and `examples/phase5_2_2_e_3_1/` sanitized evidence and handoff. No production feature,
archived runner, historical POM, dataset or earlier result was changed.

Read-only verification from the original project:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -c 'import json; from tools.verify_compile_e31 import audit; print(json.dumps(audit("/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_3_1/2026-10-19/attempt-1")["checks"],indent=2))'
```

Targeted tests:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_build_compile_e31.py tests/test_verify_compile_e31.py
```

The verification receipt contains the full 27-file regression invocation. These
read-only checks grant no further build attempt. The E.3.1 claim is consumed;
**do not rerun the compile adapter**. Binaries, dependencies, source exports,
compiled classes and raw runtime files remain outside Git.

**STOP after E.3.1 publication.** No correction is required for this compile.
The [handoff](examples/phase5_2_2_e_3_1/NEXT_REVISION_HANDOFF.md) requires separate
authorization for any next revision or action. No T+60/T+90 preparation,
acquisition, retry, SonarQube, scan, debt collection, forecasting, dataset admission
or Phase 5.3 follows. Analyzer licensing and derived-data rights remain unresolved.
