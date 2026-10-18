# E.0.2 — one genuine offline T0 compile attempt

**BLOCKED_DEPENDENCY**. Maven launched with the exact registered `compile` command.
Project dependency resolution failed on five test-scoped roots: JUnit Jupiter
API/engine/params5.11.1, Commons IO2.17.0, Mockito4.11.0. Their five JARs and five
POM descriptors are absent from the registered offline cache. No recovery/retry ran.

Setup/capture/cleanup succeeded. Actual plugin execution order is empty; enforcers,
RAT, resources, SCM/buildnumber and compiler were not reached. No classes appeared
in the complete post-build file inventory. The exact command retained test skipping;
that setting did not avoid this observed dependency-resolution requirement.

Full small setup and Maven stdout/stderr are retained as text; they are not
truncated. Private raw controller status was provisional; publication's final
status comes from evidence classification, and the original receipt hash is bound.
Frozen inputs/ledgers remain unchanged; writable-cache comparison is separate.

No dependency binary, Java class, historical source or raw private inspection is
published. Resource peaks are real EXIT-trap snapshots, not invented full-lifetime
post-cleanup measurements. E.0/E.0.1 claims and historical smoke sentinel stay intact.
