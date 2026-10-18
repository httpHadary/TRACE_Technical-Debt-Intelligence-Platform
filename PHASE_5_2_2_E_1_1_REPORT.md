# Phase 5.2.2-E.1.1 — T−30 historical Java compilation

**COMPILE_PASS.** Exactly one offline Commons CLI T−30 compilation ran. The
original lifecycle completed with Maven/Docker exit0. All26 registered production
Java inputs match the actual compiler input list;37 independently parsed class
outputs match its created-files list. Every class has Java8 major version52.
No retry,dependency acquisition,other revision,preliminary Maven goal,SonarQube,
forecasting or dataset admission ran. The task-owned container was removed.

Starting main: `cb43f8121bdb5d596f5176b6630f4b72b2a23596`.
Execution: **2026-10-18 21:53:43 EEST** to
**2026-10-18 21:53:54 EEST**. Machine receipts retain UTC.

## Verified inputs and sandbox

| Input | Verified identity |
| --- | --- |
| Revision |apache/commons-cli,T−30|
| Commit |`fb6293fcd6a9b55ac8ecb550af6572daaed18fa1`|
| Tree |`598dec4901a9adcf8e55b241c9689a8db6219c29`|
| Historical POM SHA256 |`2f322b0751115f2a5e93aabfb83372dc0511d57bbd8b4f178f08d5b449ff3fcf`|
| Source population |116 tracked files,26 production Java files|
| Parent |Commons Parent74|
| Runtime |Maven3.9.11,Temurin17.0.17+10,release8,testskip=true,no explicit profiles|
| Artifact population |710 verified files; no additional artifacts|
| Dependency manifest SHA256 |`c1211045a0d09098bb9b401f8ab019aa491c9c3fa2c7603f840c3ac7d193ce43`|
| Canonical cache SHA256 |`e5176a8b83de3359f8aa0c5d16b941af73c6e8e4a10109fb95a441dc83701d0c`|
| Actual T−30 effective-POM hash |UNAVAILABLE,null; T0 hash never substituted|

All116 paths,Git blob IDs,tree,file modes,source hashes and POM bytes were
reverified. Every710 artifact passed SHA256,exact coordinate/path,recorded Central
checksum/provenance,POM XML or JAR CRC checks. All20 descriptors and required parent
metadata passed the existing read-only T−30 static audit. Its JSON-normalized result
matches E.1; no new network request was needed. An initial private comparison
mistook in-memory tuples versus serialized JSON lists for a difference; normalizing
JSON resolved that comparison without changing evidence,inputs or the audit code.

Inputs were copied independently into a fresh E.1.1 directory,with different
inodes and unchanged bytes. No older cache was reused as writable storage or
hard-linked. The detached source contains no manufactured Git metadata or extra
Maven configuration. T0's successful result was independently rechecked and
preserved; none of its output counts,profile evidence or model hash was used as a
T−30 acceptance assertion.

New `tools/build_compile_e11.py` reuses the proven setup/capture libraries with
its own owner,`--e11-offline-compile` mode,116-source/710-artifact registration and
exclusive claim. It never calls an old runner entry point. Target lifecycle
identities come from T−30's own metadata and verified descriptors; goals must match
that allowlist and lifecycle phase order. Actual same-phase order is recorded.
The class verifier derives identities from T−30 packages/source declarations,
then checks the actual compiler-created population rather than requiring T0's count.

The existing pinned image
`sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82`
was local and used with `--pull never`. Maven launcher/core,JDK launcher and JDK
release file hashes match TaskB evidence. No preliminary JVM or Maven version/help
goal ran. Shared isolated settings are hash-pinned tool configuration only.

Admission passed immediately before startup. Controls remained2GiB memory,
768MiB heap,1CPU,64PIDs,no added swap,UID/GID1000,dropped ALL capabilities,
no-new-privileges,read-only root,network none,and read-only input/inspection mounts.
No socket,credentials or user-cache mounts were provided. Owned noexec/nosuid/nodev
tmpfs caps remain128MiB each for source/repository/tmp and32MiB for output;shm8MiB,
file cap8MiB,nofile1024,archive cap32MiB,Maven timeout240s,monitor265s,outer330s.
No unrelated process was stopped and no resource ceiling was raised.

## Actual original lifecycle

The only Maven command was:

```bash
/usr/share/maven/bin/mvn --offline --batch-mode --no-transfer-progress --errors \
  -s /inspection/settings.xml -gs /inspection/settings.xml \
  -Dmaven.repo.local=/runtime-repository -Duser.home=/tmp \
  -Dmaven.test.skip=true -Dmaven.compiler.release=8 compile
```

`MAVEN_OPTS=-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp`.
No project,plugin,profile,build-plan task,enforcer or dependency override was added.

| Observed order | Goal /execution | Result |
| --- | --- | --- |
|1|enforcer3.5.0:enforce /enforce-maven-version|PASS|
|2|enforcer3.5.0:enforce /enforce-java-version|PASS|
|3|apache-rat0.16.1:check /rat-check|PASS;105 approved,0 unknown/unapproved/generated|
|4|artifact3.5.1:check-buildplan /check-buildplan|PASS;20 deploy-plan descriptors checked|
|5|build-helper3.6.0:parse-version /parse-version|Completed|
|6|antrun3.1.0:run /javadoc.resources|Completed;2 resource files copied|
|7|remote-resources3.2.0:process /process-resource-bundles|Executed;original configuration reports skip|
|8|buildnumber3.2.0:create /default|Completed with original detached-SCM fallback|
|9|resources3.3.1:resources /default-resources|Completed;2 production resources|
|10|compiler3.13.0:compile /default-compile|Compiled26 sources,release8|

These are actual goal banners,not inferred executions from the build-plan listing.
Surefire,deploy,install,Felix,CycloneDX,SPDX,Moditect and other later goals did not
execute. No test compilation or test-class directory was observed. The original
remote-resources skip setting and offline SCM behavior are inherited behavior;
they were not introduced to bypass a check.

Buildnumber3.2.0 attempted Git commands,then retained the original `??????` revision
and `UNKNOWN_BRANCH` fallback. Its missing Git context was nonfatal. Scientific
lineage uses the verified commit/tree,never those placeholders. No fake `.git` or
SCM workaround was introduced.

The three nonfatal RAT POM warnings remain:log4j1.2.12,logkit1.0.1 and
avalon-framework4.1.3. RAT completed successfully;no fatal missing runtime artifact
was reported. The inherited generic raw analyzer labels these POM warnings too
broadly as project dependencies. The separate read-only auditor attributes them
to the actual RAT goal;that final attribution controls the public dependency
receipt. Original raw evidence remains unchanged. No JAR requirement or recovery
is inferred from these warnings.

Jansi's native library could not load from noexec `/tmp`;this was also nonfatal.
Isolation was preserved. RAT header approval does not resolve human legal/policy
acceptance or SonarSource/analyzer/derived-data rights.

## Output and evidence verification

The compiler's26 input paths exactly match the registered production Java source
population. Its37 created-file entries match37 structurally parsed class outputs:
25 named top-level classes/interfaces,11 nested classes linked by SourceFile and
owner identity,and1 package-info class. All have valid class-file magic,parsed
structure and major52. Counts were established independently for T−30,not copied
from T0. Two LICENSE/NOTICE resources are recorded separately with hashes.
This is structural parsing,not a separately executed JVM bytecode verifier.

All22 read-only acceptance checks pass. Source/POM bytes and executable modes are
unchanged. All710 artifact bytes remain unchanged;Maven added zero repository
metadata files. Setup and Maven streams are separate;complete Maven stdout is
4817 bytes and stderr569 bytes. EXIT-trap,Maven and Docker exit codes are0.
Capture includes stage/category,source/cache post-hashes,cgroup counters,container
state,task-owned events and cleanup. No required acceptance measurement is missing.
Raw logs and compiled binaries remain outside Git;published evidence contains
selected sanitized lines,identities and capture hashes.

**Actual active-profile enumeration,effective-POM export and exact compiler
classpath/argument vector remain UNAVAILABLE.** The authorized command did not
print/export them. Static dependency declarations remain labeled static metadata;
T0's D.3 model/profile results are not substituted. No extra goal or debug flags
were used to obtain those observations. Runtime compile success is not a separately
captured Maven effective-model artifact or proof of later lifecycle readiness.

See [output verification](examples/phase5_2_2_e_1_1/output_verification.json),
[class manifest](examples/phase5_2_2_e_1_1/class_output_manifest.json),
[lifecycle evidence](examples/phase5_2_2_e_1_1/lifecycle_evidence.json) and
[execution receipt](examples/phase5_2_2_e_1_1/build_execution_evidence.json).

## Measured resources

| Measurement | Actual result |
| --- | ---: |
| Host available RAM immediately before start |6,984,830,976 bytes|
| Minimum sampled host available RAM |6,666,973,184 bytes|
| Admission requirement /host headroom |4GiB /2GiB|
| Free disk immediately before start |15,753,404,416 bytes|
| Peak cgroup memory |358,346,752 bytes (341.75MiB)|
| OOM /OOM-kill /memory-max events |0 /0 /0|
| CPU usage |10.116617 CPU-seconds|
| Maven wrapper /Maven internal time |9.53s /7.410s|
| Host monitor duration |11.22s|
| Cache payload |76,381,676 bytes|
| Rounded files +directories +16MiB reserve |97,898,496 bytes|
| Repository tmpfs cap |134,217,728 bytes (128MiB),unchanged|
| Observed runtime repository payload |76,381,676 bytes|
| Containers /Maven launches /retries /downloads |1 /1 /0 /0|

[Resource evidence](examples/phase5_2_2_e_1_1/resource_evidence.json) includes
actual CPU throttling,cgroup limits and final host RAM/disk recheck. The128MiB
capacity calculation retains16MiB metadata reserve and36,319,232 bytes estimated
headroom. Controller peak RSS was not separately measured;its process address-space
cap was1GiB on CPU0. Container cgroup peak is not substituted for controller RSS.

## Regression and preservation

**637 tests passed in each checkout**,zero failures/errors/skips:
19.115s in the canonical checkout and
19.085s in the original project. This includes
589 prior E.0–E.1 relevant tests and48 new adapter/auditor tests. Before the build,
131 policy/integrity/capture tests passed without a real Maven/container launch.
Later tests inspect policy,fixtures or read-only evidence;they never retry the build.

Preservation PASS covers all18 registered commit/tree/full source inventories,
all prior caches/reports/claims and T0's successful evidence/classes,56 frozen
research bundles/322 artifacts,two Phase5.1 bundles,source SQLite/model checkpoint
hashes,6262 user-cache entries and75 rehashed reference artifacts,old SonarQube
state/volumes,and unrelated files/containers. Prior request ledgers remain
D=2000, D.1=400, D.2=52, D.3=112, E.0.3=56, E.0.5=12, E.0.5.1=52, E.1=32.
Four preexisting untracked remediation files remain unchanged. No independent
shared-container change was observed. Only the E.1.1 owned container was removed.
The original project HEAD remains unchanged;new files are mirrored there and
published through the canonical checkout as a normal descendant main commit.

See [tests](examples/phase5_2_2_e_1_1/verification.json),
[preservation](examples/phase5_2_2_e_1_1/preservation.json),
[all18 source states](examples/phase5_2_2_e_1_1/all_source_states_preservation.json)
and [T0 revalidation](examples/phase5_2_2_e_1_1/t0_preservation_verification.json).

## Files,reproduction and STOP

New code/tests only: `tools/build_compile_e11.py`,`tools/verify_compile_e11.py`,
`tests/test_build_compile_e11.py`,`tests/test_verify_compile_e11.py`,this report and
`examples/phase5_2_2_e_1_1/` sanitized evidence. No archived runner,report,cache,
historical POM,benchmark,dataset or existing production component was changed.

Private attempt directory:
`/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_1_1/2026-10-18/attempt-1/`.
Its claim is consumed. **Do not rerun the compile command.** Dependencies,raw
logs,source export,compiled classes and runtime files remain outside Git.

Read-only verification from the original project directory:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -c 'import json; from tools.verify_compile_e11 import audit; print(json.dumps(audit("/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_1_1/2026-10-18/attempt-1")["checks"],indent=2))'
```

Focused deterministic tests:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_build_compile_e11.py tests/test_verify_compile_e11.py
```

The verification receipt contains the full21-file regression invocation. Reading
and testing evidence does not grant another Maven attempt.

**STOP after E.1.1 publication.** This exact compile needs no correction. The
[next-revision handoff](examples/phase5_2_2_e_1_1/NEXT_REVISION_HANDOFF.md) requires
separate authorization,target-specific readiness and a new adapter/claim before
any other revision. No next revision was selected or prepared. No acquisition,
SonarQube/scanner,forecasting,debt measurement,dataset admission orPhase5.3 follows.
Analyzer licensing and derived-data rights gates remain unresolved and unchanged.
