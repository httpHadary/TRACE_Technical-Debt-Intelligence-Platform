# Architecture Reviewer Gate — adversarial seams and rubric

Reviewed: `2026-10-13-techdebt360.md` and `OPTIMAL_SYSTEM_ARCHITECTURE.md`, as read on 2026-10-13. Review only: neither deliverable edited. This is the independent architecture seam/adversary and good-spine rubric lens, not a claim of completed implementation validation. Line citations refer to the draft read in this pass and may move after parent edits.

**Verdict: changes needed before handoff.** The paradigm and evidence boundaries are sound, but independently compliant API/history/model/worker units can still select incompatible observations, IDs, capability states and aggregation policies. No critical defect found; seven high and three medium findings below. Clear rules for frozen evidence, unsupported forecasts, disabled unlicensed specialists and isolated verification should be retained.

## Concrete incompatible yet compliant units

**Unit A: evidence API, Unit B: history/forecast worker.** A follows solution lines 155–158 and selects the newest completed Analysis for a requested snapshot; B follows lines 39/66/130 and selects the earliest eligible Analysis in its frozen domain. Both respect exact snapshot identity and verified publication. A snapshot has multiple Analyses in the ER diagram and no canonical analysis selector is bound. They return different maintainability minutes for the same apparent snapshot/entity; the UI plots a forecast trained against B's value next to A's observed value. Both satisfy the present snapshot rules. Bind an explicit `(snapshot_id, analysis_id, domain_id)` selection contract and have all derived findings, rankings and context carry it.

**Unit C: graph evidence extractor, Unit D: ranking service.** C interprets a resolved Java graph as directed file imports and computes file fan-in, counting each importing file once. D expects primary-module resolved dependencies and computes fan-in as summed import edges, with percentiles over the current repository. Both satisfy `D is resolved graph fan-in percentile` and primary-module membership. They integrate using a number called `D`, yet mean different dependency strength and percentile populations; rankings change even though both advertise policy v1. Bind the graph direction, vertex/edge kind, resolution/coverage rules, de-duplication and normalization cohort in an immutable policy.

## High findings

### H1 — Snapshot endpoints do not select the observation domain or analysis

**Locations:** spine AD-2/AD-4 (43/55); solution 57–59, 79–83, 155–158, 161.

One snapshot may have multiple verified analyses from different domains or reruns. The snapshot-scoped measurement/finding/ranking routes provide no mandatory `analysis_id` or `domain_id` and do not define selection or conflict behavior. A caller can consequently combine current evidence, context and comparison results from different analyzer domains while preserving snapshot identity.

**Fix:** make the observation selector explicit on every evidence/history/ranking request; reject ambiguous snapshot-only requests, or specify one immutable canonical analysis alias with a versioned selection policy. Require joined responses and artifacts to carry the selected analysis/domain IDs. Define whether reruns in an identical domain supersede, coexist or must hash-match, and why any difference is acceptable. Add this invariant to AD-2/AD-4 rather than leave it entirely to the API unit.

### H2 — Shared IDs and immutable hash canonicalization are incompletely bound

**Locations:** spine 107; solution 52, 57, 60–65, 71, 121, 162–163.

`source_unit_id`, chunk IDs, recommendation IDs and some lineage IDs are used across units without owning record definitions. One adapter can identify a source unit by path/line range while another uses a parsed symbol or content hash; both are compatible with the current source-hash rule. The UUID versus immutable-SHA convention does not define domain-separated hash inputs or JSON canonicalization, so independently serialized configs/manifests can acquire different IDs.

**Fix:** bind source-unit identity to repository/snapshot/blob hash plus extractor version and an unambiguous coordinate/symbol scheme; bind chunk identity separately to chunk policy and exact content span. Assign Recommendation ownership and bind it to the immutable finding/analysis/context/prompt/model result that generated it. Define canonical hash serialization and domain namespaces once. Define common Job/Attempt IDs and minimum state fields in the ownership contract. Keep storage tables as seed, but shared identity rules belong in the spine.

### H3 — Sonar project lease does not define its contention and fencing scope

**Locations:** spine AD-3/AD-8 (49/79); solution 35–36, 45, 174–176.

`One analysis/project lease` can be interpreted as an `(analysis_id, project_key)` lease, which permits simultaneous analyses in one mutable Sonar project, or as a server/project lease covering every job. Database attempt fencing blocks stale row publication but does not itself stop an expired runner from submitting to or altering the external project while a replacement runner scans. Ownership also names Analysis service as publication owner while the spine assigns publication to worker; distinguish semantic authority from executor.

**Fix:** bind external analyzer exclusion by `(server_identity, sonar_project_key)` across all attempts/snapshots, or give each analysis a unique disposable project. Specify how a stale external runner is terminated/quarantined and how recovery proves the project is safe before reassignment. Fence both artifact publication and capability/job mutations using the current attempt; validate the exact external task/analysis identity after export. Analysis application service should own validation/publication rules, worker should execute them through a port.

### H4 — Capability expiry/revocation has no atomic serving rule

**Locations:** spine AD-5/AD-8/AD-12 (61/79/103); solution 67, 70, 75, 160, 168, 184.

The tuple and states are defined, but the scheme leaves `expires_at` behavior and concurrent grant/revocation/publication unresolved. A forecast job can pass `VALIDATED` at submission, then publish after domain/model revocation. A stored Prediction includes a capability state snapshot; the UI can display that old state even after the capability is no longer eligible. Two compliant units can disagree between historical research evidence and current product-serving eligibility.

**Fix:** define a unique immutable capability-grant ID/version, link Predictions to it, and require atomic validation against the active nonexpired grant at publication and serving. Append revocations; preserve historical predictions for research with their old provenance, while live display derives current eligibility. State exactly which data/domain/model/target revisions invalidate which grants, and how an offline evaluator prevents a stale grant from overriding a newer revocation.

### H5 — Forecast target/horizon/cohort key is thinner than the stated invariants

**Locations:** spine AD-6 (67); solution 66–70, 123, 160.

The API/Capability still keys on integer `horizon_days`, while the spine permits exact90 and approx91 and binds cohort/endpoint eligibility. `target_contract_id` is referenced without a target contract that fixes cadence, endpoint-selection tolerance, membership/aggregation semantics, censoring and label availability. A model adapter can output a 13-step weekly forecast while the evaluator expects an exact endpoint; both can assign horizon_days 91. A cohort selection rule can also change without changing the displayed target ID.

**Fix:** make `target_contract_hash` the shared immutable key, containing duration/cadence/endpoint selection, outcome/unit, aggregation membership policy, origin eligibility, missing/censoring and label availability. Require registered origin and endpoint IDs in predictions/evaluations and distinguish requested wall-clock horizon from model step count. Bind capability to that hash and the relevant cohort/lineage policy versions. If exact90 only is the MVP, disable approx91 at its boundary until a distinct contract exists.

### H6 — Ranking policy leaves graph and normalization seams divergent

**Locations:** spine AD-9 (85); solution 136–142.

The weights are explicit but graph fan-in semantics and normalization population are not. `training/development-fixed normalized trailing90day churn percentile` permits different handling of renamed/deleted files, merges, churn units, ties and repository/module populations. A file rank and module rank can be compared despite different scales. The graph example above is a concrete compliant divergence.

**Fix:** publish an immutable factor policy per granularity: source metric, units, lookback and availability cutoffs, lineage rule, normalization cohort/hash, tie method, clipping, missingness and zero-denominator behavior. Bind graph extraction direction/edge semantics and resolution coverage. Keep partial/complete rankings separate as already proposed; do not permit policy v1 labels to cover incompatible factor definitions. Treat weights as preferences, as the draft correctly does.

### H7 — Remediation verification policy and approval binding allow divergent acceptance

**Locations:** spine AD-10 (91); solution 71–73, 124, 164–170, 174.

Compile/tests/differential comparisons are required in prose, but clients supply `testpolicy`, `domain` and `attemptbudget`; the contract does not say which minimum policy is non-overridable, which test failures/no-tests/timeouts force PARTIAL, or whether findings from different analyses can enter one candidate. Approval references candidate and verification but not the exact patch/candidate tree or policy hash. A lifecycle update can change a candidate's patch while one unit considers approval stale and another treats candidate identity as sufficient.

**Fix:** bind each candidate to one exact base snapshot/analysis/domain, immutable patch and changed-file manifest, and an immutable minimum verification-policy hash; supplied budgets may bound work but cannot relax the policy. Define status transitions for failed/no/partial tests and unresolved before/after findings. Bind approval to base commit/tree, patch hash, candidate tree, verification artifact hash and policy/evaluation versions. Export must atomically recheck this tuple and stale-base status; no route should let a mutable candidate ID substitute for approved content.

## Medium findings

### M1 — Joined ordinary words obstruct the contract and blur tokens

**Locations/examples:** spine 67 `explicitly13weeks`, 107 `schema_version1`; solution 59 `requirescomplete`, 62 `uniqueanalysis/entity/metric`, 67 `onlyvalidatedpredictions`, 73 `approvalcannot survivechangedbase/patch/evaluation`; lines 118–126, 146, 170–190 contain many more.

This is widespread prose corruption, not merely stylistic compression. It makes field/enum boundaries, units and exception rules difficult to interpret. `schema_version1` also conflicts visually with literal JSON `schema_version: 1` and prose about additive minor versions.

**Fix:** perform a prose-only spacing repair after semantic fixes, preserving actual identifiers and numbers. Explicitly choose schema version representation (integer major plus minor compatibility policy, or semver string) and use the same form in envelopes/records. Re-run lint and reread the tables; do not blindly split all identifiers. No content edited in this review.

### M2 — UI/API research permission names are inconsistent

**Locations:** spine 107; solution 146/160.

Declared roles are reader/analyst/approver/administrator (solution says admin), but forecast research mode requires an undefined `researchrole`. A model worker and API can either deny all RESEARCH_ONLY work or admit it as ordinary analyst work, with different exposure of research outputs.

**Fix:** use one role enum or explicit named permissions; bind research execution and research-output visibility separately. State normal-mode versus research-mode response behavior consistently, including null/reason versus rejected execution, and preserve status labels through the UI.

### M3 — Current references do not establish a complete evaluation/novelty argument

**Locations:** spine 12/125; solution 3/7/126 and scientific validation references.

The architecture correctly labels remediation superiority a hypothesis and does not claim universal model performance or novel invention. However, evaluation and direction companions were not present when this review read the directory, so their promised coverage cannot be assessed here. This is a temporal review limitation while the parent writes, not proof the final deliverable is missing. The exact-model research supports Qwen/CodeRank task selection, not evidence of superiority for this combined workbench.

**Fix:** parent should verify companion links after all writes and ensure the evaluation plan names the unit of benefit, baseline, human rubric, repository split, patch budgets and negative-result interpretation. Preserve the distinction between an engineering combination and a claimed scientific contribution; state novelty only if a sourced related-work comparison supports it.

## Good-spine rubric result

| Criterion | Result |
| --- | --- |
| Named paradigm and dependency direction | Pass: clear modular monolith; model/analyzer isolation sensible. |
| Fixes real divergence points for independent units | Needs work: observation selectors, IDs/hash serialization, leases, capability serving and factor policies. |
| Each AD is enforceable and prevents its named divergence | Partial: principles are strong; H1–H7 need a contract/atomic guard to become enforceable. |
| Deferred items cannot permit immediate divergence | Partial: forecast activation may be deferred, but target/capability identities must be fixed before adapters/evaluation integrate. |
| Operational/environmental breadth covered | Pass for a proposed seed: host/resources, job recovery, isolation, auth, backups, drift and retention are addressed; runtime estimates explicitly unproven. |
| Named technology fit and versions | Existing research supports model tasks and caveats; the proposed runtime compatibility checks remain future work. No new technology fit claims verified by this review. |
| Brownfield/spec reconciliation | Not fully assessed: this lens had the two architecture drafts and earlier primary model research, not a repository reconciliation brief/spec. |
| Scientific honesty and novelty | Pass provisionally: superiority remains a hypothesis; public benchmark transfer is not claimed. Final companion evaluation must be reviewed. |
| Readability and consistency | Needs work: systematic joined words and role/schema-version mismatches. |

Triage: H1–H7 are clear contract fixes before independent build handoff. M1–M2 are clear polish/consistency fixes. M3 should be checked after final companion writes. No implementation, inference or environment/config changes are needed to resolve this review.
