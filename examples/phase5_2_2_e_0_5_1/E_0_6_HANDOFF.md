# E.0.6 — separately authorized single T0 compilation

E.0.5.1 has stopped. No compilation or Maven invocation ran. Static descriptor
availability is verified; actual Maven plan, runtime classpaths, SCM behavior and
compilation remain unproven. Do not run this handoff without separate authorization.

Use the new697-artifact cache, not an old653/679/682 hard-coded seed count:

- Private repository: `/home/hp/tst/research/forecasting_mvp/phase5_2_2_e_0_5_1/2026-10-18/recovery-1/repository`
- Manifest SHA256: `ed23ccde95a89081c1c19f3de39ee9199a50b15eacf0647e316f62acf1f97b84`
- Canonical cache SHA256: `a84a27a2f5f9d9bed4af8dbf56a04a91b2910580f66c67952362d215f62d0b22`
- Runtime estimate:96,309,248 bytes including16MiB reserve, against128MiB.

Reverify all697 hashes, provenance/checksum records, POM identities and JAR CRCs.
Construct independent copies in a new task directory/claim. Preserve every old
cache, ledger, report and compilation claim. Do not reuse E.0.2/E.0.4 claims.

Preserve T0 commit `4ff0d4adbc2161677e71050ba23c152831f6ad83`, tree `ac7521be84b2820a83f7b960d329a15521408214`,
historical POM `b75fb9813e3c06121caa7d84c31a471b646465966079cf10ec4c7a2e4aba55f2` and117 source identities.
D.3 effective POM remains `bf4a9243703b32ca363232c2759c8bab4f009ac544897dafab87f4b22f42e449`.
Use pinned Maven3.9.11/Temurin17.0.17+10, Parent76, Java release8,
`maven.test.skip=true`, no explicit profiles or manufactured Git metadata.

Prepare/test a new versioned adapter using proven E.0.2/E.0.4 sandbox logic,
keeping UID/GID1000 owned tmpfs and stage EXIT-trap/log capture. Do not change the
original lifecycle, plugin versions, enforcers, RAT, check-buildplan or its tasks.
The new plugin pairs are descriptor metadata; do not execute tests/install/deploy,
SBOM/SPDX generation, Moditect or Felix goals merely because they are now cached.

Admit >=4GiB available host RAM, >=2GiB host headroom, adequate disk and no prohibited
concurrent workloads. Keep2GiB container/768MiB heap/1CPU/64PIDs/no extra swap,
read-only root, dropped capabilities/no-new-privileges, UID/GID1000, owned bounded
noexec/nosuid/nodev tmpfs, network disabled, no Docker socket/credentials/user cache,
local pinned image only,240s Maven ceiling and bounded logs/outputs. Recheck the
128MiB repository tmpfs fit; never enlarge limits silently.

Only a separately authorized one-attempt command may execute:

```bash
/usr/share/maven/bin/mvn --offline --batch-mode --no-transfer-progress --errors \
  -s /inspection/settings.xml -gs /inspection/settings.xml \
  -Dmaven.repo.local=/runtime-repository -Duser.home=/tmp \
  -Dmaven.test.skip=true -Dmaven.compiler.release=8 compile
```

Capture stage/stdout/stderr/exit/resource/OOM evidence and exact first failure,
plugin execution order, classpath/SCM evidence, source/cache post-hashes and any
classes. Stop on the first result without acquisition, correction or retry. Only
Maven exit0 plus observed compiler and verified expected Java8 major52 production
class identities/completeness can establish COMPILE_PASS. Missing plugin runtime
artifacts remain possible despite zero missing static descriptor paths.

No other revision, Sonar/server/scan, model, dataset admission or Phase5.3.
Unresolved analyzer licensing and derived-dataset rights gates stay unchanged.
