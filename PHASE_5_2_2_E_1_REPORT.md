# Phase 5.2.2-E.1 — T−30 differential Maven readiness

Date:2026-10-18, Africa/Cairo. Starting main: `55ec402053952da10919faec0466a840298eb5fd`.

**PASS_STATIC_T_MINUS_30_READINESS.** All known static requirements are resolved in
one new, independently verified **710-artifact cache**:697 unchanged seeds plus13
exact additions. The four requested POM/JAR pairs, required Surefire parent and
JUnit Platform transitive pairs are present. All20 T−30 plan descriptors and12
project test-dependency candidates pass the static audit. No known missing path
remains. The cache fits the unchanged128MiB repository tmpfs.

**No Maven, Java, Docker container, compilation or plugin execution ran.** T−30's
actual effective model, active profiles and runtime classpaths remain unverified;
its actual effective-POM hash is **null**, not T0's hash. This is not COMPILE_PASS,
MODEL_VERIFIED or FULL_OFFLINE_BUILD_READY. E.1.1 has not started.

## Frozen source and preserved T0 evidence

| Target identity | Verified |
| --- | --- |
| Repository/offset |apache/commons-cli /T−30|
| Commit |`fb6293fcd6a9b55ac8ecb550af6572daaed18fa1`|
| Tree |`598dec4901a9adcf8e55b241c9689a8db6219c29`|
| Historical POM SHA256 |`2f322b0751115f2a5e93aabfb83372dc0511d57bbd8b4f178f08d5b449ff3fcf`|
| Tracked files |116, all Git blob IDs, bytes, SHA256 and modes verified|
| Production Java |26 files;25 named top-level source files plus package-info|
| Parent |Commons Parent74 ->Apache33|
| Future registered runtime |Maven3.9.11 /Temurin17.0.17+10 /release8|
| Future properties |maven.test.skip=true,user.home=/tmp,no explicit profiles|
| Actual T−30 effective model |NOT_EXECUTED; no hash available|

The new detached source export is an exact read-only file copy from the frozen
Git objects, with no `.git` or extra Maven execution configuration. All18 original
source commit/tree/full inventories across three repositories remain unchanged.
The production Java paths and bytes match T0. Six other tracked files differ and
one T0 workflow file is absent; the complete paths are in the difference matrix.
Identical Java bytes do not establish identical Maven effective models or outputs.

E.0.6 was revalidated with its read-only auditor. It remains COMPILE_PASS, with the
same37 parsed Java8 class outputs and complete evidence. Its consumed claim,
original raw evidence/classes, regression receipts and all892 previous private
files remain byte-identical to the E.1 baseline. The original T0 POM and D.3 model
remain unchanged; their hashes are not repurposed for T−30.

## Differential configuration findings

Both revisions were independently parsed from their frozen Git POMs using their
own parent inheritance, project files and the same registered user properties.
This is static inspection, not Maven's effective-model construction. T0's separate
actual D.3/E.0.6 evidence is an anchor, not a substitution for the older revision.

| Dimension | T0 | T−30 |
| --- | --- | --- |
| Commons Parent |76|74|
| Project JUnit BOM/API/engine/params |5.11.1|5.11.0|
| Surefire descriptor |3.5.0|3.4.0|
| Buildnumber compile plugin |3.2.1|3.2.0|
| Direct Commons IO, test scope |2.17.0|2.16.1|
| Direct Mockito, test scope |4.11.0|4.11.0|
| Compiler |3.13.0,release8|3.13.0,release8; not run|
| Build-plan tasks |deploy, actually checked|deploy, original metadata verified only|
| Resources/default-goal sections |Original inherited inputs|Same static section bytes|
| Production Java population |26|26,same paths/bytes|
| Actual compile |COMPILE_PASS|NOT_EXECUTED|

The full declared/managed plugin inventory also records SpotBugs4.8.6.4 vs4.8.6.2,
Failsafe3.5.0 vs3.4.0, Javadoc3.10.0 vs3.8.0 and PMD plugin3.25.0 vs3.24.0. All12
changed inherited properties, dependency-management rows/BOM imports, plugin
configurations, profile candidates, resource/default-goal inputs and source-file
changes are recorded in
[configuration_difference.json](examples/phase5_2_2_e_1/configuration_difference.json)
and the readable
[difference matrix](examples/phase5_2_2_e_1/T0_T_MINUS_30_DIFFERENCE_MATRIX.md).
These later/reporting version differences do not justify downloading their runtime
universes or executing their goals.

The original check-buildplan configuration has no task override. The exact cached
Artifact Plugin3.5.1 descriptor's default is `deploy`, with descriptor SHA256
`3ef3ebcc346fef156304b26fb8f03913a4b27848b4c58d56bd4db67384ca526d`.
The20-plugin inventory therefore includes descriptor metadata through that plan;
it does not execute deploy or later phases. Versions come from T−30's inherited/
managed model, including exact default-binding versions, never from T0's effective
POM or newest-version selection.

The static compile-bound candidates retain enforcer,RAT,check-buildplan,
build-helper,antrun,remote-resources,buildnumber,resources and compiler. The only
changed compile-plugin version is buildnumber3.2.0. Its55 conservative candidate
edges, exclusions and uncertainty are audited using existing verified bytes.
All386 registered compile candidate references from TaskD's T−30 requirements
remain present. Those are reference rows with duplicates, not386 independent new
artifacts or a Maven-mediated classpath.

The resource sections include src/main/resources and original LICENSE/NOTICE
handling; antrun's javadoc-resource task is preserved. The project defaultGoal
contains other checks, but a future explicitly authorized `compile` command does
not select that defaultGoal. No generator, resource copy or historical goal ran
in E.1. Actual resource behavior remains subject to the original runtime context.

Buildnumber's original fallback settings remain `revisionOnScmFailure=??????`,
`doCheck=false`, `doUpdate=false`. T0 tolerated its detached export, but the older
3.2.0 plugin has not executed for T−30. SCM behavior is UNKNOWN; immutable lineage
must always use the verified commit/tree rather than potential fallback strings.
No synthetic Git metadata or historical POM modification is permitted.

## Exact acquisition and expanded frontier

The known initial frontier contained eight missing paths, both POM and JAR for:

- `org.junit.jupiter:junit-jupiter-api:5.11.0`
- `org.junit.jupiter:junit-jupiter-engine:5.11.0`
- `org.junit.jupiter:junit-jupiter-params:5.11.0`
- `org.apache.maven.plugins:maven-surefire-plugin:3.4.0`

Authoritative metadata exposed five additional required paths:

- `org.apache.maven.surefire:surefire:3.4.0` parent POM.
- `org.junit.platform:junit-platform-commons:1.11.0` POM/JAR.
- `org.junit.platform:junit-platform-engine:1.11.0` POM/JAR.

All13 files were recovered with exact versions. No replacement or upgrade was
selected. JUnit5.11.0 project BOM and other parents/imports were already verified
cache entries. The complete static test closure has12 selected identities,
respecting project management, exclusions, optional flags and nonpropagating
scopes. This is a conservative XML/descriptor audit with a nearest/first candidate
selection, not proof of Maven's actual mediation or runtime classpath.

The Surefire3.4.0 JAR has matching plugin.xml and pom.properties GAVs, correct
maven-plugin packaging, CRCs and the referenced `test` goal. The same checks cover
all20 target plan descriptors, their original goals, parent chains and imported
metadata. No Surefire runner, test execution, SBOM/SPDX, Moditect or Felix runtime
graph was acquired without a compile-path justification. Their declarations and
cache presence remain visible as runtime UNKNOWNs.

Approved local sources were checked before missing artifacts were downloaded;
no local candidate bytes qualified. All downloads used only
`https://repo.maven.apache.org/maven2/`, with TLS identity, no proxies/redirects,
exact coordinates, published checksums, local SHA256, POM structure/GAV and JAR
ZIP/CRC verification. New artifacts use10 SHA512 and3 SHA1 published sidecars;
all have local SHA256. This is same-origin checksum consistency, not an
independent publisher-signature assertion.

[Frontier comparison](examples/phase5_2_2_e_1/frontier_comparison.json) separates the
initial eight paths, newly exposed five paths and final empty frontier. The full
[artifact manifest](examples/phase5_2_2_e_1/dependency_manifest.json),
[test closure](examples/phase5_2_2_e_1/test_dependency_closure.json) and
[descriptor matrix](examples/phase5_2_2_e_1/buildplan_descriptor_verification.json)
contain the actual recovered metadata and hashes. No synthetic dependency evidence
or runtime result was substituted.

## Profile UNKNOWNs and read-only qualification

T−30 has25 static project profile records. Their runtime decisions are explicitly
UNKNOWN_NOT_MAVEN_EVALUATED. Static condition evaluation is kept separate from
actual Maven activation; no T0 active-profile result is transferred to T−30.

The initial conservative audit reported PARTIAL because it could not evaluate the
OS activation of `org.apache.sshd:sshd-core:2.9.2` profile
`no-containers-for-windows`. That original result is preserved as
[initial_frontier_comparison.json](examples/phase5_2_2_e_1/initial_frontier_comparison.json).

Read-only inspection of its exact verified POM shows that profile changes only
SSHD's own Surefire excludedGroups configuration. It contains no dependency,
dependency-management, properties or repository declaration. SSHD is a transitive
dependency, not a Commons CLI parent; its own test-plugin configuration does not
propagate into Commons CLI's dependency requirements. Its activation remains
**UNKNOWN** and is not forced inactive. This scoped finding removes a false
static requirement blocker while preserving the uncertainty and original evidence.
The final static PASS means no known required metadata/path is unresolved, not
that Maven profiles/runtime semantics have been verified.

The read-only review also corrected a comparison detail: resources3.3.1 comes from
managed defaults in T0 and is unchanged, rather than a changed plugin version.
Its cached metadata was inspected, but no resource-plugin artifact was acquired.
Regression tests cover managed defaults, remote test-only profile relevance and
retention of blocking UNKNOWNs when dependencies/properties/project profiles are
involved. No profile, dependency, activation or scientific admission rule changed.

Both adjustments were offline reporting/analysis corrections after the single
batch. The original ledger/cache/initial receipts were preserved. No extra request,
new budget or second acquisition batch occurred. The executed acquisition adapter
is archived privately; source hashes are recorded. AST checks prove its transport,
request accounting, budget enforcement and sealing code are identical to the
published implementation. See
[profile/runtime uncertainty](examples/phase5_2_2_e_1/profiles_and_runtime_uncertainty.json).

## Cache identity and resource receipts

| Item | Verified result |
| --- | --- |
| Seed count |697 independently copied artifacts; all unchanged|
| Seed manifest SHA256 |`ed23ccde95a89081c1c19f3de39ee9199a50b15eacf0647e316f62acf1f97b84`|
| Seed canonical cache SHA256 |`a84a27a2f5f9d9bed4af8dbf56a04a91b2910580f66c67952362d215f62d0b22`|
| New count |710,including13 exact additions|
| New manifest SHA256 |`c1211045a0d09098bb9b401f8ab019aa491c9c3fa2c7603f840c3ac7d193ce43`|
| New canonical cache SHA256 |`e5176a8b83de3359f8aa0c5d16b941af73c6e8e4a10109fb95a441dc83701d0c`|
| Candidate payload |76,381,676 bytes|
|4KiB-rounded artifact files |77,848,576 bytes|
| Directory allocation estimate |3,272,704 bytes|
| Maven metadata reserve |16,777,216 bytes (16MiB)|
| Total runtime estimate |97,898,496 bytes (~93.36MiB)|
| Existing repository tmpfs cap |134,217,728 bytes (128MiB),unchanged|
| Acquisition requests |32/200|
| New response payload |1,536,669/67,108,864 bytes|
| Actual new artifact payload |1,535,269 bytes|
| Checksum404s /transport retries |6 /0|
| Acquisition elapsed time |110.55s /600s ceiling|
| Acquisition peak RSS |50,156KiB /1GiB address-space cap|
| Offline-audit peak RSS |49,768KiB|
| CPU /sequential workers |CPU0 /1|

FITS_128_MIB with36,319,232 estimated bytes remaining after the16MiB reserve. The
estimate uses filesystem rounding/directory overhead; it is not a measurement of
an executed tmpfs. Future runtime enforcement remains authoritative. Neither the
128MiB repository limit nor2GiB future build-container limit was increased.

At admission,6,378,368KiB host RAM and15,996,608,512 disk bytes were available;
after the static audit,6,391,000KiB RAM and15,946,162,176 disk bytes remained. New
private task storage was84,462,543 bytes at static verification, below256MiB;
publication-time accounting is included in the resource receipt. Individual
artifacts remained below32MiB. No prohibited Java/Maven/Sonar process was present.

Requests were durably counted before network I/O using flushed,fsynced atomic
ledger replacement and directory fsync. Response accounting includes checksum
payloads, excludes unread HTTP-error bodies/TLS/headers, and never resets an old
ledger. Prior request ledgers remain2000/400/52/112/56/12/52. GitHub publication is
subsequent metadata synchronization outside the sealed artifact-acquisition batch.
Unused acquisition allowance is not authorization for another batch.

## Regression and preservation

**589 passed in each checkout**, zero failures/errors/skips:19.15s in the canonical
checkout and19.43s in the original project. This is555 prior relevant tests plus34
new E.1 tests. Tests cover phase ownership, old-cache/symlink rejection, independent
copies, integrity/provenance, checksum request accounting, resource caps, durable
writes, exact target identity, managed/default versions, profile UNKNOWN handling
and prohibition of execution/T0 model substitution. No historical Java tests ran.

Two fresh offline audits were byte-identical, SHA256
`81c923196191847654fa7be7e193963584bb48e38a015dafde951682a06a9b97`.
They left the sealed ledger unchanged and reverified every710 artifact and all116
source bytes/modes. The697 seed inodes differ from the originals; no hard links or
old-cache overwrite was used.

Preservation PASS covers all18 pinned source states, T0 E.0.6's full evidence and
class outputs, all older caches/reports/claims/ledgers,56 frozen bundles/322
artifacts,two Phase5.1 bundles,source SQLite and model checkpoint hashes,6,262
user-cache entries plus75 rehashed reference artifacts,old SonarQube state/volumes
and all unrelated containers/files. Four preexisting untracked remediation files
are unchanged. No shared-container change was observed and no container needed
cleanup. Original project HEAD remains unchanged; only new task files are mirrored
there and published through the canonical checkout.

See [verification](examples/phase5_2_2_e_1/verification.json),
[preservation](examples/phase5_2_2_e_1/preservation.json),
[T0 revalidation](examples/phase5_2_2_e_1/t0_preservation_verification.json) and
[all source states](examples/phase5_2_2_e_1/all_source_states_preservation.json).

## New files and reproduction

Only new code/tests/documents are added:

- `tools/prepare_tminus30.py`: isolated exact recovery, source verification,
  separate static models, own plan inventory, scoped test/changed-plugin closure,
  profile relevance and a nonmutating offline audit mode.
- `tests/test_tminus30_readiness.py`:34 deterministic no-network/no-Maven tests.
- This report and `examples/phase5_2_2_e_1/`: difference matrices,source manifest,
  before/after frontier,cache/provenance,descriptors,closures,UNKNOWNs,resources,
  preservation/regression receipts and the E.1.1 handoff.

Private cache:
`/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_1/2026-10-18/recovery-1/repository/`.
Private verified source:
`/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_1/2026-10-18/source/`.
No dependency binary,third-party source payload,raw private log or credential is
published. No old code,POM,cache,report,dataset or experimental outcome was edited.

Read-only inspection from the project directory, requiring the private cache:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=150 --fsize=33554432 -- \
  .venv-forecast/bin/python -m tools.prepare_tminus30 --audit-only \
  --output /home/hp/tst/research/forecasting_mvp/phase5_2_2_e_1/2026-10-18/recovery-1
```

Focused deterministic tests:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_tminus30_readiness.py
```

The verification receipt records the complete19-file regression command. The
consumed acquisition directory cannot be resumed/reused. The final qualification
is read-only; reproducing the original32-request batch is not newly authorized.

## E.1.1 handoff and STOP

The smallest next step is a separately authorized single T−30 offline compilation,
using a fresh116-source/710-artifact adapter/owner/claim and the existing pinned
sandbox/resource limits. Do not reuse E.0.6's consumed claim,T0 effective-model
hash,117-source assertion,37-output assertion or hard-coded T0 goal auditor.
The expected buildnumber version is3.2.0. Derive output identities from T−30's
source population and measure actual Maven/SCM/profile/compiler behavior.

[E.1.1 handoff](examples/phase5_2_2_e_1/E_1_1_HANDOFF.md) gives exact cache/source
identities and preserved limits. No preliminary Help goal, acquisition, correction
or retry is implied. Actual Maven verification can still reveal a runtime problem;
static readiness is not an empirical build result.

**E.1 stops after GitHub publication.** No Maven/Java/container execution,
compilation,other revision,SonarQube/scanner,forecast,technical-debt collection,
dataset admission or Phase5.3 work ran. Analyzer licensing and derived-dataset
rights gates remain unresolved until independently cleared.
