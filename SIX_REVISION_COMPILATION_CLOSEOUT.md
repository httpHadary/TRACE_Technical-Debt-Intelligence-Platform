# Commons CLI compilation closeout — read-only reference

The authoritative existing result is COMMONS_CLI_SIX_REVISION_COMPILE_GATE_PASS.
No new compilation or duplicate compilation gate is created by Phase C.

Authority: [E.5.1 gate receipt](examples/phase5_2_2_e_5_1/six_revision_compile_gate.json),
SHA256 `fd823a20395367f20afe4aa458dfb17b0a541204d575891e622054c5b88e1925`.
[Original report](PHASE_5_2_2_E_5_1_REPORT.md) and
[original handoff](examples/phase5_2_2_e_5_1/SIX_REVISION_COMPILATION_HANDOFF.md) remain unchanged.

| Offset | Commit | Tree | Original POM SHA256 | Registered input | Verified output |
| --- | --- | --- | --- | --- | --- |
| T-90 | `e1529b546d9696192f4de52152777403b4a01b39` | `c1a67e730fc5729a5376c267ed559f4ae310df01` | `f4403aa060f16ca0f17d28fffb1bc6fcc42c31d480af8dc6a6436f25fddf8f15` | 116 tracked / 26 Java | 37 classes |
| T-30 | `fb6293fcd6a9b55ac8ecb550af6572daaed18fa1` | `598dec4901a9adcf8e55b241c9689a8db6219c29` | `2f322b0751115f2a5e93aabfb83372dc0511d57bbd8b4f178f08d5b449ff3fcf` | 116 tracked / 26 Java | 37 classes |
| T0 | `4ff0d4adbc2161677e71050ba23c152831f6ad83` | `ac7521be84b2820a83f7b960d329a15521408214` | `b75fb9813e3c06121caa7d84c31a471b646465966079cf10ec4c7a2e4aba55f2` | 117 tracked / 26 Java | 37 classes |
| T+30 | `7ddf691ac2afbda7473c0d07f1f4e7ae1e69e47b` | `a2ff09febdac9da6e6ee422a9144ad09d81113bf` | `674975083520370c7a691778fa6fcdfe2eb0ae672c48abc923ffc75688c73e8e` | 137 tracked / 36 Java | 55 classes |
| T+60 | `aad30eff27ac5c9a13194125226653c6c2826c58` | `d7434665397c8dd8156fff7ecaed29a14feeb951` | `1c82171f91da0f4aa2994bb367e4c9ef8e65414940100be081715605739d9e0b` | 138 tracked / 36 Java | 55 classes |
| T+90 | `af2b3e72a552cfb2a902556469868763ddea3638` | `0d773516c1c7bb0a371b2af6e084b62ef2d36546` | `87c8ed93cb21deedb52b826d520931bc175e24e5ee48643c6a21ed154c62324b` | 138 tracked / 36 Java | 55 classes |

Each record independently documents the original offline lifecycle through compile,
Maven/Docker exit0, actual compiler input/output evidence, immutable input checks,
claim/archive hashes and its own read-only verifier. All six consumed attempt
claims remain preserved. Existing records and private archives are rechecked,
not rerun. Class counts are observed outputs, never cross-revision acceptance
conditions. Major52 Java8 structures, source ownership and compiler-created-file
population are verified; these are not upstream tested behavior or separate JVM
bytecode-execution certification. No test/package/install/deploy/site success is asserted.

Pinned environment: Maven3.9.11, Temurin17.0.17+10, release8,
maven.test.skip=true, no explicit profiles, original POM and detached source.
Sandbox: container2GiB, heap768MiB, CPU1, PIDs64, no extra swap, UID/GID1000,
network none, read-only root, dropped capabilities, no-new-privileges, owned bounded
noexec/nosuid/nodev tmpfs, repository128MiB, Maven240s. Original SCM fallbacks are
not lineage. T+90 actual profile enumeration/effective-POM/classpath remain unavailable.

No scan or native debt measurement for this18-state study was produced by these
compilations. Source/scanner compatibility, server mode, analyzer domains, rights,
resources, credentials and first-scan authorization remain separate gates.
Phase C grants no execution or legal/policy permission. [Decision dossier](PHASE_5_2_2_C_RIGHTS_DECISION_REPORT.md).
