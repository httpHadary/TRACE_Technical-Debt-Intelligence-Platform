# Prior-plan reconciliation for the forecast-first MVP

Date: 2026-10-13. This is a planning input reconciliation, not a new data audit or experimental result. The original design and refinement packages were read; the read inventory appears below. No external sources were newly queried, and no code, configuration, datasets or previous documents were changed. Previously reported artifact counts and publisher contracts are explicitly inherited evidence that the execution phase must refresh.

## Current direction and authority

The latest user request sets **30/60/90-day forecasting as the primary MVP research feature**, using pretrained models, real future measurements, conventional controls and a minimal application. It authorizes simplifying earlier architectural decisions for planning. Therefore neither the original remediation-first preference nor refinement AD-13's requirement to complete the full detection/retrieval/repair arm before selecting the thesis remains binding for this MVP. A valid forecasting negative result remains acceptable research; a production forecast winner cannot be selected before measured outcomes.

Two contributors with ten hours **each** per week supply 20 team-hours/week. Hardware is unknown. No GPU can be assumed. The plan should begin with CPU-oriented Chronos-small, serial comparators and small batches, then measure runtime during a separately authorized execution phase. This is a feasibility assumption, not proven hardware adequacy.

## What still matters and what is superseded

| Prior decision | MVP disposition | Essential remaining requirement |
|---|---|---|
| Original bounded remediation-primary product | Superseded by user | Forecasting is the main experiment and earliest deliverable; no autonomous repair in scope |
| Refinement paired A/B thesis selection | Superseded for this focused MVP | Compare forecasting approaches empirically; GraphCodeBERT is an ancillary annotation task where feasible |
| Four active AI roles: classifier, retrieval, generator, forecaster | Simplify | Chronos-small is the first required pretrained forecast candidate; TTM is a fitting challenger; GraphCodeBERT is license/task gated; retrieval and generation are deferred |
| Exact immutable source/observation selection | Retain | Bind measurements to repository/revision, analysis ID, domain and source artifacts; never silently substitute latest analysis |
| CE task, project, revision, complete export and source coverage | Retain | Successful submission or CE completion alone is not a usable observation |
| Snapshot cutoff, commit timestamp, availability and scan/export clocks | Retain | Historical cutoff is distinct from actual execution; retrospective availability assumptions must be visible |
| Frozen measurement domain and quality separation | Retain | Imported V2 SQALE stock, current Sonar maintainability stock and NPF all-issue effort are separate targets/domains |
| Own VERIFIED vs imported research provenance | Retain | Unknown imported metadata remains unknown; do not create fake historical scanner proofs |
| Exact 30/60/90-day as-of endpoint contracts | Retain | A horizon is elapsed UTC days, not nearest scan, calendar month, next-k-commits or 13 weekly steps |
| Future label isolation and temporal purging | Retain | Endpoint revision/value lives label-side; predictors, fitted transforms and caches use only permitted origin/past information |
| Domain/task-scoped capability grants and revocation infrastructure | Replace | Frozen run metadata and clear RESEARCH_ONLY/VALIDATED/UNSUPPORTED labels suffice; model/domain changes require a fresh explicit evaluation |
| Tenant roles, research permissions and enterprise authorization | Defer | Local single-user operator and loopback read-only artifact API; authentication/TLS required before exposure beyond this trust boundary |
| Durable queue, leases, fencing and restore orchestration | Replace | One serial offline operator runner, run lock, status file, staged atomic publication, explicit failed/unknown submission states and manual reconciliation |
| Sonar external exclusion | Simplify, preserve invariant | Only one scan/export at a time per server/project; unknown external state stops reuse until exact task is reconciled |
| Registered immutable priorities with graph/utility study | Simplify | Deterministic factors and stable ordering; raw severity/current estimated minutes/change activity displayed. Forecast risk is visibly experimental unless separately validated |
| Untrusted repository execution and secret separation | Retain minimum | Fixed registered build commands, restricted work copy/container, no model-generated shell, no scanner/admin tokens inside build code or logs |
| Immutable datasets, model pins and environment isolation | Retain minimum | Source hashes, reproducible manifests, exact model SHA, package lock after load checks and separate incompatible runtimes |
| Repair verification, approval tuples and patch export | Defer | No patch generation, autonomous remediation or associated test/approval services in MVP |
| Module identity/decomposition and lexical graph work | Preserve, defer deployment | Reuse Git/module inventory where useful; public project aggregates must never be presented as module/file targets |
| Old API/schema v1/v2 migration | Defer | Add a distinct MVP research artifact/API namespace; preserve old artifacts without relabeling or migrating them |

This simplification removes operational machinery while preserving the scientific facts it protected. The documentation must not inherit all previous AD-5/8/10 infrastructure through an ambiguous statement that “all earlier invariants remain binding.” State the replacements explicitly.

## Data precision concerns that can invalidate a fast result

**Repository-level V2 is the strongest immediate lead.** The refinement read-only audit recorded 31 projects, 66,711 uniquely linked measure/Git records and 67,550 analysis rows. It also recorded **19,954 unmeasured commits inside the project measured spans**. Thus sorting measured rows and forward-filling their values is unsafe: the actual selected branch state may have changed through an unmeasured revision.

Select a deterministic historical branch state at each origin, each daily context cutoff and each exact endpoint. Reuse a measurement only for the same selected revision and compatible domain. Unchanged-state reuse is valid but does not add independent observations. Missing selected revisions remain missing or become explicitly budgeted collection tasks. An endpoint scan on a matching date is neither necessary nor sufficient. Previously counted exact-date and exact-second pairs are diagnostics, **not upper or lower bounds on the future eligible as-of cohort**.

The V2 audit found exact-second agreement between analysis DATE and Git author/committer timestamps, with UTC Git offsets. The analysis DATE is naive imported historical timing, not actual scan execution or branch-observation evidence. Existing parent/main-branch metadata must still support the declared reconstruction policy. When actual historical availability logs are unavailable, publish a **retrospective ancestral-branch approximation** and restrict the claim accordingly; do not call it an online deployment simulation without qualifications.

Profile metadata does not certify full analyzer comparability. The 79 serialized-profile segments and 48 transitions were not 48 proven Java rule changes; the Java profile tuple was constant on 66,683 rows. Conversely, profile-key equality cannot prove identical rules, plugin versions, build mode or remediation settings. V2 results are imported historical-domain findings, not proof that a forecaster will work on today's SonarQube measurements. Current ingestion/current Sonar measurement and historical forecast benchmarking are two connected platform paths with separate scientific domains.

Own module collection routines exist, but no admitted real module cohort was found previously. Preserve their code and contracts; do not make building a new longitudinal module corpus the MVP critical path. Kafka's eight manifest entries have execution timestamps on one day and one paired repository case; they are not eight independent temporal trajectories. Local monthly file exports contain 144 distinct repository/revision states across 180 snapshots. Their retained mart mixes 90/91/92-day endpoints and has 96.52% unchanged raw-minute pairs. Neither row count nor the prior density-model metrics proves raw-minute repository forecast performance.

NPFDataSet is a **separate optional resource**: documented 21/28/91-day all-issue effort, unknown license, source-only modern analysis of historical code and incompletely verified usable cohort. It cannot satisfy exact 30/60/90 maintainability labels by renaming columns. SDK4ED is code/method material, not independent ground truth. Weekly Zenodo series can support a separately named 91-day replication; related replication packages reuse data and do not add independent repositories.

## Model and evaluation details to preserve

1. **Chronos-2-small first.** The verified public contract supports regular series and a horizon sufficient for 90 daily steps. Weight availability and CPU documentation are not a measured local runtime or accuracy result. The runner must validate regular timestamp handling, masks, shapes, output point semantics and shared q0.1/q0.9 intervals using the exact pinned revision.
2. **TTM is branch-specific, not uniformly 512-context.** Inspected daily candidates are 90→30, 180→60 and 512→96 cropped to 90; weekly 52→16 cropped to 13 means 91 days. Context comparisons must be matched by horizon/cohort, with wider Chronos coverage reported separately. Padding does not create actual history. The explicit decomposed model class is needed for bare-SHA pinning because the inspected loader dispatch used `-dec-` substring matching. Mask-aware scaling does not establish LOWESS robustness to missing gaps. Its configured 0.5 slot is a mean, not an assumed statistical median.
3. **Keep a small control set.** Persistence, bounded drift/trend and one reused CatBoost baseline are sufficient initial controls; LightGBM is a documented alternative if its incremental runtime/dependency work fits. Seasonal controls require demonstrated seasonality. Fine-tuning, broad model searches and full Chronos/TimesFM are later extensions, not mandatory MVP integration.
4. **GraphCodeBERT annotations require their own gate.** The checkpoint exposes four independent Java category logits, normalized lowercased function input, 512-token eligibility and no explicit calibrated clean label. No data-flow graph construction was present in the inspected fine-tune recipe. Weight license remains unresolved. Do not use its scores as Sonar minutes, repository stock or future-label substitutes. Blocked licensing is not an accuracy failure.
5. **Freeze metrics and comparisons before outcomes.** Report MAE/RMSE in estimated remediation minutes, macro and per-repository results, changing/constant subsets, common origin IDs, failed predictions and useful coverage. Relative baseline improvement is undefined when the baseline MAE is zero; report absolute differences. Do not use MAPE as the primary zero-heavy metric.
6. **Quantile levels matter.** Native q0.1/q0.9 give a central 80% interval. They do not produce a 90% interval. Calibration is separate validation-only fitting. Quantile crossing and negative forecasts remain recorded; clipping or repair is a separately evaluated variant.
7. **Three separated blocks/five held repositories are governance proposals, not proof of power.** A small MVP can publish exploratory measured errors with denominators and limitations. Claimed generalization and confidence must reflect repositories/time blocks, not rows or repeated seeds. Forecast deployment and success of the software demonstration are separate gates. The prior ≥10% MAE improvement/70% repository benefit gates are chosen product preferences, not scientifically mandatory positive outcomes.
8. **Do not select after test inspection.** Pick context/missingness policy, common cohorts, model hyperparameters and normalization using contracts/development data. Purge future labels across chronological boundaries. Keep pilot-inspected outcomes out of a test described as untouched. Old public repositories can overlap foundation pretraining; disclose residual contamination.

## Capacity arithmetic and realistic sequencing

Using an explicit eight-hour person-day, 20 team-hours/week is **2.5 person-days/week**. Four weeks provides 80 hours/10 person-days; six weeks provides 120 hours/15 person-days. A 20% reserve consumes 16–24 hours of that envelope rather than creating extra capacity.

| Earlier scope | Prior effort | Elapsed time at current capacity, before contingency |
|---|---:|---:|
| Original base product | 70–119 person-days | 28–47.6 weeks |
| Refinement paired hybrid | 38–64 person-days | 15.2–25.6 weeks |
| Refinement after its 20% reserve | 45.6–76.8 person-days | 18.2–30.72 weeks |

Those prior estimates cannot be compressed to 4–6 weeks through two-person parallelism: capacity already includes both people. A newly reduced plan must budget in hours as well as person-days, with coordination, reviewer labor and delayed external access included once. Neither a GPU nor unattended compute removes cohort-audit and implementation labor.

The critical path should be **verified historical dataset → frozen splits → real baseline and pretrained predictions → observed endpoint comparison/MAE-RMSE → minimal read-only API/dashboard**. Current repository/Sonar collection and bounded classifier admission can run on a separate contributor track after shared contracts; neither a dashboard nor ambitious fresh backfill should delay the first empirical forecast result.

A 4–6-week target is conditional on useful existing V2 cohorts, ready runner dependencies, modest CPU runtime and minimal thin UI. Price the full mandatory scope honestly. If the six-week ceiling cannot fit, identify the four-to-six-week deliverable as a forecasting research demonstrator and show the additional effort needed for current repository ingestion, current compiled Sonar evidence and feasible classifier annotation. Do not silently omit mandatory capabilities while claiming a complete platform.

If exact-calendar labels fail, first narrow to better-covered repositories/horizons and calculate a deduplicated missing-state acquisition budget. A new current-domain scan cannot patch an old imported-domain series. A smaller-granularity study cannot be created from project aggregates. Only after bounded acquisition/domain checks should the plan fall back to a separately declared 91-day or next-k-observation experiment, or pretrained debt-category assessment; each has distinct targets and no forced performance claim.

## Documents actually read

All entries below were read during this reconciliation. Large duplicated model sections in the original PRETRAINED_MODEL_RESEARCH were confirmed as verbatim embedded code/forecast digests and read completely through those digest files; its unique introduction and newer-candidate sections were read separately. Redundant review logs, append-only memlogs and source-hash tables were excluded from the substantive read set.

| Package | Document | Reconciliation purpose |
|---|---|---|
| Original | README.md | Original recommendation, contracts and fifteen decisions |
| Original | brief.md | Scope, method and assumptions |
| Original | REQUIREMENTS_TRACEABILITY.md | Original instruction coverage and hierarchy |
| Original | CURRENT_SYSTEM_AUDIT.md | Existing implementation/evidence/reuse map |
| Original | RESEARCH_DIRECTION_DECISION.md | Remediation-first choice and sensitivity |
| Original | RESEARCH_SUMMARY.md | Source-backed findings and limitations |
| Original | DATASET_AND_FORECAST_FEASIBILITY.md | Data populations, horizons, acquisition scenarios |
| Original | FORECASTING_RESEARCH_PLAN.md | Target/cadence, splits, metrics and gates |
| Original | PRETRAINED_MODEL_RESEARCH.md | All candidates and role/task separation |
| Original | MODEL_EVALUATION_PLAN.md | Label independence, ablations and reproducibility |
| Original | OPTIMAL_SYSTEM_ARCHITECTURE.md | Components, schemas, APIs and operational complexity |
| Original | END_TO_END_WORKFLOW.md | Success, failure and recovery paths |
| Original | IMPLEMENTATION_ROADMAP.md | 70–119-day scope and dependencies |
| Original | PROOF_OF_CONCEPT_PLAN.md | Existing CLI versus future harness and experiment contracts |
| Original | 2026-10-13-techdebt360.md | AD-1–AD-12 and architecture hierarchy |
| Original | DELIVERABLE_VERIFICATION.md | Planning completion boundaries, unrun experiments |
| Original | digests/local-audit.md | Local source/count evidence and retained metrics |
| Original | digests/code-models.md | Classifier/generator/retriever exact task contracts |
| Original | digests/forecast-models.md | Forecast checkpoint/cadence/environment contracts |
| Original | digests/public-datasets.md | Public data target/license/provenance distinctions |
| Original | digests/additional-candidates.md | Unnecessary larger/newer models to defer |
| Refinement | README.md | Revised experiment-first hybrid direction |
| Refinement | brief.md | Revised user authority and evidence method |
| Refinement | RESEARCH_NOTES.md | Short-context TTM and as-of-count corrections |
| Refinement | REVISED_ARCHITECTURE.md | v2 shared contracts, paired research and infrastructure |
| Refinement | PRETRAINED_MODEL_STRATEGY.md | Eleven models, explicit branch/class/pinning and licensing |
| Refinement | FORECASTING_FEASIBILITY.md | Latest data readiness, as-of endpoints and acquisition |
| Refinement | RESEARCH_EXPERIMENTS.md | A/B cohorts, metrics, denominator policy and future-only commands |
| Refinement | REVISED_IMPLEMENTATION_ROADMAP.md | 38–64-day effort, reviewer hours and reuse map |
| Refinement | 2026-10-13-refinement.md | AD-13 and amended invariants requiring explicit supersession |
| Refinement | VERIFICATION.md | Verified artifact claims versus unknown efficacy |
| Refinement | digests/data-reaudit.md | Fresh prior V2 joins, domain clocks, counts and exact-count corrections |
| Refinement | digests/model-reverification.md | Short TTM branches, loader hazard and output semantics |

Links: [original package](../../2026-10-13-techdebt360/README.md), [refinement package](../../2026-10-13-refinement/README.md). The MVP's six main planning documents must be authoritative for this reduced scope; these older packages remain supporting evidence and historical design, not implicit instructions to restore deferred infrastructure.
