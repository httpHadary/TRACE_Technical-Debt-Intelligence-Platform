# Phase 5.2.2-D — Low-RAM Maven dependency recovery

Date: **2026-10-16**. Verified starting main:
`1caf129975a39aeaab1614e457a7114f0bf477e3`.

**Task D PARTIAL. Required parent POMs FIXED; full offline dependency readiness
NOT ESTABLISHED.** Real artifacts were acquired and verified. Acquisition stopped
at the fixed2,000-request ceiling. The remaining work is an explicitly listed
frontier, not an assertion that only22 files remain in the full transitive graph.
Task C's licensing clarification was not used as a prerequisite for this task.

No Maven/Java/Node command, project goal, historical build, application execution,
Sonar server, scanner, analyzer-data processing, model or dataset operation ran.
Downloaded POMs/JARs were read only as XML/ZIP data. Task C/E/F were not started.

## Actual acquisition and resource results

| Evidence | Actual result |
| --- | --- |
| Verified artifacts |509:336 POMs and173 JARs |
| Corrected static traversal candidates staged |433 |
| Earlier unused candidates, excluded from staging |76 |
| Exact missing frontier files |22; additional descendants may exist behind missing POMs |
| HTTP requests, including checksum404s and retries |2,000/2,000; no further acquisition after cap |
| Response payload bytes read |52,664,020 (~50.22MiB); excludes headers/TLS/unread404 bodies |
| Peak acquisition process RSS across recorded passes |56,732KiB (~55.40MiB) |
| Actual enforced process address-space ceiling |1,073,741,824 bytes |
| Actual affinity |CPU0 only; inherited by read-only Git subprocesses |
| Recorded timed acquisition/traversal work across resumes |about698.54s; not network-only duration |
| Cache plus staged-copy storage at seal |145,376,122 bytes (~138.64MiB) |

Strict bounds:256MiB response payloads cumulatively across resumes;32MiB per
artifact;2,000 requests;1,800s cumulative acquisition/traversal timer;15s network
operation timeout;at most3 retries to the same URL for connection/TLS timeouts.
Outer batch timeouts, CPU-time limits and32MiB per-file limits additionally bound
execution. One batch ran at a time. Total cache/staging/metadata budget544MiB;
staging checks its512MiB payload budget before copying. No service was stopped,
software installed, historical POM rewritten or original cache overwritten.

The host had6,941,244KiB available RAM and37,247,795,200 free disk bytes at the
initial capture. Task D fits its independent1GiB budget; this does not establish
the10GiB RAM gate for a future Sonar server. No container was created or started.
Read-only preservation inspection used the Docker HTTP API from bounded Python,
avoiding Go CLI virtual-address reservations under the1GiB address-space cap.

## Immutable six-state requirements

Each POM/tree was re-read using `git show`/`ls-tree`, without checkout, lazy object
fetch, hooks or project execution, and matched the published Phase5.2.1 hashes.
All18 study states, cutoffs, production scopes and project identities are unchanged.

| Offset days | Pinned Commons CLI commit | Commons Parent |
| ---: | --- | ---: |
|-90|`e1529b546d9696192f4de52152777403b4a01b39`|71|
|-30|`fb6293fcd6a9b55ac8ecb550af6572daaed18fa1`|74|
|0|`4ff0d4adbc2161677e71050ba23c152831f6ad83`|76|
|30|`7ddf691ac2afbda7473c0d07f1f4e7ae1e69e47b`|78|
|60|`aad30eff27ac5c9a13194125226653c6c2826c58`|78|
|90|`af2b3e72a552cfb2a902556469868763ddea3638`|78|

The six pinned project POMs declare test-scoped JUnit/Commons IO, later Mockito
and Commons Text dependencies; the verified static root inventory has no
non-test project library dependency. This does not mean an offline compile has
no dependencies: the inherited lifecycle binds enforcement, RAT, Ant resource
preparation, build-helper parsing, JaCoCo and SCM/build metadata plugins.
Complete root declarations, property/profile projections, imported JUnit BOMs,
plugin versions/executions and candidate closures are in
[requirements.json](examples/phase5_2_2_d/requirements.json).

The future build context remains Maven3.9.11/Temurin17.0.17+10, Java8 bytecode,
`maven.test.skip=true`, `maven.compiler.release=8`, no explicit profiles and no
user Maven settings. These are static inventory inputs; this phase never executed
that build context or verified a classpath. Maven's inherited default `clean
verify ...` goal was never invoked.

## Parent blocker resolved

Exact coordinates: `org.apache.commons:commons-parent:71`,`:74`,`:76`,`:78`.
71/74 inherit `org.apache:apache:32`;76/78 inherit `org.apache:apache:33`.
All six parent-chain POMs were fetched into the new cache, including74 to avoid
relying on either existing cache. Local SHA256 values:

| Commons Parent | SHA256 |
| --- | --- |
|17|`96e718baf534874ee62ce4d42de265f2ddacd88391a540e030d59d98fa7c4408`|
|34|`3a2e69d06d641d1f3b293126dc9e2e4ea6563bf8c36c87e0ab6fa4292d04b79c`|
|39|`87cd27e1a02a5c3eb6d85059ce98696bb1b44c2b8b650f0567c86df60fa61da7`|
|42|`cd313494c670b483ec256972af1698b330e598f807002354eb765479f604b09c`|
|45|`9c88623ecfa91f012c673ee4622c0eeb4367e5e0d222d960f76cd208b1a4fda6`|
|47|`8a8ecb570553bf9f1ffae211a8d4ca9ee630c17afe59293368fba7bd9b42fcb7`|
|48|`1e1f7de9370a7b7901f128f1dacd1422be74e3f47f9558b0f79e04c0637ca0b4`|
|51|`9b779d18b22d8de559605558e7bb0a0a31b3f00c2abb9c878117c398aacabeca`|
|52|`75dbe8f34e98e4c3ff42daae4a2f9eb4cbcd3b5f1047d54460ace906dbb4502e`|
|54|`000d8187952b223702fde296df799563f35de82ce72adb4e7bf157342378fbe3`|
|56|`560c7051ddc768e1372e4087970764e4c013903c5dc6eb52c29877370dae2694`|
|58|`2d4b12e18899063abd7c75278b5fa97a3729d80878ceecb6a40d946e9c0d5590`|
|64|`6f19638994e8357b4ed734696f992057efaafa1235673998133299798e2ccddb`|
|65|`6cf3495fc2e6ac913a2b7f2e03fb5908fb3f229fb06d3358dc45678d5af3e36e`|
|71|`95b7be70f316ae4ca22f6fbdd08de2182e87cd874a650de7c3d3386a747a82a3`|
|74|`80eb61b0c87fdd826a069313b28b672da3f1885832da447b51e6e8a6197e7ecb`|
|76|`28843bb0f9bca5b7612b788993f4a5df2b462b952f11c9f8790869cc07be0307`|
|78|`022d202e655edd04f2a10ecbe453d92977924d38380a4ca8c359f1817a80320e`|
|9|`5331b7d3e0aed59728c80f1118e4dbf78565d4109e81d16602c9cadbdb23a128`|

Each artifact's exact coordinates, immutable release path, HTTPS source URL,
SHA256, byte count and verified repository checksum are in
[dependency_manifest.json](examples/phase5_2_2_d/dependency_manifest.json).
POM XML/coordinates and JAR CRCs were checked before publication to the raw cache.
No SNAPSHOT dependency, version range, LATEST/RELEASE or arbitrary newer version
was selected. Historical project SNAPSHOT versions remain pinned Git inputs and
were not fetched as remote artifacts.

Only `https://repo.maven.apache.org/maven2/` was permitted for acquisition. Proxy
inheritance and redirects were disabled. Repository checksums were tried in
SHA512/SHA256/SHA1 order; local SHA256 was always computed. This verifies TLS
repository identity and same-origin checksum consistency, not an independently
authenticated publisher signature. All original dependency locks remain unchanged.

## Recovery findings and remaining frontier

A TLS handshake timeout aborted the initial pass safely with verified artifacts
retained. Subsequent timeout retries stayed bounded and used the same endpoint.
An inherited dependency-management test-scope bug was found during the initial
static traversal, corrected and regression-tested.76 earlier unused candidates
remain hash-accounted outside the staged cache; they were not executed or silently
relabelled as required compile inputs. The corrected433-file candidate cache is
separate and every copied artifact was rehashed. A superseded staging copy is
retained locally as `admitted-repository-pre-legacy-xml-fix`; it is not the
current candidate cache and is included in the disk tally. Older namespace-free
POMs are normalized without changing their bytes, so their dependencies cannot
silently disappear. All336 POM coordinate triples were independently checked
after normalization, with no deferred coordinate fields. Missing plugin
descriptors remain required/unknown, never automatically unnecessary.

The static inventory is deliberately **not Maven dependency mediation**. It keeps
an exact-version candidate union where multiple paths declare different releases.
Some profile activation remains unresolved:OS/file conditions and the literal
`[9` activation in Commons Parent58. Unsupported activation is reported as unknown;
it is never silently approved or rewritten. There are21 PROFILE,18 DEPENDENCY and
4 PLUGIN unresolved records (identities can recur across repositories/models).

The22 missing request paths at the verified frontier are:

- `com/jcraft/jsch.agentproxy.connector-factory/0.0.9/jsch.agentproxy.connector-factory-0.0.9.pom`
- `com/jcraft/jsch.agentproxy.svnkit-trilead-ssh2/0.0.9/jsch.agentproxy.svnkit-trilead-ssh2-0.0.9.pom`
- `com/trilead/trilead-ssh2/1.0.0-build222/trilead-ssh2-1.0.0-build222.pom`
- `commons-codec/commons-codec/1.16.0/commons-codec-1.16.0.jar`
- `commons-digester/commons-digester/1.6/commons-digester-1.6.pom`
- `commons-io/commons-io/2.13.0/commons-io-2.13.0.jar`
- `commons-logging/commons-logging/1.0.3/commons-logging-1.0.3.pom`
- `de/regnis/q/sequence/sequence-library/1.0.4/sequence-library-1.0.4.pom`
- `net/i2p/crypto/eddsa/0.3.0/eddsa-0.3.0.pom`
- `net/java/dev/jna/jna-platform/5.6.0/jna-platform-5.6.0.pom`
- `net/java/dev/jna/jna/5.6.0/jna-5.6.0.pom`
- `org/apache/commons/commons-lang3/3.12.0/commons-lang3-3.12.0.pom`
- `org/apache/commons/commons-lang3/3.13.0/commons-lang3-3.13.0.jar`
- `org/apache/maven/plugins/maven-enforcer-plugin/3.5.0/maven-enforcer-plugin-3.5.0.pom`
- `org/apache/maven/plugins/maven-jar-plugin/3.4.2/maven-jar-plugin-3.4.2.pom`
- `org/apache/maven/plugins/maven-resources-plugin/3.3.1/maven-resources-plugin-3.3.1.pom`
- `org/apache/maven/scm/maven-scm-api/2.0.0-M3/maven-scm-api-2.0.0-M3.pom`
- `org/codehaus/mojo/buildnumber-maven-plugin/3.2.1/buildnumber-maven-plugin-3.2.1.pom`
- `org/lz4/lz4-java/1.4.1/lz4-java-1.4.1.pom`
- `org/slf4j/jcl-over-slf4j/1.7.32/jcl-over-slf4j-1.7.32.pom`
- `org/slf4j/slf4j-api/1.7.32/slf4j-api-1.7.32.pom`
- `org/tmatesoft/sqljet/sqljet/1.1.15/sqljet-1.1.15.pom`

The list includes descriptor-only inspection candidates as well as compile
plugin/runtime requirements; it is not proof that every listed file would execute
in `compile`. Missing POMs hide further parents/imports/transitives. In particular,
resources3.3.1, enforcer3.5.0 and buildnumber3.2.1 readiness are not established.
The4 plugin issue identities also include jar3.4.2 descriptor inspection.

No complete offline build should be dispatched from this partial cache. A later,
separately authorized bounded acquisition continuation must start from this
frontier, preserve exact versions, and re-evaluate any newly exposed dependencies.
Only a later authorized sandbox build can independently establish effective
profiles, classpaths and compilation success. Do not skip enforcers, rewrite
historical POMs or substitute newer dependencies to obtain a successful gate.

## Cache locations and reproduction

Artifacts remain outside Git:

```text
/home/hp/tst/research/forecasting_mvp/phase5_2_2_d/2026-10-16/isolated-cache/
  repository/                 #509 verified acquisition artifacts, including earlier candidates
  admitted-repository/        #433 corrected static candidates; still incomplete
  dependency_manifest.json
  staged_dependency_manifest.json
  requirements.json
```

Small metadata only is published under `examples/phase5_2_2_d/`. No POM/JAR,
third-party binary, cache, credential, private export, model or dataset is committed.
The new code is isolated to `tools/maven_recovery/`, the Task D CLI and tests.
No existing production module/report/contract was changed.

For a separately authorized fresh recovery, use a new outside-Git path; omit
`--resume` on its first pass. Existing caches are explicitly denied as destinations.
The current cache's request budget is exhausted: do not increase it automatically.
The following audit/staging operations perform no network acquisition:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
TD522D_PY="$PWD/.venv-forecast/bin/python"
TD522D_CACHE=/home/hp/tst/research/forecasting_mvp/phase5_2_2_d/2026-10-16/isolated-cache
PYTHONDONTWRITEBYTECODE=1 timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=120 --fsize=33554432 -- \
  "$TD522D_PY" -m tools.recover_phase5_2_2_d \
  --output "$TD522D_CACHE" --resume --offline-audit
# --stage-only performs hash verification and fresh staging without network.
# It intentionally refuses an existing admitted-repository directory.
```

## Verification and preservation

**247 tests passed in each checkout**, including43 Task D cases; no failures or
skips. Tests cover exact coordinates, HTTPS/redirect/response bounds, checksum and
cache tampering, fatal budgets, retry bounds, managed test scopes, transitive
optional/exclusion handling, namespace-free POMs, unresolved plugin readiness,
non-executing offline audit/staging and all six frozen identities. Existing Task A,
Task B, production-scope, preflight and schema-v2 tests remain passing.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=120 --fsize=16777216 -- \
  "$TD522D_PY" -m pytest -q -p no:cacheprovider \
  tests/test_phase5_2_2_d_recovery.py tests/test_phase5_2_2_b_probes.py \
  tests/test_phase5_2_2_a_review.py tests/test_production_scope_readiness.py \
  tests/test_multilanguage_preflight.py tests/test_multilanguage_foundation.py
```

The suite does not launch containers, contact Maven Central, run models or execute
project code. [Verification receipt](examples/phase5_2_2_d/verification.json) and
[readiness manifest](examples/phase5_2_2_d/readiness_manifest.json) separate software
verification PASS from dependency-cache PARTIAL.

Two complete offline audits produced byte-identical requirements:
`91a055df88bca2378331602a841126a26936a6c3c05cdb9a715de774d072d165`.
The network counter remained2,000. Every raw and staged artifact was rehashed.

Preservation PASS:397 existing central files,308 existing working-project files,
4 unfinished remediation files,56 frozen experiment bundles/322 artifacts, both
Phase5.1 bundles, source SQLite and Chronos checkpoint. Both existing Maven caches
retain all5,878 path/size/mtime/mode entries;75 published reference artifacts were
also rehashed. Old server identity/state/mount mappings and pre-existing volumes
remain unchanged. Original working `main` remains at
`2e7999ea436d49449652e6c52e9066ef2e514419`.

Task B's Maven Jansi/noexec warning remains a known finding. No noexec policy,
container isolation or JVM configuration was weakened to hide it. Task A rights
acceptances, licenses and prior study admission remain unchanged; no legal or
operator approval was inferred.

Primary Maven semantics consulted:
[dependency scopes/management](https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html),
[profile activation](https://maven.apache.org/guides/introduction/introduction-to-profiles.html),
[3.9.11 lifecycle bindings](https://maven.apache.org/ref/3.9.11/maven-core/default-bindings.html).
Inherited managed versions take precedence over the documented default bindings.

**STOP after Task D verification and normal-descendant GitHub publication.
Task C/E/F, builds, scans and forecasting are not started.**
