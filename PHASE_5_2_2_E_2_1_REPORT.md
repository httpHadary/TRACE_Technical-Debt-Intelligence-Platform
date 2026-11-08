# Phase 5.2.2-E.2.1 — Single T−90 offline Java compilation

**COMPILE_PASS.** Exactly one genuine offline Commons CLI T−90 compilation ran.
The full original lifecycle through compile completed with Maven/Docker exit0.
All26 registered production Java inputs match the compiler input list. Its37
created-file entries match37 independently parsed Java8 class outputs,with no
missing top-level identity. The owned container was removed after evidence capture.

No retry,dependency acquisition,other revision,preliminary Maven goal,SonarQube,
scanner,forecasting,debt measurement or dataset admission ran. Analyzer licensing
and derived-data rights remain unresolved and unchanged.

Starting main:`1e1800893c9725290c4b94016492c608e7eb71c3`.
Execution:**2026-10-18 23:29:02 EEST** to
**2026-10-18 23:29:13 EEST**. Machine timestamps retain UTC.

## Frozen inputs and independent registration

| Input | Verified identity |
| --- | --- |
| Repository /offset |apache/commons-cli /T−90|
| Commit |`e1529b546d9696192f4de52152777403b4a01b39`|
| Tree |`c1a67e730fc5729a5376c267ed559f4ae310df01`|
| Historical POM SHA256 |`f4403aa060f16ca0f17d28fffb1bc6fcc42c31d480af8dc6a6436f25fddf8f15`|
| Source population |116 tracked files,26 production Java files|
| Parent chain |Commons Parent71 →Apache32|
| Runtime |Maven3.9.11 /Temurin17.0.17+10 /release8|
| Properties |maven.test.skip=true,user.home=/tmp,no explicit profiles|
| Artifact population |734 verified files|
| Artifact manifest SHA256 |`abbfd6711f2d16b4eb4f0992d819c01cb85c8cef385f6a7c9effb2136d35e4b6`|
| Canonical cache SHA256 |`e4870752be9fc1517fbdbb6eb785a704211950630839ac12e39d562725e95ecf`|
| Actual effective-POM hash |UNAVAILABLE,null|

All Git commit/tree/blob identities,116 source hashes,paths and modes were verified
against the frozen Git objects. CommandLine.java,HelpFormatter.java and Option.java
retain their original T−90 bytes,which differ from the two successful comparison
revisions. Every734 artifact passed exact-coordinate/path,recorded Central checksum
provenance,SHA256,POM XML or JAR structure/CRC checks. All20 descriptors,their
parent/import metadata and400 original compile-candidate references were rechecked
with the E.2 read-only audit. Its result is identical to E.2's frozen final audit.

Independent source/cache copies use different inodes in a new private directory.
No older cache/export or user Maven repository was mounted writable or overwritten.
No historical POM or source was edited,and no Git metadata was manufactured.
Both previous successful builds were independently reverified before and after
execution;their raw receipts,class archives,claims and inputs remain unchanged.

New `tools/build_compile_e21.py` and `tools/verify_compile_e21.py` reuse the proven
sandbox/capture and parser libraries with E.2.1's own owner,label,mode,
116-source/734-artifact registration and exclusive claim. They never invoke the
consumed E.1.1 execution entry point. The new mode is `--e21-offline-compile`.
T−90's own frozen metadata and verified descriptors define permitted goals and
phase order. Source declarations and actual compiler-created files define output
completeness;no previous37-class or RAT-approval count was an acceptance condition.

The pinned local image was
`sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82`.
Four binary identities—Maven launcher/core and Java launcher/release file—match
TaskB's published hashes. Verification copied these files from the one stopped
owned container;no preliminary JVM,probe container,Help Plugin or build ran.
The shared isolated settings are hash-pinned tooling,not transferred T0/T−30
model/profile evidence. Executed wrapper SHA256:
`92a6567d213e6fbd73eaba04c30b8ee935147a33c92da0626220b7490f406870`.

## One original Maven lifecycle

The sole Maven command was:

```bash
/usr/share/maven/bin/mvn --offline --batch-mode --no-transfer-progress --errors \
  -s /inspection/settings.xml -gs /inspection/settings.xml \
  -Dmaven.repo.local=/runtime-repository -Duser.home=/tmp \
  -Dmaven.test.skip=true -Dmaven.compiler.release=8 compile
```

`MAVEN_OPTS=-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp`.
HOME=/tmp,MAVEN_CONFIG=/tmp/.m2,MAVEN_SKIP_RC=true;MAVEN_ARGS,JAVA_TOOL_OPTIONS
and JDK_JAVA_OPTIONS empty. No profile,version,skip,build-plan task,enforcer,
resource or compiler override was added beyond the registered original properties.

| Actual order | Goal /execution | Observed result |
| --- | --- | --- |
|1|enforcer3.4.1:enforce /enforce-maven-version|PASS|
|2|enforcer3.4.1:enforce /enforce-java-version|PASS|
|3|apache-rat0.16.1:check /rat-check|PASS;105 approved,0 unknown/unapproved/generated|
|4|artifact3.5.1:check-buildplan /check-buildplan|PASS;20 deploy-plan descriptors checked|
|5|build-helper3.6.0:parse-version /parse-version|Completed|
|6|antrun3.1.0:run /javadoc.resources|Completed;2 resource files copied|
|7|remote-resources3.2.0:process /process-resource-bundles|Goal executed;original config reports skip|
|8|buildnumber3.2.0:create /default|Completed with original detached-SCM fallback|
|9|resources3.3.1:resources /default-resources|Completed;2 nonclass resources|
|10|compiler3.13.0:compile /default-compile|Compiled26 sources with javac release8|

Only actual goal banners count as executed goals. Check-buildplan's mentions of
Surefire,Felix,CycloneDX,SPDX,Moditect,install/deploy and later plugins were metadata
checks. Their goals did not execute. No test compilation,test-class directory or
unapproved phase was observed. The original inherited remote-resources skip
configuration was preserved;the agent did not add a skip flag.

Buildnumber tried Git commands in the detached export,then used the original
`??????` revision and `UNKNOWN_BRANCH` fallback. That behavior was nonfatal and
required no SCM workaround. Scientific lineage uses the independently verified
commit/tree,never these placeholders. No fake `.git` metadata was introduced.

Three nonfatal POM warnings occurred during RAT:log4j1.2.12,logkit1.0.1 and
avalon-framework4.1.3. Both the new analyzer and independent verifier attribute them
to actual RAT metadata collection,not fatal project dependencies. RAT succeeded;
no fatal missing offline artifact was reported. No JAR requirement or acquisition
is inferred from these POM warnings. Jansi could not load its native library from
noexec `/tmp`;this was nonfatal and all isolation controls stayed in place.
RAT's license-header result does not resolve human rights/policy gates.

## Verified outputs and observation limits

All22 independent acceptance checks pass. The actual compiler input list exactly
matches the26 frozen T−90 Java sources. The37 created-file entries match37 parsed
classes:25 top-level identities,11 nested classes linked to their owning source,
and1 package-info class checked separately. Each class has valid magic,parsed
structure,matching internal/path identity,SourceFile mapping and major52 (Java8).
The count was measured for T−90,not required to equal the other builds. LICENSE.txt
and NOTICE.txt are2 nonclass resources,recorded separately with hashes.
Structural parsing is not a separately executed JVM bytecode verifier.

All116 source/POM bytes and executable modes remain unchanged. All734 artifact
bytes remain unchanged;Maven added zero repository metadata files. Setup and Maven
stdout/stderr are separate. Complete Maven stdout is4817 bytes,stderr569 bytes;
no log was truncated. Setup stages,EXIT-trap,Maven and Docker terminal exit0,
cgroup counters,source/cache post-hashes,task-owned events and cleanup were captured.
No required acceptance evidence is missing. Raw logs,source exports and class
archives remain private;published capture inventories identify them by hashes.

**Actual profile enumeration,effective-POM export and exact compiler classpath or
argument vector remain UNAVAILABLE.** The approved command did not log/export
them. No previous model/profile/classpath identity is substituted. E.2's three
remote compiler-property activation uncertainties remain UNKNOWN,with their prior
scoped static assessment unchanged. Build success establishes empirical compile
readiness for this context,not a separately captured effective model or proof of
other revisions/later lifecycle goals.

See [output verification](examples/phase5_2_2_e_2_1/output_verification.json),
[class identities](examples/phase5_2_2_e_2_1/class_output_manifest.json),
[lifecycle evidence](examples/phase5_2_2_e_2_1/lifecycle_evidence.json) and
[execution receipt](examples/phase5_2_2_e_2_1/build_execution_evidence.json).

## Resources and isolation

| Measurement | Result |
| --- | ---: |
| Available host RAM immediately before start |8,351,924,224 bytes|
| Minimum sampled host available RAM |8,083,869,696 bytes|
| Admission /host headroom requirement |4GiB /2GiB|
| Free disk immediately before start |15,466,950,656 bytes|
| Container memory /JVM heap cap |2GiB /768MiB|
| Cgroup peak memory |356,397,056 bytes (339.89MiB)|
| OOM /OOM-kill /memory-max events |0 /0 /0|
| CPU usage |9.966012 CPU-seconds|
| Maven wrapper /internal time |9.39s /7.369s|
| Host monitor duration |11.23s|
| Artifact payload /observed runtime repository payload |78,245,716 /78,245,716 bytes|
| Rounded files /directory estimate /metadata reserve |79,753,216 /3,325,952 /16,777,216 bytes|
| Total runtime repository estimate |99,856,384 bytes (~95.23MiB)|
| Existing repository tmpfs cap |134,217,728 bytes (128MiB),unchanged|
| Containers /Maven launches /retries /downloads |1 /1 /0 /0|

Live admission found no prohibited workload or running container. The local image
was used with pull-never. Controls remained1CPU,64PIDs,no added swap,UID/GID1000,
ALL capabilities dropped,no-new-privileges,read-only image root,network none,
owned noexec/nosuid/nodev tmpfs,and read-only input/inspection binds only. No Docker
socket,credentials or user-cache mount was provided. Source/repository/tmp caps
remain128MiB each,output32MiB,shm8MiB,file cap8MiB,nofile1024,archive cap32MiB,
Maven timeout240s,monitor265s and outer330s. No resource limit was raised and no
unrelated process was stopped. Container cleanup removed only the task-owned resource.

The capacity estimate includes the original16MiB metadata reserve and34,361,344
bytes estimated headroom. Kernel tmpfs enforcement stayed authoritative. Resource
receipts retain actual CPU throttling,memory events,terminal state and post-task
host RAM/disk observations. Controller RSS was not separately measured;its1GiB
address-space cap on CPU0 is distinct from the measured container cgroup peak.

## Tests and preservation

**740 tests passed in each checkout**,zero failures/errors/skips:
20.712s canonical and20.953s original project.
The suite contains686 prior relevant tests and54 new E.2.1 tests. Before the single
attempt,137 policy/identity/capture tests passed without a real Maven/container
launch. The new tests cover exact734/116 registration,own target/plugin versions,
claim exclusivity,old-task protection,resource guards,unsafe sandbox settings,
fatal dependency/SCM/build handling,nonfatal warning attribution,unavailable evidence,
dynamic class populations and rejection of unapproved goals. A test fixture's old
phase path was corrected before execution;it consumed no build attempt.

Preservation PASS covers both previous successful builds and class/raw archives,
all old private caches,reports,request ledgers and consumed claims,all18 registered
source snapshots,56 frozen research bundles/322 artifacts,two Phase5.1 bundles,
source database/model hashes,6262 user-cache entries and75 rehashed reference
artifacts,old SonarQube state/volumes,and unrelated files/containers. Prior request
counts remain D=2000,D.1=400,D.2=52,D.3=112,E.0.3=56,E.0.5=12,E.0.5.1=52,
E.1=32,E.2=67. Four preexisting untracked remediation files remain unchanged.
No independent shared-container change was observed. The original project HEAD
stays unchanged;new task files are mirrored there and published via the canonical
checkout as a normal descendant main commit.

See [tests](examples/phase5_2_2_e_2_1/verification.json),
[preservation](examples/phase5_2_2_e_2_1/preservation.json),
[all18 source states](examples/phase5_2_2_e_2_1/all_source_states_preservation.json)
and [previous successful builds](examples/phase5_2_2_e_2_1/successful_builds_preservation.json).

## Files,reproduction and STOP

New files only: `tools/build_compile_e21.py`,`tools/verify_compile_e21.py`,
`tests/test_build_compile_e21.py`,`tests/test_verify_compile_e21.py`,this report
and `examples/phase5_2_2_e_2_1/` sanitized evidence and handoff. No archived runner,
historical POM,previous report,cache,dataset or production feature was modified.

Private attempt directory:`/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_2_1/2026-10-18/attempt-1`.
Its exclusive claim is consumed. **Do not repeat the compile command.**
Dependencies,binaries,raw logs,historical source exports and class outputs remain
outside Git. Small manifests contain hashes and sanitized observations only.

Read-only output audit from the original project directory:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -c 'import json; from tools.verify_compile_e21 import audit; print(json.dumps(audit("/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_2_1/2026-10-18/attempt-1")["checks"],indent=2))'
```

Focused deterministic tests:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_build_compile_e21.py tests/test_verify_compile_e21.py
```

The verification receipt lists the full24-file regression command. These read-only
commands do not grant another build attempt.

**STOP after E.2.1 publication.** No correction is needed for this successful
compile. The [next-revision handoff](examples/phase5_2_2_e_2_1/NEXT_REVISION_HANDOFF.md)
requires separate authorization for any subsequent revision or action. No next
revision was selected,exported or prepared. No retry,acquisition,SonarQube/scanner,
forecast,debt measurement,dataset admission orPhase5.3 follows automatically.
Analyzer licensing and derived-data rights gates remain unresolved and unchanged.
