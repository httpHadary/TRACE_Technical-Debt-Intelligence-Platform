# Phase 5.1 implementation plan — feature and multi-language data readiness

Date: 2026-10-15. **PROPOSED future work; not authorized or executed by Phase5.** Authoritative design: [architecture](MULTILANGUAGE_ARCHITECTURE.md), [feature column/classification matrix](FEATURE_AVAILABILITY_MATRIX.md), [research/evaluation protocol](PHASE_5_RESEARCH_REPORT.md).

## Outcome and scope

Implement a small **new** `forecasting_multilanguage/` batch package that imports historical evidence, validates domain/state/time identities, emits auditable F0/F1 feature records and separate exact-horizon label-status records, and demonstrates those contracts on a tiny real multi-language development pilot. Do not change previous source/configuration/constants, datasets, splits, baselines, weights, numerical outputs or reports. Importing a legacy archive into a new candidate/quarantine lane does not certify its missing analyzer metadata.

Phase5.1 ends at **data readiness**, not modeling. No fitting Ridge/CatBoost, pretrained inference, calibration, performance claims, dashboard/backend or autonomous remediation. The later evaluation roster/protocol is already specified; it requires separate authorization after the data gate. A new CLI package avoids accidentally calling old weekly/scanning or `evaluate-chronos` commands.

Two acquisition routes are fixed:

- **A — archive-first:** import already available immutable Git/Sonar exports whose metadata, licensing and cutoff state proofs pass admission. This is the shortest implementation route. **No suitable new Python/JS archive has yet been admitted**; obtaining it is a real dependency, not assumed completed.
- **B — bounded historical replay:** only if the next authorization explicitly includes scans/build execution and a suitable pinned analyzer environment is available, create up to18 new development-only measurements under the limits below. The current Phase5 request authorizes none. Do not install/upgrade a server, download new large datasets or run unbounded scans as an implicit fallback.

If route A is unavailable and B is not authorized/possible, deliver the working contracts/adapters, verified legacy-source audits and explicit `PARTIAL/BLOCKED_NONJAVA_DATA` readiness. Do not invent a real pilot or silently expand scope.

## Existing-code treatment

| Existing component | Treatment in Phase5.1 | Reason / reuse boundary |
| --- | --- | --- |
| `forecasting_mvp/io.py`, root `contracts.py`, timestamp/hash helpers | Reuse read-only pure helpers with code-hash provenance, or a thin new wrapper when schema differs | Existing serialization/checksum conventions already work; no rewrite |
| Phase1 `historical_debt.csv`, `git_history.csv`, audit/manifests and `v2_import.py` identity rules | Reuse as immutable source/evidence; new adapter supplements raw measures by exact keys | Do not add columns to or rebuild the frozen export |
| Phase2/2.1 target, state-proof, past-input and purge rules | Reuse principles/tests; new v2 implementation/IDs | New languages/domains/feature vectors cannot masquerade as old core90 IDs |
| Existing Phase3/4.x forecast code/results/checkpoint/environments | Preserve; data readiness has no model invocation | No rescoring or benchmark replacement |
| `build_module_mart.py.collect_history` and scalar window/statistic helpers | Inspect/reuse algorithms selectively; implement strict cutoff/family source events in new package | Existing no-merge/Java/weekly assumptions differ; never call the whole pipeline |
| `modules.py` Java production-file mapper | Preserve and replace only within the new package with registry-driven inventory | Old module lineage/weekly functionality must remain intact |
| `compute_project_sonar_features.py` nearest-value/zero-fill/combined-effort behavior | Do not reuse for admitted observations/features/targets | Conflicts with exact states, missingness and native maintainability target |
| Existing scan scripts / server projects | Preserve; do not call automatically | Route B uses a separately planned fresh project/output scope only when scans are authorized |
| Old NPF/CMR/TDPSN marts and Zenodo series | Quarantine/exposure inventory, optional metadata inspection | No automatic target conversion, raw-value copy into confirmation or training |
| Existing authorization/job/serving/dashboard infrastructure | Defer | Not necessary for a reproducible local data pilot |

## Milestones and critical path

One person-day =8h. Estimates assume two contributors at10h/week each (20h total/week), existing Python tooling and modest repositories. They are engineering estimates, not measured runtime. Core effort **6–9 person-days =48–72h =2.4–3.6 elapsed weeks**. Critical path: M0 source/scope admission →M1 contracts→M2 adapters→M3 features/target proofs→M4 real-data pilot→M5 verification/publication. M0 metadata acquisition and M1 contract tests can partially overlap across contributors. Waiting for data/permissions is additional calendar time.

| Milestone | Person-days | Primary contributor | Dependency / concrete deliverable |
| --- | --- | --- | --- |
| M0: preregistration and source quality | .75–1 | A | Exposed-family inventory, dataset/license/capability manifests, accepted acquisition route and pinned cutoffs |
| M1: new contracts and immutable I/O | 1–1.5 | B | M0 policy; tested schema2 records, deterministic manifests and split-store isolation |
| M2: source adapters and lineage | 1–1.5 | A | M1; legacy candidate import, archive adapter, Git graph/numstat quality evidence |
| M3: F0/F1 and exact target admission | 1.5–2 | B | M2; feature/evidence bundle and separate labels/statuses, no fitting |
| M4: smallest real multi-language pilot | 1–1.5 | A+B | Acquired admitted data; up to3 dev families/18 states/9 exact endpoint cases, coverage and failure report |
| M5: regression, preservation and publication | .75–1.5 | A+B | M4 or documented acquisition blocker; Phase5.1 implementation/readiness report and verified safe GitHub commit |

### M0 — Freeze study and source selection

Expected new files: `forecasting_multilanguage/study.schema2.example.json`, `forecasting_multilanguage/registry.py`, data-source/feature/target contract templates and a new study output manifest. No old config is edited. Real local paths/tokens belong to ignored local config, not examples.

Tasks:

1. Hash and verify previous bundles/code/locks/checkpoint inventories; save a new outside-repo preservation receipt. Start central checkout from remote `main`, preserve working checkout's unrelated history and use explicit-file sync only.
2. Build a repository exposure union from V2 `PROJECTS`, all previous MVP splits, local NPF/CMR repository registries, NPF card/viewer identifiers and the209-name Zenodo benchmark. Map aliases/provider IDs/forks; unresolved family identity is quarantined. Do not open prospective held-out numerical outcomes.
3. Record source licenses and revision/digest metadata. NPF unknown licensing and Zenodo ND redistribution restrictions do not disappear because files are readable. Obtain owner archive rights or use fresh code sources with an explicit compatible data-publishing policy.
4. Register **three development families only** for the engineering pilot: Java-dominant, Python-dominant and genuinely mixed Python+JS/TS. The mixed project is not JS/TS-dominant; a fourth JS/TS-dominant project is outside this pilot. Prefer a small Python+JS/TS mixed project; Java with only XML does not satisfy the mixed-programming-language case. Use metadata/build feasibility, a fixed hash order and frozen pre-outcome spare list; log all attempts/failures. No claim that those projects are reserved today.
5. Choose a retrospective-fixed-analyzer or operational-as-of mode. For replay choose a fixed historical lineage and origin T0 from metadata coverage with the−90/+90d span; write UTC cutoffs before inspecting numerical snapshot values. For imports require corresponding state proofs. Operational mode requires contemporaneous availability metadata; otherwise do not assert it.
6. Register future confirmatory protocol, not labels: target24 new families/12 final held-out, development temporal folds and exposure exclusion as in the report. Concrete final URLs, exact split boundaries and counts remain **not reserved** until this gate is completed; no random reassignment of old tests.

I/O: source/capability manifests + metadata-only coverage -> registration, attempted-ID/cutoff policy and typed blocker list. Acceptance: no exposed family in a reserved held-out role; missing data rights/domain/runtime are explicit; no raw numeric future-label access needed to select projects/cutoffs. If source admission fails, stop acquisition and continue only metadata/contract work.

### M1 — Minimal additive contract and serialization foundation

Expected files: `forecasting_multilanguage/__init__.py`, `contracts.py`, `io.py`, `cli.py`, `__main__.py`; `tests/test_multilanguage_contracts.py`.

Implement dataclasses/validators for repository/capability/domain, snapshots/measures, Git events, feature evidence, origin/target/label status and COMPLETE manifests. Logical schemas and units are fixed by the architecture. Keep observations, features, labels and cohort metadata in separate files/bundles. Feature input must not accept a label-store object.

I/O: validated registration + typed records -> new deterministic CSV/JSON bundles. No package upgrade is needed for ordinary dataclasses/stdlib CSV/JSON/hash handling. Dependency requirements, if any later prove necessary, get a new separate lock/environment rather than editing old locks.

Acceptance tests: round-trip null versus0, numeric units, finite-value rejection, UTC-aware timestamps and exact30/60/90 duration; duplicate identity rejection; unknown domain !=known compatible domain; changed payload/hash fails integrity; write failure cannot leave COMPLETE; stable sort/serialization; reject91-day use under a90-day contract. Unit fixtures are explicitly synthetic software tests, never published as real-world measurements.

### M2 — Read-only sources, state identities and conflict handling

Expected files: `adapters/v2.py`, `adapters/sonar_archive.py`, `git_events.py`, `inventory.py`, `admission.py`; `tests/test_multilanguage_sources.py`.

Implement read-only V2 access, strict nonnegative text-numstat parsing and exact project/analysis/revision joins. Emit V2 candidate metrics with raw row references and `LEGACY_DOMAIN_UNVERIFIED`; do not invent server/plugin versions. Import external archived snapshots only when native payloads/manifests prove exact revision/domain/scope. Normalize comma/semicolon NCLOC distributions with unparsed-token reporting; a profile-only language is never marked measured.

Git graph admission must check cutoff ancestry, complete windows, merge/root behavior and chronology. Duplicate `(project,SHA,path)` groups must be kept with conflict provenance. For optional F2, compare a deterministic development-only sample of at least10 conflicting +10 clean keys across>=3 projects against pinned first-parent Git diffs **if those objects are already available or acquisition was separately approved**. This is a correctness check, not a model experiment. No SUM/MAX/MIN repair. Binary, missing-parent and unresolved conflicts make affected churn aggregates missing. Without accessible Git proof, F2 stays disabled; F1 commit activity remains viable.

I/O: raw immutable sources -> admitted events/snapshots or candidate/quarantine/exclusion records. Acceptance: reproduce Phase5 raw source counts/coverage where source hash matches; detect a known conflicting non-merge group; exact raw-to-normalized provenance; same-state/domain key with contradictory values rejects; whole scope unavailable when an expected language fails; no current filesystem/branch rewrite of old evidence.

### M3 — Past-only feature views and independent exact targets

Expected files: `features.py`, `targets.py`, `cohorts.py`; `tests/test_multilanguage_features.py`, `tests/test_multilanguage_targets.py`.

Implement exactly the matrix's F0/F1 column lists with value statuses/reasons and dependency evidence; no learned transformation/embedding. F2 is separately gated and can remain disabled. Retain missing rows/features rather than manufacturing observability. Snapshot size/complexity/categories join only by admitted observation identity, never nearest date. Sparse debt slopes use actual elapsed times and>=3 distinct measured states/timestamps; the past30-day debt change requires its own exact state proof.

Target builder resolves future states independently at exact30/60/90 days. A valid same-unchanged-state endpoint needs complete state/domain proof; otherwise emit unknown/excluded without numerical value. Predictions are not generated. Existing frozen labels/splits are never rebuilt. All model-facing names are explicitly allowlisted; metadata/labels/split roles are separate.

I/O: origin/state proofs + admitted past inputs -> `features.csv`, `feature_evidence.jsonl`; independent endpoint evidence -> `labels.csv`; metadata registration -> `cohorts.json`. Output names refer to a **new schema2 study**, not replacements of `forecasting_dataset.csv` or the old registered split files.

Acceptance tests: inject future source values/statuses and verify X unchanged or rejected; reject `actual_*`, `TD_*`, endpoint observation IDs, future paths and partition roles at the predictor boundary; verify events after cutoff and unresolved chronology never contribute; no churn-zero on incomplete history; feature source time<=cutoff and, in operational mode, availability<=cutoff; exact endpoint proofs, domain changes and missing states behave correctly. Test overlapping examples are purged by their registered information intervals without consulting outcomes.

### M4 — Three-family engineering pilot

Expected files: `analysis_plan.py` (plan-only unless route B is explicitly authorized), `tests/test_multilanguage_pilot.py`; new external pilot artifact directory and readiness report.

Per family freeze six UTC state cutoffs relative to T0: **−90,−30,0,+30,+60,+90 days**. Those are planned state-measurement times, not fabricated sample values. Resolve the source revision actually active at each cutoff using admitted lineage/chronology. Each independent native observation must have raw payload and complete analyzer/scope provenance. If unchanged cutoffs share a revision, record state/measurement reuse instead of claiming six independent changes.

Route A imports those states (or reports unavailable proof). Route B, if explicitly authorized, runs **at most18** new development snapshot jobs total in a separate server project/output namespace, sequentially,20min per job and<=8GiB total monitored server/build/job budget,<=5GB new artifacts and>=10GB disk reserve. Capture exact versions, dependency/build context, scanner completion and component/language coverage; never report a failed/partial scan as zero debt. Do not change old projects, force scanner upgrades or retry an unbounded build. Planning/acquisition/replay overhead adds estimated2–4 person-days (16–32h) to the core route; failures/data permissions may extend elapsed time or block it.

For one admitted T0 per family, up tothree exact targets give **at most9 endpoint cases**. These cases verify serialization, provenance and exact-target contracts; they are **not a training/evaluation corpus**, independent90-day time series or evidence of model accuracy. Three measured past states cannot satisfy Chronos's existing90-daily-state input contract; no synthetic daily grid is created. Git activity features still use the complete true event windows, not only the six scan times.

Acceptance: real evidence for one Java-dominant, one Python-dominant and one genuinely mixed Python+JS/TS development family, all present values traceable; per-repository/horizon eligible/unknown counts and exact missing reasons; domain/scope mismatches stop strict target admission; all original hashes unchanged. If required non-Java data cannot be acquired, publish PARTIAL/BLOCKED readiness with the working adapters and precise blocker. Do not substitute classification datasets or synthetic repository metrics for real observations.

### M5 — Proof, report and safe publication

Expected files: new `PHASE_5_1_IMPLEMENTATION_REPORT.md`, package README and small approved evidence. Tests reuse the existing harness; do not add parallel infrastructure.

Run focused new contract/source/feature/target/pilot checks and the relevant full regression suite with the actual CatBoost training test excluded. No model fitting/inference or scan begins because a test has a convenient helper; scan execution remains confined to route B's explicit authorization. Verify deterministic artifact output and source manifests; no empirical result is invented for unavailable data.

The report must include actual source coverage, newly acquired languages, exact target proof counts (not aggregate row inflation), distinct scans/states/contexts, unresolved churn conflicts/domain/availability gaps, failed acquisitions, resource measurements if any, missingness, version/hash provenance, tests and an honest PASS/PARTIAL/BLOCKED next-study gate. Separate operational evidence from retrospective reconstruction.

Publish only verified new source/tests/templates/docs and small license-safe evidence to the same GitHub `main` using normal descendant commits; preserve remote changes and unrelated original checkout state. Exclude source databases, environments, model weights, secrets and large/raw private exports. Verify remote SHA and changed contents, then STOP. Phase6 fitting/evaluation is not automatically authorized.

## Confirmatory-study prerequisites after the pilot

Before later Ridge/CatBoost evaluation, require a new frozen family/cutoff registry, complete domain and exact-target evidence, development-only transforms/selection, source licensing and a documented prediction-seal/label-open boundary. A12-family held-out enrollment is a proposed inferential minimum for this study, not a guarantee of power; actual accepted clusters and missing endpoints must be reported. Three-family engineering success alone does not pass this gate.

Use a larger development history to support the three strict purged temporal folds; the six-state pilot does not. Optional Chronos is NOT APPLICABLE unless independent daily contexts genuinely meet its original input contract. If new test history/outcomes remain insufficient, report feasibility as blocked and prefer a transparent retrospective data-quality contribution over an unsupported forecasting superiority claim. Preserve the pretrained capability as optional research without forcing it into a sparse-data comparison.

## Risks and predetermined fallbacks

| Risk | Response fixed before outcomes |
| --- | --- |
| No licensed new non-Java archive | Request/acquire owner exports in a future authorized step, or bounded replay if authorized; otherwise BLOCKED_NONJAVA_DATA |
| Git numstat conflicts/objects missing | F2 disabled or affected windows explicitly missing; run F0/F1 readiness without unsafe sums |
| No complete analyzer/rule/build metadata | Quarantine legacy candidate data; no strict confirmation or made-up version |
| Incompatible historical build / unsupported scanner language | Record failure, leave target unavailable; do not substitute source-only or partial whole-repo metrics |
| Mixed repository only partially analyzed | Whole-repository target unavailable; a separate partial-scope study would need its own preregistration |
| Exact30/60/90 endpoint unavailable | Null/status, no nearest timestamp/91-day substitution; acquire the actual state measurement later if authorized |
| Few independent scans or repeated states | Report diversity; do not inflate observations through rows/files/grid filling |
| Host RAM/disk/build limits | Sequential jobs, fixed caps, imported archives or defer to an approved larger host; no automatic budget expansion |
| Future confirmatory cohort is exposed or leaked | Quarantine/deviation; no relabeling old test IDs as fresh or outcome-informed replacement |
| No significant benefit over persistence later | Publish negative/inconclusive results and retain persistence; no test-tuned pivot |

The current task stops after the four Phase5 design documents are verified and published. This plan supplies decisions and gates for an explicitly authorized Phase5.1; it is not an instruction to execute its tasks now.

> Phase 5.1 scope correction (2026-10-15): the three engineering development targets are Java-dominant, Python-dominant and genuinely mixed Python+JS/TS. The mixed target is not JS/TS-dominant; no fourth project is included. Original Phase 5 findings remain historical design evidence. Current implementation/data readiness: [Phase 5.1 report](PHASE_5_1_IMPLEMENTATION_REPORT.md).
