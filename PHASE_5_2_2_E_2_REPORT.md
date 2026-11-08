# Phase 5.2.2-E.2 — T−90 differential Maven readiness

**PASS_STATIC_T_MINUS_90_READINESS.** The new cache contains734 verified artifacts:
710 unchanged seeds and24 exact additions. All seven requested POM/JAR pairs,
additional install/deploy descriptors,required parent metadata and milestone test
transitives are present. The final static audit has no missing paths and verifies
all20 build-plan descriptors. The candidate fits the unchanged128MiB repository cap.

**No Maven,Java,Docker CLI/container,compiler,scanner or model executed.** No second
acquisition batch ran. Actual T−90 effective model,profile activation,runtime
classpaths,SCM behavior and compilation remain UNKNOWN. This is not COMPILE_PASS.
Starting main:`6b9fabc476e44ca74da19c5d8721e90411930a8a`. Date:2026-10-18.

## Frozen source and preserved builds

| Item | Independently verified |
| --- | --- |
| Repository/offset |apache/commons-cli,T−90|
| Commit |`e1529b546d9696192f4de52152777403b4a01b39`|
| Tree |`c1a67e730fc5729a5376c267ed559f4ae310df01`|
| POM SHA256 |`f4403aa060f16ca0f17d28fffb1bc6fcc42c31d480af8dc6a6436f25fddf8f15`|
| Tracked source files |116,all Git blobs,SHA256,bytes and modes verified|
| Production Java files |26|
| Parent chain |Commons Parent71 →Apache32|
| Future runtime |Maven3.9.11 /Temurin17.0.17+10 /release8|
| Future properties |maven.test.skip=true,user.home=/tmp,no explicit profiles|
| Actual effective-model hash |null; no model execution|

The exact Git commit and tree object hashes were checked directly. All116 files
were exported from verified frozen blob objects into a new read-only private
source directory;no original worktree,POM or source was modified. No `.git` or
extra Maven configuration was manufactured. The26 production Java paths are
registered independently. CommandLine.java,HelpFormatter.java and Option.java differ
from both successful targets;future output identities must be derived from T−90.

Both previous builds were revalidated using their read-only output auditors.
T0 E.0.6 and T−30 E.1.1 remain COMPILE_PASS,with unchanged class archives,claims,
source/cache hashes,raw execution evidence and receipts. Their37-class results
are preserved observations,not T−90 expectations. No previous Maven command reran
and no old active-profile/effective-model result was used to construct T−90's model.

## Three-way configuration findings

Each revision was parsed independently from its own POM and parent inheritance,
using the same registered future user properties. These are conservative static
models,not Maven effective models.

| Component | T−90 | T−30 | T0 |
| --- | --- | --- | --- |
| Commons Parent /Apache |71 /32|74 /33|76 /33|
| Project version |1.9.0-SNAPSHOT|1.9.1-SNAPSHOT|1.9.1-SNAPSHOT|
| Project JUnit BOM/API/engine/params |5.11.0-M2|5.11.0|5.11.1|
| Enforcer |3.4.1|3.5.0|3.5.0|
| Surefire descriptor |3.2.5|3.4.0|3.5.0|
| Install/deploy descriptors |3.1.1|3.1.2|3.1.2|
| CycloneDX descriptor |2.8.0|2.8.1|2.8.1|
| SPDX descriptor |0.7.3|0.7.4|0.7.4|
| Moditect descriptor |1.2.1.Final|1.2.2.Final|1.2.2.Final|
| Buildnumber |3.2.0|3.2.0|3.2.1|
| Compiler /resources |3.13.0 /3.3.1|3.13.0 /3.3.1|3.13.0 /3.3.1|
| Commons IO,direct test dependency |2.16.1|2.16.1|2.17.0|
| Mockito,direct test dependency |Not declared|4.11.0|4.11.0|
| Actual compile result |NOT_EXECUTED|COMPILE_PASS|COMPILE_PASS|

The complete declared/managed version inventory is in the
[configuration matrix](examples/phase5_2_2_e_2/T_MINUS_90_CONFIGURATION_MATRIX.md).
[Configuration differences](examples/phase5_2_2_e_2/configuration_difference.json)
record44 changed inherited properties relative to T−30 and47 relative to T0,
source changes,dependency management/BOMs,profile candidates,plugin configurations
and inherited resource sections. Reporting-only differences do not authorize their
plugin runtime dependency trees or goal execution.

The original Artifact Plugin3.5.1 `check-buildplan` descriptor defaults to `deploy`;
no task override is configured. All20 original plan descriptors and referenced
goals were checked as XML/ZIP metadata. Their later test/install/deploy/SBOM/SPDX/
Moditect/Felix goals did not run. Original compile-bound candidates retain enforcer,
RAT,check-buildplan,build-helper,antrun,remote-resources,buildnumber,resources and
compiler. Enforcer3.4.1 is the changed compile-plugin root relative to T−30;its
10 conservative runtime candidate edges were audited. All400 registered T−90
compile candidate references are present;these are repeated static references,
not400 independent artifacts or a proven Maven runtime classpath.

Historical source/target properties are1.8;the registered future user property is
release8. Original LICENSE/NOTICE/resource and javadoc-resource configurations
remain visible in the matrix. The project defaultGoal includes other checks,but a
future explicit `compile` command must not select it or override lifecycle checks.
Original buildnumber fallback settings remain unchanged. T−30 tolerated detached
SCM,but T−90's actual behavior is UNKNOWN. Immutable lineage must use the frozen
commit/tree,never an SCM fallback value.

## Exact recovery and expanded frontier

The requested initial roots were JUnit Jupiter API/engine/params5.11.0-M2,
Surefire3.2.5,CycloneDX2.8.0,SPDX0.7.3 and Moditect1.2.1.Final,both POM and JAR.
All14 requested paths were absent from the710-file seed and are now verified.
The complete pre-acquisition audit identified18 missing paths by additionally
finding install/deploy3.1.1 POM/JAR pairs. Metadata exposed six more paths:
Surefire3.2.5 parent POM,Moditect parent1.2.1.Final POM,and JUnit Platform
commons/engine1.11.0-M2 POM/JAR pairs. These24 additions are all present.

The JUnit5.11.0-M2 BOM was already verified in the seed. Milestone versions were
preserved exactly;none was replaced with a final release. The project test closure
contains8 selected identities,respecting scopes,optional flags,exclusions and
nearest/first candidate selection. This static approximation is not actual Maven
mediation. Optional and later-lifecycle runtime requirements remain listed as
UNKNOWN;no complete unrelated runtime universe was downloaded.

Approved local sources were checked before network acquisition. Three exact
Surefire files qualified from existing local bytes only after fresh Central
checksum/provenance validation;their original caches stayed unchanged. The other
21 additions were downloaded. Every admitted artifact has exact coordinates,
packaging/POM or plugin metadata checks,local SHA256,published checksum and JAR CRC
verification. All20 plugin descriptors have matching plugin.xml/pom.properties
GAVs and referenced historical goals. Parent/BOM metadata is recorded separately
from runtime dependency declarations. New checksum types:13 SHA512 and11 SHA1;
all24 files also have locally calculated SHA256. This is TLS/same-origin checksum
consistency,not an independent publisher-signature claim.

[Frontier evidence](examples/phase5_2_2_e_2/frontier_comparison.json),
[descriptor verification](examples/phase5_2_2_e_2/buildplan_descriptor_verification.json),
[test closure](examples/phase5_2_2_e_2/test_dependency_closure.json) and the
[artifact manifest](examples/phase5_2_2_e_2/dependency_manifest.json) give exact paths,
GAVs,parents,imports,hashes and resolved/uncertain classifications.

## Profile UNKNOWNs and final qualification

All26 T−90 project profile records explicitly retain runtime activation UNKNOWN.
The initial audit was PARTIAL despite zero missing paths because three transitive
dependency models inherit Commons Parent58's `jdk9-compiler` activation literal
`[9`:commons-lang3 3.13.0,commons-codec1.16.0 and commons-io2.13.0. The conservative
parser cannot determine that activation. The
[initial receipt](examples/phase5_2_2_e_2/initial_frontier_comparison.json) remains
unchanged;the result was not silently replaced.

Read-only inspection proves this exact profile sets only
`maven.compiler.release=${commons.compiler.release}`. It contributes no dependency,
BOM,parent,repository or other property. No inheritance layer for those three
models reads that property in POM expressions or profile activation. Commons
Parent58 is their ancestor,not Commons CLI's Parent71. The property affects those
dependencies' own compiler configuration and cannot change the audited dependency
identities or propagate into Commons CLI inheritance. This narrow scope proof
makes the metadata uncertainty nonblocking while its activation stays UNKNOWN.
The evidence records exact POM layer hashes and the profile XML.

Regression tests reject this qualification if another property,dependency,property
reference or activation consumer appears,or if the issue belongs to an unknown
model or the Commons CLI project. No activation is forced true/false,no POM is
changed,and no previous Maven profile result is transferred. The new scope review
is a static reporting correction after the batch. The executed adapter is archived
privately;AST equality proves its Recovery transport,accounting,limits and sealing
methods match the published code. The sealed67-request ledger is byte-identical.
No additional acquisition occurred. See
[profile/runtime evidence](examples/phase5_2_2_e_2/profiles_and_runtime_uncertainty.json).

## Cache identity and resource receipts

| Item | Measured result |
| --- | ---: |
| Seed artifacts |710 independently copied,unchanged|
| New artifacts /total |24 /734|
| Manifest SHA256 |`abbfd6711f2d16b4eb4f0992d819c01cb85c8cef385f6a7c9effb2136d35e4b6`|
| Canonical cache SHA256 |`e4870752be9fc1517fbdbb6eb785a704211950630839ac12e39d562725e95ecf`|
| Cache payload |78,245,716 bytes|
| Rounded4KiB file allocation |79,753,216 bytes|
| Directory overhead estimate |3,325,952 bytes|
| Maven metadata reserve |16,777,216 bytes|
| Estimated runtime total |99,856,384 bytes (~95.23MiB)|
| Original repository tmpfs cap |134,217,728 bytes (128MiB),unchanged|
| HTTP requests |67 /200|
| Transferred response payload |1,794,287 /67,108,864 bytes|
| New artifact payload,including local bytes |1,864,040 bytes|
| Checksum404 responses /transport retries |22 /0|
| Acquisition elapsed time |85.70s /600s|
| Acquisition peak RSS |46,032KiB|
| Process address-space /CPU /workers |1GiB /CPU0 /1|

The99,856,384-byte estimate retains16MiB metadata reserve and34,361,344 bytes
headroom under the128MiB cap. Kernel tmpfs enforcement remains authoritative for
a future build;no tmpfs/container-memory policy was increased. Private task storage
at verification was87,361,935 bytes,under256MiB. Every new artifact
is below32MiB. Host RAM/disk admission and final measurements are in the resource
receipt. Acquisition had6,786,400,256 available RAM bytes and15,778,111,488 disk bytes.

HTTP requests were durably counted before I/O using fsync/atomic ledger updates.
Only `https://repo.maven.apache.org/maven2/` was allowed;no proxies,redirects or
alternate versions. Automatic transport retries were disabled. Accounting includes
read response/checksum bodies,excluding unread HTTP-error bodies,TLS and headers.
Response payload is smaller than new artifact payload because three local files
were reused after verification. GitHub publication is a separate metadata sync,
not an extension of the Maven acquisition budget. Unused allowance grants no
second batch. A later audit is network-disabled and cannot reset the ledger.

## Regression and preservation

**686 passed in each checkout**,zero failures/errors/skips:
19.793s canonical and20.373s original project.
This includes637 earlier relevant tests and49 new E.2 tests. Before acquisition,
42 focused tests passed. Added coverage includes exact source/cache identities,
independent copies,checksum provenance,durable requests,all resource caps,symlinks,
no automatic retry,milestone BOM resolution,descriptor versions,profile UNKNOWN
scope and refusal to accept a failed prior build proof. No Maven/Java/container
execution is part of the tests.

Two fresh offline audits were byte-identical,SHA256
`390181fcb3f43812534b8df259bba3d471c31cca10885f0ffd3d89d08bc8e3eb`. All734 artifact structures/hashes and116 source
identities/modes were reverified. Preservation PASS covers both successful builds,
all previous private caches/evidence/attempt claims,all18 registered source states,
56 frozen research bundles/322 artifacts,two Phase5.1 bundles,source SQLite/model
hashes,6262 user-cache entries and75 rehashed reference artifacts,old SonarQube
container/volumes,and unrelated files/containers. Four preexisting untracked
remediation files remain untouched. Prior ledgers stay D=2000,D.1=400,D.2=52,
D.3=112,E.0.3=56,E.0.5=12,E.0.5.1=52,E.1=32.

No unrelated service was stopped and no shared-container change was observed.
Preservation used only read-only GETs of existing daemon metadata;no Docker CLI,
container creation/start or server mutation occurred. Original project HEAD stays
unchanged;new task files are mirrored there and published through the canonical
checkout as a normal descendant main commit.

See [regressions](examples/phase5_2_2_e_2/verification.json),
[preservation](examples/phase5_2_2_e_2/preservation.json),
[source states](examples/phase5_2_2_e_2/all_source_states_preservation.json) and
[successful builds](examples/phase5_2_2_e_2/successful_builds_preservation.json).

## New files,reproduction and STOP

Only new files: `tools/prepare_tminus90.py`,`tests/test_tminus90_readiness.py`,this
report and `examples/phase5_2_2_e_2/` metadata/matrices/handoff. Existing production
code,historical sources/POMs,caches,benchmarks and reports were not edited.

Private cache:`/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_2/2026-10-18/recovery-1/repository`.
Private source export:`/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_2/2026-10-18/source`.
No downloaded binary,third-party source payload,compiled output or credential is
published. The one acquisition batch is complete;do not resume its directory.

Read-only audit from the original project directory:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=150 --fsize=33554432 -- \
  .venv-forecast/bin/python -m tools.prepare_tminus90 --audit-only \
  --output /home/hp/tst/research/forecasting_mvp/phase5_2_2_e_2/2026-10-18/recovery-1
```

Focused deterministic tests:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_tminus90_readiness.py
```

The verification receipt contains the complete22-file regression command.

**STOP after E.2 publication.** The
[E.2.1 handoff](examples/phase5_2_2_e_2/E_2_1_HANDOFF.md) identifies the exact
734-artifact cache and frozen target for a separately authorized single compile,
with the existing2GiB container,768MiB heap,1CPU and128MiB repository cap.
Actual Maven execution may still expose runtime issues. No Maven,Java,Docker
startup,compilation,retry,acquisition batch,other revision,SonarQube/scanner,forecast,
technical-debt collection,dataset admission orPhase5.3 follows automatically.
Analyzer licensing and derived-dataset rights gates remain unresolved and unchanged.
