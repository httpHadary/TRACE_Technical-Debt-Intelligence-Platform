# E.0.6 single-T0-compilation handoff — not executed

E.0.5 recovered the exact Felix5.1.9 descriptor/POM/JAR and parent metadata.
It did not prove complete build-plan readiness. Six other frozen plugin POM/JAR
pairs remain missing in `plan_after.json`:Surefire3.5.0, Install3.1.2, Deploy3.1.2,
CycloneDX2.8.1, Moditect1.2.2.Final and SPDX0.7.4. These are static plan candidates,
not actual new Maven failures. The next compile may stop at another descriptor.
Do not automatically acquire these or claim the broader closure is complete.

A separately authorized E.0.6 attempt should:

1. Verify manifest SHA256 `b19c9c644d21b9a8700ff1628beb1516aa286f1f4f0b917f2a94dd893868a202` and canonical682-file cache
   identity `1d56fa167a1a296a680bd22bba4f5223e4d2a90fe099dc38fe8a1703b046120d`, then recheck provenance/checksums,
   POM coordinates, JAR CRCs and independent copies. Keep E.0.3/E.0.5 and earlier
   caches and request ledgers2000/400/52/112/56/12 unchanged.
2. Create a new versioned adapter/claim for682 files. Preserve the117 frozen T0
   source files, commit/tree/POM/D.3 identities and detached source context.
   Never reset/reuse E.0.2/E.0.4 attempts or repurpose smoke mode.
3. Re-admit >=4GiB host available RAM with2GiB headroom, pinned local Maven3.9.11/
   Temurin17.0.17+10 image,2GiB container,768MiB heap,1CPU,64PIDs,no additional swap,
   UID/GID1000,dropped capabilities,no-new-privileges,read-only root,owned noexec
   tmpfs,no network/socket/credentials/user cache,240s Maven ceiling and original
   bounded outputs. The682-file estimate is95,735,808 bytes including16MiB reserve,
   below128MiB. Recheck actual capacity and concurrent workloads before startup.
4. Run only the exact original offline `compile` command, release8,testskip=true,
   Parent76,no explicit profiles. Keep enforcer,RAT,check-buildplan and all original
   bindings. Do not change `check.buildplan.tasks` or skip checks to avoid later
   descriptor lookups. Do not execute deploy/package/test goals themselves.
5. Capture complete bounded setup/Maven streams, goal order,first failure,exact
   missing coordinates,SCM/classpath evidence,exits,source/cache hashes and actual
   cgroup/OOM/resources before owned cleanup. Any failure ends the one attempt;
   no automatic acquisition/correction/retry. Only actual compiler/class identity/
   structure/major52 verification can establish COMPILE_PASS.

If the priority is avoiding another known descriptor blocker, request a separately
bounded metadata-only recovery for the listed exact plugin pairs before authorizing
compilation. Its own parents/imports may expose more metadata; no version guesses
or unrestricted runtime download is justified. E.0.5 has stopped; unused request
allowance is not a continuation authorization.

No other revision,Sonar/server/scan,model,debt measurement,dataset admission or
Phase5.3 action is authorized. SonarSource licensing and dataset rights stay open.
