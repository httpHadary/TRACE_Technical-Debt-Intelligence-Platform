# Phase 5.2 — Real multi-language acquisition preflight

Date: **2026-10-15**. Base commit:
`d9ead157d12ac08c9a260af6a9d85eb0b5425772`.

**Preflight: PARTIAL. Historical collection: BLOCKED.** Three real development
sources, their complete selected-branch Git histories, 18 exact UTC cutoff states
and full tracked-file inventories are pinned. Existing offline binaries support
the intended Java/Python/JS route in principle. The live analyzer mode, active
rules/settings, revised production scope, Java build success and dispatch resource
headroom remain unverified or blocked. **Do not run the collection plan yet.**

Actual work: source/metadata inspection, three small bounded bare Git mirrors,
offline image/JAR inspection, a data-only planning module and tests. **Zero scans,
historical builds, native measurements, labels, model training or inference.** No
software installation/upgrade, server start, old database mutation or confirmatory
outcome access occurred.

## Deliverables and decisions

- [Candidate selection](REAL_PILOT_REPOSITORY_CANDIDATES.md): Commons CLI,
  Click and Django Browser Reload; Debug Toolbar and Flask are documented
  alternatives, not additional pilot targets.
- [Historical execution plan](HISTORICAL_SCAN_EXECUTION_PLAN.md): immutable states,
  required domain/scope/build evidence, proposed settings, budgets and fail-closed
  dispatch gates. It is a future plan, not an executed runner.
- [Machine-readable evidence](examples/phase5_2/README.md): source, capability,
  scope, contract, inventory, build-provenance, readiness and verification records.
- `forecasting_multilanguage/preflight.py`: source-only plan generation using the
  existing Git, UTC, hashing, manifest and lineage contracts. No build, scanner,
  HTTP collector, model or admission-bypass path was added.
- `tests/test_multilanguage_preflight.py`: 34 deterministic software cases.

The four Phase5 documents, Phase5.1 report/contracts and all earlier experiments
were reviewed and preserved. The new package module does not alter their scope
constant, source adapters, validators, model inputs or target builders.

## Source feasibility

The selected three development families are:

| Development target | Source | Pinned provider ID | First-parent commits | Inversions |
| --- | --- | ---: | ---: | ---: |
| Java-dominant | `apache/commons-cli` | 212343 | 1,956 | 0 |
| Python-dominant | `pallets/click` | 19103692 | 1,384 | 0 |
| Genuine Python+JS mix | `adamchainz/django-browser-reload` | 438426152 | 424 | 0 |

Source objects pass nonshallow, connectivity, first-parent/root and immutable-tip
checks. This certifies the selected lineage, not every remote branch or GitHub
fork. Source metadata identifies all three as non-forks; global fork/exposure
certification is still incomplete. Commons CLI is already exposed in prior
studies; all three are permanently **development-only** in this preflight. No
fresh confirmatory cohort is claimed or enrolled.

Commons CLI reused local objects. Click, Debug Toolbar and Browser Reload were
copied into new bare mirrors outside the project; recorded sizes were 6,100,884,
10,911,105 and 1,214,373 bytes respectively, **18,226,362 bytes total**. Each copy
had a 64MiB/120s stop limit. No checkout, repository build/install hook or source
program was executed. No large historical dataset, model or scanner image was downloaded.

The common origin was fixed at **2024-10-01T00:00:00Z**, before any debt outcomes.
Cutoffs are July3, September1, October1, October31, November30 and December30,
2024, all midnight UTC. They are exact −90/−30/0/+30/+60/+90-day offsets,
not calendar-month arithmetic or 91-day weeks.

There are 18 distinct selected commits and full trees, but only **5 Commons CLI,
4 Click and 3 Browser Reload distinct production-source inventories** across the
six cutoffs per repository. Rows/commits must not be treated as 18 independent
debt trajectories. All actual debt values/analysis IDs remain absent.

At T0, path inventories contain 26 Java files; 16 Click Python files; and
8 Browser Reload Python plus 2 JS files. Browser Reload has 257 Python and
116 JS nonblank source-text lines, a provisional 68.9%/31.1% programming-text
mix. These are **not Sonar NCLOC**, and the mixed stratum remains provisional
until a future complete native analysis confirms both programming families ≥10%.
The mixed repository is never labeled JS/TS-dominant. No fourth dominant target
was added.

Debug Toolbar was not selected: its complete first-parent history contains
three timestamp inversions. Although none is in the proposed 2024 window, the
frozen `GitArchive` rejects the whole chain. We did not truncate, reorder,
rewrite or bypass it. Its additional production CSS and Django templates also
need scope/coverage extensions. Browser Reload supplies a smaller two-language
alternative whose frozen chronology check passes. Selection used these metadata
and feasibility conditions, never debt magnitudes or forecast errors.

## Scope and analyzer coverage

Every tracked path at each of the 18 selected states was enumerated with Git
mode/object ID and a scope disposition: **2,046 path-state entries**. The
deterministic compressed inventory contains no source file contents. It covers
outside-scope assets/configuration too, rather than silently dropping unfamiliar
extensions.

Proposed production roots are `src/main` for Commons CLI, `src/click` for Click
and `src/django_browser_reload` for Browser Reload. Tests, examples, documentation,
vendor/generated files, binary assets and Java `overview.html` documentation
are separately identified. At T0 there are **no unrecognized extensions inside
the proposed selected production roots**. `py.typed` is a package marker, not an
unmeasured Python source file. This path-based screen is not proof that no file
contains generated or vendored code; header/origin review remains a dispatch gate.

Repository-wide unfamiliar/out-of-scope extensions include Java-site `.vm`,
`.cgi`, `.xcf`, `.jacoco` and fixture `.file`; Click `.bat`, `.in` and docs/assets;
Browser Reload example `.css`/`.html` and dependency `.in`/`.txt` files. Their
paths and roles are retained. The current selected production sources themselves
use `.java`, `.py` and `.js` only. No unsupported suffix is silently mapped to a
supported language or given zero debt.

The frozen schema2 policy is insufficient for the intended production roots:
at T0 it includes two Commons CLI site JS paths, fifteen Click docs/example Python
paths and seven Browser Reload example Python paths outside those roots. The
unchanged registration validator correctly rejects the proposed new scope hashes
as **Unsupported scope policy**. This is an integration blocker, not permission
to scan partial scope and describe it as admitted schema2 whole-scope debt.

[Scope extension proposal](examples/phase5_2/scope_extension_proposal.json) fixes
the per-repository roots, exclusions, unknown-file policy and future contract-ID
boundary. It is **not applied**. Before collection, a separately authorized
versioned dispatcher/new study must support it and preserve all frozen schema2
artifacts. New `.mjs/.cjs/.pyi`, HTML/CSS or framework-specific suffixes require
their own actual analyzer/suffix/coverage checks; listing them is not support.

## Existing tools and licenses

No container is running. The existing `td-target-sonar` container is stopped,
based on **SonarQube Community Build 26.8.0.126808**. Its prior port mapping was
19003; read-only `/api/system/status` and `/api/server/version` requests to that
port returned connection refused. It was not started. Existing data/log volumes
and historical analysis outcomes were not inspected or changed.

| Tool | Verified offline identity / limitation |
| --- | --- |
| Server image | `sonarqube@sha256:9026624a61cd25542a402a9e7213dd7dbb39724ac9597e331e6b85362558c079`; stopped-container release file reports Temurin25.0.4+7 |
| Scanner image | `sonarsource/sonar-scanner-cli@sha256:23ca0f137965d9dff2198074043fd48d386280bc5d0ccac8c8349cea4cf096a9`; JAR/launcher prove CLI8.0.1.6346; image release file proves Corretto21.0.11 |
| Build image | `maven@sha256:e4a7ace3dc0d645ed97f8d9ad0b0d3f0b14fa8d150138f27f116d7105a639b82`; Maven3.9.11 image tag, declared `jdk-17.0.17+10`; not run |
| Host tools | Java17.0.20.1, Maven3.8.7, Python3.12.3, Node24.20.0, Go1.23.12, GCC13; no host `sonar-scanner` or Gradle found; `dotnet --list-sdks` empty |
| JS runtime | Existing JS plugin contains Linux-x64 Node24.11.0; version file, compressed and decompressed SHA256 recorded; not executed/deployed |

The scanner image and existing plugin JARs were inspected by streaming local
Docker archive bytes; no containers were created or started. An optional Maven
image-layer inventory probe could not parse its layer format with the stdlib;
the build image's patch/runtime identity remains image-declared, not binary-run
verified. No package was installed to work around this.

Nineteen bundled plugin JARs were hashed. Relevant versions are Java8.37.0.45887,
Python5.27.0.35548 and JavaScript13.4.0.43982; the latter declares JS/TS/CSS
support. HTML/web3.30.0.8241, XML2.18.0.7959, Go1.40.0.6765 and
C#10.31.0.145097 are also present offline. **Binary presence is not live
enablement or successful coverage.** No CFamily plugin/paid C++ entitlement was
verified; C++ and .NET acquisition remain outside this pilot.

Java/Python/JS plugin manifests declare **SSALv1**, not Apache/MIT. The scanner's
publisher license is LGPLv3. No third-party binaries/rule text are redistributed.
Record and review the actual tool/source/data terms before future collection;
the code license alone does not establish derived-dataset publication rights.
[SSAL terms](https://www.sonarsource.com/license/ssal/),
[scanner license](https://github.com/SonarSource/sonar-scanner-cli/blob/master/LICENSE.txt).

## Metric and configuration readiness

The first strict study requires **Standard Experience + native `sqale_index`**,
estimated minutes for code-smell remediation. MQR's
`software_quality_maintainability_remediation_effort` uses maintainability impacts
and is a different registered semantic family; no automatic equivalence, effort
conversion or cross-domain pooling is allowed. These are analyzer estimates, not
actual developer repair time.
[Native metric definitions](https://docs.sonarsource.com/sonarqube-community-build/user-guide/code-metrics/metrics-definition).

New Community Build instances default to MQR; instance mode can be configured.
The stopped server's actual mode, full active rules/remediation overrides,
profiles, suppression configuration and project permissions are **unverified**.
No live evidence was replaced with an old cached setting. A fresh isolated
future namespace must explicitly establish Standard mode and freeze the exported
domain before the first job.
[Instance modes](https://docs.sonarsource.com/sonarqube-community-build/instance-administration/analysis-functions/instance-mode/instance-mode-overview).

The existing `analyzer_domain()` returns INCOMPLETE for the available template;
unknown mode/rule/build/scope/runtime/dependency/suppression fields are not valid
hash equivalence. Proposed configuration and the exact required exports are in
the execution plan. Java requires matching compiled classes; cached parent POMs
and plugins do not prove a complete offline dependency graph or successful build.
No compilation was authorized or attempted.
[Java bytecode requirements](https://docs.sonarsource.com/sonarqube-community-build/analyzing-source-code/languages/java).

## Resources and collection gate

Observed host: Ryzen5 PRO5650U, 12 logical CPUs, **16,036,016,128 bytes RAM**.
Available RAM varied during inspection; the captured capability manifest records
**7,316,103,168 bytes**, below the proposed 10GiB available-at-dispatch threshold.
Captured free disk is **20,613,398,528 bytes**, above the 15GiB start threshold
but with little room for uncontrolled downloads. Availability must be rechecked
at dispatch; swap does not certify usable RAM.

Proposed hard bounds: one job, shared2 CPUs, total8GiB replay budget, at least2GiB
extra host RAM headroom; ≤20min per complete snapshot including build/CE/export;
≤18 jobs; ≤5GiB new artifacts with ≥10GiB disk reserve. Server3.5GiB plus
scanner4GiB plus .5GiB monitoring fit the8GiB budget. Java builds use2GiB with
the server stopped; build and scan do not overlap. These are **proposed caps**,
not measured successful scan requirements. Stop on OOM/time/disk/coverage failure,
without silently increasing caps.
[JS memory guidance](https://docs.sonarsource.com/sonarqube-community-build/analyzing-source-code/languages/javascript-typescript-css).

Readiness gates are explicit in
[`readiness_manifest.json`](examples/phase5_2/readiness_manifest.json).
Source metadata and pinned states PASS. Scope dispatch, live Standard mode/rules,
Java build proof, actual runtime deployment, reuse-policy/permission acceptance,
resource headroom and separate collection authorization do not yet PASS.

## Verification, preservation and publication

**438 tests passed / 1 training test deselected in each checkout.** The 34 new
cases cover UTC/exact offsets, complete inventories, unknown/generated/test/vendor
dispositions, immutable identities, chronology/shallow failures, future/absent
states, outcome-field rejection, provisional language evidence, deterministic
publication, source preservation, duplicate families and output isolation.
The excluded test actually trains CatBoost; no real model or scan ran in tests.

Two final plan runs are byte-identical, including all inventories and COMPLETE
manifests. Preservation checks reverified **56 frozen bundles / 322 artifacts**,
Phase5.1 evidence bundles, all335 pre-existing central files and all246 matching
existing working-project files before adding only the navigation/sync notes.
Final publication allows only those two navigation edits; all333 other old
central files and244 old working files stay byte-identical. The source SQLite
hash remains
`8eb329e5e5690b884b98df824c4b94fc7582c5d610fa3bd12784b1e417b2684e`.
The working project's unrelated `main` remains at
`2e7999ea436d49449652e6c52e9066ef2e514419`.

Local audit receipts/logs/source mirrors are outside Git at
`/home/hp/tst/research/forecasting_mvp/phase5_2/2026-10-15/`.
Reproduce the source-only planner with the published config adjusted to existing
immutable local sources, preserving the pinned tips/cutoffs:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
TD52_PY="$PWD/.venv-forecast/bin/python"
PYTHONDONTWRITEBYTECODE=1 "$TD52_PY" -m forecasting_multilanguage.preflight \
  --config examples/phase5_2/replay_sources.example.json \
  --output /path/outside/git/to/new-preflight-bundle
PYTHONDONTWRITEBYTECODE=1 "$TD52_PY" -m pytest -q -p no:cacheprovider \
  tests/test_multilanguage_preflight.py
PYTHONDONTWRITEBYTECODE=1 "$TD52_PY" -m pytest -q -p no:cacheprovider tests \
  -k 'not test_actual_catboost_models_shared_folds_predictions_and_purging'
```

Publication uses a normal descendant commit on central `main`, explicit file
sync and post-push GitHub content verification. Full mirrors, raw binaries,
proprietary rules, credentials and original datasets remain excluded. The
post-push receipt/commit hash is recorded outside Git and in the completion
response to avoid self-referential hashes.

**STOP after Phase5.2 publication.** The future collection plan remains blocked
until every gate is resolved and collection is separately authorized.
