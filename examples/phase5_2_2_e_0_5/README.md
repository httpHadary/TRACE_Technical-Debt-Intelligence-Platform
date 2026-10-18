# E.0.5 targeted Felix build-plan recovery

**RECOVERED_EXACT_FELIX_PLUGIN**. The new cache has682 verified files:679 unchanged
seeds plus Felix5.1.9 POM/JAR and Felix Parent7 POM. Only12 requests and242,951
response bytes were used. The candidate fits the unchanged128MiB runtime tmpfs.

Felix runtime dependencies are recorded, not downloaded en masse:the observed
build-plan lookup reads a descriptor, and the manifest goal is after compile.
Six other plugin POM/JAR pairs remain absent from the static deploy-plan inventory.
Therefore STATIC_BUILD_PLAN_CLOSURE_COMPLETE and offline-build readiness are not
claimed. See `plan_after.json` and `frontier_comparison.json` for exact paths.

Three RAT POM warnings remain classified as nonfatal with no proven need for
acquisition. Cached declarations show candidate paths via Doxia/Velocity Tools/
Commons Logging1.1; this does not assert Maven's final mediated classpath.

No Maven, Java, container, scan, model or compilation retry ran. Evidence includes
hashes/provenance, descriptor/embedded metadata identity, parent chains, runtime
classification, capacity, resource accounting, tests and preservation receipts.
No dependencies, third-party binaries, raw private logs or credentials are in Git.
The E.0.6 handoff requires separate authorization; rights gates are unchanged.
