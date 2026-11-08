# Phase 5.2.2-E.0.5 — Targeted Maven build-plan plugin recovery

Date:2026-10-18, Africa/Cairo. Base main:
`2ab7993630135c3921b86c6d8739b92d3afa69a8`.

**RECOVERED_EXACT_FELIX_PLUGIN.** The exact Felix5.1.9 POM,JAR,plugin descriptor and
required parent metadata are verified in a new independent cache. It contains
**682 artifacts:679 unchanged seeds plus3 additions**. The cache fits the existing
128MiB repository tmpfs. No Maven,Java,plugin,container,compile retry,scan,model or
dataset operation ran.

**Full static build-plan readiness remains PARTIAL.** A read-only inventory found
six other plugin descriptor pairs missing from the frozen `deploy` plan. The Felix
blocker is recovered; STATIC_BUILD_PLAN_CLOSURE_COMPLETE, COMPILE_PASS and
FULL_OFFLINE_BUILD_READY are not claimed. No additional batch was started.

## What was recovered

| Exact artifact | Evidence |
| --- | --- |
|`org.apache.felix:maven-bundle-plugin:5.1.9` POM|Verified coordinates,packaging,Central checksum and SHA256|
|Same5.1.9 JAR|Verified Central checksum,SHA256,ZIP structure/CRC and embedded metadata|
|`org.apache.felix:felix-parent:7` POM|Exact declared parent,checksum/coordinate verified|

The authoritative parent chain is Felix plugin5.1.9 ->Felix Parent7 ->Apache23.
Apache23 was already present in the verified seed; it was not downloaded again.
No BOM import was declared in this plugin's resolved metadata. Five profile
records were inspected; no unresolved metadata/profile condition was found in
this recovered Felix model. Broader pre-existing profile uncertainties remain
unchanged and are not silently relabelled.

`META-INF/maven/plugin.xml` was read as XML data. Its GAV matches the exact target,
the `manifest` goal exists,and its default phase is `process-classes`. Embedded
`pom.properties` matches the same GAV; the embedded POM equals the verified external
POM byte-for-byte. Descriptor SHA256:
`77573d6537a1b548ce60b11972d588ec31137b1358d92a79174fc689e6a2cb77`.
No classes were loaded or executed. All descriptors/metadata in the report are
actual recovered bytes,not generated stand-ins.

The plugin descriptor lists50 runtime entries. The direct POM also distinguishes
compile,provided and test declarations. They are preserved in the evidence with
existing-cache presence and later-runtime dispositions. **None of this runtime
universe was downloaded.** The observed failure was a descriptor lookup by
check-buildplan,not an execution of Felix's later `manifest` goal. Its
`requiresDependencyResolution=test` descriptor field does not itself prove that
a plan lookup creates the plugin runtime realm. Required future manifest-runtime
classpath resolution remains unverified.

This follows Maven3.9.11's separate code paths:
[getPluginDescriptor](https://raw.githubusercontent.com/apache/maven/maven-3.9.11/maven-core/src/main/java/org/apache/maven/plugin/internal/DefaultMavenPluginManager.java)
extracts plugin XML from the artifact; plugin realm setup occurs separately.
The single-plugin
[dependency resolver](https://raw.githubusercontent.com/apache/maven/maven-3.9.11/maven-core/src/main/java/org/apache/maven/plugin/internal/DefaultPluginDependenciesResolver.java)
reads the artifact descriptor and resolves the plugin JAR,while its runtime-graph
resolver is a different overload. These primary sources support this narrow
metadata recovery; actual offline Maven still must confirm the result.

## Why the broader plan is still incomplete

The cached Artifact Plugin3.5.1 descriptor specifies a default plan task of
`deploy`. The frozen effective POM has no task override. Its
[pinned source](https://raw.githubusercontent.com/apache/maven-artifact-plugin/maven-artifact-plugin-3.5.1/src/main/java/org/apache/maven/plugins/artifact/buildinfo/CheckBuildPlanMojo.java)
calculates that execution plan and checks planned plugins; it does not execute
those later goals. E.0.4's actual failure stack independently shows the descriptor
lookup inside plan calculation. Thus a compile command can require metadata for
later phases without running those phases.

The static inventory covers the fixed effective plugin executions and jar-packaging
default bindings through that plan. Exact versions come from the verified model,
not newest-version selection. Before recovery it found14 missing POM/JAR paths;
after recovery the Felix pair is resolved and12 paths remain:

| Frozen plugin | Missing metadata |
| --- | --- |
|`org.apache.maven.plugins:maven-surefire-plugin:3.5.0`|POM and JAR|
|`org.apache.maven.plugins:maven-install-plugin:3.1.2`|POM and JAR|
|`org.apache.maven.plugins:maven-deploy-plugin:3.1.2`|POM and JAR|
|`org.cyclonedx:cyclonedx-maven-plugin:2.8.1`|POM and JAR|
|`org.moditect:moditect-maven-plugin:1.2.2.Final`|POM and JAR|
|`org.spdx:spdx-maven-plugin:0.7.4`|POM and JAR|

These are authoritative **static plan candidates**,not new observed Maven errors.
Their exact paths and configured goals/phases are in
[plan_after.json](examples/phase5_2_2_e_0_5/plan_after.json). Missing descriptors may
expose more parents/imports; runtime/fork behavior is not assumed. No unsupported
profile/version decision was substituted. The six additional plugins and their
runtime trees were outside the targeted Felix batch and were not acquired.
Do not simply call the full plan ready because Felix's exact pair is now present.
Do not skip check-buildplan or change its tasks to conceal the remaining gaps.

## Separate RAT warning audit

All three exact POMs and corresponding JARs are absent from the679 seed and remain
absent from the682-file cache:

- `log4j:log4j:1.2.12`
- `logkit:logkit:1.0.1`
- `avalon-framework:avalon-framework:4.1.3`

Each is **NONFATAL_WARNING_NO_PROVEN_NEED_FOR_ACQUISITION** for this objective.
E.0.4's actual RAT execution succeeded despite the warnings. No warning was
reclassified as a fatal missing JAR,and no warning artifact was downloaded.

A no-network bounded audit of cached authoritative POMs finds this declaration
path for each exact warning:

```text
apache-rat-plugin:0.16.1
  -> org.apache.maven.doxia:doxia-site-renderer:1.11.1
  -> org.apache.velocity:velocity-tools:2.0
  -> commons-logging:commons-logging:1.1
  -> each exact warning coordinate
```

[Warning evidence](examples/phase5_2_2_e_0_5/rat_warning_classification.json) records
per-POM hashes,scope,optional flags and exclusions,other matching references and
that candidate path. RAT's flattened descriptor instead includes Commons
Logging1.2. The candidate path can explain dependency-collection metadata warnings
before mediation; it is **not proof that Commons Logging1.1 or those warning JARs
were on the actual resolved classpath**. Other static metadata/profile issues met
while traversing this existing graph remain explicit. They are not new Felix
closure uncertainties and were not used to justify broad acquisition.

## Verified cache, limits and resource results

All679 E.0.3 seed artifacts were reverified against the published manifest SHA256
`73de04d94fe2a1c85fd49f38bfdc14df47e0f93855a8ac5258a10d72f714b113`
and canonical cache SHA256
`f4bc6cbab0f8e0bc14557408173290a8453854c35226b40348bffe7a58011daa`.
Each path,coordinate,size,local SHA256,recorded Central checksum,POM and JAR CRC
was checked. Independent copies use different inodes,not hard links. All679 copied
seed hashes were rechecked after acquisition and in two independent offline audits.

Only `https://repo.maven.apache.org/maven2/` was permitted. Redirects/proxies were
disabled; exact versions were retained. Approved local paths were checked first,
but none of the3 new files existed there. All3 came from Central. SHA512/SHA256
sidecars were absent,so existing policy's SHA1 fallback was verified; local SHA256
is always recorded. TLS/same-origin checksums are not independent publisher
signatures. No unverified filename or local cache byte was trusted.

| Measurement | Actual / cap |
| --- | ---: |
| HTTP requests,including retries/checksum probes |12 /120|
| SHA512/SHA256 checksum404s |6|
| Transport retries |0|
| New response payload bytes read |242,951 /50,331,648 (~0.23 /48MiB)|
| New artifact bytes |242,831|
| New files |2 POMs,1 JAR|
| Per-artifact ceiling |32MiB|
| Acquisition elapsed time |18.029s /600s|
| Peak acquisition process RSS |37,932KiB (~37.04MiB)|
| Enforced address-space limit |1,073,741,824 bytes|
| Actual affinity/workers |CPU0 /one sequential acquisition worker|
| Task storage at static audit |77,517,544 bytes /268,435,456|
| Available RAM after acquisition |7,304,212KiB|
| Free disk after acquisition |20,267,065,344 bytes|
| Maven/Java/container executions |0 /0 /0|

Request attempts were sealed before I/O. Payload accounting counts bytes actually
read,including checksum data; it excludes TLS/headers and unread HTTP-error bodies.
One batch ran. No budget reset,second batch or further network after sealing
occurred. The unused allowance is not a continuation authorization.
Admission observed no running container or Java/Maven/Sonar process. No service
was stopped. User caches were only read; no Maven settings/cache was rewritten.

New cache payload:74,395,184 bytes. Rounded4KiB file allocations:75,804,672;
directory allowance:3,153,920; metadata reserve:16,777,216. Total estimated runtime
storage **95,735,808 bytes (~91.30MiB)**,below134,217,728 bytes (128MiB).
[Capacity status](examples/phase5_2_2_e_0_5/runtime_cache_capacity.json):**FITS_128_MIB**.
The estimate includes reserve; the actual kernel tmpfs cap is still authoritative.
No storage or2GiB container policy was increased. Later additions need a fresh
capacity check.

Final private cache:

```text
/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_5/2026-10-18/recovery-1/repository/
```

Manifest SHA256:`b19c9c644d21b9a8700ff1628beb1516aa286f1f4f0b917f2a94dd893868a202`.
Canonical682-file cache identity:`1d56fa167a1a296a680bd22bba4f5223e4d2a90fe099dc38fe8a1703b046120d`.
Recipe:sorted Maven paths,each encoded as
`sha256 + two spaces + byte_count + two spaces + relative_path + LF`.
The complete safe manifest,individual hashes/provenance and3-file addition list
are published. Downloaded payloads remain outside Git.

The private launch wrapper initially shadowed its task-path variable with the
read-only helper's research-root variable. After acquisition,the newly created
E.0.5 cache was moved into the dedicated phase directory. Its sealed12-request
manifest stayed byte-identical; there was no re-download,ledger reset,prior-cache
mutation or Maven execution. The private correction receipt records the move.

Two no-network audits produced identical evidence SHA256
`c5fb55aacdd0cf13cad8d5edf8aefc8ce85543030c5ea7ea96d4d7525a3ef33b` and left the acquisition ledger unchanged.
The post-acquisition code adds only read-only RAT path analysis; no subsequent
acquisition ran. Static closure verification and measured execution are distinct.

## Regression and preservation

**479 tests passed in each checkout**,zero failures/errors/skips,including29 new
E.0.5 cases. Central:21.579s;working project:
21.470s. Tests cover exact/versioned seeds,
independent copies,integrity/provenance rejection,fresh checksums for local bytes,
request/time/payload/disk limits,allowlisting,CRC and descriptor identity/duplicate/
size checks,no implicit runtime traversal,capacity blocking and nonexecuting plan
inventory. Existing recovery/build/sandbox/scope/foundation regressions passed.

Preservation **PASS**:551 pre-existing publication files,462 working files and4
unrelated unfinished files retain their hashes. D/D.1/D.2/D.3/E.0/E.0.1/E.0.2/
E.0.3/E.0.4 retain1378/615/630/842/790/818/832/703/869 file hashes respectively.
Ledgers remain2000/400/52/112/56;all prior attempt claims and reports are unchanged.
All117 T0 Git blob/source identities,tree,historical POM and D.3 model are verified.
All56 frozen experiment bundles/322 artifacts,both Phase5.1 bundles,SQLite and model
checkpoint hashes pass. User-cache6262 metadata entries and75 reference hashes
are unchanged. Old Sonar identity/state/mounts,existing volumes and pre-existing
containers are preserved; mount-array ordering was canonicalized by destination.
No unrelated container was owned,restored or stopped.

Original working HEAD remains `2e7999ea436d49449652e6c52e9066ef2e514419`;only
publication tracking refs advance after a normal descendant commit is verified.

## Reproduction and next step

New code:`tools/recover_buildplan_plugin.py`. Tests:
`tests/test_buildplan_plugin_recovery.py`. This report and
`examples/phase5_2_2_e_0_5/` contain metadata only;no binaries,caches,raw logs or
credentials are published. No existing code,configuration or prior report changed.

Read-only audit (no network,Maven or ledger mutation):

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
PYTHONDONTWRITEBYTECODE=1 timeout 90s taskset -c 0 \
  prlimit --as=1073741824 --cpu=60 --fsize=16777216 -- \
  .venv-forecast/bin/python -m tools.recover_buildplan_plugin --audit-only \
  --output /home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_5/2026-10-18/recovery-1
```

Relevant test command:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=120 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_buildplan_plugin_recovery.py tests/test_build_compile_e04.py \
  tests/test_compile_test_dependency_recovery.py tests/test_build_compile_e02.py \
  tests/test_build_sandbox.py tests/test_phase5_2_2_e_0_compilation.py \
  tests/test_phase5_2_2_d_3_inspection.py tests/test_phase5_2_2_d_2_recovery.py \
  tests/test_phase5_2_2_d_1_continuation.py tests/test_phase5_2_2_d_recovery.py \
  tests/test_phase5_2_2_b_probes.py tests/test_phase5_2_2_a_review.py \
  tests/test_production_scope_readiness.py tests/test_multilanguage_preflight.py \
  tests/test_multilanguage_foundation.py
```

[E.0.6 handoff](examples/phase5_2_2_e_0_5/E_0_6_HANDOFF.md) records the682-file
seed and unchanged original command/source/runtime/resource rules for a separately
authorized single T0 attempt. It warns that six known descriptor gaps remain.
To avoid another predictable descriptor stop,the smallest useful next recovery is
metadata-only POM/JAR/parent-import inspection for those exact plan candidates,
with a new explicit bounded authorization—not their complete future runtime
universes. Neither that recovery nor compilation started here.

**STOP after E.0.5 verification and GitHub publication. No Maven,compile retry,
other revision,Sonar/server/scan,model,debt measurement,data admission/rebuild or
Phase5.3 ran. SonarSource licensing and derived-dataset rights gates remain open
and unchanged.**
