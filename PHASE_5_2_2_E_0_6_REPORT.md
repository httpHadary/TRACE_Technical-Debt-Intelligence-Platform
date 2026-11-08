# Phase 5.2.2-E.0.6 — Single T0 offline Java compilation

Date: 2026-10-18, Africa/Cairo. Starting main: `351852ac458633e9954a753ef6932659a628f319`.

**COMPILE_PASS. Exactly one genuine offline Maven compile attempt ran.**
The original lifecycle completed, including `check-buildplan`, and Maven/Docker
both exited0. Compiler3.13.0 compiled26 production Java sources using release8.
All37 produced class files pass structure/identity/major52 checks: **25 expected
top-level classes,11 nested classes and1 package-info class**. Two nonclass
LICENSE/NOTICE resources are recorded separately. No top-level class is missing.

No dependency was downloaded, no version/POM/profile/check was changed, and no
retry or other revision was compiled. No test,package,install,deploy,site,scan,
model or data-admission work ran. The task-owned container was removed after
complete bounded capture. Unresolved analyzer licensing and dataset rights remain
unchanged. This proves this exact T0 compile context, not full later-lifecycle or
multi-revision readiness.

## Frozen inputs and runtime

| Identity | Verified value |
| --- | --- |
| Commons CLI T0 commit | `4ff0d4adbc2161677e71050ba23c152831f6ad83` |
| Tree | `ac7521be84b2820a83f7b960d329a15521408214` |
| Historical POM SHA256 | `b75fb9813e3c06121caa7d84c31a471b646465966079cf10ec4c7a2e4aba55f2` |
| D.3 effective POM SHA256 | `bf4a9243703b32ca363232c2759c8bab4f009ac544897dafab87f4b22f42e449` |
| E.0.5.1 manifest SHA256 | `ed23ccde95a89081c1c19f3de39ee9199a50b15eacf0647e316f62acf1f97b84` |
| Canonical697-artifact cache SHA256 | `a84a27a2f5f9d9bed4af8dbf56a04a91b2910580f66c67952362d215f62d0b22` |
| Pinned Maven/JDK image | `sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82` |
| Executed adapter SHA256 | `39be69b9721050b9cb9d021a4e24390d399dfa03f5a5318e411a08b15bc71d1c` |
| Executed wrapper SHA256 | `dbd760f0962b5be344cd1fad6b66041de70bb80e3a6d66610a290dd4833e9903` |

All117 tracked source files were matched against frozen Git blobs, modes and
SHA256 values. Independent copies retained source/POM bytes and executable modes;
runtime modes before/after match the original Git population. No `.git` metadata
was present or fabricated. Commons Parent76, Maven3.9.11, Temurin17.0.17+10,
release8, `maven.test.skip=true` and no explicitly selected profiles were preserved.
D.3's settings/model/profile evidence remained unchanged. No additional Help or
version-only JVM goal ran.

All697 exact artifact paths, counts, GAVs, recorded Central checksum provenance,
SHA256 hashes, POM XML and JAR ZIP/CRC checks were independently reverified. The
20-plugin parent/import metadata audit had no missing metadata. No unregistered
artifact was admitted. New copies use independent inodes; no old cache or user
Maven repository was mounted writable or altered.

Four current stopped-container binary hashes (Maven launcher, Maven core, Java
executable and Java release file) matched TaskB's pinned runtime manifest before
startup. This verifies exact binaries without a second container or probe JVM.
See [registration](examples/phase5_2_2_e_0_6/compile_registration.json),
[input verification](examples/phase5_2_2_e_0_6/input_verification.json) and
[runtime inputs](examples/phase5_2_2_e_0_6/runtime_inputs.json).

## One versioned attempt

`tools/build_compile_e06.py` reuses E.0.4's proven setup/capture recipe and E.0.2's
command/parser libraries, with a new E.0.6 owner, `--e06-offline-compile` mode,
697-artifact registration and exclusive claim. It never calls an archived runner
entry point or reuses E.0.2/E.0.4 claims. Archived adapters, early-failure receipts
and the E.0.1 smoke sentinel are unchanged. The executed adapter/wrapper hashes
still match the published code and registration.

The only recipe extension collects source modes before/after compilation. It does
not change Maven configuration or historical inputs. UID/GID1000-owned tmpfs,
copy/hash/population checks, the early EXIT trap, separate setup/Maven streams,
race-tolerant capture, bounded archives, terminal logs/events and owned cleanup
remain the established implementation. All16 recorded setup/lifecycle stages
passed. Pre-attempt policy/integrity/failure tests passed before any container was
created. A new registration-digest typo was caught and corrected by those tests;
it consumed no real build attempt.

The exact Maven command ran once:

```bash
/usr/share/maven/bin/mvn \
  --offline --batch-mode --no-transfer-progress --errors \
  -s /inspection/settings.xml -gs /inspection/settings.xml \
  -Dmaven.repo.local=/runtime-repository -Duser.home=/tmp \
  -Dmaven.test.skip=true -Dmaven.compiler.release=8 compile
```

`MAVEN_OPTS=-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp`.
HOME=/tmp, MAVEN_CONFIG=/tmp/.m2, MAVEN_SKIP_RC=true; MAVEN_ARGS,
JAVA_TOOL_OPTIONS and JDK_JAVA_OPTIONS were empty. The source export and registered
build context were preserved. No skip property, profile override or build-plan
`tasks` override was added.

## Actual lifecycle and warnings

| Order | Actual goal/execution | Observed result |
| ---: | --- | --- |
|1|Enforcer3.5.0: enforce-maven-version|RequireMavenVersion passed|
|2|Enforcer3.5.0: enforce-java-version|RequireJavaVersion passed|
|3|RAT0.16.1: rat-check|0 unapproved/unknown;106 approved license headers|
|4|Artifact3.5.1: check-buildplan|Passed;20 plugin entries reported no known issue|
|5|Build-helper3.6.0: parse-version|Completed|
|6|Antrun3.1.0: javadoc.resources|Executed tasks;copied2 files|
|7|Remote-resources3.2.0: process-resource-bundles|Invoked;reported internal skip|
|8|Buildnumber3.2.1: default/create|Completed using original SCM fallback|
|9|Resources3.3.1: default-resources|Copied2 resources into target/classes/META-INF|
|10|Compiler3.13.0: default-compile|Compiled26 source files with javac [debug release8]|

Remote-resources' own `Skipping remote resources execution` message is retained.
The original bound goal ran; the agent did not add a skip override. Similarly,
planned Surefire/Felix/CycloneDX/SPDX/Moditect/install/deploy entries in
check-buildplan are descriptor checks, not actual executions. The complete actual
10-goal sequence matches the frozen original compile lifecycle; no extra goal,
test compilation or test-class directory was observed.

Buildnumber tried the original Git commands in the detached export. The original
effective POM already specifies `revisionOnScmFailure=??????`, `doCheck=false` and
`doUpdate=false`. It tolerated unavailable SCM revision/branch information and
stored `??????` and `UNKNOWN_BRANCH`. This is **nonfatal fallback behavior**, not
successful SCM lineage extraction and not BLOCKED_SCM_CONTEXT. Scientific source
identity remains the independently verified commit/tree, never those placeholders.
No fake Git repository or metadata workaround was introduced.

The same three nonfatal RAT POM warnings remain: Log4j1.2.12, Logkit1.0.1 and
Avalon Framework4.1.3. No missing runtime JAR or fatal resolution failure occurred.
The final dependency receipt attributes these warnings to the actual RAT banner,
without assuming a required JAR. The inherited generic private analyzer labels
such warnings too broadly as PROJECT_DEPENDENCY; its original result is preserved,
and a separate read-only auditor provides the correct plugin-context attribution.
This reporting correction did not modify or rerun the build.

Jansi still reported that `/tmp` is noexec and its native library could not load.
It was nonfatal; no mount, native-library or isolation setting was weakened. RAT's
license-header result does not clear human legal/policy or SonarSource rights gates.

## Output and evidence verification

[Class manifest](examples/phase5_2_2_e_0_6/class_output_manifest.json) records each
class hash, internal identity, SourceFile link, structure and Java8 major52.
All25 top-level source identities match;11 nested classes are linked to their
owning source and package-info is separate. The actual compiler input list matches
all26 registered Java sources; the37 compiler-created entries match the37 parsed
class outputs. LICENSE.txt and NOTICE.txt are nonclass resources, not extra classes.
The class parser is structural verification, not a separately executed JVM verifier.

The compiler goal and javac/release8 log are observed. **Its exact runtime classpath
and compiler argument vector were not printed by the registered command and are
UNAVAILABLE.** D.3 declares five project dependencies, all test-scoped, with no
compile/provided/system project dependency declaration. Those declarations are
not substituted for an observed compiler classpath. No debug flag, extra Maven
goal or second process was used to obtain additional diagnostics.

Full private Maven streams are complete: stdout5,164 bytes and stderr569 bytes.
Setup streams are separate. Docker's terminal excerpts, exact stage/category,
EXIT-trap0, Maven0, Docker0, cgroup metrics and post-run inventories were captured;
no measurement required for the compile acceptance checks is missing. The command
did not print the classpath; that separate observability limitation is explicit.
Original raw logs/classes remain private; only selected sanitized lifecycle lines
and hashes are published. All697 cache bytes and117 tracked source bytes/modes
remain unchanged. Maven added zero repository metadata files in this attempt.

A separate read-only `tools/verify_compile_e06.py` validates the exact allowed goal
sequence, warning context, class/input/output completeness, modes, immutable
wrapper, one start, cleanup and exits. It executes no Docker/Maven/Java command and
does not rewrite the original result. See
[output verification](examples/phase5_2_2_e_0_6/output_verification.json),
[execution receipt](examples/phase5_2_2_e_0_6/build_execution_evidence.json),
[capture inventory](examples/phase5_2_2_e_0_6/capture_inventory.json) and
[dependency result](examples/phase5_2_2_e_0_6/runtime_dependency_resolution.json).

## Actual resources and isolation

The attempt ran from **2026-10-18 20:00:30 to 20:00:46 Africa/Cairo**.
Raw daemon timestamps retain their explicit UTC suffix in the machine evidence.

| Resource | Measured/registered result |
| --- | ---: |
| Available host RAM immediately before start |6,787,158,016 bytes (~6.32GiB)|
| Minimum sampled host available RAM |6,481,297,408 bytes (~6.04GiB)|
| Required admission/headroom |4GiB available /2GiB host headroom|
| Free disk immediately before start |16,152,514,560 bytes|
| Container memory cap /heap maximum |2GiB /768MiB|
| Cgroup peak memory |353,783,808 bytes (~337.39MiB)|
| OOM /OOM-kill /memory-max events |0 /0 /0|
| CPU usage |14.207514 CPU-seconds|
| Maven wrapper wall time |13.52 seconds (limit240s)|
| Maven-reported internal total |10.471 seconds|
| Host container-monitor duration |15.42 seconds|
| Candidate artifact payload |74,846,407 bytes|
| Rounded files +directories +16MiB reserve |96,309,248 bytes (~91.85MiB)|
| Repository tmpfs cap |128MiB, unchanged|
| Observed runtime repository payload |74,846,407 bytes|
| New containers /Maven launches /retries /downloads |1 /1 /0 /0|

The existing pinned local image was used with `--pull never`. Runtime controls
remained1CPU,64PIDs,no additional swap,UID/GID1000,dropped capabilities,
no-new-privileges,read-only root,network none,owned noexec/nosuid/nodev tmpfs,
read-only inputs/inspection only,no socket/credentials/user-cache mount.
Source/repository/tmp caps128MiB each,output32MiB,shared memory8MiB,
file cap8MiB,archive cap32MiB,nofile1024,Maven240s,monitor265s and outer330s were
preserved. Admission found no concurrent prohibited workload or running container;
no unrelated service was stopped. Actual cgroup limits,CPU/throttle counters,
memory events and Docker OOM state are in
[resource evidence](examples/phase5_2_2_e_0_6/resource_evidence.json) and
[sandbox policy](examples/phase5_2_2_e_0_6/sandbox_policy.json).
Controller peak RSS was not separately measured and is not inferred from the
container peak. Its address-space ceiling was1GiB on CPU0.

## Tests and preservation

**555 passed in each checkout**, zero failures/errors/skips:18.23s in the canonical
publication checkout and18.29s in the original project. This includes all507 prior
relevant tests plus36 E.0.6 adapter tests and12 read-only audit tests. Pre-attempt
policy tests passed123 checks before execution; later tests only analyze policy
or synthetic/read-only evidence and never launch a second build. The verification
receipt lists the full18-file regression suite and exact run hashes/timings.

Preservation PASS covers all18 pinned source commit/tree/full inventories across
three repositories, all117 T0 blob identities/modes, original POM and D.3 evidence,
all previous private task files/caches/claims, request ledgers
2000/400/52/112/56/12/52,56 frozen bundles/322 artifacts,two Phase5.1 bundles,
SQLite and model hashes,6,262 user-cache entries plus75 rehashed reference artifacts,
old SonarQube container/volumes and unrelated working-tree/container state. Four
preexisting untracked remediation files remain untouched. No independent shared
Docker inventory change was observed. The owned E.0.6 container was removed;
there was no other task container or retry.

See [regression receipt](examples/phase5_2_2_e_0_6/verification.json),
[preservation](examples/phase5_2_2_e_0_6/preservation.json) and
[all source states](examples/phase5_2_2_e_0_6/all_source_states_preservation.json).

## Files, reproduction and stop

Only new files are added: the versioned adapter, read-only auditor, their two test
files, this report and `examples/phase5_2_2_e_0_6/` metadata/handoff. No archived
adapter/report, historical POM, old cache, benchmark or dataset was rewritten.
The original project HEAD stays unchanged; new files are mirrored there and
published via the canonical checkout as a normal descendant main commit.

Private inputs/capture remain under:
`/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_6/2026-10-18/attempt-1/`.
They contain third-party binaries/classes/raw runtime data and are excluded from
Git. The attempt claim is consumed; **do not repeat the compile command**.

Read-only verification from the project directory:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -c 'import json; from tools.verify_compile_e06 import audit; print(json.dumps(audit("/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_6/2026-10-18/attempt-1")["checks"], indent=2))'
```

Focused tests without a real Maven/Docker launch:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_build_compile_e06.py tests/test_verify_compile_e06.py
```

**STOP: E.0.6 is complete.** No correction/retry is needed for this exact successful
compile. Other revisions need separate review/authorization; do not infer their
readiness or later Maven lifecycle readiness from this result. No dependency
acquisition,SonarQube server/scan,forecast,technical-debt measurement,dataset
admission or Phase5.3 action follows automatically.

[Next-step handoff](examples/phase5_2_2_e_0_6/NEXT_STEP_HANDOFF.md) preserves the
remaining scope and rights gates. SonarSource/analyzer licensing and derived-data
publication rights are still unresolved until independently cleared.
