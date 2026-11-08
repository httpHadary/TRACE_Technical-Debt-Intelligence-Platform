# Phase 5.2.2-E.5 — Final T+90 static Maven readiness

**PASS_STATIC_T_PLUS_90_READINESS.** The frozen T+90 source export and a new
758-artifact cache are verified. All known required static paths are present;
20 original build-plan plugin descriptors are verified. The conservative cache
estimate fits the unchanged 128 MiB repository tmpfs.

**No Maven, Java, container, compiler, scanner or forecasting model ran.**
T+90 has not been compiled. Five of six historical revisions retain independently
verified COMPILE_PASS; E.5 does not finish the six-revision compilation gate.
Actual T+90 effective model, active profiles, mediated classpaths, SCM behavior and
compiler outputs remain UNKNOWN. E.5.1 requires separate explicit authorization.

Starting main: `a575071b5a2dc30b3844542293248ca189b58b88`.
Date: 2026-10-19, Africa/Cairo. One sealed acquisition batch; static verification only.

## Frozen target and independent source verification

| Input | Verified value |
| --- | --- |
| Repository / offset | apache/commons-cli / T+90 |
| Commit | `af2b3e72a552cfb2a902556469868763ddea3638` |
| Tree | `0d773516c1c7bb0a371b2af6e084b62ef2d36546` |
| Original POM SHA256 | `87c8ed93cb21deedb52b826d520931bc175e24e5ee48643c6a21ed154c62324b` |
| Tracked / production Java files | 138 / 36 |
| Project parent chain | Commons Parent 78 → Apache Parent 33 |
| Future runtime | Maven 3.9.11 / Temurin 17.0.17+10 / Java release 8 |
| Future properties | maven.test.skip=true; no explicitly selected profiles |
| Actual effective POM / class population | UNKNOWN / UNKNOWN |

Commit/tree object bytes, every registered path, Git blob, source SHA256 and mode
were checked directly against frozen Git objects and the versioned registry.
The new source export is read-only and outside Git. No POM/source/worktree was
modified and no Git metadata was manufactured. All 18 registered source states
were independently rechecked.

Relative to T+60 there are 11 changed tracked paths, no added/removed paths and no
mode changes. The two changed production files are CommandLine.java and Option.java.
The four changed test files are ApplicationTest.java, CommandLineTest.java,
HelpFormatterTest.java and OptionsTest.java. Three GitHub workflows, pom.xml and
src/changes/changes.xml also changed. There is no changed non-Java production file.
The count of 36 Java sources was verified independently, including the help package.
No class count, bytecode identity or earlier effective model is transferred to T+90.

## Differential static model and build plan

| Component | T+60 | T+90 |
| --- | --- | --- |
| Commons Text, test scope | 1.12.0 | 1.13.0 |
| Commons IO, test scope | 2.18.0 | 2.18.0 |
| JUnit Jupiter / imported BOM | 5.11.2 | 5.11.2 |
| Mockito, test scope | 4.11.0 | 4.11.0 |
| Parent chain | Commons78 / Apache33 | Commons78 / Apache33 |
| Enforcer / RAT | 3.5.0 / 0.16.1 | 3.5.0 / 0.16.1 |
| Artifact / Compiler | 3.5.1 / 3.13.0 | 3.5.1 / 3.13.0 |
| Buildnumber / Resources | 3.2.1 / 3.3.1 | 3.2.1 / 3.3.1 |
| Surefire / CycloneDX descriptors | 3.5.1 / 2.9.0 | 3.5.1 / 2.9.0 |
| Actual compilation | COMPILE_PASS | NOT_EXECUTED |

Each model uses its own frozen POM and inventory. Parent/import/management,
inherited property and resource-section comparisons are recorded. The original
Antrun declaration changes from literal 3.1.0 to the existing inherited property
`${version.maven-antrun-plugin}`, statically resolving to 3.1.0. Its XML was not
silently treated as identical. No compile-bound plugin version changed.
Actual effective-model equivalence is not claimed.

The independently derived original plan contains 20 descriptors. Exact GAV,
packaging, plugin.xml, pom.properties, goal names, parent metadata and imports
were verified. The original check-buildplan descriptor defaults to deploy;
that selection remains unchanged. Compile-bound candidates preserve Enforcer,
RAT, check-buildplan, Build-helper, Antrun, Remote-resources, Buildnumber,
Resources and Compiler. Later Surefire, Felix, CycloneDX, SPDX, Moditect,
packaging/install/deploy goals are descriptor evidence only, never execution.

The 318 registered compile-candidate references are present, including repeated
references and legacy unspecified-phase records. Exact target descriptors
reconcile those original phase candidates without rewriting the old registration.
They are not 318 independent artifacts or a Maven-mediated runtime classpath.
Successful T+60 execution supports reuse of unchanged plugin versions, but does
not establish T+90 runtime classpath or original detached-SCM behavior.
All 24 project profile candidates retain UNKNOWN actual activation decisions.

See [configuration matrix](examples/phase5_2_2_e_5/T_PLUS_60_T_PLUS_90_CONFIGURATION_MATRIX.md),
[descriptor verification](examples/phase5_2_2_e_5/buildplan_descriptor_verification.json)
and [compile requirements](examples/phase5_2_2_e_5/compile_phase_requirements.json).

## Exact recovery and transitive metadata

Both original missing Commons Text 1.13.0 paths were resolved. Its nonoptional
compile dependency requires Commons Lang 3.17.0, whose own parent is Commons
Parent73 → Apache33. Thus the complete addition is five artifacts, rather than
only the two requested roots:

| Added artifact | Bytes | SHA256 |
| --- | ---: | --- |
| commons-lang3-3.17.0.jar | 673,587 | `6ee731df5c8e5a2976a1ca023b6bb320ea8d3539fbe64c8a1d5cb765127c33b4` |
| commons-lang3-3.17.0.pom | 31,256 | `351c6e4940e939b1f330df47f60f13ba383db81ee008181af541f3a2a6d2a56c` |
| commons-parent-73.pom | 77,692 | `4ed44560b07f8448479dfd1e83a422ba4e83e60b36e51b2871ac502a6d5c1bea` |
| commons-text-1.13.0.jar | 257,863 | `1e323a501127df78ed0987f345d69d65d0ea7fa3d4fb5b3f84aaeba3a8b20f38` |
| commons-text-1.13.0.pom | 23,327 | `d46614bdca6d1195c333ba9f730cd08585c4f332a43ea7b90b6035ad804871d8` |

Commons Text's parent is Commons78 → Apache33, with JUnit BOM5.11.2 metadata.
Commons Lang3.17.0 uses Commons73 → Apache33 and JUnit BOM5.11.0 metadata; the latter
was already verified in the seed. Existing Commons IO2.18.0, JUnit5.11.2 and Mockito
identities were reverified and reused without substitution. All six direct target
dependencies are test-scoped. The conservative project closure selects 14 identities,
retains scopes/exclusions/optional flags and has no known missing path.

The two Commons Text files were downloaded. The two Commons Lang files and
Commons Parent73 POM came from approved local sources, admitted only after fresh
Central checksum consistency and exact-coordinate/integrity verification.
Every new POM was parsed; every JAR passed ZIP/CRC checks. All 753 old artifacts
were independently copied with different inodes and reverified, with no extra
unregistered cache files. All 758 recorded paths/hashes/provenance were rechecked.

The allowlisted origin was https://repo.maven.apache.org/maven2/ only. SHA512 and
SHA256 sidecar probes returned ten 404s; published SHA1 consistency was verified,
and SHA256 calculated locally. Same-origin checksums over TLS are not independent
publisher signatures. There were no redirects, proxies, automatic retries,
artifact execution or broad acquisition of later-plugin runtime trees.

## Conservative profile qualification

The sealed acquisition's initial receipt is **PARTIAL**, preserved verbatim in
[initial frontier](examples/phase5_2_2_e_5/initial_frontier_comparison.json). Its
missing-path list was already empty. The static checker flagged Commons Text's
java-8-10, java-11-21 and java-22-up dependency profiles without scope analysis.

A new fail-closed proof inspects all three profiles and their inheritance layers.
They declare only Commons Text's own test-scoped dependency additions. The changed
Mockito/GraalVM properties and any aliases cannot change a non-test dependency,
managed dependency, parent or artifact coordinate, or a relevant activation
consumer. Remote build/test configuration is not inherited by Commons CLI.
Profile activation remains UNKNOWN; no JDK activation outcome was guessed.
Negative tests reject runtime dependencies, dependency management, property aliases,
inherited coordinate consumers, activation consumers, unknown sections and extra
profiles. This proves nonpropagation for this metadata scope, not a Maven model.

Final qualification is PASS_STATIC_T_PLUS_90_READINESS with zero blocking metadata
issues. Initial receipt, raw audits, artifact manifest and request ledger remain
byte-identical. Only the new E.5 scope-classification function and its call changed
after acquisition; AST comparison verifies unchanged transport, budgets and
acquisition logic. No prior phase code or report was rewritten. No further
request occurred. [Profile proof](examples/phase5_2_2_e_5/profile_scope_verification.json).

Two offline audits are byte-identical, SHA256:
`de35524f1fec0e76acf68c788edacc10f67c1889bb894ee3e45cf3ef3f3a675d`.
The actual Maven profile/classpath/model limitations are separately retained in
[uncertainty evidence](examples/phase5_2_2_e_5/profiles_and_runtime_uncertainty.json).

## Resource and cache accounting

| Item | Measured or conservatively estimated value |
| --- | ---: |
| Seeds / additions / final artifacts | 753 / 5 / 758 |
| HTTP requests, including failed probes | 17 / 80 |
| New response payload / limit | 281,390 / 25,165,824 bytes |
| Added artifact payload, including verified local bytes | 1,063,725 bytes |
| Checksum 404s / transport failures / automatic retries | 10 / 0 / 0 |
| Acquisition elapsed / cap | 68.44s / 600s |
| Acquisition peak RSS | 45,156 KiB |
| Static audit peak RSS | 45,772 KiB |
| Process address space / CPU affinity / workers | 1 GiB / CPU0 / 1 |
| Task storage at static verification / cap | 94,982,602 / 268,435,456 bytes |
| Candidate artifact payload | 81,751,871 bytes |
| Rounded 4 KiB file allocation | 83,296,256 bytes |
| Directory overhead estimate | 3,379,200 bytes |
| Maven metadata reserve | 16,777,216 bytes |
| Future repository estimate | 103,452,672 bytes |
| Unchanged tmpfs cap | 134,217,728 bytes |
| Estimated headroom | 30,765,056 bytes |

Before snapshot: 9,154,469,888 available RAM bytes and 15,257,423,872 free disk bytes;
no running containers. Final static verification: 9,276,452,864
available RAM bytes and 15,337,668,608 free disk bytes. Final selected
Java/Maven/Sonar process-name inspection found none. These are point observations,
not continuous shared-host workload telemetry. The acquisition used kernel
address-space/CPU bounds; the storage, response, request, artifact and wall-time
budgets were enforced. The cache estimate is not an actual future tmpfs reading.
HTTP accounting includes response/checksum payloads; unread error bodies,
headers/TLS framing and separately authorized GitHub publication are excluded.
The 17-request ledger is sealed; no additional batch is authorized.

Full manifest SHA256: `eb471e18cca6828bb2abbe2273184faaa693298807363b0280630cb180a6adba`.
Canonical cache SHA256: `df9f176ceeea2f165cbf463dd3eb43675741b0932d1134c756386f0f7259462d`.
Private repository: `/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_5/2026-10-19/recovery-1/repository`.
Private export: `/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_5/2026-10-19/source`.
Binaries, source payloads and private execution files remain outside Git.

## Tests and preservation

Before acquisition, 57 policy/integrity tests passed. The final suite contains
69 E.5 tests, including negative scope-proof and real sanitized evidence checks.
All 1,049 applicable regressions passed in each checkout: no failures/errors/skips.
Central runtime 23.911s; original project runtime
24.083s. The authoritative test-file list,
commands and log/JUnit hashes are in [verification.json](examples/phase5_2_2_e_5/verification.json).

Reproduce static inspection without acquisition:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s taskset -c 0 prlimit --as=1073741824 --cpu=150 --fsize=33554432 -- \
  .venv-forecast/bin/python tools/prepare_tplus90.py --audit-only \
  --output /home/hp/tst/research/forecasting_mvp/phase5_2_2_e_5/2026-10-19/recovery-1
PYTHONDONTWRITEBYTECODE=1 timeout 60s taskset -c 0 \
  prlimit --as=1073741824 --cpu=45 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_tplus90_readiness.py
```

The acquisition entry point is non-resumable and refuses the existing owned output.
Do not rerun it or create another batch without authorization. The published adapter
includes the documented post-acquisition scope proof; the private acquisition-source
snapshot preserves the exact originally executed code.

Read-only auditors independently reverified T−90 E.2.1, T−30 E.1.1, T0 E.0.6,
T+30 E.3.1 and T+60 E.4.1, their class archives, exit/lifecycle evidence, input
identities and consumed claims. All previous task directory files were rehashed.
All request ledgers remain unchanged: D2000, D.1 400, D.2 52, D.3 112,
E.0.3 56, E.0.5 12, E.0.5.1 52, E.1 32, E.2 67, E.3 46, E.4 8.

Preservation passed for all 18 registered source states, 56 frozen experiment
bundles / 322 artifacts, both Phase5.1 bundles, database/checkpoint hashes,
old caches/claims and original source/POM identities. User Maven cache metadata
was checked for 6,262 entries and the 75 earlier reference artifacts rehashed.
Original SonarQube container state/mounts/volume metadata, preexisting unrelated
containers, four unrelated untracked files and all preexisting tracked content
remain unchanged. No service was stopped, modified or restored. These inspections
do not claim byte-level hashing of live SonarQube volume contents.

## Changes, publication and next gate

New source: tools/prepare_tplus90.py. New tests: tests/test_tplus90_readiness.py.
New report and sanitized evidence: this file and examples/phase5_2_2_e_5/.
No existing tracked file is modified. Publication uses the canonical main checkout
at /home/hp/tst/TechDebt360-MVP, preserving the original project's older HEAD and
unrelated work; the new files are mirrored into the requested project directory.
The normal descendant commit must preserve all 821 prior remote blobs. No force
push, dependency binary, historical source export, raw log or secret is published.
Post-push verification is retained in the private github_publication_receipt.json.

[The E.5.1 handoff](examples/phase5_2_2_e_5/E_5_1_HANDOFF.md) records the exact
758-artifact identity, independent source population, original offline command,
resource admission and separate one-attempt ownership requirements. E.5.1 has
**not** been executed or authorized by this phase. The six-state compilation gate
remains five completed, one pending; no collection/data-admission gate is cleared.
Analyzer licensing and derived-dataset rights remain **UNRESOLVED_UNCHANGED**.

E.5 ends here: no compilation, extra acquisition, scanner, debt collection,
forecasting, dataset admission or Phase5.3.
