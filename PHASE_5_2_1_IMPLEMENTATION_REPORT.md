# Phase 5.2.1 — Collection readiness gate resolution

Date: **2026-10-15**. Base: `01ebbb46a64b9af1886979947968f15add8192d2`.

**Implementation PASS. Overall PARTIAL. Later runtime/collection BLOCKED.**
The missing versioned production-root interface is implemented and verified.
Existing offline runtime identities are now better verified, including the Maven
image's actual JDK release and Maven core. Java dependency gaps and unverified live analyzer semantics still prevent
collection. The final resource capture passes both RAM and disk thresholds,
with only a narrow RAM margin; dispatch must recheck them. This report does not authorize server startup or Phase5.3.

Zero historical scans/builds, new native measurements, real forecasting targets,
model training or inference. No installation, analyzer upgrade, old server/volume
mutation, numerical test-outcome access, dataset rebuild or resource relaxation.
All previous reports/contracts/results remain byte-identical.

## Implemented scope, registration and admission

New isolated package:
[`forecasting_multilanguage/production_scope/`](forecasting_multilanguage/production_scope/README.md).
Version: `production-root-study-v1`, retaining schema2 serialization with new
scope, feature and target contract identities. The frozen schema2 CLI and
validators continue to enforce their original scope; no automatic migration.

| Development source | Production root | Admitted suffixes | Planned files at six cutoffs |
| --- | --- | --- | --- |
| Commons CLI | `src/main` | `.java` | 26,26,26,36,36,36 |
| Click | `src/click` | `.py` | 16 at every cutoff |
| Django Browser Reload | `src/django_browser_reload` | `.py`, `.js` | 8 Python+2 JS at every cutoff |

All18 original commits, full trees, exact cutoffs, project-key plans and three
provider/family identities were retained. Full inventory: **2,046 tracked
path-state entries**, including **342 production path-state entries**. Distinct
production inventories remain **5/4/3** for CLI/Click/Browser Reload, not18
independent debt histories. The mixed source is **Python+JS**, not JS-dominant.
Native NCLOC must still verify both programming families≥10% before admission.
No actual native language/debt result exists for this study.

The new scope hashes are distinct from the frozen policy and from the unimplemented
Phase5.2 proposal. Full policy/feature/target hashes are in
[`scope_contracts.json`](examples/phase5_2_1/scope_contracts.json).
The feature contract binds the scoped source-event population; the target contract
binds independently measured exact30/60/90-day states. F0/F1 algorithms and UTC/
missingness semantics are reused; F2 stays disabled. Pure legacy algorithm/shape
validation projections are internal only and never published as legacy admission.

Inventory records every tracked object, mode, blob and role. Production root
prefixes must match exactly. Tests/fixtures/docs/examples/vendor/generated paths,
minified files and source maps are explicit exclusions. `py.typed` and Java
Javadoc overview/package HTML have explicit noncode dispositions. Other unknown
production extensions, symlinks/submodules/nonregular in-root objects and empty
production scope block success. `.ts/.mjs/.pyi/.css/.html` are not enabled merely
because some analyzer could support them.

Admission now requires a full inventory equal to recomputed Git objects,
hash-verified raw metric/file/completion/review payloads, matching native revision,
project/analysis/CE-task identities and **exact production path/language equality**.
Equal file counts with different/missing/extra/duplicate files cannot pass.
A bound full-root header/origin/exclusion review is required; path heuristics do
not certify absence of generated/vendor code. All real registrations therefore
remain **quarantined, development-only**, pending actual rights/domain/review
proof. None becomes a confirmatory holdout.

The past-only numerical model interface remains allowlisted and denies label,
split and future-source fields. Changed but unmeasured states remain UNKNOWN;
no nearest timestamps, interpolation, missing→zero or unproved carry-forward.
SonarQube estimated remediation minutes remain separate from developer labor.

## Read-only runtime and dependency findings

[`runtime_artifact_inspection.json`](examples/phase5_2_1/runtime_artifact_inspection.json)
records selected image metadata and offline executable/JAR/release hashes.
No container was created or started. Existing installed `zstd` decoded local
Maven image layers, resolving the previous image-format inspection limitation.

| Role | Verified static artifact | Remaining limitation |
| --- | --- | --- |
| Server | Existing pinned26.8.0.126808 image; stopped server JDK release25.0.4+7 | Not running; Standard/MQR mode and active profiles/rules unknown |
| Scanner | CLI8.0.1.6346 JAR/launcher; image Corretto21.0.11 release and Java executable hashes | No isolated version probe/engine deployment or scan |
| Java build | Maven core3.9.11 JAR properties; Temurin17.0.17+10 release; launcher/Java hashes | No historical build/effective classpath verified |
| JS runtime | Existing JS plugin Node24.11.0 version file; compressed/decompressed hashes match Phase5.2 | No extraction/deployment/execution in a job sandbox |
| Plugins | Java8.37.0.45887, Python5.27.0.35548, JS13.4.0.43982 JAR hashes match earlier evidence | Presence is not live enablement or complete coverage |
| Host | Java17.0.20.1, Maven3.8.7, Python3.12.3, Node24.20.0 | Host versions do not replace pinned image runtimes |

Pinned image identities are unchanged from Phase5.2. No proprietary binaries/rule
text are redistributed; only small version/hash metadata is published.

Static inspection of all six selected Commons CLI POMs and both approved local
Maven caches found:

- Required parent versions: **71,74,76,78,78,78**.
- **71,76,78 are missing from both caches**, affecting five of six planned Java
  states. Only74 is present in one approved cache.
- **75 cached parent/plugin artifacts** were hashed;13 JAR CRC checks passed and
  the62 POMs parsed. Cache presence does not prove a complete transitive graph.
- Direct selected-POM dependencies are test-scoped. Inherited dependencies,
  plugins, profiles and required parent chains remain unresolved; this is not a
  claim that a production build needs no dependencies.
- Source/target declarations stay Java1.8; the future fixed JDK17/`--release8`
  policy remains a plan, not a build result. No Maven project goal ran.

Evidence: [`dependency_inspection.json`](examples/phase5_2_1/dependency_inspection.json).
Missing dependencies cannot be fetched under this authorization. No POM rewrites,
enforcer skipping or source-only Java fallback were introduced.

## Resources and protected server

The sealed capture at **2026-10-15T02:14:35.016437Z** records:

| Resource | Actual | Gate |
| --- | --- | --- |
| Host RAM | 16,036,016,128 bytes total;10,786,017,280 bytes available (~10.05GiB) | **PASS at capture, narrowly**: required≥10,737,418,240 bytes (10GiB) |
| Free disk | 37,176,807,424 bytes (~34.62GiB), improved after user cleanup | **PASS**:≥16,106,127,360 bytes (15GiB) |
| CPU |12 logical CPUs; effective cpuset0–11 |2 shared replay CPUs remain the unchanged cap; no replay started |
| Docker |29.6.2, cgroup2; daemon reports CPU quota/cpuset, RAM and swap-limit support | Actual sandbox enforcement still needs the authorized runtime step |
| Containers |0 running; old `td-target-sonar` stopped | Old container state and all volume mappings unchanged |

The host-visible `cpu.max` file was unavailable; no unlimited CPU assumption was
made. Docker's reported capabilities do not replace per-container limit checks.
Host `vm.max_map_count=1048576`, `fs.file-max=9223372036854775807`,
open-file limit1048576 and process limit53951 meet the documented host minima.
Future container/user limits still need independent inspection; no sysctl or
ulimit was changed. [Linux requirements](https://docs.sonarsource.com/sonarqube-community-build/server-installation/pre-installation/linux).

All original limits, including8GiB total budget,20-minute whole-job wall budget,
18 jobs,5GiB artifacts and10GiB disk reserve, remain identical. Resources fluctuate:
this capture is not a reservation or permission to dispatch.
No unrelated service was stopped and no user data was deleted by this phase.

## Verification and preservation

The final regression result and reproducible commands are sealed in
[`verification.json`](examples/phase5_2_1/verification.json). Final suite:
**512 passed /1 deselected in each checkout**;74 new scope cases included.
The excluded case actually fits CatBoost and remains forbidden. Existing tests
use fixtures/mocks; no real model, scan or historical build was executed.

Conformance covers roots and exclusion dispositions; unknown suffixes; native
language strata/analyzer domains; raw-byte integrity; tree/family/scope/analysis/
CE identities; fully consistent but wrong file sets; partial/paginated completion;
missing values and zero debt preservation; exact30/60/90 endpoints; unmeasured
changes; past-only/operational availability; deterministic18-state audit; and
frozen-contract rejection of the new registration.

Two final source-only publications are byte-identical, including COMPLETE
manifests. Preservation reverified **all353 pre-existing central tracked files**,
**264 matching pre-existing working-project files**, **56 frozen schema1 bundles /
322 artifacts**, both Phase5.1 evidence bundles, the SQLite source and pinned
Chronos checkpoint. No old report or code file needed editing.
[`preservation.json`](examples/phase5_2_1/preservation.json).

The original working `main` stays at
`2e7999ea436d49449652e6c52e9066ef2e514419`; publication uses a normal descendant
commit from the central checkout, followed by explicit path sync and safe
`github-main` tracking-reference advancement. Remote commit/content verification
is recorded in a local publication receipt and the final response, avoiding a
self-referential commit hash in this report.

## New files and reproduction

New files only:

- `forecasting_multilanguage/production_scope/`: `scope.py`, `registry.py`,
  `archive.py`, `admission.py`, `interfaces.py`, `readiness.py`, `__init__.py`, README.
- `tests/test_production_scope_readiness.py`.
- `tools/inspect_phase5_2_1_artifacts.py` and `inspect_phase5_2_1_dependencies.py`.
- This report, `FUTURE_ISOLATED_SERVER_INSPECTION.md`, and the small attributed
  metadata-only `examples/phase5_2_1/` evidence bundle.

Use existing interpreter/dependencies; outputs must be new local directories or
files outside Git. The archive inspector reads only pinned local images and
stopped-server static binaries. It does not run those binaries or read old data/
log volumes. The dependency inspector reads Git objects/public cache artifacts,
not Maven settings or secrets.

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
TD521_PY="$PWD/.venv-forecast/bin/python"
PYTHONDONTWRITEBYTECODE=1 "$TD521_PY" -m forecasting_multilanguage.production_scope.readiness \
  --config examples/phase5_2/replay_sources.example.json \
  --pinned-readiness examples/phase5_2/readiness_manifest.json \
  --output /path/outside/git/to/new-scope-evidence
PYTHONDONTWRITEBYTECODE=1 "$TD521_PY" tools/inspect_phase5_2_1_artifacts.py \
  --output /path/outside/git/to/new-runtime-inspection.json
PYTHONDONTWRITEBYTECODE=1 "$TD521_PY" -m tools.inspect_phase5_2_1_dependencies \
  --output /path/outside/git/to/new-dependency-inspection.json
PYTHONDONTWRITEBYTECODE=1 "$TD521_PY" -m pytest -q -p no:cacheprovider \
  tests/test_production_scope_readiness.py
PYTHONDONTWRITEBYTECODE=1 "$TD521_PY" -m pytest -q -p no:cacheprovider tests \
  -k 'not test_actual_catboost_models_shared_folds_predictions_and_purging'
```

## Remaining gates and safe next actions

1. **G03 software resolved.** Scope dispatch, new IDs and strict admission are
   implemented; no actual source is admitted from code conformance alone.
2. **G08 resources pass at the final capture.** RAM clears the unchanged10GiB
   threshold by only48,599,040 bytes (~46.3MiB); disk passes. Earlier captures
   failed RAM. Recheck at later admission; this is not a persistent resource
   reservation or startup authorization. No threshold relaxation.
3. **G06 Java blocked.** Separately authorize pinned parent/transitive dependency
   acquisition, then later isolated historical compilation/classpath proof.
   Do not fetch dependencies or build in this phase.
4. **G04/G05/G07 runtime/domain incomplete.** Follow
   [future isolated inspection commands](FUTURE_ISOLATED_SERVER_INSPECTION.md)
   only after separately authorized/resource-admitted disposable startup.
   No old-container/volume reuse. Verify actual Standard mode and all native
   profiles/rules/remediation/runtime hashes rather than infer from defaults.
5. **G09 rights/content/permissions pending.** Obtain source/data/tool policy
   acceptance and complete bound production-content review. Keep quarantine.
6. **G10/G11 collection not executed/authorized.** Only a separately authorized
   collection phase may build/scan the same18 pinned states after all gates pass.

The new future-inspection document includes exact guarded container/API checks,
pagination/evidence requirements, secret handling and failure rules. Official
Community Build docs describe MQR defaults and mark the generic MQR system
property unsupported for Community Build; an empty settings response cannot
establish Standard mode. No environment-variable shortcut is assumed.
[Mode overview](https://docs.sonarsource.com/sonarqube-community-build/instance-administration/analysis-functions/instance-mode/instance-mode-overview),
[property limitations](https://docs.sonarsource.com/sonarqube-community-build/server-installation/system-properties/system-properties),
[installed Web API discovery](https://docs.sonarsource.com/sonarqube-community-build/extension-guide/web-api).

**STOP after verification and GitHub publication. No Phase5.3 or scan dispatch.**
