# E.5.1 handoff — separate authorization required

E.5 stops at PASS_STATIC_T_PLUS_90_READINESS. No Maven, Java, container, compiler, scan or model ran.
Five of six pinned historical states have independently verified COMPILE_PASS.
T+90 has NOT been compiled. E.5 does not finish the six-revision compilation gate.
This document grants no execution, compilation or additional acquisition authority.

Target: apache/commons-cli T+90.
Commit: `af2b3e72a552cfb2a902556469868763ddea3638`
Tree: `0d773516c1c7bb0a371b2af6e084b62ef2d36546`
POM SHA256: `87c8ed93cb21deedb52b826d520931bc175e24e5ee48643c6a21ed154c62324b`
Source: `/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_5/2026-10-19/source` — 138 tracked files, 36 production Java sources.
Commons Parent78 → Apache Parent33. No manufactured Git metadata or POM edits.
Two production sources differ from T+60: CommandLine.java and Option.java.
Derive expected classes from T+90 declarations. Do not require 55 classes or reuse earlier output hashes.

Cache: `/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_5/2026-10-19/recovery-1/repository` — 758 artifacts.
Manifest SHA256: `eb471e18cca6828bb2abbe2273184faaa693298807363b0280630cb180a6adba`
Canonical SHA256: `df9f176ceeea2f165cbf463dd3eb43675741b0932d1134c756386f0f7259462d`
All 753 seeds are unchanged independent copies. Five artifacts were added:
Commons Text1.13.0 POM/JAR, Commons Lang3.17.0 POM/JAR and Commons Parent73 POM.
The acquisition batch is sealed at 17 requests, 281390 response bytes.
Never resume it, reset it or use unused budget for another batch.
All 20 original build-plan descriptors and known required static paths are present.
Actual effective POM, active profiles, Maven-mediated plugin realms/classpath,
SCM behavior, compiler arguments and output identities remain UNKNOWN.

The initial conservative qualification was PARTIAL because Commons Text declares
three own-test profiles. A fail-closed metadata proof now verifies all three add
only test dependencies and cannot change non-test dependency coordinates through
profile properties. Runtime activation is still UNKNOWN. Raw audits, initial
receipt, manifest, ledger and acquisition transport remain unchanged. See
profile_scope_verification.json and initial_frontier_comparison.json.

After separate explicit E.5.1 authorization, create a new target-specific adapter,
verifier, task owner, independent input copies and fresh exclusive one-attempt claim.
Do not reuse consumed runners or claims. Reverify 138 source modes/blobs and all
758 artifact coordinates, hashes, provenance, XML/ZIP/descriptor metadata.
Use only the pinned local Maven3.9.11 / Temurin17.0.17+10 image, Java release8,
maven.test.skip=true and no explicit profiles. Preserve the complete original
compile lifecycle, Enforcer, RAT, check-buildplan deploy-task behavior, remote
resources, Build-helper, Buildnumber, Antrun, Resources and Compiler. No skips,
SCM workaround, property substitutions, dependency upgrades or preliminary Help goals.

Require immediately before startup: >=4 GiB host available RAM, >=2 GiB headroom
beyond the container, adequate disk, no prohibited workloads, verified local image
and fresh input/cache checks. Retain container2 GiB, heap768 MiB, CPU1, PIDs64,
no additional swap, UID/GID1000, dropped capabilities, no-new-privileges, read-only
root and network disabled. No credentials, Docker socket or user-cache mounts.
Use owned size-bounded noexec/nosuid/nodev tmpfs, repository128 MiB, timeout240s.
Current estimated repository occupancy: 103,452,672 bytes
including 16 MiB metadata reserve; this is not an actual future tmpfs measurement.
Recheck live. Do not raise limits or stop unrelated services to gain admission.

Only one separately authorized original offline compile invocation may then run:

```bash
/usr/share/maven/bin/mvn --offline --batch-mode --no-transfer-progress --errors -s /inspection/settings.xml -gs /inspection/settings.xml -Dmaven.repo.local=/runtime-repository -Duser.home=/tmp -Dmaven.test.skip=true -Dmaven.compiler.release=8 compile
```

Preserve MAVEN_OPTS=-Xms32m -Xmx768m -XX:ActiveProcessorCount=1 -Duser.home=/tmp.
Capture actual lifecycle banners, separate streams, failures, cache metadata,
resource/exit evidence and compiler input/created-file lists. Verify source and
artifact post-run integrity. COMPILE_PASS requires actual original lifecycle
success and independently parsed complete Java8 major52 class outputs, with
nested/anonymous/synthetic/package-info ownership derived from this target.
A failure ends the attempt: no retry or acquisition is pre-authorized.

No SonarQube/scanner, debt collection, forecasting, dataset admission or Phase5.3
follows this handoff. Analyzer licensing and derived-data rights remain
UNRESOLVED_UNCHANGED.
