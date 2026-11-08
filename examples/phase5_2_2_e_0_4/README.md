# E.0.4 single offline T0 attempt

**BLOCKED_DEPENDENCY.** Exactly one offline Maven compile command ran. Both
enforcer checks and RAT passed. Artifact3.5.1 check-buildplan failed while resolving
Felix maven-bundle-plugin5.1.9. Its later process-classes goal did not execute.
No compiler, test compilation or class output was reached.

The five missing paths are one fatal plugin JAR plus four POM warnings. Three
warnings occurred during successful RAT; they are not fabricated fatal JAR errors.
The 679 artifact seeds and 117 frozen source files remained unchanged. Cache
metadata additions:0. Complete full private stdout/stderr stay outside Git;
`maven_failure_excerpt.txt` is explicitly a sanitized diagnostic excerpt.

`resource_evidence.json` records actual bounded resource and OOM observations;
`capture_completeness.json` verifies capture. `preservation.json` separates passing
protected research/source/cache/Sonar checks from a shared Docker inventory change:
an unrelated container was destroyed before the E.0.4 container was created.
The task's cleanup targeted only its own labelled disposable container.

No recovery download, retry, other revision, Sonar/server/scan, model or data
admission ran. See the report and next-step handoff; later work requires separate
authorization. Analyzer licensing and dataset-rights gates remain unresolved.
