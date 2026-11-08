# Next authorization: targeted build-plan descriptor recovery, not a compile retry

E.0.4 is BLOCKED_DEPENDENCY after exactly one original offline T0 compile command.
Both enforcer checks and RAT succeeded. The first fatal failure is Artifact3.5.1
`check-buildplan` while obtaining Felix maven-bundle-plugin5.1.9 metadata/JAR.
No compiler or SCM/buildnumber command was reached. No further task is authorized
by this handoff.

The smallest separately authorized recovery should:

1. Start from the actual E.0.4 failure manifest and complete private logs. Create
   a new outside-Git cache from independently reverified copies of the679 admitted
   artifacts. Preserve E.0.4's consumed claim and all previous ledgers/caches.
2. Prioritize exact `org.apache.felix:maven-bundle-plugin:5.1.9` POM and JAR. Its
   frozen `manifest` execution is bound to `process-classes`, after `compile`.
   Nevertheless, the actual validate-phase check-buildplan requested its descriptor.
   Do not remove the execution or skip check-buildplan to bypass this requirement.
3. Inspect that exact POM/JAR descriptor, parent/BOM imports and authoritative
   dependency declarations as data only. Distinguish descriptor/plan metadata from
   runtime JARs actually needed through compile. Do not automatically download the
   entire later-phase plugin runtime graph or claim the manifest goal executed.
   Additional necessary coordinates remain UNKNOWN until this evidence exists.
4. Separately audit the exact missing POM warnings emitted during successful RAT:
   `log4j:log4j:1.2.12`, `logkit:logkit:1.0.1`,
   `avalon-framework:avalon-framework:4.1.3`. These are POM warnings, not observed
   fatal JAR errors. Do not infer that each corresponding JAR is required.
5. Check approved local bytes first, admitting only provenance/checksum/coordinate/
   CRC-verified artifacts. If acquisition is explicitly authorized, use only the
   established HTTPS Maven Central endpoint with a new fixed request/byte/time/
   disk ledger, one worker, one CPU and <=1GiB process address space. Preserve exact
   versions and old 2000/400/52/112/56 ledgers; never reset budgets. Do not execute
   Maven, JARs or plugins during recovery.
6. Publish a bounded static closure/frontier receipt that keeps dependency/profile
   uncertainties visible. Static completion is not offline build success.

Only after separate later authorization may a new versioned adapter and fresh claim
run one more T0 attempt. Preserve the exact command, release8, testskip=true,
Parent76, Maven3.9.11/Temurin17.0.17+10, pinned image, detached117-file source tree,
2GiB container/768MiB heap/1CPU/64PIDs/no additional swap, owned noexec tmpfs,
128MiB repository limit, no network/credentials/socket, >=4GiB host RAM admission,
>=2GiB runtime host headroom and240s Maven timeout. Recheck capacity for any additions.
Never reuse E.0.4 or automatically correct SCM/build/dependency failures and retry.

No other revision, Sonar/server/scan, debt measurement, model, dataset admission or
Phase5.3 work is authorized. RAT's license-header result does not resolve
SonarSource licensing or derived-dataset rights gates.
