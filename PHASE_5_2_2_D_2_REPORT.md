# Phase 5.2.2-D.2 — Finish the known Maven dependency frontier

Date: **2026-10-16**. Verified starting `main`:
`e57cfe77241cdda1130ac1a7fd88ee4dd4f8a879`.

**PASS_STATIC_CLOSURE_COMPLETE.** All known candidates in the unchanged static
compile projection are present. The exact missing-path frontier fell from two
files to zero after acquiring 13 artifacts in 52 requests. **Offline Java build
readiness remains UNKNOWN**, and Maven effective-model verification is pending.
No actual Maven execution, final dependency mediation, conditional-branch
completeness or compilation success is claimed.

Task D.2 ran one bounded acquisition attempt and stopped when the known frontier
was empty. No additional batch, Task C/E/F, project goal, historical compilation,
downloaded JAR/plugin execution, Sonar server/scanner, training/inference or
experimental-data operation started. No historical POM, enforcer, profile,
analyzer license decision or scientific admission policy changed.

## Actual resources and accounting

| Evidence | Actual result |
| --- | --- |
| Seed cache | 611 independently verified D.1 artifact copies; zero seed downloads |
| New artifacts | 13: 6 POMs and 7 JARs |
| New cache total | 624 verified artifacts |
| D.2 HTTP requests | 52/100, including checksum probes/retries |
| D.2 response payloads read | 715,695 bytes (~0.68 MiB) of 32 MiB; excludes headers/TLS/unread404 bodies |
| Per-artifact cap | 32 MiB |
| Peak acquisition-process RSS | 62,456 KiB (~61.00 MiB) |
| Enforced address space | 1,073,741,824 bytes |
| Enforced CPU affinity | CPU 0, one sequential worker |
| Acquisition plus offline checkpoints | 68.82 seconds; 600-second outer/phase limit |
| New cache plus internal evidence | 66,653,980 bytes (~63.57 MiB), below 256 MiB |
| Earlier ledgers | Task D: 2,000 requests; D.1: 400 requests; both unchanged |

Initial available RAM was 9,793,580 KiB; free disk was 35,750,789,120 bytes.
No unrelated service was stopped. Network operations have 15-second timeouts,
up to three counted same-URL connection retries and cumulative request/response
budgets. CPU time and per-file output sizes are also bounded by `prlimit`.
Disk is checked before copying seeds, before new downloads and after sealing.
Read-only audits and GitHub publication are separate from new Maven acquisition;
they do not reset a ledger or authorize another acquisition attempt.

## Seed integrity and provenance

The private D.1 manifest exactly matched its published JSON object. All 611 files
were verified against SHA256, recorded same-origin checksums, POM coordinates or
JAR ZIP/CRC integrity before copying. Destination bytes were rehashed and distinct
inodes confirmed independent copies. A fresh directory outside Git was required;
all earlier cache roots are protected from nesting/overwrite. The seeded audit
reproduced exactly the two frozen missing files at zero network requests.

Only `https://repo.maven.apache.org/maven2/` was allowed. Inherited proxies and
redirects were disabled. Exact immutable release coordinates were used, without
ranges, latest-version lookup, SNAPSHOT artifacts or version substitution.
All 13 new artifacts were verified before admission. Local SHA256, source URL,
byte count, coordinates and repository checksum are retained in
[dependency_manifest.json](examples/phase5_2_2_d_2/dependency_manifest.json).
SHA512/SHA256 sidecars are preferred; SHA1 was used where that is the available
sidecar. HTTPS and same-origin checksums are not an independent publisher-signature
claim. Third-party bytes remain outside Git and were never executed.

## Exact frontier and exposed dependencies

Before:

```text
commons-logging/commons-logging/1.0.3/commons-logging-1.0.3.pom
commons-digester/commons-digester/1.6/commons-digester-1.6.jar
```

The two exact files took eight requests. The newly readable legacy Commons
Logging POM exposed five initial dependency candidates, followed by additional
POM/JAR requirements as the graph expanded. The unchanged model was rerun offline
after each increment; no downloaded code or Maven goals were used.

| Checkpoint | D.2 requests | New verified artifacts | Missing paths |
| --- | ---: | ---: | ---: |
|1: SEEDED_OFFLINE|0|0|2|
|2: AFTER_EXACT_FRONTIER|8|2|5|
|3: AFTER_EXACT_FRONTIER|28|7|4|
|4: AFTER_EXACT_FRONTIER|44|11|1|
|5: AFTER_EXACT_FRONTIER|48|12|1|
|6: AFTER_EXACT_FRONTIER|52|13|0|
|7: FINAL_OFFLINE|52|13|0|

After: **empty**. There are no known missing static candidates, unresolved
non-profile dependencies or unresolved plugin descriptors in this projection.
The [comparison](examples/phase5_2_2_d_2/frontier_comparison.json) preserves the
exact before/after identities and every newly exposed checkpoint frontier.

New SHA256 evidence:

| Exact artifact path | SHA256 |
| --- | --- |
|`commons-beanutils/commons-beanutils/1.6/commons-beanutils-1.6.jar`|`77d8fe257bd9b186cce1261bea2364384ae861b1999815d549121710b0f89407`|
|`commons-beanutils/commons-beanutils/1.6/commons-beanutils-1.6.pom`|`f1309fdb6c64284485bc39188e55d0a30ddbb9311e4d4b6ee08bb038fa4b556d`|
|`commons-collections/commons-collections/2.0/commons-collections-2.0.jar`|`b5d8a9f671a4e6698d553d0ec98d33ba70358e9b2180c845c88fc7176ddfbb1e`|
|`commons-collections/commons-collections/2.0/commons-collections-2.0.pom`|`dafa5cd143542dca7ec092ef4c670a3fd285dfc02b00e790cbe25687bef513cc`|
|`commons-collections/commons-collections/2.1/commons-collections-2.1.jar`|`443c2f6379ea2d9300af4733a3ad561032139c5a7890b5876c0b33212dd478f5`|
|`commons-collections/commons-collections/2.1/commons-collections-2.1.pom`|`f8a93d50bfaf6fc0720eee8fde6e8fde20da33238ba296e9b1b7cba50ca6d772`|
|`commons-digester/commons-digester/1.6/commons-digester-1.6.jar`|`4040c63d0dba10ce048ec02bcaf67092f58ac5662ae1ba7b050f77cf86265249`|
|`commons-logging/commons-logging/1.0.3/commons-logging-1.0.3.jar`|`bcfa023daea8525d6db029ea82e8f58dbf1a06006db6526d9f984dbf215d8a75`|
|`commons-logging/commons-logging/1.0.3/commons-logging-1.0.3.pom`|`8c23c6e92f1df7f58b455cd2caa009dcc87a2fe64976e6ce461522e635aea41e`|
|`commons-logging/commons-logging/1.0/commons-logging-1.0.jar`|`45c22f543d2b5d0c20f2cac58b9cc0c8afedc273b6fc77c7545b3ad0b0041459`|
|`commons-logging/commons-logging/1.0/commons-logging-1.0.pom`|`52b3caa59ca5e8f6279421ecb517a0b24571d666ea86bb145462076760026a6f`|
|`xml-apis/xml-apis/1.0.b2/xml-apis-1.0.b2.jar`|`8232f3482c346d843e5e3fb361055771c1acc105b6d8a189eb9018c55948cf9f`|
|`xml-apis/xml-apis/1.0.b2/xml-apis-1.0.b2.pom`|`7bc38e7a0f8ca20b0caed607e00cbb144dc8d006ebec4aa193f55dcf391bad50`|

The static candidate union retains declared historical versions, including both
Commons Collections 2.0/2.1 and Commons Logging 1.0/1.0.3 where different paths
require them. This is not a claim that Maven mediation places all versions on
one effective classpath. Old namespace-free POMs are read using the existing
normalization code; raw POM bytes are preserved.

## Per-revision readiness and profiles

All six frozen POM, commit and full-tree identities were re-read and matched
Phase 5.2.1. Their original Java 1.8 source/target declarations and parent
versions remain unchanged. The existing static context is Maven 3.9.11,
Temurin 17.0.17+10, `maven.test.skip=true`, `maven.compiler.release=8`, no explicit
profiles and no user Maven settings. This context is an audit input, not an
executed build or authorization to modify it.

| Offset days | Frozen Commons CLI commit | Parent | UNKNOWN profile records | Missing files | Offline build |
| ---: | --- | ---: | ---: | ---: | --- |
|-90|`e1529b546d9696192f4de52152777403b4a01b39`|71|21|0|UNKNOWN|
|-30|`fb6293fcd6a9b55ac8ecb550af6572daaed18fa1`|74|19|0|UNKNOWN|
|0|`4ff0d4adbc2161677e71050ba23c152831f6ad83`|76|20|0|UNKNOWN|
|30|`7ddf691ac2afbda7473c0d07f1f4e7ae1e69e47b`|78|20|0|UNKNOWN|
|60|`aad30eff27ac5c9a13194125226653c6c2826c58`|78|20|0|UNKNOWN|
|90|`af2b3e72a552cfb2a902556469868763ddea3638`|78|20|0|UNKNOWN|

Each revision has `static_closure_status=PASS_STATIC_CLOSURE_COMPLETE`,
`effective_model_verification=PENDING` and `offline_build_readiness=UNKNOWN`.
The [matrix](examples/phase5_2_2_d_2/compile_readiness_matrix.json) keeps plugin
versions, required-through-compile decisions, declared/default phases and source
hashes. The zero frontier does not close the runtime/build gate.

Artifact roles were re-evaluated without changing the old audit algorithms:

- 378 required static compile candidate files, all present.
- 15 distinct conditional profile sources, explicitly UNKNOWN.
- 10 later-phase descriptor files and 161 parent/BOM/configuration metadata files.
- 725 optional/non-runtime declaration records, kept separate from required
  runtime traversal; these are declarations, not distinct artifact downloads.
- 75 cached seed files unused in the current projection.

The resources, enforcer and buildnumber plugin projections have no known missing
files. Maven JAR `jar`/`test-jar` goals remain later-phase (`package`) descriptor
evidence; their runtime dependencies were not automatically acquired as compile
requirements. No optional library was promoted to required merely to fill a cache.

[unknown_profile_evidence.json](examples/phase5_2_2_d_2/unknown_profile_evidence.json)
records each profile's exact verified upstream POM hash, activation structure,
raw coordinate declarations and unresolved reason. These include OS/file conditions
and the literal `[9` JDK activation. UNKNOWN was preserved; there was no attempt
to infer activation from host state, silently disable a profile or run Maven to
resolve it. Reproducible source evidence lives in the hash-verified new cache.

## Verification and preservation

**283 tests passed in each checkout**, including 17 new D.2 cases, with zero
failures or skips. They verify immutable seed copies and prior ledgers, nested
cache rejection, checksum and coordinate failures, the 100th-request boundary,
32 MiB payload/artifact caps, disk limits, redirects/retries, read-only accounting,
static completeness versus UNKNOWN build readiness, all six frozen identities
and existing Task A/B/D/D.1 and scope/foundation behavior.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=120 --fsize=16777216 -- \
  /home/hp/tst/td_pipeline_module_level/td_pipeline/.venv-forecast/bin/python \
  -m pytest -q -p no:cacheprovider \
  tests/test_phase5_2_2_d_2_recovery.py tests/test_phase5_2_2_d_1_continuation.py \
  tests/test_phase5_2_2_d_recovery.py tests/test_phase5_2_2_b_probes.py \
  tests/test_phase5_2_2_a_review.py tests/test_production_scope_readiness.py \
  tests/test_multilanguage_preflight.py tests/test_multilanguage_foundation.py
```

Tests use fixtures and recorded evidence; they do not contact Maven Central,
start containers, execute downloaded code or run models.
[Verification receipt](examples/phase5_2_2_d_2/verification.json) binds the tested
source, prior references, preservation checks and evidence hashes.

The independent read-only audit reproduced the final private audit byte-for-byte:
`94c0c37683b8a2526417a116593f739dfac781ce9dac4790879d8964657f35b0`. It reverified all 624 cache artifacts, without a network-capable
transport, acquisition request or ledger write. Public large objects use compact
deterministic JSON; semantic equality and both private/public byte hashes are
recorded in verification. The metadata bundle has its own SHA256 manifest.

Preservation PASS: 423 pre-existing central files, 334 working-project files,
four unfinished remediation files, all 1,378 Task D cache files, all 615 D.1 cache
files, 56 frozen experiment bundles/322 artifacts, both Phase 5.1 bundles, the
source SQLite and Chronos checkpoint. The user Maven caches retain 5,878 entries;
75 prior reference artifacts were also rehashed. Old Sonar container identity,
stopped state and mount mappings remain unchanged. Task B's Jansi/noexec warning
was retained without weakening isolation. No rights/permission approval was inferred.
Original working `main` remains at `2e7999ea436d49449652e6c52e9066ef2e514419`.

## Files, reproduction and next actions

New files: `tools/recover_phase5_2_2_d_2.py`, its targeted test module, this report
and the metadata-only `examples/phase5_2_2_d_2/` bundle. All Task D/D.1 source,
reports and evidence remain byte-identical.

The new cache is outside Git:

```text
/home/hp/tst/research/forecasting_mvp/phase5_2_2_d_2/2026-10-16/recovery-1/
  repository/                 # 624 independently verified artifacts
  dependency_manifest.json    # D.2-only52-request ledger linked to D/D.1
  requirements.json
  checkpoints.json
  frontier_comparison.json
  artifact_classification.json
  compile_readiness_matrix.json
```

The once-executed acquisition used `timeout 600s taskset -c 0` with
`prlimit --as=1073741824 --cpu=400 --fsize=33554432` and a fresh `--output`.
Do not rerun acquisition or create an additional batch automatically. Safe
read-only reproduction is:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
TD522D2_PY="$PWD/.venv-forecast/bin/python"
TD522D2_CACHE=/home/hp/tst/research/forecasting_mvp/phase5_2_2_d_2/2026-10-16/recovery-1
PYTHONDONTWRITEBYTECODE=1 timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=120 --fsize=33554432 -- \
  "$TD522D2_PY" -m tools.recover_phase5_2_2_d_2 \
  --output "$TD522D2_CACHE" --audit-only > /tmp/td522d2-readonly-audit.json
```

No known missing artifact remains to acquire. The next gate is separately
authorized verification of applicable profiles, Maven effective-model semantics
and final classpaths; historical compilation would still be separate authorized
work. Do not treat static closure completeness as proof that this sandbox can
build successfully or that analyzer-derived data is licensed for the research.

Only safe source, tests, reports and small provenance/diagnostic metadata are
published to GitHub using a normal descendant commit, followed by remote byte
verification. No dependency POM/JAR, cache, credential, dataset or weight is uploaded.

**STOP after Task D.2 publication. No Task C/E/F or additional acquisition batch.**
