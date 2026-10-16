# Phase 5.2.2-D.1 — Targeted Maven recovery continuation

Date: **2026-10-16**. Verified base `main`:
`8be4c79ab02f67d53bbefa597df56c65f4f97055`.

**Task D.1 PARTIAL. New batch safely stopped at400 requests. Offline build
readiness BLOCKED for all six revisions.**21 of Task D's22 original missing
paths are resolved. The final frontier has two files:one original missing POM
and one newly exposed JAR. Missing POMs and UNKNOWN profiles can expose additional
requirements; two files are not a proven complete remaining effective graph.

No Task C/E/F, Maven goal, historical build, downloaded-JAR execution, application,
Sonar server/scanner, model training/inference or dataset operation was started.
No rights, license or dataset permission was assumed. Task B's Jansi/noexec warning
and all previous experiments remain unchanged.

## What was verified and acquired

| Evidence | Actual result |
| --- | --- |
| Independently verified seed copies |509;0 seed downloads |
| Newly acquired artifacts |102:59 POMs and43 JARs |
| Total verified cache artifacts |611 |
| New Maven Central HTTP requests |400/400, including retries and checksum404 probes |
| Newly transferred response payloads |11,277,676 bytes (~10.76MiB), below96MiB |
| Largest allowed individual artifact |32MiB |
| Peak acquisition-process RSS |71,328KiB (~69.66MiB) |
| Enforced address-space limit |1,073,741,824 bytes |
| Enforced affinity |CPU0; one sequential acquisition worker |
| Acquisition and checkpoint wall time |177.07s;900s phase/outer timeout |
| New cache plus evidence storage at seal |65,458,810 bytes (~62.43MiB), below352MiB |
| Original Task D accounting |2,000 requests retained byte-for-byte; not reset or extended |

The initial host capture had7,076,896KiB available RAM and36,793,688,064 free disk
bytes. No unrelated process/service was stopped. One batch ran; no second batch
was authorized or started after the cap. Network acquisition stopped before any
401st request. Requests to publish/verify the explicitly authorized GitHub commit
are separate from this Maven artifact-acquisition ledger.

The original Task D manifest was checked against its published inventory. Every
seed file was independently rehashed, checked against its recorded repository
checksum, validated as coordinate-consistent POM XML or CRC-valid JAR, copied
without hard links, and rehashed at its destination. The first offline audit
reproduced the exact frozen22-file frontier at **zero network requests**.

Every new release uses the same allowlisted
`https://repo.maven.apache.org/maven2/` endpoint. Redirects and inherited proxies
are disabled. Checksums prefer SHA512, then SHA256, then SHA1 when only that
sidecar exists; local SHA256 is always recorded. HTTPS plus same-origin checksums
is not claimed as independent publisher-signature authentication. No version
substitution, SNAPSHOT dependency, metadata-based latest selection or POM rewrite
was used. Existing verified paths return local bytes without a request.

## Targeted collection and actual descriptor findings

| Checkpoint | Cumulative new requests | New verified artifacts | Offline missing frontier |
| --- | ---: | ---: | ---: |
|SEEDED_OFFLINE|0|0|22|
|COMPILE_DESCRIPTORS|38|10|30|
|JAR_DESCRIPTOR_ONLY|46|12|29|
|CLOSURE_maven-resources-plugin|64|17|27|
|CLOSURE_maven-enforcer-plugin|100|26|25|
|CLOSURE_buildnumber-maven-plugin|388|99|4|
|PRIORITY_CLOSURES_FINISHED|388|99|4|
|FINAL_OFFLINE|400|102|2|

The three compile-priority descriptors were acquired first. The JAR descriptor
was then inspected without fetching its runtime closure as a compile requirement:

- Resources3.3.1:`resources` binds to `process-resources`.
- Enforcer3.5.0:`enforce` binds to `validate`.
- Buildnumber3.2.1:`create` defaults to `initialize`. Registered inherited execution
  phases still take precedence; the pinned roots bind their buildnumber execution
  to `generate-resources`.
- JAR3.4.2:`jar` and `test-jar` bind to `package`; `help` has no bound phase.
  Actual pinned execution/descriptor evidence places those JAR goals after compile.

No goal was executed. Parent chains, imported BOMs, plugin dependencies and
configured dependency overrides were read as data. Independent final read-only
checks found **no known missing artifacts or non-profile errors** in the three
priority plugin projections. Buildnumber still has two unknown profile issues;
this is a static projection result, not a Maven-effective-model or build PASS.
See [priority_plugin_readiness.json](examples/phase5_2_2_d_1/priority_plugin_readiness.json).

## Before/after frontier and exact next actions

Resolved21/22 original paths. The remaining original path is:

```text
commons-logging/commons-logging/1.0.3/commons-logging-1.0.3.pom
```

The newly exposed remaining path is:

```text
commons-digester/commons-digester/1.6/commons-digester-1.6.jar
```

Neither is declared unavailable:there is no artifact404 evidence for these paths.
They are **not verified within the exhausted budget**. A response whose checksum
cannot be obtained within the budget is not admitted as a verified artifact.
The exact next actions, requiring separate authorization, are:

1. Acquire those two exact paths and checksums from the same allowlist in a new,
   independently accounted bounded continuation. Preserve both exhausted ledgers.
2. Read the newly available Commons Logging1.0.3 POM and expand its exact parents,
   imports and applicable transitive candidates. Do not assume the two-file list
   contains all descendants. Reject or isolate unresolved versions and conditions.
3. Re-run the offline six-revision audit after each bounded acquisition step.
   Confirm applicability of the remaining UNKNOWN profiles under explicitly
   authorized work. Do not silently disable profiles or weaken enforcers.
4. Keep offline build readiness BLOCKED/UNKNOWN until required artifacts and
   applicable profiles are sufficiently established. Any historical compilation
   remains a separately authorized later task; Task D.1 does not start it.

Exact source URLs are recorded in the
[readiness manifest](examples/phase5_2_2_d_1/readiness_manifest.json).
The [comparison](examples/phase5_2_2_d_1/frontier_comparison.json) retains all22
original paths, resolved identities, new frontier, descriptor findings and the
budget-stop reason.

## Per-revision compile-dependency readiness

| Offset days | Frozen commit | Parent | UNKNOWN profile records | Missing paths | Offline build |
| ---: | --- | ---: | ---: | ---: | --- |
|-90|`e1529b546d9696192f4de52152777403b4a01b39`|71|21|2|BLOCKED|
|-30|`fb6293fcd6a9b55ac8ecb550af6572daaed18fa1`|74|19|2|BLOCKED|
|0|`4ff0d4adbc2161677e71050ba23c152831f6ad83`|76|20|2|BLOCKED|
|30|`7ddf691ac2afbda7473c0d07f1f4e7ae1e69e47b`|78|20|2|BLOCKED|
|60|`aad30eff27ac5c9a13194125226653c6c2826c58`|78|20|2|BLOCKED|
|90|`af2b3e72a552cfb2a902556469868763ddea3638`|78|20|2|BLOCKED|

All six revisions share the two missing files. UNKNOWN counts are per-revision
projection records, not independent histories. There are15 distinct upstream
profile sources across the audit:OS/file activation conditions and the literal
`[9` JDK activation remain unresolved. No Maven effective model was executed.

The [matrix](examples/phase5_2_2_d_1/compile_readiness_matrix.json) retains tree/POM
hashes, exact plugin versions, declared/default phases, known/unknown compile
requirements and missing paths. The full static audit remains a conservative
version union, without claiming Maven nearest-definition mediation, final
classpaths, runtime success or scientific data admission.

Artifact roles are separated in
[artifact_classification.json](examples/phase5_2_2_d_1/artifact_classification.json):

- 367 required compile candidates, including the two unverified files;365 present.
- 15 conditional profile sources with raw declarations;activation stays UNKNOWN,
  and their dependencies are not silently admitted or fetched as required.
- 10 later-phase descriptor paths;161 parent/BOM/configuration metadata paths.
- 75 verified cached paths unused in the final projection. Seed copying is not
  a claim that all509 old artifacts are required for compile.
- Optional and non-runtime dependency declarations are recorded separately.
  Missing compile dependencies remain classified as required even when absent
  from the successful closure-edge list.

## Reverification, tests and preservation

**266 tests passed in each checkout**, including19 new Task D.1 cases; no
failures or skips. The suite covers independent-copy/hash/ledger identity,
source-cache separation before any directory creation, zero-request cache hits,
checksum-probe/retry accounting, redirect/payload/artifact/disk caps, fatal budget
stops, unknown-profile classification, per-revision identity, actual plugin
phase evidence and previous Task A/B/D and scope/foundation regressions.

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=120 --fsize=16777216 -- \
  /home/hp/tst/td_pipeline_module_level/td_pipeline/.venv-forecast/bin/python \
  -m pytest -q -p no:cacheprovider \
  tests/test_phase5_2_2_d_1_continuation.py tests/test_phase5_2_2_d_recovery.py \
  tests/test_phase5_2_2_b_probes.py tests/test_phase5_2_2_a_review.py \
  tests/test_production_scope_readiness.py tests/test_multilanguage_preflight.py \
  tests/test_multilanguage_foundation.py
```

Tests use recorded evidence and mocked transports; they do not contact Maven
Central, run downloaded code, start containers or execute models.
[Verification receipt](examples/phase5_2_2_d_1/verification.json) distinguishes
software verification PASS from dependency/readiness PARTIAL/BLOCKED.

An independent read-only audit reproduced `requirements.json` byte-for-byte:
`b11d01e9a2294d327be0a606846e67bddbd4beb5e96d712a7e6c19772c0ef525`.
It rehashed all611 cache artifacts without a network-capable transport or ledger
write. Public metadata is deterministic compact JSON for the larger objects;
its byte hashes differ from the equivalent private pretty JSON and are sealed
in the public bundle manifest. Both identities are recorded in verification.

Preservation PASS covers all409 earlier central files,320 working-project files,
4 unfinished remediation files,all1,378 original Task D cache files,56 frozen
experiment bundles/322 artifacts,both Phase5.1 bundles,the source SQLite and
pinned Chronos checkpoint. Both existing user Maven caches retain5,878 entries;
75 published reference artifacts were rehashed. Old server identity, stopped
state and mount mappings remain unchanged. No old cache ledger, study scope,
source state, historical POM, model, result, dataset or prior report changed.
Original working `main` remains at
`2e7999ea436d49449652e6c52e9066ef2e514419`.

## Files and reproducible safe commands

New source only:
`tools/maven_recovery/continuation.py`, `tools/recover_phase5_2_2_d_1.py`,
`tests/test_phase5_2_2_d_1_continuation.py`, this report and the small metadata-only
`examples/phase5_2_2_d_1/` bundle. Task D's original implementation is unchanged.

New independently copied cache, outside Git:

```text
/home/hp/tst/research/forecasting_mvp/phase5_2_2_d_1/2026-10-16/continuation-1/
  repository/                 #611 verified files; no project execution
  dependency_manifest.json    #new400-request ledger, linked to unchanged Task D
  requirements.json
  frontier_comparison.json
  checkpoints.json
```

The original acquisition command ran **once** with a fresh output path:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
TD522D1_PY="$PWD/.venv-forecast/bin/python"
TD522D1_CACHE=/home/hp/tst/research/forecasting_mvp/phase5_2_2_d_1/2026-10-16/continuation-1
# Historical command only; do not start another batch without authorization:
# PYTHONDONTWRITEBYTECODE=1 timeout 900s taskset -c 0 \
#   prlimit --as=1073741824 --cpu=600 --fsize=33554432 -- \
#   "$TD522D1_PY" -m tools.recover_phase5_2_2_d_1 --output "$TD522D1_CACHE"

# Safe read-only reproduction; does not create a new batch or modify accounting:
PYTHONDONTWRITEBYTECODE=1 timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=120 --fsize=33554432 -- \
  "$TD522D1_PY" -m tools.recover_phase5_2_2_d_1 \
  --output "$TD522D1_CACHE" --audit-only > /tmp/td522d1-audit-reproduced.json
```

Fresh-cache construction refuses existing destinations. All POMs/JARs and logs
remain outside Git; only source, tests, reports, source URLs/hashes and small
metadata are published using a normal descendant commit. No credentials or
third-party binaries are included. GitHub publication is byte-verified separately.

**STOP after Task D.1 verification/publication. No new acquisition batch and
no Task C/E/F, historical build, scan, training or inference.**
