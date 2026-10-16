# Task E.0 — one blocked T0 build-container attempt

**BLOCKED_BUILD_OR_RESOURCE**: the setup wrapper exited123 before Maven.
Docker daemon events prove exactly one startup and its exit. No second container
or Maven attempt ran. No lifecycle plugin, dependency resolution or compiler result
is claimed. There is no missing-artifact finding; that stage was not reached.

The known setup ownership defect is documented in the report and failure manifest.
Exact setup stderr and peak cgroup memory were not captured; absence of evidence
is explicit. The complete original attempt receipt is retained without rewriting
it. The failure manifest supplements it with authoritative daemon events.

All117 source identities and653 artifacts were independently reverified/copied.
Prior caches/ledgers and original experiments remain unchanged. Third-party source,
POM/JAR bytes, runtime cache and private attempt records remain outside Git.

The controller's attempt claim is exhausted. Do not rerun it or create another
build workspace automatically. The proposed ownership/capture correction and a
new one-container attempt require a separately authorized continuation.
