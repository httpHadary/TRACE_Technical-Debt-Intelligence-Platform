# E.0.6 — single T0 offline compile

**COMPILE_PASS.** One original Maven compile lifecycle ran in the pinned,
network-disabled2GiB sandbox. Both Maven and Docker exited0. Check-buildplan passed;
26 production Java sources produced37 verified Java8 class files:25 top-level,
11 nested and package-info. Two nonclass license/notice resources are separate.

All117 source identities/modes and697 artifact bytes are unchanged. No artifact
was downloaded, no retry ran, and the owned container was removed after complete
capture. Both555-test regression runs and preservation checks passed.

Known nonfatal observations:three RAT POM warnings, configured detached-SCM
fallbacks and Jansi/noexec. Remote-resources was invoked and skipped internally
under original configuration. The compiler's runtime classpath was not logged;
its exact argument vector is unavailable, not invented. No test/package/deploy or
later-phase plugin goal ran. This proves T0 compile readiness only.

Metadata, hashes, selected sanitized lifecycle lines and test receipts are
published. JARs, raw logs, class binaries and private runtime files remain outside
Git. Other revisions and scans need separate authorization. Analyzer licensing
and derived-dataset rights remain unresolved.
