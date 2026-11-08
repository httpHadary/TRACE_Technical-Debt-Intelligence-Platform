# Phase 5.2.2-E.0.3 — Exact Maven test-dependency recovery

Date: **2026-10-18**, Africa/Cairo. Base main:
`b3dc64abea6451395cf5dc170fbb95077a09acf0`.

**STATIC_TEST_DEPENDENCY_CLOSURE_COMPLETE.** All ten missing paths reported by the
actual E.0.2 Maven failure are recovered at their original versions. Required
parent/BOM metadata and seven transitive libraries have been verified. The new
isolated candidate cache contains **679 artifacts: 653 unchanged seeds plus 26
additions**. There are no known missing files or dependency-affecting profile
uncertainties in this specific test-dependency closure.

This is **not COMPILE_PASS or FULL_OFFLINE_BUILD_READY**. No Maven, Java, JAR,
plugin, historical build, container startup, Sonar/scanner, model execution or dataset mutation
ran. No E.0.2 retry or other historical revision was attempted. Effective
plugin runtime classpaths, SCM/buildnumber behavior and eventual compilation remain
unproven. Broader frozen profile questions and rights gates remain unchanged.

## Observed roots and recovered closure

The starting frontier comes from E.0.2's published actual stdout/stderr and
[failure manifest](examples/phase5_2_2_e_0_2/failure_manifest.json), not a guessed
compile requirement. D.3's actual T0 effective POM declares precisely these five
roots with scope `test`. Both POM and JAR are now independently verified for each:

| Exact observed root | Recovery |
| --- | --- |
| `org.junit.jupiter:junit-jupiter-api:5.11.1` | Exact POM and JAR recovered |
| `org.junit.jupiter:junit-jupiter-engine:5.11.1` | Exact POM and JAR recovered |
| `org.junit.jupiter:junit-jupiter-params:5.11.1` | Exact POM and JAR recovered |
| `commons-io:commons-io:2.17.0` | Exact POM and JAR recovered |
| `org.mockito:mockito-core:4.11.0` | Exact POM and JAR recovered |

Seven required transitive libraries, each with exact POM and JAR:

| Exact transitive coordinate | Authoritative dependency path / declared scope |
| --- | --- |
| `org.opentest4j:opentest4j:1.3.0` | Jupiter API / compile |
| `org.apiguardian:apiguardian-api:1.1.2` | Jupiter API/engine/params and Platform / compile |
| `org.junit.platform:junit-platform-commons:1.11.1` | Jupiter API and Platform engine / compile |
| `org.junit.platform:junit-platform-engine:1.11.1` | Jupiter engine / compile |
| `net.bytebuddy:byte-buddy:1.12.19` | Mockito core / compile |
| `net.bytebuddy:byte-buddy-agent:1.12.19` | Mockito core / compile |
| `org.objenesis:objenesis:3.3` | Mockito core / runtime |

New parent POMs: `net.bytebuddy:byte-buddy-parent:1.12.19` and
`org.objenesis:objenesis-parent:3.3`. Existing verified metadata was reused for
Commons IO's Commons Parent74 -> Apache33 chain and imported JUnit BOMs5.11.0 and
5.11.1. No parent or BOM JAR was requested. Parent74 here belongs to the Commons IO
library descriptor; the frozen Commons CLI T0 project still uses Parent76.

The 26 additions are 10 root files +14 transitive files +2 parent POMs, totaling
**14 POMs and12 JARs**. The cache retains all historical/helper seed artifacts;
this is not a claim that all679 files are minimally necessary for T0.

The static traversal reads XML declarations and their parents/imports, applies
concrete T0 dependency-management versions, and records deterministic breadth-first
nearest/first selection. All12 library identities enter this consumer through its
test-scoped roots. Their effective consumer scope remains `test`, including the
runtime-declared Objenesis path. No tests were run or test compilation enabled.
E.0.2's observed lifecycle resolution, despite `maven.test.skip=true`, is why these
exact dependencies are recovered; this is not a universal claim about `compile`.

Dependency management does not itself request every managed library. Only
referenced compile/runtime transitives propagate. Exclusions and optional flags
are audited; dependency-descriptor test/provided dependencies are omitted. For
example, Commons IO's own JUnit Pioneer/JMH/Mockito-inline/Jimfs/Commons Lang/Codec
test dependencies, Byte Buddy's provided JNA/annotation dependencies and old
agent test dependencies are not acquired. No extra runner, later-phase plugin,
newer version or arbitrary dependency substitution was introduced.

[Closure evidence](examples/phase5_2_2_e_0_3/closure_evidence.json) contains model
chains, imported BOMs, management entries, profiles, exact dependency paths and
all omitted declarations. No actual Maven dependency tree or runtime classpath is
claimed. [Remaining uncertainties](examples/phase5_2_2_e_0_3/remaining_uncertainties.json)
references all15 unchanged D.2 static profile records. D.3's already verified T0
project-profile decisions remain intact; they are not extended to the other five
historical revisions or silently treated as verification of plugin classpaths.

## Acquisition, local reuse and integrity

The entire653-file E.0.2 seed was matched against published D.2's624 records and
D.3's29 separate helper records, with the original E.0 prerequisites as an
additional cross-check. Every source byte, coordinate, SHA256, recorded Central
checksum and XML/JAR structure was reverified. Independent file copies were made
into a fresh directory; no hard links, cache overwrite or ledger reset occurred.
All653 seed destination hashes were independently rechecked after recovery.

Only `https://repo.maven.apache.org/maven2/` was permitted. HTTPS/TLS repository
identity, no inherited proxy, no redirects, exact immutable release paths,
per-request timeouts, bounded sequential retries, checksum probes and strict
byte/request/storage ceilings remain enforced. POM repository declarations do not
add allowed network destinations. No artifact was executed.

Approved local sources were checked before downloading each missing artifact.
**16 files reused5,619,293 bytes** from the previously approved user/operator
caches, admitted only after fresh same-origin Central checksum validation,
coordinate checks and structural/CRC validation. A matching filename alone was
never sufficient. **10 files were downloaded**. All newly admitted rows carry
exact coordinates, source URL, local SHA256, verified checksum and origin.
SHA512 is preferred, then SHA256, then SHA1 where only that sidecar is available.
This is TLS/same-origin checksum consistency, not independent publisher-signature
authentication. The source user caches were read only.

| Accounting | Actual / limit |
| --- | ---: |
| New HTTP requests, including checksum404s and retries | **56 /200** |
| Checksum404 responses |20; no missing artifact payload404 |
| Transport retries |0 |
| Newly read response payload bytes |1,473,004 /67,108,864 (~1.40 /64MiB) |
| New artifact bytes, including approved local reuse |7,089,849 |
| Per-artifact ceiling |32MiB |
| Cache payload, all679 files |74,152,353 bytes (~70.72MiB) |
| Task storage at static verification |77,355,525 bytes; below256MiB ceiling |
| Acquisition elapsed time |38.893s /600s |
| Acquisition peak process RSS |39,708KiB (~38.78MiB) |
| Enforced process address-space limit |1,073,741,824 bytes |
| Actual CPU affinity /acquisition workers |CPU0 /one sequential worker |
| Available RAM after acquisition |7,876,136KiB |
| Free disk after acquisition |21,115,871,232 bytes |
| Maven invocations /compile retries /containers started |0 /0 /0 |

Request attempts are durably recorded before I/O. No resumed/reset/second batch
was started. Payload accounting measures artifact/checksum response bytes read;
it excludes headers/TLS and unread error bodies. Error responses were closed.
No full wire-byte or unmeasured CPU-utilization claim is made. One CPU affinity,
address-space and per-file/outer time limits were enforced by the command below.

Original ledgers remain **D2000 /D.1 400 /D.2 52 /D.3 112** byte-for-byte. The new
56-request ledger is separate and sealed. The unused request allowance is not
authorization for another acquisition phase.

## Reusable cache and deterministic verification

Private isolated cache, outside Git:

```text
/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_3/2026-10-18/
  recovery-1/repository/          #679 exact verified artifacts
  recovery-1/dependency_manifest.json
  recovery-1/closure_evidence.json
  before.json                    #private preservation baseline
  static_verification.json
  preservation.json
  central-regression.xml
  working-regression.xml
```

Full [dependency manifest](examples/phase5_2_2_e_0_3/dependency_manifest.json) SHA256:
`73de04d94fe2a1c85fd49f38bfdc14df47e0f93855a8ac5258a10d72f714b113`.
Canonical679-file cache identity:
`f4bc6cbab0f8e0bc14557408173290a8453854c35226b40348bffe7a58011daa`.
The identity recipe is the concatenation, sorted by Maven relative path, of
`sha256 + two spaces + byte_count + two spaces + relative_path + LF`, encoded UTF8.
It covers artifact identities/bytes independently of changing execution timestamps.

Two independent no-network audits reverified all679 files and produced identical
closure evidence SHA256 `b7940f478d50fd5ce4942410238735a81312ae9e0871e01e29de78f26eb3b343`. They agree with the
acquisition's static audit. The sealed request ledger was byte-identical before
and after both audits. All ten original paths are resolved, no newly exposed
required static path is missing, and no descriptor/profile ambiguity affects this
specific test-dependency closure.

Actual acquisition command (historical record; **do not rerun this consumed output
path or start another batch without authorization**):

```bash
cd /home/hp/tst/TechDebt360-MVP
PYTHONDONTWRITEBYTECODE=1 timeout 660s taskset -c 0 \
  prlimit --as=1073741824 --cpu=180 --fsize=33554432 -- \
  /home/hp/tst/td_pipeline_module_level/td_pipeline/.venv-forecast/bin/python \
  -m tools.recover_compile_test_dependencies \
  --output /home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_3/2026-10-18/recovery-1
```

Reproduce the read-only audit, with no network or Maven:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
PYTHONDONTWRITEBYTECODE=1 timeout 90s taskset -c 0 \
  prlimit --as=1073741824 --cpu=60 --fsize=16777216 -- \
  .venv-forecast/bin/python -m tools.recover_compile_test_dependencies \
  --audit-only \
  --output /home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_3/2026-10-18/recovery-1
```

## Regression and preservation receipts

**419 tests passed in each checkout**, zero failures/errors/skips;30 new E.0.3
cases. Central16.424s; working project
15.972s. Cases cover independent seed copies,
tampering/provenance/checksum rejection, fresh checksum admission of local bytes,
request/disk/time/payload limits, transport allowlisting/redirect refusal, CRCs,
non-executing offline missing-frontier collection, dependency management, imported
BOMs, nearest-first selection, scope/optional/exclusion handling and preservation
of unknown dependency-affecting profiles. Network is disabled by unit-test guards;
no Maven/container entry point exists in the recovery module.

Run the same relevant regression suite from the project:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=120 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_compile_test_dependency_recovery.py \
  tests/test_build_compile_e02.py tests/test_build_sandbox.py \
  tests/test_phase5_2_2_e_0_compilation.py tests/test_phase5_2_2_d_3_inspection.py \
  tests/test_phase5_2_2_d_2_recovery.py tests/test_phase5_2_2_d_1_continuation.py \
  tests/test_phase5_2_2_d_recovery.py tests/test_phase5_2_2_b_probes.py \
  tests/test_phase5_2_2_a_review.py tests/test_production_scope_readiness.py \
  tests/test_multilanguage_preflight.py tests/test_multilanguage_foundation.py
```

[Preservation PASS](examples/phase5_2_2_e_0_3/preservation.json):all511 pre-existing
central files,422 working-project files and4 unrelated unfinished files retain
exact hashes. No existing code/report/configuration was modified. D/D.1/D.2/D.3/
E.0/E.0.1/E.0.2 directories retain their1378/615/630/842/790/818/832 file hashes,
including request ledgers and original attempt claims. All56 frozen experiment
bundles/322 artifacts, both Phase5.1 bundles, source SQLite and model checkpoint
hashes pass. T0's Git tree and117 blobs/POM remain exact. All6262 user-cache
metadata entries and75 reference artifact hashes remain unchanged.

Old `td-target-sonar` state, identity and volumes are preserved. All pre-existing
containers and volumes remained stable; mount arrays were canonicalized by
Destination because API array ordering alone is not a configuration change.
An unrelated transient toolchain container appeared during preservation checks
at01:00:36UTC, after acquisition sealed at00:57:22UTC; this task made only read-only
Docker API inspections and did not start/stop it or any service. It was absent on
subsequent inspection. This is recorded rather than claiming the entire shared
Docker inventory stayed identical across all observations.

Original working HEAD remains `2e7999ea436d49449652e6c52e9066ef2e514419`; only the
publication tracking refs advance after verified normal-descendant publication.

## Files and E.0.4 handoff

New source: `tools/recover_compile_test_dependencies.py`, reusing the existing
acquisition, model and integrity-verification utilities. New tests:
`tests/test_compile_test_dependency_recovery.py`. This report and
`examples/phase5_2_2_e_0_3/` contain only safe metadata, manifests and instructions;
no POM/JAR payload, historical classes, credentials or private caches are committed.

[E.0.4 handoff](examples/phase5_2_2_e_0_3/E_0_4_HANDOFF.md) specifies a separately
versioned adapter and one newly authorized T0 attempt, seeded with679 verified
files and the unchanged117-file source export. It retains the pinned image,
original offline command/profiles/lifecycle, Java8 target, testskip, exact hashes,
owned unprivileged tmpfs,2GiB/768MiB/1CPU/64PID/no-swap/no-network limits,240s Maven
ceiling, fresh resource admission and strict evidence/class-output verification.
Do not reuse an old claim or weaken rules if a plugin/SCM issue is exposed.

Maven semantics are supported by its official
[dependency mechanism](https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html)
and [profile documentation](https://maven.apache.org/guides/introduction/introduction-to-profiles.html).
Actual artifact identity/version/checksum/closure evidence comes from the exact
Central resources recorded in the manifest and the frozen D.3 model, not generic
claims from those guides.

**STOP after E.0.3 static verification and GitHub publication. No compile retry,
Maven goal, other revision, Sonar/scan, technical-debt measurement, forecasting,
dataset rebuild or Phase5.3 started. Analyzer licensing and dataset-rights gates
remain unresolved and unchanged.**
