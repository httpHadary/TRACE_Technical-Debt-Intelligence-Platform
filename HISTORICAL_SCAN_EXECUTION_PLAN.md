# Historical collection execution plan — Phase 5.2

**PLAN ONLY — collection is BLOCKED and not authorized in Phase5.2.**
Date: 2026-10-15. Existing schema2 contracts remain frozen. No command in the
future-job specification below was used to build or scan a historical revision.

## Frozen study intent and states

Three development families only: Commons CLI (Java-dominant), Click
(Python-dominant), Django Browser Reload (genuine Python+JS). The latter is not
JS/TS-dominant. T0 is **2024-10-01T00:00:00Z**, chosen from historical metadata,
with exact UTC offsets −90/−30/0/+30/+60/+90 days.

[`selected_source_plans.json`](examples/phase5_2/selected_source_plans.json)
contains every full40-character commit/tree ID, ref-observation clock, lineage
hash, raw inventory hash, production inventory hash and missing-scope evidence.
[`readiness_manifest.json`](examples/phase5_2/readiness_manifest.json) enumerates
all18 planned jobs, deterministic future project keys, expected source counts,
resource limits and gate statuses. Those files are the executable plan inputs,
not a statement that jobs or analyses exist.

| Offset | Exact cutoff UTC | Commons CLI commit | Click commit |
| --- | --- | --- | --- |
| −90 | 2024-07-03T00:00:00Z | `e1529b546d9696192f4de52152777403b4a01b39` | `14f735cf59618941cf2930e633eb77651b1dc7cb` |
| −30 | 2024-09-01T00:00:00Z | `fb6293fcd6a9b55ac8ecb550af6572daaed18fa1` | `99015e1456b6952054fda8312b40ea646737168d` |
| 0 | 2024-10-01T00:00:00Z | `4ff0d4adbc2161677e71050ba23c152831f6ad83` | `4a758f5c38636ecd9d030356d85bcca3d8fbd0ca` |
| +30 | 2024-10-31T00:00:00Z | `7ddf691ac2afbda7473c0d07f1f4e7ae1e69e47b` | `02046e7a19480f85fff7e4577486518abe47e401` |
| +60 | 2024-11-30T00:00:00Z | `aad30eff27ac5c9a13194125226653c6c2826c58` | `5961d31fb566f089ad468a5b26a32f1ebfa7f63e` |
| +90 | 2024-12-30T00:00:00Z | `af2b3e72a552cfb2a902556469868763ddea3638` | `8a47580a00f3404e7071b9ecfec3692a1e18309f` |

Browser Reload's six exact commit/tree pairs are linked in the same machine
manifest; no shortened SHA or mutable branch name may be used as a job input.
The full tree IDs must equal `git rev-parse <commit>^{tree}` before preparation.

Each state is the last ancestry-ordered first-parent commit active at the cutoff,
under the admitted monotonic committer-UTC convention. A commit need not occur
exactly at midnight. This is exact code-state resolution, not nearest-time debt
label selection. All selected source lineages pass the original chronology
check. Debug Toolbar's failed lineage is not used or silently repaired.

Six commits per repository are six jobs, but production inventory diversity is
5/4/3 for Commons CLI/Click/Browser Reload. Repeated code/equal future metrics
must be reported as such. At most nine exact endpoint cases could be constructed
after successful collection; **zero exist today**. Six sparse measurements are
not a90-daily-state pretrained context or a confirmatory training/evaluation set.

## Gate order — nothing dispatches until all prerequisites pass

1. **Authorization:** a later instruction must explicitly authorize controlled
   historical build/scan collection and its isolated server/project/output scope.
   This phase authorizes none. Retain this plan and every failed attempt.
2. **Source/data rights:** accept the pinned Apache-2.0/BSD-3-Clause/MIT source
   notices and a documented derived-data publication policy. Review SSALv1
   analyzer terms separately. Raw third-party source/binaries/rule descriptions
   stay local unless their redistribution terms are independently satisfied.
3. **Scope dispatch:** implement/approve the proposed versioned production-root
   contract as a new study, with new scope/feature/target IDs. Do not edit the
   frozen schema2 policy or reuse its ID for a different population. Existing
   validators currently reject the new scope IDs; no scanner workaround bypasses
   that failure. Extend the registry/inventory/admission boundary together and
   add conformance tests before any scans.
4. **Resources:** verify actual available RAM≥10GiB and free disk≥15GiB at dispatch.
   Budget8GiB total plus2GiB host headroom; swap is not a substitute. Current
   captured memory fails. No installation/upgrade/cleanup of unrelated user data
   is an implicit remedy.
5. **Existing runtime verification:** use only the pinned local images below;
   validate exact executable/runtime hashes and a no-scan version probe in the
   future sandbox. Do not pull `latest`, auto-upgrade analyzers, or reach remote
   package/model registries. The Maven image's JDK patch is currently
   image-declared; it still needs direct sandbox verification.
6. **Isolated live domain export:** establish a dedicated disposable server data
   scope using the existing server image only after authorization; do not restart
   or modify the published-experiment server/volumes. Verify Standard Experience,
   actual plugin loading, full profiles/rules/remediation/suppression settings and
   operator permissions. A fresh instance defaults to MQR; it must not silently
   pass the Standard gate.
7. **Java build proof:** complete cache-only compilation/classpath and SDK evidence
   at every selected Java state. Source-only Java scans are disallowed. If this
   fails, publish the failed Java attempt and leave that slot blocked; do not
   install dependencies or skip enforcers automatically.
8. **Pre-dispatch sealing:** freeze configuration, runtime/dependency inventory,
   domain/scope/source/code hashes and all18 attempted IDs before native metric
   outcomes are inspected. Only then is the18-job budget eligible for dispatch.

Items3–8 are concrete unresolved gates, not assumed finished engineering. If
scope amendment or domain preparation requires additional code, do it only in a
separately authorized step; Phase5.2 does not implement a scanner runner.

## Pinned tools and native metric policy

Use these already-present images by digest:

```text
server:  sonarqube@sha256:9026624a61cd25542a402a9e7213dd7dbb39724ac9597e331e6b85362558c079
scanner: sonarsource/sonar-scanner-cli@sha256:23ca0f137965d9dff2198074043fd48d386280bc5d0ccac8c8349cea4cf096a9
build:   maven@sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82
```

Server26.8.0.126808, CLI8.0.1.6346, Java8.37.0.45887,
Python5.27.0.35548 and JS13.4.0.43982 are statically verified. The scanner image
contains Java21.0.11; the server release reports Java25.0.4+7. The build image
declares Maven3.9.11/JDK17.0.17+10. Capture actual running versions later; these
are different runtime roles, not interchangeable Java requirements.

Use the existing JS plugin's Linux-x64 Node24.11.0. Its decompressed binary
SHA256 is `d918479037f14dc30c8d21df3767a010fe710685373baec7edf680ca8c3edbee`;
the compressed `node.xz` SHA256 is
`736345edae40f4b5fcab5d7ec2c9b62f99667b78c47622a6239699ec975cb6be`.
Deploy this already-present artifact into a new runtime cache after authorization,
verify its version/hash there, and pin its explicit path. Do not substitute the
host's Node24.20.0 or depend on an unrecorded internet runtime download.

The single primary semantic family is **STANDARD /
native_sqale_index_minutes_v1 / estimated_remediation_minutes**. Require the
instance mode and rule classification proof. Archive both metric definitions and
the actual raw `sqale_index`; do not accept MQR's differently defined
`software_quality_maintainability_remediation_effort` under the same target ID.
Do not sum reliability/security effort or interpret estimated minutes as actual
developer labor. Current26.8 measurements remain a different analyzer domain from
the legacy V2 dataset.
[Metrics](https://docs.sonarsource.com/sonarqube-community-build/user-guide/code-metrics/metrics-definition),
[mode behavior](https://docs.sonarsource.com/sonarqube-community-build/instance-administration/analysis-functions/instance-mode/instance-mode-overview).

## Scope/configuration to freeze before dispatch

The [scope proposal](examples/phase5_2/scope_extension_proposal.json) is the
authority for future roots and IDs. Enumerate each pinned Git tree; materialize a
new unprivileged, disposable job directory from those objects. Disable hooks,
filters, submodule execution and implicit dependency fetching. Never use today's
working-tree files as the historical source. Compare prepared path/blob/mode
inventory with the sealed source manifest before building and again before scan.

Expected sources: Commons CLI26 Java files at the first three cutoffs and36 at
the last three; Click16 Python throughout; Browser Reload8 Python+2 JS throughout.
No per-language overlapping scans or summed project metrics are allowed: each
mixed snapshot is one native project analysis over its whole declared scope.

Only actual reviewed production `.java/.py/.js` enter this pilot population.
Archive explicit dispositions for tests/docs/examples/site assets, `py.typed`,
Javadoc HTML, configs and binaries. New/unrecognized production suffixes, symlinks,
submodules, generated/vendor uncertainty or source-inventory mismatches block the
job. HTML/CSS templates in the unselected Toolbar candidate are not licensed by
this plan as partially analyzed whole-repository debt.

Generate an immutable properties file per job outside the source repository.
The fixed settings are:

| Property/configuration | Planned value / verification |
| --- | --- |
| `sonar.projectKey` | Exact unique key from `readiness_manifest.json`; one fresh project per snapshot in the isolated server,≤18 total |
| `sonar.projectBaseDir` | Disposable prepared revision root |
| `sonar.scm.revision` | Full pinned commit SHA, checked against CE analysis revision |
| `sonar.sources` | `src/main`, `src/click` or `src/django_browser_reload` as registered |
| `sonar.inclusions` | Exact sealed per-job production-file allowlist; explicit wildcard/comma escaping conformance before dispatch; fail if an unsafe path cannot be represented |
| `sonar.tests` / test inclusion | No test population in this target; test and example paths explicitly excluded, not counted as failed production files |
| `sonar.sourceEncoding` | UTF-8; fail on unexpected encoding rather than silently omit source |
| `sonar.scanner.skipJreProvisioning` | `true`; use pinned scanner-image Java21 |
| `sonar.nodejs.executable` | Verified local Node24.11.0 runtime-cache path for the mixed job |
| `sonar.scanner.skipNodeProvisioning` | `true`; explicit runtime prevents uncontrolled fallback/download |
| `sonar.javascript.node.maxspace` | 2048MiB within4GiB scanner RSS limit; stop on OOM |
| `sonar.python.version` | Fixed **3.9** for both Python-family studies; compatible with all six declared source baselines, not the host interpreter version |
| Python concurrency | `sonar.python.analysis.threads=1`; verify property support from this plugin before enabling; no automatic6-core policy |
| `sonar.java.source` | `8` for the Java study |
| `sonar.java.binaries` | Exact manifest-verified compiled `target/classes` directory |
| `sonar.java.libraries` | Exact production dependency JAR allowlist/classpath snapshot, hashed; no nearest/current cache substitute |
| `sonar.java.jdkHome` | Read-only snapshot of the **same pinned Maven-image JDK17** used for compilation, mounted at `/analysis-jdk`; capture full SDK manifest first |
| Java unchanged-analysis/cache optimization | Disable skip/cache behavior where supported; archive the effective setting. Fresh snapshot projects prevent prior-state caches masquerading as full analyses |
| Credentials | Future least-privilege isolated-server secret through ignored runtime environment; never emitted in properties/log evidence or Git |

Browser Reload raises its declared minimum Python version from≥3.8 to≥3.9 at
the+30 cutoff. Click remains≥3.8. The fixed3.9 analysis baseline deliberately
holds this analyzer setting constant across all states; it is a retrospective
fixed-method choice, not a claim about the original historical deployment.
Archive the per-revision declarations and test version-specific parsing/rule
coverage. Do not quietly vary the analysis property at the endpoint.
[Python version property](https://docs.sonarsource.com/sonarqube-community-build/analyzing-source-code/languages/python).

The Java compiler baseline is pinned JDK17 with `--release8`; record this fixed
counterfactual SDK policy rather than claiming historical JDK8 execution.
Materialize the same existing build-image SDK for `sonar.java.jdkHome`; the host's
different Java17 patch is not a replacement. The scanner itself stays Java21.
[Java SDK/bytecode handling](https://docs.sonarsource.com/sonarqube-community-build/analyzing-source-code/languages/java),
[scanner runtime/provisioning](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/scanners/scanner-environment/managing-jre-auto-provisioning).

## Java build preparation — future, not executed

Run only in an unprivileged container from the pinned existing Maven image,
with a new job directory/cache snapshot, no credentials/Docker socket, no remote
network and a2GiB/2CPU cap. Stop the isolated server during builds. Historical
source is untrusted executable build configuration, not just inert Java text.

The fixed first attempt is Maven offline batch `compile`, with
`maven.test.skip=true`, `maven.compiler.release=8` and an explicit new cache
snapshot path. Do not run tests, install packages, fetch dependencies or invoke
the Sonar Maven goal. Preserve the original POMs and their parent versions
71/74/76/78 as pinned by state. Do not rewrite historical POMs or skip enforcement
to make a snapshot appear successful.

Capture compiler/plugin versions, effective dependency/profile/classpath inputs,
all source compilation units and output `.class` hashes. A source-file/class-file
count equality is insufficient because of inner classes/package metadata. Verify
each expected compilation unit and absence of unresolved bytecode/classpath
warnings. Cache presence is only a starting inventory, not success. Missing
parent/plugin/transitive artifacts or incompatible JDK policy produce a typed
build failure and block Java collection pending separately approved recovery.

Python/JS source scans do not require pip/npm installation, application startup,
transpilation, Django migration or test execution for this pilot. Do not execute
repository code merely to create a runtime environment for static analysis.

## Full analyzer/rule/build domain record

Before the first scan, obtain the live server's API description and archive
paginated read-only exports for:

- Actual server version/status/edition/mode and all loaded plugins with binary
  hashes matching the offline inventory; installed is distinct from enabled.
- The exact selected language profile keys, complete profile backups/active rule
  keys, parameters, rule types/quality impacts and remediation function/base/
  multiplier plus overrides. Profile keys/backups alone do not prove full effort
  semantics; export rule details and remediation configuration too.
- Every effective global/project/scanner property influencing scope, parsing,
  issue suppression/acceptance, exclusions, source versions, new-code behavior
  and native metrics. Redact credentials without dropping semantic settings.
- Runtime image/JRE/Node/SDK manifest hashes, build/dependency/classpath policy,
  source/test/generated/vendor inventory policy and actual per-revision lock/
  dependency artifacts. Save all raw exports with ordered page manifests and
  hashes so silent pagination limits cannot pass.

`analyzer_domain()` remains the hash/completeness rule. Fields currently unknown
must stay null/INCOMPLETE until those exports exist. The future scope extension
must keep equivalent completeness checks. A convenient hash of an “unknown”
mode/profile is not a valid compatible domain.

Hold this domain fixed across all six states within a repository. Source and
dependency declarations may evolve, but any change to measurement semantics,
profile, SDK policy, plugin, target population or mode requires a documented
boundary/new study, not silent pooling. Different per-repository scope IDs remain
distinct; no cross-language metric equivalence claim is assumed.

## Scanner completion and native artifact protocol

After prerequisite sealing, process repositories in the manifest order and each
repository's cutoffs chronologically, at most18 jobs. Create only the planned
fresh snapshot project in the isolated server. Use a single native mixed-language
analysis for Browser Reload. Do not backdate server execution using
`sonar.projectDate` to imitate the code cutoff; the archive carries distinct
cutoff, committer, execution, first-available and retrieval clocks.

For each job require all of:

1. Source/SDK/dependency/properties/configuration hashes match the sealed plan.
   Start monotonic wall/RSS/disk monitoring; failure to monitor blocks dispatch.
2. Scanner exits0 with full sensor completion. Archive sanitized stdout/stderr,
   runtime versions and effective configuration, not just a final success line.
3. `.scannerwork/report-task.txt` supplies the correct server/project/CE task.
   Poll the task within the same20min overall budget; require `SUCCESS` and an
   immutable `analysisId`. Submission success alone is insufficient.
4. Query the native analysis metadata and verify full revision/project/analysis
   identity. Immediately export native project metrics and all component/file/
   language coverage pages before any later analysis can replace the response.
   An unbound latest `/api/measures/component` response is not historical truth.
5. Reconcile exact expected production paths/languages with analyzed components;
   require zero unsupported, failed, missing or unexpectedly included source
   files. Parser/sensor/ClassLoader warnings, ignored files or absent language
   NCLOC trigger explicit exclusion/review. Equal counts alone do not prove the
   sets match. Native NCLOC is measured, never borrowed from source-text proxies.
6. Archive raw SQALE and same-snapshot F1 metrics with metric definitions/units,
   plus domain/profile/rule/settings exports, Git tree/input inventory, compiler
   manifest, task/analysis metadata, file coverage and raw response checksums.
   Do not reconstruct stock from mutable issue lifecycle fields.
7. Emit the existing archive envelope/index/coverage/inventory contracts only
   from verified native exports. Record the raw-export mapping and bytes digest;
   no manufactured analysis ID, successful coverage assertion or missing-to-zero
   conversion is allowed. An envelope's syntax alone is not evidence of truth.

The archive adapter should hash/parse exactly the same bytes; the unchanged
`PastStore`, `build_features`, `prediction_input` and `target_status` gates remain
the reference behavior. The newly versioned scope dispatcher must preserve those
identity/time/missingness semantics, not catch admission errors and call them PASS.

## Output, target construction and failure handling

Publish a new external root with one immutable attempt directory per planned ID:
source plan, Git inventory, build evidence, runtime/config/domain exports,
scanner/CE metadata, raw native payloads, component coverage and status/reason.
Write COMPLETE only after every hash/identity/coverage gate passes. Failed jobs
remain FAILED/QUARANTINED with no debt value, never COMPLETE or zero. No automatic
retry, model fallback or budget expansion is registered; a new authorized attempt
must preserve the previous one and count against an explicitly revised budget.

If all origin/endpoint states pass, build a **new versioned study** independently:
features from past states only, labels in a separate store, exact30/60/90×86400
endpoints, no interpolation or carry across unmeasured changes. Each valid target
keeps endpoint proof/domain/scope/source references. Missing/failed endpoints
remain null/status/reason and are included in attempted-ID coverage accounting.
Do not rebuild the original Java forecasting dataset or reuse its benchmark IDs.

The six-state schedule provides at most nine engineering endpoint cases, not
enough to establish model superiority,90-day daily contexts or a new held-out
benchmark. Keep F2 disabled. No Ridge/CatBoost/Chronos/Granite work, model tuning,
dashboard or API is part of this collection plan.

**Current decision: BLOCKED.** Resolve the named gates, obtain separate collection
authorization, then implement/verify the scope amendment and controlled runner
before considering dispatch. Phase5.2 ends with this plan and its publication.

## Pinned tree-identity appendix

Every value below is a full Git object ID, verified against the available source objects. These are planned code states, not completed scans.

| Repository / offset | Commit SHA | Tree SHA |
| --- | --- | --- |
| adamchainz/django-browser-reload / -90 | `012e1801e54cc6fcd3b5178fa4a90652415e4019` | `3ec6d8a24548b4712e725c6ba6bdebb9ce70c8cc` |
| adamchainz/django-browser-reload / -30 | `2549365d0837d3e26df534fe8009db370a2e7b60` | `5df3c134bdd4cfdab03d498ea1a2174828690532` |
| adamchainz/django-browser-reload / 0 | `188589e57c4aa60a4171f185ce747a5e1c4e58cd` | `de6672cfb271f7d5d89fc25730554a6d73b8953b` |
| adamchainz/django-browser-reload / 30 | `caf60603a19a52380f752fb6700c1a06cef63a75` | `fb0feba811b7747ad65501f26612c5019662b6f4` |
| adamchainz/django-browser-reload / 60 | `d1927745863edf55cc943361d7035ea5104609cb` | `cc8ca96220f07d0a3172067ed614f0d672ce828b` |
| adamchainz/django-browser-reload / 90 | `692abf52546294103e39d4d41ee217274f42f04d` | `a60025d3d031d5e78ae86a894e9ea90eccd26197` |
| apache/commons-cli / -90 | `e1529b546d9696192f4de52152777403b4a01b39` | `c1a67e730fc5729a5376c267ed559f4ae310df01` |
| apache/commons-cli / -30 | `fb6293fcd6a9b55ac8ecb550af6572daaed18fa1` | `598dec4901a9adcf8e55b241c9689a8db6219c29` |
| apache/commons-cli / 0 | `4ff0d4adbc2161677e71050ba23c152831f6ad83` | `ac7521be84b2820a83f7b960d329a15521408214` |
| apache/commons-cli / 30 | `7ddf691ac2afbda7473c0d07f1f4e7ae1e69e47b` | `a2ff09febdac9da6e6ee422a9144ad09d81113bf` |
| apache/commons-cli / 60 | `aad30eff27ac5c9a13194125226653c6c2826c58` | `d7434665397c8dd8156fff7ecaed29a14feeb951` |
| apache/commons-cli / 90 | `af2b3e72a552cfb2a902556469868763ddea3638` | `0d773516c1c7bb0a371b2af6e084b62ef2d36546` |
| pallets/click / -90 | `14f735cf59618941cf2930e633eb77651b1dc7cb` | `2e93f3ec459431b62ad482a68d6d7b99e592ba73` |
| pallets/click / -30 | `99015e1456b6952054fda8312b40ea646737168d` | `45ee71dbd1f8a9e98aec7bbaec4a809a0cce5e7f` |
| pallets/click / 0 | `4a758f5c38636ecd9d030356d85bcca3d8fbd0ca` | `dc3c8e1cea4b87066fb2d49b1ef1ac81e31613ec` |
| pallets/click / 30 | `02046e7a19480f85fff7e4577486518abe47e401` | `c764e16f14d1e7c066789ced2876f39fcdf5b647` |
| pallets/click / 60 | `5961d31fb566f089ad468a5b26a32f1ebfa7f63e` | `c7dbe6691b5c9884a9b83806566dcabdfaf44816` |
| pallets/click / 90 | `8a47580a00f3404e7071b9ecfec3692a1e18309f` | `163366aab835a523175b60ec6fa6813774fac930` |
