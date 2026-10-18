# E.0.3 recovery handoff — not executed

E.0.2: **BLOCKED_DEPENDENCY** after one actual offline Maven compile invocation.
The exact five test-scoped roots need POMs and JARs. Ten currently absent paths are
in `failure_manifest.json`. Parent/BOM/transitive versions are not yet established
because these POMs are missing; do not guess a closure or declare build readiness.

A separately authorized smallest recovery should:

1. Inspect only previously approved local sources for these exact artifacts, then
   use the allowlisted Maven Central endpoint if acquisition is needed. Verify
   coordinates, source identity, checksums, POMs and JAR CRCs before admission.
   No approved/provenance-complete local replacement is assumed to exist.
2. Use a new isolated cache seeded with independently verified copies of the653
   admitted artifacts, with a fresh explicit request/byte/time/storage budget and
   one acquisition worker. Preserve D/D.1/D.2/D.3 ledgers2000/400/52/112 and E.0,
   E.0.1/E.0.2 claims. Do not overwrite user caches or old research caches.
3. Recover the exact listed POM/JAR roots and only parent/BOM/runtime dependencies
   exposed by authoritative POM/descriptor evidence. Keep unknown profiles explicit.
   Do not execute Maven goals, plugins or builds during acquisition; do not select
   newer versions, skip enforcers or delete declared test dependencies.
4. After recovery, a separately authorized new single T0 attempt may recheck the
   original offline lifecycle. Preserve release8, `maven.test.skip=true`, profiles,
   detached source context, command and resource/security bounds. Missing SCM or
   further runtime dependencies remain possible. Do not infer success from static
   frontier completion. Compile the other revisions only after separate approval.

No acquisition, build retry, SCM correction, Sonar operation, scan, model or dataset
admission is authorized by this document. Analyzer licensing/rights gates remain.
