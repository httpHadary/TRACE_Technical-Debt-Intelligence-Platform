# Phase 5.2.2-E.3 — T+30 static Maven readiness

**PASS_STATIC_T_PLUS_30_READINESS.** All known static paths and metadata are
resolved in a new751-artifact cache:734 unchanged seeds plus17 exact additions.
All six requested POM/JAR pairs and five newly exposed parent/transitive paths
are present. The independent target plan contains20 verified plugin descriptors.
The cache estimate fits the unchanged128MiB repository tmpfs.

**No Maven,Java,Docker container,compiler,SonarQube,scanner or model executed.**
This is not COMPILE_PASS or FULL_OFFLINE_BUILD_READY. T+30's actual effective
model,active profiles,runtime classpaths,SCM behavior and class outputs remain
UNKNOWN. All three previous COMPILE_PASS builds remain independently verified.

Starting main:`ce833d41f9d65ff59179beee5a08cc7bb6293e12`.
Date:2026-10-18,Africa/Cairo. Scope:E.3 only,one non-resumable recovery batch.

## Source identity and historical context

| Identity | Verified |
| --- | --- |
| Repository/offset |apache/commons-cli,T+30|
| Commit |`7ddf691ac2afbda7473c0d07f1f4e7ae1e69e47b`|
| Tree |`a2ff09febdac9da6e6ee422a9144ad09d81113bf`|
| Historical POM SHA256 |`674975083520370c7a691778fa6fcdfe2eb0ae672c48abc923ffc75688c73e8e`|
| Full tracked inventory |137 files,not116/117|
| Production Java population |36 files,not26|
| Parent chain |Commons Parent78 →Apache33|
| Future runtime |Maven3.9.11 /Temurin17.0.17+10 /Java release8|
| Future properties |maven.test.skip=true,user.home=/tmp,no explicit profiles|
| Actual effective-POM identity |null /UNKNOWN_NOT_EXECUTED|

The commit/tree object bytes and every frozen blob ID were verified directly from
local Git objects against the versioned source registry. All137 exported files
have exact bytes,SHA256 and executable modes,with no historical POM/source edit,
extra Maven configuration or manufactured Git metadata. A new private read-only
export is used;no old export or worktree was modified.

T+30 adds10 Java files under the new `org.apache.commons.cli.help` package and10
test/example files relative to T0. It changes five existing production Java files:
CommandLine,DefaultParser,DeprecatedAttributes,the original HelpFormatter and Parser.
The full source/property/configuration difference matrix records all changed paths.
The36-file population is verified independently and is not a previous class-count
expectation. A future compiler verifier must derive its own class identities and
handle package-info/nested classes;E.3 produces no compiled outputs.

T0 E.0.6,T−30 E.1.1 and T−90 E.2.1 were revalidated with their separate read-only
output auditors. All three remain COMPILE_PASS with unchanged class archives,
claims,raw execution records,source/cache hashes and receipts. No build command
reran and no consumed claim was reused. Their model/profile/output identities
were not substituted for the T+30 target.

## Independent T0 versus T+30 audit

Both static models were built from their own original POMs and parent inheritance,
using the same registered future properties. T0's actual D.3 model is preservation
evidence only,not input to T+30's effective-model construction.

| Component | T0 | T+30 |
| --- | --- | --- |
| Commons Parent /Apache |76 /33|78 /33|
| Project version |1.9.1-SNAPSHOT|1.10.0-SNAPSHOT|
| Tracked files /production Java |117 /26|137 /36|
| JUnit BOM/API/engine/params |5.11.1|5.11.2|
| Commons IO,test scope |2.17.0|2.17.0|
| Commons Text,test scope |Not declared|1.12.0|
| Mockito,test scope |4.11.0|4.11.0|
| Surefire descriptor |3.5.0|3.5.1|
| CycloneDX descriptor |2.8.1|2.9.0|
| Enforcer |3.5.0|3.5.0|
| Buildnumber |3.2.1|3.2.1|
| Compiler /resources |3.13.0 /3.3.1|3.13.0 /3.3.1|
| Actual compilation |COMPILE_PASS|NOT_EXECUTED|

The [configuration matrix](examples/phase5_2_2_e_3/T0_T_PLUS_30_CONFIGURATION_MATRIX.md)
and [full version inventory](examples/phase5_2_2_e_3/full_plugin_version_inventory.json)
cover all configured and managed plugins,including reporting/later-phase entries.
[Detailed differences](examples/phase5_2_2_e_3/configuration_difference.json) record
20 changed inherited properties,dependency management/imports,profiles,source layout,
resource/default-goal sections and plugin configuration. Reporting-only changes
were not treated as authorization to recover their complete runtime graphs.

The Artifact Plugin3.5.1 check-buildplan descriptor defaults to `deploy`,with no
project task override. Exact target metadata identifies20 plan descriptors,each
checked for packaging,GAV,embedded plugin.xml/pom.properties,goal identity,parents
and imports. Plan membership is not evidence of goal execution. Surefire tests,
CycloneDX generation,SPDX,Moditect,Felix,install and deploy did not run.

Original compile-bound candidates retain enforcer,RAT,check-buildplan,build-helper,
antrun,remote-resources,buildnumber,resources and compiler. Their pinned plugin
versions match successful T0;that is reuse evidence,not proof of T+30's runtime
classpath or effective-model equivalence. No changed compile-plugin root requires
an additional runtime closure. Original target configuration and all plan metadata
were independently checked. The318 original known compile-candidate references
are present;they include duplicates and are not318 independent artifacts.

The older TaskD registration left Enforcer and JAR plugin phases unspecified.
Exact target descriptors resolve Enforcer's two original goals to validate and
JAR/test-jar to package. The new report records this reconciliation without editing
the historical registration. Enforcer remains a required compile-bound check;
JAR descriptor availability does not execute package. Some legacy UNKNOWN plugin
rows contain no transitive reference list,so those318 rows are not presented as a
complete mediated runtime dependency graph.

[Compile-phase evidence](examples/phase5_2_2_e_3/compile_phase_requirements.json)
separates exact goal bindings,parent/import metadata,legacy reference coverage,
unchanged-plugin reuse and runtime UNKNOWNs. Original source/target values are1.8;
registered future release8 is unchanged. Resource processing preserves original
LICENSE/NOTICE and javadoc-resource handling. The original defaultGoal includes
other checks,but a future explicit compile must retain its own lifecycle without
selecting other goals. Buildnumber's original detached-SCM fallback configuration
is recorded;actual T+30 SCM behavior is UNKNOWN,not inferred from prior successes.

## Exact acquisition and closure

All12 requested missing paths were recovered at their original versions:

- JUnit Jupiter API,engine and params5.11.2,POM/JAR.
- Commons Text1.12.0,POM/JAR.
- Maven Surefire Plugin3.5.1,POM/JAR.
- CycloneDX Maven Plugin2.9.0,POM/JAR.

Metadata exposed five additional required paths:Surefire parent3.5.1 POM and
JUnit Platform commons/engine1.11.2 POM/JAR pairs. All17 additions are verified.
Commons Parent78,JUnit BOM5.11.2 and relevant Commons Text parent/import metadata
already existed in the verified seed and were rechecked. Commons IO2.17.0 and
Mockito4.11.0 remain the exact declared versions. No replacement or upgrade occurred.

The project test closure has14 selected identities,including Commons Text's
justified nonoptional transitives. All six direct project declarations are
**test-scoped**;classification is not confused with production compilation or
actual test execution. Static nearest/first mediation,management,optional flags,
exclusions and scopes are recorded conservatively. This is not Maven's actual
runtime mediation or compiler classpath. Optional/later-plugin runtime declarations
remain separately listed as UNKNOWN;no unrelated plugin universe was recovered.

Approved local sources were checked before network acquisition. The exact Commons
Text POM/JAR qualified only after fresh Central checksum/provenance validation;
15 other additions were downloaded. Existing user caches were not trusted by
filename and were not modified. Every artifact has exact path/coordinates,
POM XML/packaging or plugin metadata checks,recorded Central URL/checksum,local
SHA256 and JAR ZIP/CRC verification. New checksum sidecars use10 SHA512 and7 SHA1;
all17 artifacts have local SHA256. This is same-origin checksum consistency over
TLS,not an independent publisher-signature assertion.

[Frontier comparison](examples/phase5_2_2_e_3/frontier_comparison.json),
[artifact manifest](examples/phase5_2_2_e_3/dependency_manifest.json),
[test closure](examples/phase5_2_2_e_3/test_dependency_closure.json) and
[descriptor verification](examples/phase5_2_2_e_3/buildplan_descriptor_verification.json)
contain the exact recovered paths,parents,BOMs,goals and hashes. The final frontier
is empty and the original batch already qualified static PASS;no post-batch
semantic correction or further acquisition was needed.

## Profiles and later common requirements

All24 project profile records retain actual runtime activation
UNKNOWN_NOT_MAVEN_EVALUATED. The static checker reports no unresolved significant
metadata issue for this target. Zero blocking static issues does not mean actual
active profiles are known. T+30 effective-model SHA remains null. Runtime plugin
realms and compiler arguments are unverified;no JVM/Maven command was used.
See [profile/runtime evidence](examples/phase5_2_2_e_3/profiles_and_runtime_uncertainty.json).

The requested read-only T+60/T+90 metadata comparison confirms both also inherit
Parent78 →Apache33 and declare JUnit5.11.2. T+60 shares Commons Text1.12.0 but
uses Commons IO2.18.0. T+90 uses Commons IO2.18.0 and Commons Text1.13.0.
Both have138 tracked/36 production Java files,not the T+30 full-file count.
Their pinned POM/tree identities were checked against the registry;no source
export,artifact recovery,build preparation or execution occurred for those states.
The comparison permits cached metadata reads only and rejects a missing path
rather than acquiring an artifact for another revision. It makes no later-revision
readiness claim. See
[later common requirements](examples/phase5_2_2_e_3/later_common_requirements.json).

## Cache and bounded resource evidence

| Item | Actual result |
| --- | ---: |
| Independently copied seed artifacts |734,all unchanged|
| Exact additions /total |17 /751|
| Manifest SHA256 |`2e77c1a9578231e6b9f8d6425fb6ebe45304d7905f8e91d02346e1ca0d199fa9`|
| Canonical cache SHA256 |`a6469c15e4a99fcb4b59f8c4c3a9c19892523cffa8a5a2467711cda11399b463`|
| Candidate payload |80,129,204 bytes|
| Rounded4KiB file allocation |81,666,048 bytes|
| Directory overhead estimate |3,362,816 bytes|
| Maven metadata reserve |16,777,216 bytes|
| Runtime repository estimate |101,806,080 bytes (~97.09MiB)|
| Original tmpfs cap |134,217,728 bytes (128MiB),unchanged|
| HTTP requests |46 /200|
| New response payload |1,613,981 /67,108,864 bytes|
| New artifact payload,including local reuse |1,883,488 bytes|
| Checksum404s /transport retries |14 /0|
| Acquisition elapsed time |92.66s /600s|
| Acquisition peak RSS |47,868KiB|
| Read-only verification peak RSS |48,520KiB|
| Process address-space /CPU /workers |1GiB /CPU0 /1|

The estimate leaves32,411,648 bytes after the16MiB metadata reserve. Actual future
tmpfs enforcement remains authoritative;no repository or2GiB build-container cap
was raised. Private task storage at verification was89,652,755 bytes,
below256MiB;new artifacts are below32MiB each. Admission found8,778,846,208 host
RAM bytes and15,475,539,968 disk bytes available,with no prohibited workload.
Final RAM/disk and publication-time task storage are in the resource receipt.

Requests were durably recorded before I/O using flushed/fsynced atomic ledger
replacement and directory fsync. HTTPS traffic was restricted to
`https://repo.maven.apache.org/maven2/`,with no proxies,redirects,alternate
repositories,automatic retries or budget resets. Payload accounting includes read
artifact/checksum response bodies,excluding unread error bodies,headers and TLS.
Local reused bytes are artifact storage,not new network payload. GitHub sync is
subsequent publication of metadata and does not reopen the sealed recovery ledger.
Unused allowance grants no second batch.

## Regression and preservation

**794 tests passed in each checkout**,zero failures/errors/skips:
21.552s canonical and21.465s original project.
The suite contains740 previous relevant tests and54 new E.3 tests,including the
full137/36 inventory,exact versions,BOM/parent closure,descriptor identity,legacy
phase reconciliation,scope UNKNOWNs,integrity/provenance,durable request/resource
limits,symlink/path guards,independent copies and all three required read-only
build auditors. The54 focused tests passed before acquisition. Tests executed no
Maven,Java or container process.

Two fresh offline audits were byte-identical,SHA256:
`4a8d2d74e61cadfa535a4bbded3fb03ace722ce699fba8a69191981ef0eaf3e5`.
The complete executed adapter equals published source;no post-batch code change or
ledger reset occurred. All751 hashes/structures and137 source bytes/modes were
reverified. Every734 seed copy has a different inode from its original.

Preservation PASS covers all three successful build receipts/class archives,
all previous private caches,reports,claims and acquisition ledgers,all18 registered
source states,56 frozen research bundles/322 artifacts,two Phase5.1 bundles,
SQLite/model hashes,6262 user-cache entries and75 rehashed reference artifacts,
old SonarQube state/volumes,and unrelated files/containers. Four existing untracked
remediation files remain unchanged. Earlier request counts stay D=2000,D.1=400,
D.2=52,D.3=112,E.0.3=56,E.0.5=12,E.0.5.1=52,E.1=32,E.2=67.

Only read-only existing-daemon metadata GETs were used for preservation;no Docker
CLI,container creation/start,service stop or server mutation occurred. No independent
shared-container change was observed. Original project HEAD remains unchanged;
new files are mirrored there and published via the canonical checkout as a normal
main descendant commit. See
[verification](examples/phase5_2_2_e_3/verification.json),
[preservation](examples/phase5_2_2_e_3/preservation.json),
[all source states](examples/phase5_2_2_e_3/all_source_states_preservation.json) and
[three successful builds](examples/phase5_2_2_e_3/successful_builds_preservation.json).

## Files,reproduction and STOP

New source:`tools/prepare_tplus30.py`. New tests:`tests/test_tplus30_readiness.py`.
This report and `examples/phase5_2_2_e_3/` contain sanitized matrices,manifests,
closures,resource/test/preservation receipts and the E.3.1 handoff. No historical
POM/source,old cache/report,production feature,dataset or benchmark was edited.

Private cache:`/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_3/2026-10-18/recovery-1/repository`.
Private source:`/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_3/2026-10-18/source`.
Binaries,downloaded dependencies,raw historical files and private runtime artifacts
remain outside Git. The recovery directory is consumed;do not resume it.

Read-only audit from the original project directory:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=150 --fsize=33554432 -- \
  .venv-forecast/bin/python -m tools.prepare_tplus30 --audit-only \
  --output /home/hp/tst/research/forecasting_mvp/phase5_2_2_e_3/2026-10-18/recovery-1
```

Focused deterministic tests:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_tplus30_readiness.py
```

The verification receipt contains the full25-file regression invocation.

**STOP after E.3 publication.** The
[E.3.1 handoff](examples/phase5_2_2_e_3/E_3_1_HANDOFF.md) gives the exact
137-source/751-artifact identities for a separately authorized single T+30 compile.
It retains2GiB container,768MiB heap,1CPU,128MiB repository tmpfs and240s timeout.
No Maven,compile,Docker startup,acquisition continuation,other-revision recovery,
SonarQube/scanner,forecast,debt collection,dataset admission orPhase5.3 follows.
Analyzer licensing and derived-data rights gates remain unresolved and unchanged.
