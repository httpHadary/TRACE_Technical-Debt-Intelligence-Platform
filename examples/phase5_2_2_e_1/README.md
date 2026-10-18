# E.1 — T−30 static Maven readiness

**PASS_STATIC_T_MINUS_30_READINESS.** All known static paths are present in a new
710-artifact cache:697 unchanged independent seeds plus13 exact additions. Four
root pairs, the Surefire3.4.0 parent and JUnit Platform1.11.0 POM/JAR pairs were
verified. All20 target build-plan descriptors and12 test-dependency candidates
are verified. No Maven/Java/container or compilation ran.

T−30 is Parent74/buildnumber3.2.0/Surefire3.4.0/JUnit5.11.0/CommonsIO2.16.1, not
T0's effective model. The116 source files and original POM are verified; actual
T−30 effective-model hash and active profiles remain unavailable/unverified.

An initial conservative PARTIAL result is retained. Read-only qualification
confirmed its SSHD OS-profile issue changes only that dependency's own Surefire
configuration and cannot propagate into Commons CLI dependencies. Its activation
remains UNKNOWN. The managed default resources plugin is unchanged; that audit
comparison was corrected without new requests or ledger/cache changes.

32 requests /1,536,669 response bytes; cache estimate97,898,496 bytes including
16MiB reserve, below128MiB. Both589-test runs and preservation checks passed.
Binaries/raw caches stay outside Git. E.1.1 needs separate authorization and a
new116-source/710-artifact adapter; no T0 effective-model hash or claim reuse.
