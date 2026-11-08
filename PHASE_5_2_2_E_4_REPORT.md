# Phase 5.2.2-E.4 — T+60 static Maven readiness

**PASS_STATIC_T_PLUS_60_READINESS.** The frozen T+60 source and a fresh
753-artifact cache are verified. The exact Commons IO 2.18.0 POM and JAR are the
only two additions to 751 unchanged seeds. No known required static paths remain
missing. The independently derived plan contains 20 verified plugin descriptors.
The repository estimate fits the unchanged 128 MiB tmpfs with a 16 MiB reserve.

**No Maven, Java, build container, compiler, SonarQube, scanner or model ran.**
This is not COMPILE_PASS or FULL_OFFLINE_BUILD_READY. A separate E.4.1 authorization
is required for one actual T+60 compilation. Actual effective model, profiles,
Maven-mediated classpaths, SCM behavior and outputs remain UNKNOWN. The four
previous successful builds remain independently verified and unchanged.

Starting main: `9c582dcf2916b18061885002ad4d136e787d0757`.
Date: 2026-10-19, Africa/Cairo. Scope: E.4 only; one sealed acquisition batch.

## Frozen source and context

| Input | Verified identity |
| --- | --- |
| Repository / offset | apache/commons-cli / T+60 |
| Commit | `aad30eff27ac5c9a13194125226653c6c2826c58` |
| Tree | `d7434665397c8dd8156fff7ecaed29a14feeb951` |
| Historical POM SHA256 | `1c82171f91da0f4aa2994bb367e4c9ef8e65414940100be081715605739d9e0b` |
| Full tracked population | 138 files |
| Production Java population | 36 files, including the help package |
| Parent chain | Commons Parent 78 → Apache Parent 33 |
| Future runtime | Maven 3.9.11 / Temurin 17.0.17+10 / Java release 8 |
| Future properties | maven.test.skip=true; user.home=/tmp; no explicit profiles |
| Actual target effective-POM identity | UNAVAILABLE, null |

Commit/tree bytes, every Git blob ID, source SHA256, path and executable mode were
verified directly against the frozen registry and local Git objects. A new
read-only source export was created outside Git. No historical POM, source file,
Git worktree or prior export was changed. No `.git` metadata was manufactured.
The full source manifest records all 138 identities and the separate 36-source
compiler input population.

The added tracked file relative to T+30 is `.github/pull_request_template.md`,
not production Java. Fourteen production Java files changed:

- `src/main/java/org/apache/commons/cli/BasicParser.java`
- `src/main/java/org/apache/commons/cli/CommandLine.java`
- `src/main/java/org/apache/commons/cli/CommandLineParser.java`
- `src/main/java/org/apache/commons/cli/Converter.java`
- `src/main/java/org/apache/commons/cli/DefaultParser.java`
- `src/main/java/org/apache/commons/cli/GnuParser.java`
- `src/main/java/org/apache/commons/cli/HelpFormatter.java`
- `src/main/java/org/apache/commons/cli/Option.java`
- `src/main/java/org/apache/commons/cli/OptionBuilder.java`
- `src/main/java/org/apache/commons/cli/PosixParser.java`
- `src/main/java/org/apache/commons/cli/TypeHandler.java`
- `src/main/java/org/apache/commons/cli/help/AbstractHelpFormatter.java`
- `src/main/java/org/apache/commons/cli/help/HelpFormatter.java`
- `src/main/java/org/apache/commons/cli/help/Util.java`

The comparison also records changes to the original POM, change log, three GitHub
workflows and CommandLineTest.java. Nothing was selected using numerical debt
outcomes. No T+90 preparation, source export, recovery or compilation occurred.
T+30's 55 class files are not a T+60 acceptance condition; future output identities
must be derived from the original T+60 source and actual compiler evidence.

## Independent model and descriptor comparison

Both static models use their own historical POM/source inventory. No earlier
runtime effective model, active-profile result, compiler classpath or output hash
was substituted for T+60.

| Component | T+30 | T+60 |
| --- | --- | --- |
| Commons Parent / Apache Parent | 78 / 33 | 78 / 33 |
| Project version | 1.10.0-SNAPSHOT | 1.10.0-SNAPSHOT |
| Tracked / production Java files | 137 / 36 | 138 / 36 |
| Commons IO, test scope | 2.17.0 | 2.18.0 |
| JUnit Jupiter / imported BOM | 5.11.2 | 5.11.2 |
| Commons Text, test scope | 1.12.0 | 1.12.0 |
| Mockito, test scope | 4.11.0 | 4.11.0 |
| Enforcer | 3.5.0 | 3.5.0 |
| Artifact / Compiler | 3.5.1 / 3.13.0 | 3.5.1 / 3.13.0 |
| Buildnumber / Resources | 3.2.1 / 3.3.1 | 3.2.1 / 3.3.1 |
| Surefire / CycloneDX descriptors | 3.5.1 / 2.9.0 | 3.5.1 / 2.9.0 |
| Actual compilation | COMPILE_PASS | NOT_EXECUTED |

Parent chains, imported BOMs, dependency management, inherited properties,
profiles, plugin configuration and build/resource sections compare equal under
static inspection. The direct dependency difference is Commons IO 2.18.0. This is
not a claim that actual effective models are equal. The full version inventory
includes managed and reporting/later-phase declarations.

The target's original Artifact Plugin configuration and embedded descriptor select
`deploy` for check-buildplan. All 20 exact plan descriptors were independently
established, rather than requiring the earlier inventory count. Each POM/JAR,
packaging, embedded plugin.xml and pom.properties GAV, original goal, parent and
BOM import was checked against recorded identities. Compile-bound executions
retain Enforcer, RAT, check-buildplan, build-helper, antrun, remote-resources,
Buildnumber, resources and compiler. Later-phase Surefire, Felix, CycloneDX, SPDX,
Moditect, packaging/install/deploy entries remain descriptor evidence only.

The 318 historical compile-candidate references are present; they include duplicate
references and legacy UNKNOWN rows with incomplete transitive lists. They are not
318 independent artifacts or a fully mediated runtime dependency graph. Exact
descriptor default phases reconcile the legacy unspecified Enforcer/JAR phases,
without rewriting the old registration. No changed compile-plugin version required
an additional runtime graph. Successful T+30 execution is reuse evidence only.

All 24 project-profile records retain UNKNOWN_NOT_MAVEN_EVALUATED runtime decisions.
The scoped static checker reports zero blocking metadata issues. This does not
establish actual active profiles. Original compiler/resource/SCM settings remain
unchanged; actual T+60 Buildnumber and detached-SCM behavior are UNKNOWN. Its
original configuration was recorded, not executed.

See [configuration matrix](examples/phase5_2_2_e_4/T_PLUS_30_T_PLUS_60_CONFIGURATION_MATRIX.md),
[descriptor evidence](examples/phase5_2_2_e_4/buildplan_descriptor_verification.json),
[compile candidates](examples/phase5_2_2_e_4/compile_phase_requirements.json) and
[profile/runtime uncertainty](examples/phase5_2_2_e_4/profiles_and_runtime_uncertainty.json).

## Exact dependency recovery

The initial frontier contained only the two requested Commons IO 2.18.0 paths.
Both were obtained from `https://repo.maven.apache.org/maven2/` at their original
coordinates. Approved local sources were checked but supplied no admitted bytes.
Both additions passed authoritative checksum consistency, locally calculated
SHA256, exact POM coordinates/packaging and JAR ZIP structure/CRC verification.
The published checksum sidecars were SHA1; SHA512/SHA256 probes returned 404.
Local SHA256 was calculated for every artifact. Same-origin checksums over TLS do
not establish an independent publisher signature.

| New artifact | Bytes | SHA256 |
| --- | ---: | --- |
| commons-io-2.18.0.pom | 20,032 | `63d96941eb44df9c90d2adb2ad8c3f699c2e065e707045c5daf713fca52bcfca` |
| commons-io-2.18.0.jar | 538,910 | `f3ca0f8d63c40e23a56d54101c60d5edee136b42d84bfb85bc7963093109cf8b` |

Its authoritative parent chain is Commons Parent 78 → Apache Parent 33, already
in the verified seed. Required parent/import/management metadata was rechecked;
no extra missing artifact emerged. Commons IO's own ten dependency declarations
are test-scoped, so their test trees do not propagate into the target's dependency
closure and were not downloaded. Scope, optional flags and exclusions are retained
in the metadata evidence. No alternative version was selected.

All six direct Commons CLI dependency declarations are test-scoped. The conservative
project/test closure contains 14 selected identities with no known missing path.
JUnit 5.11.2, Commons Text 1.12.0 and their required metadata/transitives were reused
from verified artifacts. Static selection respects scope, management, optional
flags and exclusions; actual Maven mediation remains UNKNOWN. Later-plugin runtime
requirements are separately recorded, with no wholesale acquisition of their
optional/later-phase JAR graphs.

The new cache uses independent copies with different inodes for all 751 seeds.
Every old and new hash, exact path, coordinate, recorded checksum provenance,
POM structure and JAR CRC was reverified. No unregistered cache file is present.
The empty final frontier is a static result, not permission to compile or acquire
another batch.

## Determinism correction

The initial read-only repetition exposed a metadata-reporting defect inherited
from a shared helper: per-plugin `metadata_paths` used the difference from a
previously populated global read set. Repeated audits could omit already read
parent POM paths from that diagnostic list. Artifact hashes, parent identities,
goals, missing frontier and all other audit fields were unchanged.

Only the new E.4 `plan_inventory` now gives each plugin its own scoped path tracker.
No earlier helper/report/experiment was modified. A regression fixture verifies
that shared parents appear even after prior cache reads. Two corrected offline
audits are byte-identical, SHA256:
`7f8c13a8ae05e6bc634d9f6f56672e67dd39d39b75627a9a5b4fa8e3d41d2069`.

The original acquisition-source snapshot and manifest are preserved. The published
source differs only in this static reporting function; AST comparison establishes
that transport, resource caps, request accounting and acquisition code are unchanged.
All nontracking audit fields match the original post-acquisition receipt. Initial
and final readiness are both PASS_STATIC_T_PLUS_60_READINESS. The 8-request ledger
was not reopened or resealed; no further request was made. See
[correction receipt](examples/phase5_2_2_e_4/static_tracking_correction.json).

## Resource and cache accounting

| Item | Actual result |
| --- | ---: |
| Verified seed artifacts / additions / total | 751 / 2 / 753 |
| HTTP requests | 8 / 80 |
| Newly transferred response payload | 559,022 / 25,165,824 bytes |
| New artifact payload | 558,942 bytes |
| Checksum 404s / transport failures / retries | 4 / 0 / 0 |
| Acquisition elapsed time | 64.54s / 600s |
| Acquisition peak RSS | 45,200 KiB |
| Offline verification peak RSS | 48,052 KiB |
| Process address-space cap / CPU / workers | 1 GiB / CPU0 / 1 |
| Largest new artifact / cap | 538,910 / 16,777,216 bytes |
| Task storage at static verification / cap | 93,619,625 / 268,435,456 bytes |
| Full candidate payload | 80,688,146 bytes |
| Rounded 4 KiB file allocation | 82,227,200 bytes |
| Directory overhead estimate | 3,366,912 bytes |
| Maven metadata reserve | 16,777,216 bytes |
| Runtime repository estimate | 102,371,328 bytes |
| Original repository tmpfs cap | 134,217,728 bytes (128 MiB) |
| Estimated capacity headroom | 31,846,400 bytes |

Artifact manifest SHA256:
`396219aa616a8724f4a1d00285e04b4ad4f19bc8921e67e0ef6bc79c69c474d7`.
Canonical 753-artifact cache SHA256:
`ce62e9b970dfeeaf397f8ec67774c4c4d2a16a216d89075023e1ac944477a2cf`.
The estimate remains distinct from future live tmpfs usage; no container was
started in E.4. No memory or tmpfs ceiling was raised. Network requests were
flushed/fsynced durably before I/O. HTTPS acquisition had no proxies, redirects,
alternative repositories or automatic retries, and stopped after this one batch.
Accounting includes read response/checksum bodies; unread error bodies, headers
and TLS are excluded. GitHub metadata publication is separate from the sealed
Maven acquisition ledger. Unused budget grants no second batch.

## Tests and preservation

**912 tests passed in each checkout**, zero failures/errors/skips:
22.769s canonical and
24.658s original project. The suite includes
857 previous relevant tests and 55 new E.4 tests. All 54 initial tests passed before
acquisition; one additional test proves the post-acquisition diagnostic correction.
Coverage includes exact 138/36 identities, Commons IO 2.18.0 and reused dependencies,
parent/BOM handling, descriptors, UNKNOWN profiles, provenance and integrity,
request/storage/time limits, durable accounting, symlink/output ownership,
independent copies and all four read-only successful-build auditors.

Preservation PASS covers all four COMPILE_PASS class archives, raw receipts,
source/cache identities and consumed claims; all earlier caches/reports/ledgers;
all 18 registered source states; 56 frozen research bundles and 322 artifacts;
two Phase 5.1 bundles; the SQLite database and model checkpoints; 6,262 user-cache
entries and 75 rehashed reference artifacts. Old SonarQube state/volumes and
unrelated files/containers are unchanged. Four preexisting untracked remediation
files remain untouched. No shared-container change was observed.

Prior request counts remain D=2000, D.1=400, D.2=52, D.3=112, E.0.3=56,
E.0.5=12, E.0.5.1=52, E.1=32, E.2=67, E.3=46. No old claim was reused.
Only read-only daemon GETs inspected existing container/volume metadata; there was
no Docker CLI, container creation/start, server mutation or service stop.
The original project HEAD remains unchanged. New files are mirrored there and
published via a normal main descendant commit from the canonical checkout.

## Artifacts, reproduction and stop

New source: `tools/prepare_tplus60.py`. New tests: `tests/test_tplus60_readiness.py`.
This report and `examples/phase5_2_2_e_4/` provide source/cache manifests, the
configuration matrix, dependency/descriptor closure, compile-phase metadata,
profile/runtime uncertainty, resource/test/preservation receipts and E_4_1_HANDOFF.md.
No production feature, historical source/POM, previous dataset/result or old cache
was rewritten. Downloaded dependencies, full source exports and private logs remain
outside Git.

Private cache: `/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_4/2026-10-19/recovery-1/repository`.
Private source: `/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_4/2026-10-19/source`.
The recovery directory is consumed and must not be resumed.

Read-only audit from the original project directory:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=150 --fsize=33554432 -- \
  .venv-forecast/bin/python -m tools.prepare_tplus60 --audit-only \
  --output /home/hp/tst/research/forecasting_mvp/phase5_2_2_e_4/2026-10-19/recovery-1
```

Deterministic focused tests:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_tplus60_readiness.py
```

[Verification](examples/phase5_2_2_e_4/verification.json) lists the full 28-file
regression command. [Preservation](examples/phase5_2_2_e_4/preservation.json),
[source states](examples/phase5_2_2_e_4/all_source_states_preservation.json) and
[four successful builds](examples/phase5_2_2_e_4/successful_builds_preservation.json)
record the independent checks.

**STOP after E.4 publication.** The
[E.4.1 handoff](examples/phase5_2_2_e_4/E_4_1_HANDOFF.md) requires separate
authorization for one T+60 compile using the existing 2 GiB container, 768 MiB heap,
1 CPU, 128 MiB repository tmpfs and 240s Maven timeout, with live resource admission.
Do not compile now, retry acquisition, prepare T+90, start a server/scanner, collect
debt measurements, run forecasting, admit data or begin Phase 5.3. Licensing and
derived-dataset rights remain unresolved and unchanged.
