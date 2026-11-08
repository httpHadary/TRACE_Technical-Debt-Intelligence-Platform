# Phase 5.2.2-E.0.5.1 — Maven build-plan descriptor frontier

Date: 2026-10-18, Africa/Cairo. Starting main: `b80afcf305943de5dc1c3efc5bf51b04c2146810`.

**PASS_STATIC_DESCRIPTOR_CLOSURE.** All six exact plugin POM/JAR pairs and their
necessary parent/import metadata are verified. The candidate cache contains
**697 artifacts: 682 unchanged independent seed copies + 15 additions**. All12
previously missing plugin paths are resolved. The frozen static inventory covers
20 plugins; their descriptor coordinates, referenced goals, embedded properties
and parent/BOM metadata pass the data-only audit.

**Actual Maven plan resolution, plugin runtime classpaths and Java compilation
remain unverified.** No Maven, JVM, plugin class, container, scanner, forecast or
dataset admission executed. COMPILE_PASS and FULL_OFFLINE_BUILD_READY are not
claimed. E.0.6 has not started and needs separate authorization.

## Recovery results

| Exact frozen plugin | Configured/default plan phase and goal | POM/JAR/descriptor | Actual execution |
| --- | --- | --- | --- |
|`org.apache.maven.plugins:maven-surefire-plugin:3.5.0`|test: test|Verified|NOT_EXECUTED|
|`org.apache.maven.plugins:maven-install-plugin:3.1.2`|install: install|Verified|NOT_EXECUTED|
|`org.apache.maven.plugins:maven-deploy-plugin:3.1.2`|deploy: deploy|Verified|NOT_EXECUTED|
|`org.cyclonedx:cyclonedx-maven-plugin:2.8.1`|package: makeAggregateBom|Verified|NOT_EXECUTED|
|`org.moditect:moditect-maven-plugin:1.2.2.Final`|package: add-module-info|Verified|NOT_EXECUTED|
|`org.spdx:spdx-maven-plugin:0.7.4`|package: createSPDX|Verified|NOT_EXECUTED|

Each plugin completed checksum/GAV/packaging/ZIP-CRC/embedded-property/goal checks
before the next plugin began. `completed_plugins` in the sealed acquisition ledger
records this exact order. The pairs were downloaded only from
`https://repo.maven.apache.org/maven2/`; approved local sources were checked, but
no local candidate bytes were admitted. Historical versions were preserved.

The only additional POMs acquired were:

- `org.apache.maven.surefire:surefire:3.5.0`
- `org.moditect:moditect-parent:1.2.2.Final`
- `org.moditect:moditect-org-parent:1.4.0.Final`

Other parents and imported BOMs were already verified cache entries. Surefire's
chain is plugin3.5.0 ->Surefire3.5.0 ->Maven Parent43 ->Apache33. Install/Deploy3.1.2
use Maven Plugins42 ->Maven Parent42 ->Apache32. Moditect uses its exact two parent
POMs listed above. CycloneDX2.8.1 and SPDX0.7.4 have no parent declaration.
Exact JUnit BOM imports5.10.3 (Surefire/CycloneDX) and5.10.2 (Install/Deploy) were
reused without downloading replacements. No missing parent/import metadata or
unresolved static model issue remains in the20-plugin descriptor inventory.
[Parent/BOM evidence](examples/phase5_2_2_e_0_5_1/parent_bom_closure.json) includes
hashes and static profile conditions for every plugin.

## What the static PASS establishes

E.0.4 actually failed in Artifact Plugin3.5.1 `check-buildplan` while requesting
Felix5.1.9's descriptor. E.0.5 recovered Felix and identified the six remaining
pairs in the frozen effective model's static `deploy` plan inventory. This phase
closed those known paths; it did not calculate a plan with Maven.

Pinned Maven3.9.11 separates
[plugin descriptor lookup](https://raw.githubusercontent.com/apache/maven/maven-3.9.11/maven-core/src/main/java/org/apache/maven/plugin/internal/DefaultMavenPluginManager.java)
from runtime realm setup. Its
[plugin dependency resolver](https://raw.githubusercontent.com/apache/maven/maven-3.9.11/maven-core/src/main/java/org/apache/maven/plugin/internal/DefaultPluginDependenciesResolver.java)
also separates single-artifact descriptor/JAR resolution from runtime graph
resolution. The pinned
[check-buildplan source](https://raw.githubusercontent.com/apache/maven-artifact-plugin/maven-artifact-plugin-3.5.1/src/main/java/org/apache/maven/plugins/artifact/buildinfo/CheckBuildPlanMojo.java)
uses a default task of `deploy` to inspect planned executions. These are the same
semantics documented in E.0.5; source URLs are references, not new runtime tests.

Accordingly, the inventory does not authorize or demonstrate Surefire tests,
install/deploy, CycloneDX/SPDX generation, Moditect bytecode changes or Felix
manifest generation. Their runtime declarations and present/absent cache entries
are recorded in [runtime uncertainty](examples/phase5_2_2_e_0_5_1/plugin_runtime_uncertainty.json).
No recursive runtime JAR graph was acquired. Actual mediation, realms, classpaths,
profile behavior and execution remain UNKNOWN where not already established by
D.3. Static dependency-POM profile records are not new actual Maven active-profile
results. The original T0 effective model and active-profile evidence are unchanged.

The three E.0.4 RAT POM warnings (Log4j1.2.12, Logkit1.0.1 and Avalon Framework4.1.3)
remain unchanged, nonfatal and unacquired. RAT succeeded in that attempt; these
warnings do not prove required missing runtime JARs. A later compile can still
reveal another runtime dependency, SCM or original build failure.

## Cache identity, integrity and capacity

| Item | Verified result |
| --- | --- |
| Seed manifest SHA256 | `b19c9c644d21b9a8700ff1628beb1516aa286f1f4f0b917f2a94dd893868a202` |
| Seed canonical682-artifact identity | `1d56fa167a1a296a680bd22bba4f5223e4d2a90fe099dc38fe8a1703b046120d` |
| New manifest SHA256 | `ed23ccde95a89081c1c19f3de39ee9199a50b15eacf0647e316f62acf1f97b84` |
| New canonical697-artifact identity | `a84a27a2f5f9d9bed4af8dbf56a04a91b2910580f66c67952362d215f62d0b22` |
| New files | Six exact JARs, six matching POMs, three required parent POMs |
| Candidate payload | 74,846,407 bytes |
| Files rounded to4KiB | 76,288,000 bytes |
| Directory allocation estimate | 3,244,032 bytes |
| Maven metadata reserve | 16,777,216 bytes (16MiB) |
| Total estimated runtime usage | 96,309,248 bytes (91.85MiB) |
| Existing tmpfs cap | 134,217,728 bytes (128MiB), unchanged |

**FITS_128_MIB**, with37,908,480 estimated bytes remaining. This is a conservative
allocation/reserve estimate, not an actual tmpfs runtime measurement; the future
sandbox cap remains authoritative. The2GiB build-container limit was not changed.

Private candidate cache:
`/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_5_1/2026-10-18/recovery-1/repository/`.
All682 seed files were independently copied, with different inodes; every one of
the697 artifacts was rehashed and rechecked for coordinates, checksum provenance,
POM integrity or JAR CRC. Checksums establish same-origin Central consistency over
TLS; independent publisher signatures are not claimed. Canonical identity uses
sorted lines `SHA256  bytes  relative_path\n`, UTF-8, then SHA256.

## Resource and request accounting

The one sequential batch used **52/160 requests** and **452,175/50,331,648 response
bytes**, including checksum probes. New artifact bytes total451,223. There were22
checksum404 responses and no transport retries; missing stronger sidecars used
the established published-checksum fallback. Eleven new artifacts use published
SHA1 checksums; four use SHA512. All have locally computed SHA256 identities.
No weak checksum is represented as an independent publisher signature.

Acquisition peak RSS was40,572KiB, with an enforced1GiB address-space cap and CPU0
only. Elapsed recorded acquisition/setup time was84.29s against600s. The static
audit peak was40,936KiB. Host available RAM was7,583,564KiB at admission and
7,658,872KiB after acquisition; available disk after acquisition was19,968,757,760
bytes. New private task storage at the static audit was79,538,689 bytes against
256MiB; final publication-time accounting is in the resource receipt. Individual
responses remained below32MiB. No concurrent Maven/Java/Sonar workload was found
at admission. HTTPS I/O was allowlisted, proxy-free and redirect-rejecting, with
15s request timeouts. Requests were atomically recorded before network I/O.
Unused request allowance is not permission for another batch.

Before the first HTTP request, the initial inventory comparison exposed a Python
tuple-versus-JSON-list equality defect. It stopped with zero requests, zero bytes
and all682 seed copies verified. The comparison was normalized, a regression test
was added, and acquisition continued on the same ledger/copies with original
elapsed time retained. No request count, allowance, old claim or cache was reset;
no second network batch or compile attempt occurred. The correction receipt is
published separately. New acquisitions are non-resumable by the public CLI.

## Tests and preservation

**507 passed, zero failures/errors/skips in each checkout**, including28 new
E.0.5.1 tests and every relevant E.0–E.0.5 recovery/sandbox regression. Tests cover
exclusive path ownership, symlink/wrong-root rejection before writes, independent
copies, integrity/provenance failures, checksum request accounting, budgets,
redirect/path policy, descriptor/embedded identity and goals, static UNKNOWNs and
no artifact execution. Synthetic test fixtures are not real dependency evidence.

Two fresh offline audits were byte-identical and left the sealed ledger unchanged.
Their SHA256 is `0763458e697c5a92521bffadc353c734595c7c832a10944ccd3942372ea39b67`.
[Verification](examples/phase5_2_2_e_0_5_1/verification.json) and
[preservation](examples/phase5_2_2_e_0_5_1/preservation.json) record the checks.

Preservation PASS covers all117 Git blob/mode/source identities, frozen T0
commit/tree/POM and D.3 model/profiles, all previous task files/caches/claims,
request ledgers2000/400/52/112/56/12,6,262 user-cache entries and75 independently
rehashed reference artifacts,56 frozen research bundles/322 artifacts, two
Phase5.1 bundles, source database and model checkpoint hashes, the original
SonarQube server/volumes and unrelated files. No task containers existed or needed
cleanup. Four preexisting untracked remediation files were preserved. The original
project HEAD remains unchanged; only the canonical publication checkout gets the
normal descendant commit. New source/tests/evidence are mirrored into the project.

## Files and reproduction

Only new paths are added:

- `tools/recover_buildplan_frontier.py`: versioned six-plugin adapter, exclusive
  task-path ownership, independent seed verification, one-at-a-time acquisition,
  per-plugin sealing, static descriptor audit and read-only offline audit.
- `tests/test_buildplan_frontier_recovery.py`:28 deterministic tests.
- This report and `examples/phase5_2_2_e_0_5_1/`: full metadata manifest, before/after
  inventory, descriptor verification matrix, parent/BOM closure, runtime UNKNOWNs,
  capacity/resources, preservation/tests/source identities and E.0.6 handoff.

No old code, report, dependency cache, POM or research artifact was rewritten.
Third-party dependency payloads, raw runtime files and credentials stay outside Git.

Read-only reproduction from the project directory:

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 120s taskset -c 0 \
  prlimit --as=1073741824 --cpu=100 --fsize=33554432 -- \
  .venv-forecast/bin/python -m tools.recover_buildplan_frontier \
  --audit-only --output /home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_5_1/2026-10-18/recovery-1
```

The audit requires the private cache; GitHub contains reproducible identities,
metadata and tests rather than third-party binaries. Do not rerun acquisition
against this consumed directory or automatically authorize a fresh budget.

Targeted tests (no downloads/Maven/Java):

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 180s taskset -c 0 \
  prlimit --as=1073741824 --cpu=120 --fsize=33554432 -- \
  .venv-forecast/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_buildplan_frontier_recovery.py tests/test_buildplan_plugin_recovery.py
```

The complete507-test command list and run timings are captured in the verification
receipt and the local regression logs. The test files are the Phase5 multilingual
foundation/preflight/scope, TaskA/B/D/D.1/D.2/D.3, E.0 sandbox, E.0.2/E.0.4 compile
adapter, E.0.3 test-dependency recovery, E.0.5 and E.0.5.1 suites.

## Remaining gates and handoff

The smallest next step is a separately authorized **E.0.6 single T0 offline compile
attempt**, using the697-artifact cache and unchanged original lifecycle/security/
resource limits. Its adapter must update the seed count and hashes; it must stop
on the first outcome without acquisition or retry. Actual plan resolution may
succeed while a later plugin realm still lacks an artifact. Detached-export SCM
behavior, compiler execution and Java8 class completeness are not yet established.
See [E.0.6 handoff](examples/phase5_2_2_e_0_5_1/E_0_6_HANDOFF.md).

SonarSource/analyzer licensing and derived-dataset rights gates remain unresolved.
No scans, model work, data admission or Phase5.3 action is authorized. E.0.5.1 stops
at recovery, static verification and GitHub publication.
