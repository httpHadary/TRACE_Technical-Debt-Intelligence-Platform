# E.0.4 single-attempt handoff — not executed

E.0.3 recovered all five exact observed roots and their authoritative static
test-dependency closure. Status: STATIC_TEST_DEPENDENCY_CLOSURE_COMPLETE.
**Offline Maven build readiness remains UNKNOWN. No compile retry is authorized
by this handoff or by E.0.3.**

When separately authorized for one E.0.4 attempt:

1. Verify E.0.3 `dependency_manifest.json` SHA256 `73de04d94fe2a1c85fd49f38bfdc14df47e0f93855a8ac5258a10d72f714b113`
   and the independent cache identity `f4bc6cbab0f8e0bc14557408173290a8453854c35226b40348bffe7a58011daa`.
   Reverify all 679 artifact hashes, Central provenance/checksums, POM coordinates
   and JAR CRCs. Preserve E.0.3 and all earlier caches/ledgers. Build a fresh runtime
   repository from independent copies; never reuse or reset an old attempt claim.
2. Extend the tested sandbox with a separately named/versioned E.0.4 adapter,
   registration and command allowlist for the 679-file candidate cache. Do not
   call the archived E.0 runner, repurpose E.0.1 smoke mode, or retry E.0.2. Test
   policy and evidence capture without running Maven before the one admitted attempt.
3. Reverify the exact 117 tracked T0 source files, commit
   `4ff0d4adbc2161677e71050ba23c152831f6ad83`, tree
   `ac7521be84b2820a83f7b960d329a15521408214`, historical POM and D.3 effective-model
   hashes. Keep Commons Parent76, Maven3.9.11, Temurin17.0.17+10, release8,
   testskip=true, no explicit profiles and detached export with no synthetic Git.
4. Immediately re-admit >=4GiB host available RAM, >=2GiB headroom beyond the
   2GiB container, bounded disk and no concurrent prohibited workload. Use the same
   pinned local image, UID/GID1000, 1CPU, 64PIDs, no additional swap, 768MiB heap,
   no capabilities/new privileges, read-only root, owned size-capped noexec tmpfs,
   no network/socket/credentials/user cache and 240s Maven ceiling. Recheck that
   74,152,353 bytes of artifact payload plus bounded metadata fit the registered
   runtime-repository tmpfs. Do not weaken the registered storage limit.
5. Run exactly the original offline `compile` command from E.0.2. Do not skip
   enforcer/RAT/remote-resources/buildplan/build-helper/buildnumber/antrun/resources/
   compiler, change dependency versions/POM/profiles, run tests or add goals.
6. Capture setup and Maven streams separately, exact missing coordinates, actual
   plugin order/SCM behavior, cache/source hashes, exit/OOM/resources and bounded
   evidence before owned cleanup. An early missing artifact or SCM/build failure
   ends that attempt. No automatic acquisition, fix or rerun.
7. Only if Maven succeeds, verify expected top-level and nested class identities,
   valid class structure/major52, no test compilation, compiler/classpath evidence
   and unchanged source/POM/seed bytes before claiming COMPILE_PASS.

The known test dependency frontier is closed. Plugin runtime/classpath behavior,
SCM/buildnumber and eventual compilation remain unproven. Existing broader profile
uncertainties, analyzer licensing and derived-dataset rights gates remain unchanged.
No other revision, SonarQube, scans, debt labels, models or Phase5.3 is authorized.
