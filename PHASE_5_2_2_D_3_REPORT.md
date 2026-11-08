# Phase 5.2.2-D.3 — T0 offline Maven effective-model verification

Date: **2026-10-16**. Starting `main`: `fbfd7bb0fde4a367e97d4e118b8cf2a26dd93079`.

**MODEL_VERIFIED.** Maven3.9.11 successfully ran both explicitly approved
Help Plugin3.5.1 goals offline for the single pinned Apache Commons CLI T0
revision. The effective project model and all25 project-chain profile decisions
are now observed. **Offline Java build readiness remains UNKNOWN**: no project
lifecycle phase, compilation, enforcer execution or final plugin-runtime-classpath
resolution was attempted. Maven's generic `BUILD SUCCESS` means the model goal
succeeded; it is not Java-build evidence.

## Immutable source, runtime and cache

- Commit: `4ff0d4adbc2161677e71050ba23c152831f6ad83`.
- Full tree: `ac7521be84b2820a83f7b960d329a15521408214`.
- Historical POM SHA256: `b75fb9813e3c06121caa7d84c31a471b646465966079cf10ec4c7a2e4aba55f2`; Commons Parent76, Apache Parent33.
- All117 registered tracked blobs were reconstructed individually and Git-blob/SHA256
  checked, including all26 `src/main` production files and every tracked file outside
  production scope. No export-ignore filtering, synthetic markers, Git checkout,
  POM edits or original repository changes occurred.
- Build image: `sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82`.
  The Maven launcher/core JAR and Temurin Java executable/release were independently
  copied from each stopped container and matched TaskB's published SHA256 before
  startup. Maven3.9.11 / Temurin17.0.17+10 identities remain pinned.
- Registered properties: `maven.test.skip=true`, `maven.compiler.release=8`,
  `user.home=/tmp`, no explicitly selected profiles; no user settings/cache mounted.
- All624 D.2 artifacts matched the published manifest, SHA256, repository checksum,
  POM coordinates or JAR CRC before independent copying. No hard links were used.
  Runtime mounts were read-only; all653 final runtime artifact hashes were verified
  again after execution. TaskD/D.1/D.2 ledgers remain **2000/400/52** unchanged.

The exported source tree has no `.git`, untracked files or parent-relative POM.
It includes the actual historical profile marker files. `site-content` is absent;
`src/site/resources/profile.jacoco` exists. The temporary home has no toolchains,
settings or credentials. These conditions are explicit in this model observation;
a future writable compilation sandbox must preserve/re-register its own exact
context and cannot infer full SCM/build behavior from this read-only export.

## Helper tooling, acquisition and provenance

The D.2 inventory had no Help Plugin. A separately identified helper batch acquired
only `org.apache.maven.plugins:maven-help-plugin:3.5.1`, its descriptor's16 exact
runtime dependency identities, and required parent/import metadata. Already verified
historical artifacts were reused without redownloading. No unrestricted recursive
project/test/optional dependency acquisition occurred.

| Helper batch evidence | Actual |
| --- | ---: |
| New artifacts |29|
| HTTP requests, including checksum probes/retries |112 /150|
| Response payload bytes read |2,508,354 /67,108,864|
| Acquisition wall time |42.06s /600s|
| Acquisition peak RSS |33,220 KiB|
| Enforced acquisition address space |1,073,741,824 bytes|
| CPU / workers |CPU0 /one sequential worker|
| New helper plus historical runtime cache |653 artifacts|

The batch uses only `https://repo.maven.apache.org/maven2/`, rejects redirects
and inherited proxies, verifies same-origin SHA512/SHA256/SHA1 sidecars plus local
SHA256, validates POM coordinates and JAR ZIP/CRC, and rejects ranges/SNAPSHOT
artifact acquisition. Counts include failed checksum requests; byte counts exclude
HTTP headers/TLS and unread error bodies. HTTPS plus repository-side checksums do
not constitute independent publisher-signature verification. The150-request and
64MiB caps were not reset. No Maven or downloaded artifact execution occurred during
acquisition; no further acquisition occurred after Maven startup.

The plugin descriptor requires Maven3.6.3+ and Java8+, compatible with the pinned
runtime. Both requested mojos have no forked phase/goal and request no project
dependency resolution. This was checked from the exact verified3.5.1 JAR descriptor,
not assumed from current3.5.2 documentation. Current official requirements history
also includes3.5.1: [Apache Help Plugin requirements](https://maven.apache.org/plugins/maven-help-plugin/plugin-info.html).
Goal purpose: [active-profiles](https://maven.apache.org/plugins/maven-help-plugin/active-profiles-mojo.html),
[effective-pom](https://maven.apache.org/plugins/maven-help-plugin/effective-pom-mojo.html).

The [helper manifest](examples/phase5_2_2_d_3/helper_dependency_manifest.json) is
separate from historical project manifests. POM/JAR bytes remain outside Git.

## Actual offline execution and isolation

| Approved goal | Exit | Goal wall time | Cgroup peak bytes | Minimum host available RAM |
| --- | ---: | ---: | ---: | ---: |
| active-profiles | 0 | 2.52s | 85,737,472 | 9.09 GiB |
| effective-pom | 0 | 2.91s | 90,804,224 | 9.11 GiB |

Both goals used one sequential Maven JVM with `-Xmx512m`, one active processor,
a1.5GiB container cap and memory+swap cap of the same size (cgroup swap allowance0).
Host headroom stayed above2GiB. Cgroup memory-event counters show no OOM, OOM kill
or limit hit. Each goal was bounded to180seconds; the host monitor had a190second
timeout and killed/removed only its task-owned container on failure.

Other enforced controls: network `none`, image pulling disabled, user1000:1000,
all capabilities dropped, no-new-privileges, read-only root/source/runtime cache,
no Docker socket/host credentials,64PIDs,8MiB per-file output cap,1024file descriptors,
128MiB noexec `/tmp`,32MiB noexec output tmpfs,8MiB shared memory and bounded logs.
The runtime cache plus helper and evidence occupied about70MiB at verification;
all writable container filesystems were size-capped. No existing container/volume
was reused, stopped or modified, and no Sonar process ran concurrently.

Two initial **evidence-capture attempts** did not retain tmpfs outputs: the stopped
container export was empty, and then the live Docker archive API also omitted this
tmpfs. They are not accepted as model proof. The runner was corrected to stream a
bounded tar from the live container namespace before acknowledging collection;
it validates member names/types/sizes before extraction. There were four task
container startups total: three attempts of the same approved `active-profiles`
goal, then one `effective-pom` goal, never overlapping. No other revision or goal
was executed. All four containers were disposed. The successful captures provide
actual goal output, cgroup readings and exit codes. These retries did not alter
Maven properties, sources, profiles, dependencies, network or resource limits.

The known Jansi native-console/noexec warning is retained in both stderr logs.
It did not fail either model goal; no writable executable temporary filesystem or
console-library change was introduced to suppress it.

## Active and inactive profiles

Maven reported **8 active profiles**:

- `jdk9+` — `org.apache:apache:33`
- `parse-target-version` — `org.apache.commons:commons-parent:76`
- `jacoco` — `org.apache.commons:commons-parent:76`
- `svn-buildnumber` — `org.apache.commons:commons-parent:76`
- `java-9-up` — `org.apache.commons:commons-parent:76`
- `java-11-up` — `org.apache.commons:commons-parent:76`
- `java-17-up` — `org.apache.commons:commons-parent:76`
- `setup-checkout` — `commons-cli:commons-cli:1.9.1-SNAPSHOT`

The remaining17 profiles in the three project-inheritance POMs were not active in
this exact context; their declarations remain conditional for other contexts.
All25 decisions agree with the frozen static project profile projection.
The literal file-presence and JDK activation paths are preserved in the source
inventory and full effective POM. `setup-checkout` only declares a `pre-site` task;
its activation did not run SVN. The jacoco agent is bound to `process-test-classes`,
and its report/check tasks are later phases; no agent or test was run.

The [exact profile output](examples/phase5_2_2_d_3/active-profiles.txt) and
[comparison](examples/phase5_2_2_d_3/static_vs_maven.json) are committed metadata.

### The literal `[9` activation and unresolved transitive profiles

`unknown_profile_evidence.json` contains15 distinct **transitive** source-model
uncertainties. None belongs to T0's project inheritance chain (CLI → Parent76 →
Apache33). The literal `[9` comes from `commons-parent:58`, not Parent76. Maven's
observed T0 JDK9+ profile uses `[9,)`; the actual JDK17 context activated `jdk9+`,
`java-9-up`, `java-11-up` and `java-17-up` as reported above.

This execution does **not** establish how Maven evaluates Parent58's literal `[9`
while building a different dependency/plugin model. Its status remains UNKNOWN /
not directly evaluated here. No artificial replacement POM, extra `-P`, auxiliary
project or extra Help goal was used to manufacture an answer. Similarly, OS/file
profiles in QDox, Plexus, SSHD and HTTPComponents remain outside the observed
project model and unresolved until their actual required runtime closure is
verified. Inactivity in the CLI project is not proof of inactivity in those models.
The15-source evidence is retained unchanged and explicitly reconciled in the new
comparison; no prior UNKNOWN was silently marked solved.

## Effective-model identity and static comparison

Full effective POM:113,258bytes, private local artifact:

```text
/home/hp/tst/research/forecasting_mvp/phase5_2_2_d_3/2026-10-16/effective-pom/effective-pom.xml
```

SHA256:

```text
bf4a9243703b32ca363232c2759c8bab4f009ac544897dafab87f4b22f42e449
```

The model's group/artifact/version is `commons-cli:commons-cli:1.9.1-SNAPSHOT`.
Effective properties include `maven.compiler.release=8`, `commons.compiler.release=8`,
`maven.compiler.source=1.8` and `maven.compiler.target=1.8`. The historical compiler
configuration/enforcers were not edited or disabled. `maven.test.skip=true` was
supplied exactly as registered; it is not a claim about later test-plugin behavior.

The five effective direct dependencies match the earlier static declarations,
including JUnit5.11.1, Commons IO2.17.0 and Mockito4.11.0. **All five are test-scoped**;
there are no direct compile-scoped project library declarations. Help goals did
not resolve these test artifacts or produce a mediated plugin/runtime classpath.
No missing runtime artifact was observed for the two Help goals. This is scoped
to the helper model inspection, not a claim that all historical plugin/lifecycle
runtime requirements are available.

The effective model and cached descriptors identify these through-compile
candidate bindings; **none executed**:

| Effective plugin | Binding(s) |
| --- | --- |
| org.apache.maven.plugins:maven-remote-resources-plugin:3.2.0 | process → generate-resources |
| org.apache.maven.plugins:maven-enforcer-plugin:3.5.0 | enforce → validate, enforce → validate |
| org.apache.maven.plugins:maven-antrun-plugin:3.1.0 | run → generate-sources |
| org.apache.maven.plugins:maven-compiler-plugin:3.13.0 | compile → compile |
| org.apache.rat:apache-rat-plugin:0.16.1 | check → validate |
| org.apache.maven.plugins:maven-artifact-plugin:3.5.1 | check-buildplan → validate |
| org.codehaus.mojo:build-helper-maven-plugin:3.6.0 | parse-version → validate |
| org.codehaus.mojo:buildnumber-maven-plugin:3.2.1 | create → generate-resources |
| org.apache.maven.plugins:maven-resources-plugin:3.3.1 | resources → process-resources |

Lifecycle-default bindings are now visible in the effective model. Default phases
for phase-less executions were read from already verified plugin descriptors,
not guessed. Maven JAR `jar`/`test-jar` stays at `package`, after compile. Enforcers,
RAT and buildplan checks remain enabled for any later separately authorized
lifecycle execution; a Help goal does not establish their successful execution.
Buildnumber's historical SCM-failure fallback remains part of the unchanged POM;
this phase neither exercised it nor used it to admit source/measurement provenance.

## Tests, preservation and files

**313 tests passed in each checkout**, including30 new D.3 cases, zero failures,
errors or skips. Central: 17.616s; original working project:
16.327s. Tests cover approved-goal restrictions, immutable source/
cache admission, exact helper request/byte boundaries, failed-request accounting,
forbidden lifecycle forks, complete bounded tmpfs evidence extraction, archive
traversal/binary rejection, network isolation, retained model/classpath separation,
actual published profile reconciliation and prior A/B/D/D.1/D.2/scope foundations.

[Verification receipt](examples/phase5_2_2_d_3/verification.json) binds source,
test-log/JUnit hashes and preservation checks. Preservation PASS:436 previous
central files,347 working files,4 unrelated unfinished files,1378/615/630 prior
D/D.1/D.2 cache files and their original ledgers,5878 user-cache entries plus75
reference artifact hashes,56 frozen bundles/322 artifacts,2 Phase5.1 bundles,
source SQLite and pinned model checkpoint, original source blobs, old Sonar
container state/mounts and existing containers/volumes. Original working `main`
stays `2e7999ea436d49449652e6c52e9066ef2e514419`.

New source: `tools/inspect_phase5_2_2_d_3.py`; new tests:
`tests/test_phase5_2_2_d_3_inspection.py`; this report and the new metadata-only
`examples/phase5_2_2_d_3/` bundle. Existing source, contracts/reports and all benchmark
artifacts remain unchanged. Third-party POMs/JARs, full raw effective POM,
runtime caches and private inspection artifacts are not committed.

## Reproduction and next gate

Read-only verification and comparison can be repeated without Maven execution:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
PYTHONDONTWRITEBYTECODE=1 timeout 90s taskset -c 0 \
  prlimit --as=1073741824 --cpu=60 --fsize=33554432 -- \
  .venv-forecast/bin/python - <<'PY_READONLY'
from pathlib import Path
from tools.inspect_phase5_2_2_d_3 import compare_model
r = Path('/home/hp/tst/research/forecasting_mvp/phase5_2_2_d_3/2026-10-16')
print(compare_model(Path.cwd(), r)['status'])
PY_READONLY
```

Actual container command arrays, JVM environment, image/binary hashes, cgroup
settings, properties and settings hash are in
[execution evidence](examples/phase5_2_2_d_3/execution_evidence.json) and
[model identity](examples/phase5_2_2_d_3/effective_model_identity.json). The exact
executed commands ended with only:

```text
org.apache.maven.plugins:maven-help-plugin:3.5.1:active-profiles
org.apache.maven.plugins:maven-help-plugin:3.5.1:effective-pom
```

Re-running acquisition or Maven is unnecessary for this phase; the112-request
helper batch is closed. The source functions preserve the narrow recipe for later
explicitly authorized reproduction. Regression command (bounded as above):

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s taskset -c 0 prlimit --as=1073741824 --cpu=120 --fsize=16777216 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_phase5_2_2_d_3_inspection.py tests/test_phase5_2_2_d_2_recovery.py \
  tests/test_phase5_2_2_d_1_continuation.py tests/test_phase5_2_2_d_recovery.py \
  tests/test_phase5_2_2_b_probes.py tests/test_phase5_2_2_a_review.py \
  tests/test_production_scope_readiness.py tests/test_multilanguage_preflight.py \
  tests/test_multilanguage_foundation.py
```

Readiness: **T0 project model VERIFIED; historical offline build UNKNOWN;
SCM/lifecycle execution, mediated plugin-runtime closure and compilation pending.**
The other five revisions remain uninspected. Any future compilation must be
separately authorized with a bounded writable build sandbox and immutable inputs;
no successful build or classpath claim follows from this report. Sonar/analyzer
licensing and derived-dataset approvals remain unresolved outside this task.

Safe source, tests and metadata are published as a normal descendant commit on
GitHub main and remote bytes are verified. **STOP after D.3. No historical
compilation, other revision inspection, Sonar, TaskC/E/F or Phase5.3 starts.**
