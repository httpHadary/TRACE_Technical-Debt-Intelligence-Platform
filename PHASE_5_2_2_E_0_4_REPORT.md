# Phase 5.2.2-E.0.4 — Single T0 offline compilation retry

Date: **2026-10-18**, Africa/Cairo. Starting main:
`a5f7fb1500d02477ca3584e0fb57c1262f472f96`.

**BLOCKED_DEPENDENCY. Exactly one new offline Maven `compile` invocation ran.**
Setup passed. Both original Maven/Java enforcer executions and Apache RAT passed.
The original `maven-artifact-plugin:3.5.1:check-buildplan` then failed to resolve
`org.apache.felix:maven-bundle-plugin:5.1.9`. Maven and Docker both exited1.
The compiler and SCM/buildnumber were **NOT_REACHED**; no classes were produced.
This is not COMPILE_PASS.

No dependency was acquired, version changed, POM edited, check skipped or retry
performed. No other revision, test goal, package/install/deploy, Sonar/server/scan,
forecast/model execution, technical-debt label or dataset-admission operation ran.
The task-owned container was removed after complete bounded evidence capture.

## Immutable inputs and new adapter

| Identity | Verified |
| --- | --- |
| Commons CLI T0 commit |`4ff0d4adbc2161677e71050ba23c152831f6ad83`|
| Tree |`ac7521be84b2820a83f7b960d329a15521408214`|
| Historical POM SHA256 |`b75fb9813e3c06121caa7d84c31a471b646465966079cf10ec4c7a2e4aba55f2`|
| D.3 actual effective POM SHA256 |`bf4a9243703b32ca363232c2759c8bab4f009ac544897dafab87f4b22f42e449`|
| E.0.3 dependency manifest SHA256 |`73de04d94fe2a1c85fd49f38bfdc14df47e0f93855a8ac5258a10d72f714b113`|
| Canonical679-artifact cache identity |`f4bc6cbab0f8e0bc14557408173290a8453854c35226b40348bffe7a58011daa`|
| Pinned local Maven/JDK image |`sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82`|

All117 tracked source files were checked against their frozen Git inventory,
individual blob identities and SHA256 values. All679 artifact paths, coordinate
triples, SHA256 values, recorded Central checksum/provenance, POM XML and JAR CRCs
were independently reverified. The source cache has exactly those679 files, with
no unregistered artifact. Copies use independent inodes, not hard links. All inputs
were rehashed after copying and before admission. The historical source/POM, E.0.3
cache, original caches/ledgers and old claims remain unchanged.

`tools/build_compile_e04.py` is a new versioned adapter with its own E.0.4 owner
label, registration, `--e04-offline-compile` mode and exclusive one-attempt claim.
It reuses E.0.2's command, tested setup/capture recipe, bounded archive handling and
Java8 class parser. It does **not** invoke an old E.0/E.0.2 runner, reuse a claim,
repurpose smoke mode or modify any archived evidence. The source/cache manifests,
wrapper, settings, command and immutable identities are rechecked before startup.

The generated wrapper requires exactly117 source and679 artifact files. It keeps
UID/GID1000 ownership checks, the early EXIT trap and separate setup/Maven streams.
The archived E.0.1 shell/smoke sentinel and E.0.2 implementation remain unchanged.
No Git metadata was manufactured. The new class-output verifier retains identity/
structure/major52 checks while accounting separately for ordinary nonclass
resources such as generated LICENSE files; those are not mislabelled as classes.
This behavior was verified with explicitly synthetic unit fixtures only.

The executed adapter SHA256 is
`fc222df5249741571f47d6e0b6b1fec73401ebefeb1c0df8731770032847f3fb`; it is unchanged since the actual attempt.
[Registration](examples/phase5_2_2_e_0_4/compile_registration.json) binds the executed
wrapper, settings, exact command, pinned runtime and input/cache identities.

## Resource admission and exact execution

The679 artifact payload is74,152,353 bytes. A conservative estimate rounds each
file and directory to4KiB and reserves16MiB for Maven metadata:95,465,472 bytes
(~91.04MiB), within the unchanged128MiB repository tmpfs. The kernel's tmpfs cap
remains authoritative. In this attempt Maven added **zero** cache metadata files.

Immediately before startup:5,995,515,904 available host RAM bytes (~5.58GiB),
20,661,628,928 free disk bytes, zero running containers and no prohibited Java,
Maven, Sonar/scanner or model processes observed. The admission requirement stayed
>=4GiB available, comprising2GiB container budget plus2GiB host headroom. The
minimum sampled available host RAM during execution was5,802,532,864 bytes
(~5.40GiB), above the2GiB runtime headroom threshold. No service was stopped or user
data deleted to obtain admission.

The pinned image was already local; `--pull never` prevented a pull. Before start,
Maven launcher/core and Java executable/release hashes from the same stopped task
container matched TaskB's pinned Maven3.9.11 /Temurin17.0.17+10 evidence. No extra
version-probe container or Java command was launched.

Exactly this command ran once:

```bash
/usr/share/maven/bin/mvn \
  --offline --batch-mode --no-transfer-progress --errors \
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

Original Commons Parent76 and all configured executions/profiles were preserved.
No explicit profile was selected. D.3's exact effective model, settings and profile
receipt were rechecked; no separate runtime profile listing or Help goal ran.
The compile logs do not enumerate profiles, so no new runtime profile listing is
invented. The context remains the registered detached export with `/tmp` user home.

Isolation:2GiB RAM,768MiB maximum heap,1CPU,64PIDs, no additional swap,
UID/GID1000, all capabilities dropped, no new privileges, read-only image root,
owned/noexec/nosuid/nodev source/repository/tmp/output tmpfs, no network,
read-only inputs/inspection mounts and no Docker socket/host credentials/user cache.
Repository/source/tmp caps remain128MiB each; output32MiB, shared memory8MiB,
per-file8MiB, archive32MiB and descriptor limit1024. Maven timeout240s,
monitor limit265s and hard outer controller timeout330s remain unchanged.

## Actual lifecycle and first failure

| Order | Actual execution | Outcome |
| ---: | --- | --- |
|1|Enforcer3.5.0: `enforce-maven-version`|RequireMavenVersion passed|
|2|Enforcer3.5.0: `enforce-java-version`|RequireJavaVersion passed|
|3|Apache RAT0.16.1: `rat-check`|Completed:0 unapproved,0 unknown,106 approved license headers|
|4|Artifact3.5.1: `check-buildplan`|Failed during execution-plan/plugin-descriptor resolution|

The first fatal error is preserved verbatim:

```text
Failed to execute goal org.apache.maven.plugins:maven-artifact-plugin:3.5.1:check-buildplan (check-buildplan) on project commons-cli: Cannot calculate Maven execution planPlugin org.apache.felix:maven-bundle-plugin:5.1.9 or one of its dependencies could not be resolved
```

Exact fatal missing JAR:

```text
org/apache/felix/maven-bundle-plugin/5.1.9/maven-bundle-plugin-5.1.9.jar
```

A missing-POM warning also names the exact same plugin's5.1.9 POM. The frozen D.3
model binds its `manifest` goal (`bundle-manifest`) to **process-classes**, after
compile. That goal did not run. Nevertheless, the original validate-phase
check-buildplan requested its descriptor while calculating a plan; the actual
stack shows `CheckBuildPlanMojo.calculateExecutionPlan`, Maven's execution-plan
calculator and `getPluginDescriptor`. Plan calculation is not execution of later
lifecycle goals. Do not skip check-buildplan, remove the later execution or assume
that all later-phase plugin runtime JARs must automatically be downloaded.

Three additional **nonfatal missing-POM warnings** occurred during successful RAT:

| Exact POM warning | Path |
| --- | --- |
|`log4j:log4j:1.2.12`|`log4j/log4j/1.2.12/log4j-1.2.12.pom`|
|`logkit:logkit:1.0.1`|`logkit/logkit/1.0.1/logkit-1.0.1.pom`|
|`avalon-framework:avalon-framework:4.1.3`|`avalon-framework/avalon-framework/4.1.3/avalon-framework-4.1.3.pom`|

The [failure manifest](examples/phase5_2_2_e_0_4/failure_manifest.json) distinguishes
**one fatal JAR resolution error and four missing-POM warnings**. All belong to
plugin/plan-resolution context, not a recurrence of E.0.2's five missing project
test roots. The necessity of JARs corresponding to the three RAT warnings is not
inferred from a POM warning. Unseen parent/BOM/runtime descendants remain UNKNOWN.
No remote availability or checksum for missing bytes is fabricated.

The observed blocker is dependency/plugin descriptor resolution, not SCM context,
an enforcer rejection, Jansi, timeout or OOM. Buildnumber/SCM, remote resources,
build-helper, antrun, resources and compiler were not reached. No test compilation,
package/install/deploy or other unapproved goal execution was observed.
The inherited Jansi/noexec warning remains in full private stderr; no isolation
workaround was used. RAT's automated license-header result is not human legal or
policy acceptance and does not resolve SonarSource or derived-dataset permissions.

E.0.3's test-dependency closure is still a valid frozen static result. This real
attempt shows progress beyond it and exposes a different metadata requirement of
the original build-plan checker. It does not retrospectively redefine a previous
phase as build-ready or successful compilation.

## Capture, class outputs and resource observations

| Evidence | Actual |
| --- | ---: |
| New containers started /Maven invocations /retries |1 /1 /0|
| Setup |Passed, exact117/679 population and ownership/hash checks|
| Maven exit /Docker exit /EXIT-trap exit |1 /1 /1|
| Actual plugin goal banners |4:two enforcer executions,RAT,check-buildplan|
| Compiler invocation /classpath evidence |NOT_REACHED /NOT_REACHED|
| Produced `.class` files |0; complete post-run file inventory confirms absence|
| Expected top-level Java identities |25, plus separate package-info source|
| Tracked source bytes /artifact bytes |All117 /679 unchanged|
| Generated source-tree output |One isolated RAT report; content stays outside Git|
| New cache metadata files |0|
| Complete private Maven stdout /stderr |12,542 /569 bytes; no truncation|
| Capture unavailable fields /controller errors |0 /0|
| Owned cleanup /remaining task containers |Complete /0|
| EXIT-trap cgroup memory.peak |261,582,848 bytes (~249.46MiB)|
| Cgroup CPU usage |6,057,683µs|
| Cgroup memory max /swap max |2,147,483,648 /0 bytes|
| Cgroup CPU quota /period /PIDs |100,000 /100,000µs /64|
| OOM /OOM-kill counters /Docker OOMKilled |0 /0 /false|
| Wrapper Maven wall time |5.50s|
| Maven's reported internal elapsed time |3.399s|
| Host monitoring/capture elapsed time |7.175s|

The cgroup peak/CPU values are actual EXIT-trap snapshots after post-run diagnostics
and before later export/cleanup; no unobserved full-lifetime peak is invented.
Full bounded setup/Maven streams, Docker logs, terminal inspect, task-owned daemon
events, post-source/cache hashes and original execution receipt remain private.
Only a clearly marked sanitized diagnostic excerpt is published, not represented
as a complete log. [Log inventory](examples/phase5_2_2_e_0_4/log_inventory.json)
records exact byte counts, hashes and complete/truncated status for private files.

[Capture completeness](examples/phase5_2_2_e_0_4/capture_completeness.json) passes
all checks, including one actual start, matching exits, retained logs, unchanged
source/cache, no unexpected capture error and owned cleanup. The class-output
manifest records NOT_PRODUCED, not a fictitious major52 or class-completeness PASS.
The unit-test class/resource fixture is explicitly synthetic and never substituted
for real Java compilation evidence.

## Regression and preservation

**450 tests passed in each checkout**, zero failures/errors/skips. The current
central suite took18.416s; working project17.682s.
The pre-launch suite also passed450 tests in16.475s before the
single allowed attempt. There are31 new E.0.4 cases covering exact command/mode,
679-file cache identity, tmpfs capacity, exclusive claims, resource/input admission,
security settings, input/hash preservation including the26 recovered additions,
plugin-versus-project/SCM failure classification, absent evidence, no false
initialization/class success and separate class/resource accounting.

The executed adapter bytes are identical to the published adapter. A post-attempt
test-fixture refinement selects a recovered addition specifically for the cache
tampering check; it changes no adapter or runtime behavior and caused no Maven
rerun. Pre-/post-test source hashes and regression receipts are retained in
[verification.json](examples/phase5_2_2_e_0_4/verification.json).

Protected research/source/cache preservation **PASS**:all529 pre-existing central
files,440 working-project files and4 unrelated unfinished files retain their
hashes. D/D.1/D.2/D.3/E.0/E.0.1/E.0.2/E.0.3 retain all
1378/615/630/842/790/818/832/703 file hashes. Prior ledgers remain2000/400/52/112/56,
and all earlier attempt claims/reports remain unchanged. All56 frozen experimental
bundles/322 artifacts, both Phase5.1 bundles, source SQLite and Chronos checkpoint
hashes pass. T0 Git tree/blobs/POM,6262 user-cache metadata entries and75 reference
artifact hashes are preserved. No old source, configuration or implementation
module was changed; all implementation changes are new E.0.4 files.

Old `td-target-sonar` identity/state/mounts and existing volumes are unchanged.
The broader container inventory cannot be declared wholly preserved:an unrelated
`olympus-quivr-toolchain:20261017` container (`d3cf1248657f`) present at the initial
snapshot was subsequently destroyed. Narrow read-only daemon events show its
`die`/`destroy` before the E.0.4 container's `create`, about339 seconds earlier.
The task's audited cleanup targeted only its own distinct E.0.4 labelled UUID
container. No unrelated container was stopped/recreated by this task. Remaining
pre-existing container identities/state/mounts are preserved. Therefore the receipt
explicitly labels shared-container inventory **PARTIAL_SHARED_CONTAINER_INVENTORY_CHANGE**
while separately recording protected research/source and old Sonar preservation PASS.
No blanket preservation claim or unauthorized restoration is made.

Original working HEAD stays `2e7999ea436d49449652e6c52e9066ef2e514419`; only publication
tracking refs advance after normal-descendant GitHub verification.

## Reproduction, files and exact next action

Private task root:

```text
/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_4/2026-10-18/
  attempt-1/attempt_claim.json       #consumed; NEVER reuse/reset
  attempt-1/inputs/                  #independent117/679 source/artifact seeds
  attempt-1/inspection/              #executed wrapper/settings/hash manifests
  attempt-1/capture/                 #complete bounded private logs/diagnostics
  attempt-1/execution.json
  attempt-1/result.json
```

Read-only result reclassification (does not run Maven):

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
PYTHONDONTWRITEBYTECODE=1 timeout 60s taskset -c 0 \
  prlimit --as=1073741824 --cpu=45 --fsize=33554432 -- \
  .venv-forecast/bin/python - <<'PY_READONLY'
from pathlib import Path
from tools.build_compile_e04 import analyze
r = Path('/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_4/2026-10-18/attempt-1')
print(analyze(r)['status'])
PY_READONLY
```

This rewrites only the deterministic E.0.4 derived result receipt, preserving raw
execution evidence and all old phases. Never call `execute_once` again for this
claim. Relevant deterministic regression command:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=120 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_build_compile_e04.py tests/test_compile_test_dependency_recovery.py \
  tests/test_build_compile_e02.py tests/test_build_sandbox.py \
  tests/test_phase5_2_2_e_0_compilation.py tests/test_phase5_2_2_d_3_inspection.py \
  tests/test_phase5_2_2_d_2_recovery.py tests/test_phase5_2_2_d_1_continuation.py \
  tests/test_phase5_2_2_d_recovery.py tests/test_phase5_2_2_b_probes.py \
  tests/test_phase5_2_2_a_review.py tests/test_production_scope_readiness.py \
  tests/test_multilanguage_preflight.py tests/test_multilanguage_foundation.py
```

New files: `tools/build_compile_e04.py`, `tests/test_build_compile_e04.py`, this
report and `examples/phase5_2_2_e_0_4/` sanitized metadata/diagnostic evidence.
No Maven binary, dependency payload, raw private log, generated historical build
output or cache is published.

[E.0.5 handoff](examples/phase5_2_2_e_0_4/E_0_5_HANDOFF.md):separately authorize a
new bounded, non-executing recovery starting with the exact Felix5.1.9 POM/JAR and
authoritatively necessary descriptor/plan metadata. Audit the three RAT POM
warnings separately. Keep descriptor-only and later-phase runtime requirements
separate; unknown descendants remain unknown until inspected. A later single
compile requires another explicit authorization, fresh adapter/claim and the same
original lifecycle/security/resource limits. Do not skip checks, change versions,
add Git metadata or automatically fix-and-retry.

**STOP after E.0.4 verification and GitHub publication. No dependency acquisition,
second attempt, other revision, Sonar/server/scan, forecasting/model, debt labels,
data admission/rebuild or Phase5.3 was started. SonarSource licensing and derived-
dataset rights gates remain unresolved and unchanged.**
