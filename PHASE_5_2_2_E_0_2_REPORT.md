# Phase 5.2.2-E.0.2 — First actual T0 Maven compilation attempt

Date: **2026-10-18**, Africa/Cairo. Starting main: `67f2d304e2739e281edbc88e59fcc5840c4f1dea`.

**BLOCKED_DEPENDENCY.** Exactly one genuine offline Maven invocation of the original
`compile` lifecycle ran for T0. Setup passed. Maven then failed in project dependency
resolution because five test-scoped roots lack their POMs and JARs in the registered
cache. Maven exit1 and Docker exit1 agree; complete bounded setup/Maven logs,
resource observations and cleanup evidence were retained. **The compiler and all
lifecycle plugin goals were not reached. Java compilation readiness remains UNKNOWN.**

No recovery, network enablement, dependency substitution, source/POM edit or retry
was attempted. No other revision, test goal, package/install/deploy/site, Sonar,
scan, model or dataset-admission operation ran. E.0 and E.0.1 evidence/claims remain
unchanged; their historical BLOCKED and SETUP_AND_CAPTURE_PASS results stand.

## Immutable prerequisites and separate adapter

T0 commit: `4ff0d4adbc2161677e71050ba23c152831f6ad83`. Tree: `ac7521be84b2820a83f7b960d329a15521408214`.
Historical POM SHA256: `b75fb9813e3c06121caa7d84c31a471b646465966079cf10ec4c7a2e4aba55f2`; Commons Parent76.
D.3 effective POM SHA256:
`bf4a9243703b32ca363232c2759c8bab4f009ac544897dafab87f4b22f42e449`.
Exact active-profile evidence matched D.3. No profile was explicitly selected.

All117 source-file Git identities, complete tree identity, POM and byte hashes
were rechecked. All653 artifact coordinates/provenance, checksums, POM structure
and JAR CRCs were independently verified and copied into a new task directory.
The source population includes26 production Java files. No Git metadata, marker
file or fake source was introduced. All frozen tracked bytes remain exact after
Maven; the complete post-build source tree still contains only the117 seed files.

Existing pinned image:
`sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82`. Maven3.9.11 and Temurin17.0.17+10 launcher/core/executable/release hashes
matched TaskB before startup; there was no image pull, installation or version goal.
D.3 settings were copied exactly, with no user Maven cache or host settings mounted.

`tools/build_compile_e02.py` is the explicit, separately tested `--e02-offline-compile`
adapter. It never calls the archived E.0 runner and does not repurpose
`--no-maven-smoke`. It derives a new wrapper from the proven setup prefix, with a
2GiB runtime guard and an allowlisted compile tail. The original smoke shell and
its injected exit73 sentinel remain byte-identical. The generated wrapper hash and
setup-template/settings hashes are in
[compile_registration.json](examples/phase5_2_2_e_0_2/compile_registration.json).

Shared capture code in `tools/build_sandbox.py` received small backward-compatible
optional parameters for the owner label, collector and explicit archive allowlist.
Default smoke behavior is unchanged; generic path safety now also applies
independently of the allowlist. Original reports/receipts/private artifacts were
not edited. The helper's before/after hashes are recorded as the single intentional
pre-existing source change, not disguised as frozen-source preservation.

## Exact execution

```bash
/usr/share/maven/bin/mvn --offline --batch-mode --no-transfer-progress --errors \
  -s /inspection/settings.xml -gs /inspection/settings.xml \
  -Dmaven.repo.local=/runtime-repository -Duser.home=/tmp \
  -Dmaven.test.skip=true -Dmaven.compiler.release=8 compile
```

```text
MAVEN_OPTS=-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp
HOME=/tmp
MAVEN_CONFIG=/tmp/.m2
MAVEN_SKIP_RC=true
MAVEN_ARGS=
JAVA_TOOL_OPTIONS=
JDK_JAVA_OPTIONS=
```

The wrapper invoked this command once under GNU timeout240s (TERM, then KILL after
5s if needed). One fresh exclusive claim permits one container only. The controller
re-admitted resources immediately before startup, retained independent setup and
Maven streams, post-build source/cache inventories, terminal state, filtered daemon
events and EXIT-trap cgroup statistics, then removed only its owned container.

Actual output begins with Maven project scanning and `Building Apache Commons CLI
1.9.1-SNAPSHOT`. This confirms actual Maven activity; it is stronger evidence than
the wrapper's `LAUNCH_REQUESTED` marker alone. The first real failure is:

```text
[ERROR] Failed to execute goal on project commons-cli: Could not resolve dependencies for project commons-cli:commons-cli:jar:1.9.1-SNAPSHOT
```

The stack includes `LifecycleDependencyResolver` and
`MojoExecutor.ensureDependenciesAreResolved`. **No plugin execution banner appears**;
actual plugin order is an empty list. All original bindings remained present, but
enforcer, RAT, remote resources, artifact/buildplan, build-helper, buildnumber,
antrun, resources and compiler bodies did not execute. They were not skipped by
configuration; resolution failed before goal execution. SCM/buildnumber behavior
and runtime plugin classpaths remain NOT_REACHED/unproven.

The cached enforcer3.5.0 `enforce` descriptor declares `requiresDependencyCollection=test`.
That is descriptor evidence, not a successful enforcer run. Under this unchanged
lifecycle, the observed Maven resolution still required these test-scoped roots
with `maven.test.skip=true`. Do not remove the declarations or weaken checks merely
to progress. This observation does not assert that every possible `compile` project
always resolves all test dependencies.

## Exact missing frontier

Five JAR resolution errors and five missing-POM warnings map to these physically
absent seed-cache files; their exact versions come from the actual logs:

| Exact root | Type | Missing registered-cache path |
| --- | --- | --- |
| `org.junit.jupiter:junit-jupiter-api:5.11.1` | `jar` | `org/junit/jupiter/junit-jupiter-api/5.11.1/junit-jupiter-api-5.11.1.jar` |
| `org.junit.jupiter:junit-jupiter-engine:5.11.1` | `jar` | `org/junit/jupiter/junit-jupiter-engine/5.11.1/junit-jupiter-engine-5.11.1.jar` |
| `org.junit.jupiter:junit-jupiter-params:5.11.1` | `jar` | `org/junit/jupiter/junit-jupiter-params/5.11.1/junit-jupiter-params-5.11.1.jar` |
| `commons-io:commons-io:2.17.0` | `jar` | `commons-io/commons-io/2.17.0/commons-io-2.17.0.jar` |
| `org.mockito:mockito-core:4.11.0` | `jar` | `org/mockito/mockito-core/4.11.0/mockito-core-4.11.0.jar` |
| `org.junit.jupiter:junit-jupiter-api:5.11.1` | `pom` | `org/junit/jupiter/junit-jupiter-api/5.11.1/junit-jupiter-api-5.11.1.pom` |
| `org.junit.jupiter:junit-jupiter-engine:5.11.1` | `pom` | `org/junit/jupiter/junit-jupiter-engine/5.11.1/junit-jupiter-engine-5.11.1.pom` |
| `org.junit.jupiter:junit-jupiter-params:5.11.1` | `pom` | `org/junit/jupiter/junit-jupiter-params/5.11.1/junit-jupiter-params-5.11.1.pom` |
| `commons-io:commons-io:2.17.0` | `pom` | `commons-io/commons-io/2.17.0/commons-io-2.17.0.pom` |
| `org.mockito:mockito-core:4.11.0` | `pom` | `org/mockito/mockito-core/4.11.0/mockito-core-4.11.0.pom` |

No remote availability claim or checksum is invented for missing bytes.
`failure_manifest.json` includes each line of supporting evidence and
`seed_bytes_present=false`. The Maven JAR exceptions and POM warnings are kept
separate in counts:5JARs +5POMs. No new acquisition occurred. Required parents,
BOMs and transitive dependency identities cannot be completed until these exact
POMs are available; no closure or offline-build PASS is claimed.

The measured blocker is dependency resolution, **not** absent `.git`, an enforcer
rejection, setup ownership, Jansi, timeout or OOM. No SCM command was reached and no
synthetic Git context was added. The known Jansi/noexec native-console warning is
retained unchanged in stderr; Maven reached the project resolution failure despite
that warning. No isolation workaround was used to suppress it.

## Evidence completeness and outputs

| Evidence | Actual |
| --- | --- |
| Container startups / Maven invocations / retries |1 /1 /0|
| Setup |Passed; exact UID/GID1000 ownership and117/653 pre-launch hashes|
| Maven / Docker terminal exit |1 /1|
| First failed stage |Project dependency resolution|
| Actual plugin goal executions |0 observed banners; downstream goals NOT_REACHED|
| Compiler / tests / unapproved phases |Not reached /not run /none observed|
| Class files produced |0, verified from complete post-build source inventory|
| Expected named production top-level identities |25, plus separate `package-info.java`|
| Source/POM bytes after attempt |All117 match frozen hashes|
| Seed artifact bytes after attempt |All653 match; no missing/changed seed artifact|
| Writable-cache metadata additions |0 observed; full653-file inventory unchanged|
| Complete Maven stdout /stderr |10,901 /565 bytes; no truncation|
| Capture and cleanup errors |None|
| Task-owned container remaining |0|

Full small sanitized setup/Maven streams are published as text. Raw private
inspections, build seeds and binary artifacts stay outside Git. The8MiB per-file
cap and32MiB archive bound remained enforced. Code marks a log at its cap as
potentially truncated; this attempt's streams were far below the cap. Docker logs
also retain clearly labelled last-65,536-byte diagnostic excerpts, which are not
misrepresented as complete replacement logs.

[class_output_manifest.json](examples/phase5_2_2_e_0_2/class_output_manifest.json)
records no output classes and no completeness PASS. A structural Java8 parser and
identity-based completeness verifier were implemented/tested using explicitly
synthetic unit fixtures; **no historical class structure or bytecode-major52 PASS
is asserted because no actual class was generated**. The verifier checks binary
structure, EOF, constant references, major52, internal names/paths, SourceFile,
expected top-level identities and separate nested/package-info cases. It is not a
full JVM instruction verifier. Compiler-classpath evidence is NOT_REACHED.

The original controller receipt's initial status was provisional and remains
private/unchanged. Its SHA256 is bound in publication; the published execution
status is the evidence classifier's BLOCKED_DEPENDENCY. No prior phase or raw
historical result was retroactively relabelled.

## Actual resource observations

| Evidence | Actual |
| --- | ---: |
| Available RAM immediately before startup |6,646,808,576bytes (~6.19GiB)|
| Minimum sampled host available RAM |6,485,413,888bytes (~6.04GiB)|
| Required admission |4GiB available:2GiB container +2GiB headroom|
| Free disk before startup |21,152,604,160bytes|
| Container memory /extra swap |2GiB /0|
| JVM heap /CPU /PIDs |768MiB /1 /64|
| EXIT-trap cgroup memory.peak |199,073,792bytes (~189.85MiB)|
| EXIT-trap CPU usage |3,289,657µs|
| OOM /OOM-kill counters |0 /0|
| Maven command wall time |2.75s|
| Host monitoring/capture duration |4.50s|
| Docker start-to-finish |~4.35s|

The trap snapshot follows post-build diagnostics and precedes later export/cleanup;
no unobserved full-lifetime peak is invented. Docker OOMKilled is false. No other
container or prohibited workload was running at admission. The actual2GiB memory,
zero extra swap, one-CPU quota and64PIDs are recorded from the cgroup. The original
unprivileged1000:1000/no capabilities/no-new-privileges/read-only image/no network
and read-only seed mounts were retained. No credentials/socket/user cache was
mounted. Owned source/repository/tmp each retained128MiB caps; output32MiB and
shared memory8MiB. File cap8MiB, descriptor cap1024; monitor threshold265s and hard
outer controller timeout330s. No resource limit was weakened or service stopped.

## Regression and preservation

**389 tests passed in each checkout**, including21 new E.0.2 cases, zero failures,
errors or skips. Central: 20.466s; working project:
15.812s. New checks cover the exact command, compile-mode isolation
from smoke,2GiB/768MiB policy,4GiB admission, exclusive claims, owner labels, archive
extension safety, actual missing roots/no false compiler success, and Java8 class
structure/identity/completeness. Tests themselves do not run Docker/Maven. All prior
E.0.1/E.0/D.3/D.2/D.1/D/B/A/scope/foundation tests passed unchanged.

Preservation PASS:all frozen research caches/claims and56 bundles/322 experimental
artifacts,2 Phase5.1 bundles, source SQLite and model checkpoint;1378/615/630 files
in D/D.1/D.2 caches,842 D.3 private files,790 E.0 private files and818 E.0.1 private
files remain byte-identical. Request ledgers stay2000/400/52/112. The fresh6262-entry
user-cache baseline matches (75 reference artifact hashes also checked), with no
user-cache write mount. E.0 remains BLOCKED and E.0.1 remains SETUP_AND_CAPTURE_PASS.
Old Sonar state/mounts and unrelated containers/volumes remain unchanged.

Of489 central and400 working pre-existing files, only the explicitly approved
`tools/build_sandbox.py` compatibility extension changed; all other488/399 files
and4 unrelated unfinished files are preserved. The helper transition hashes are
published. Original working `main` remains
`2e7999ea436d49449652e6c52e9066ef2e514419`; only publication tracking refs advance.

Files:the modified shared capture helper, new `tools/build_compile_e02.py`,
`tests/test_build_compile_e02.py`, this report and the metadata/text evidence bundle.
Private task root:

```text
/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_2/2026-10-18/
```

Read-only classification reproduction, with no Maven:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
PYTHONDONTWRITEBYTECODE=1 timeout 60s taskset -c 0 \
  prlimit --as=1073741824 --cpu=45 --fsize=33554432 -- \
  .venv-forecast/bin/python - <<'PY_READONLY'
from pathlib import Path
from tools.build_compile_e02 import analyze
r = Path('/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_2/2026-10-18')
print(analyze(r)['status'])
PY_READONLY
```

Relevant regression suite, under the same bounded pytest invocation as E.0.1:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s taskset -c 0 prlimit --as=1073741824 --cpu=120 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_build_compile_e02.py tests/test_build_sandbox.py \
  tests/test_phase5_2_2_e_0_compilation.py tests/test_phase5_2_2_d_3_inspection.py \
  tests/test_phase5_2_2_d_2_recovery.py tests/test_phase5_2_2_d_1_continuation.py \
  tests/test_phase5_2_2_d_recovery.py tests/test_phase5_2_2_b_probes.py \
  tests/test_phase5_2_2_a_review.py tests/test_production_scope_readiness.py \
  tests/test_multilanguage_preflight.py tests/test_multilanguage_foundation.py
```

## Smallest next action

[E.0.3 recovery handoff](examples/phase5_2_2_e_0_2/E_0_3_NEXT_ACTION.md) proposes a
separately authorized fresh, bounded recovery of the exact ten missing paths and
only their authoritative required parent/BOM/runtime closure. Check approved local
sources first; do not assume an unverified local copy is admissible. Preserve
versions and ledgers; acquire from the allowlisted endpoint only within new explicit
limits. No Maven during acquisition. A later new one-attempt T0 compile requires
separate authorization. Further plugin/SCM blockers remain possible.

**STOP after E.0.2 verification and normal-descendant GitHub publication. No recovery,
retry, other revision, Sonar/scan, model, dataset admission or Phase5.3 started.**
Analyzer licensing and dataset-rights gates remain unresolved and unchanged.
