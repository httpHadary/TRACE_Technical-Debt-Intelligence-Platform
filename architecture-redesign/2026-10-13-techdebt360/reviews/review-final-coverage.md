# Final requirement reconciliation

Review date: 2026-10-13. Read the original [1,097-line user request](/home/hp/tst/TECHDEBT360_BMAD_DESIGN_ONLY_COMPLETE.md) and all ten named deliverables, including the model-specific sections and the updated architecture/contracts. No documents were edited by this review. No scans, installs, inference, tests or training were run.

**Verdict:** all ten deliverables and all major requested capabilities are covered. The package supports a practical, defensible **provisional evidence/remediation product direction**, a serious early V2 repository forecasting branch and a final present-day conclusion that **reliable deployed exact 90-day own-module forecasting is unsupported**. One interval-promotion contract mismatch should be resolved before final handoff; an early-gate scheduling clarification is also advisable. Runtime, label, hardware and scientific efficacy questions correctly remain future experiments rather than fabricated results.

## Handoff corrections

### P1 — Make interval promotion requirements consistent

[Feasibility, value gate](../DATASET_AND_FORECAST_FEASIBILITY.md) requires calibrated **90%** intervals with 85–95% coverage. [Forecast protocol, metrics/promotion](../FORECASTING_RESEARCH_PLAN.md) requires common native **80%** intervals with 75–85% coverage, treats calibrated 90% as a separate layer, and permits promotion after the common 80% gate. [Architecture](../OPTIMAL_SYSTEM_ARCHITECTURE.md) and [workflow](../END_TO_END_WORKFLOW.md) correctly expose native 0.1/0.9 intervals as 80%.

**Correction:** one governing requirement should say native 80% comparison/promotion, with separate held-out calibration and 90% coverage criteria **only if a 90% product interval is promised**. Alternatively require 90% everywhere and explicitly budget that calibration layer. Do not let evaluation and capability serving choose different promotion predicates. This is a design-handoff blocker, not a request to run calibration now.

### P2 — Clarify the early gate's resource/time meaning

[Direction decision](../RESEARCH_DIRECTION_DECISION.md) and [roadmap](../IMPLEMENTATION_ROADMAP.md) name a first two-week thesis-selection gate. M0 + M1 + M4 estimate **13–21 person-days**, while the envelope assumes **3–5 effective contributor-days/week**; full M7 repair pilot is later. Two elapsed weeks at the stated capacity cannot complete those milestones plus validate superiority. This does not invalidate a fast preliminary feasibility gate.

**Correction:** label the early gate a capped preliminary audit/smoke/harness check, with a task/effort subset and a provisional decision, or make elapsed timing conditional on adequate staffing. Definitive accuracy/repair efficacy selection still follows M5/M7 registered outcomes. The total base milestone arithmetic itself is correct: 70–119 person-days. This is a planning clarification, not missing implementation.

## Ten-deliverable coverage

| Required artifact | Coverage verified |
|---|---|
| [CURRENT_SYSTEM_AUDIT.md](../CURRENT_SYSTEM_AUDIT.md) | Existing repository/runtime reality, retained versus synthetic results, failures, scan-export semantics, component reuse/modify/defer/remove choices and positive V2 provenance |
| [PRETRAINED_MODEL_RESEARCH.md](../PRETRAINED_MODEL_RESEARCH.md) | All 17 requested candidate groups; exact artifacts/revisions, task/input/output/preprocessing, licenses, runtime constraints, hardware estimates/unmeasured latency, publication/benchmark limits, disposition and adoption gates |
| [DATASET_AND_FORECAST_FEASIBILITY.md](../DATASET_AND_FORECAST_FEASIBILITY.md) | Seven datasets/resources, real numerical and categorical units, population counts, 30/60/90/91/92 distinctions, source-only/imported/verified separation, missingness/identity/leakage, staged acquisition cost and alternative |
| [RESEARCH_DIRECTION_DECISION.md](../RESEARCH_DIRECTION_DECISION.md) | Requested A/B/C/D plus bounded alternative E and CMR F; split A1/A2, weighted judgments, hard gates, sensitivity, contrary evidence, provisional choice and revisit |
| [OPTIMAL_SYSTEM_ARCHITECTURE.md](../OPTIMAL_SYSTEM_ARCHITECTURE.md) | Modular monolith, diagrams, service ownership, typed schemas/ports/APIs, exact observation selector, source units/chunks, durable jobs/recovery, model isolation, deployment/auth/approval, capability expiry/revocation, data retention and missing-output behavior |
| [END_TO_END_WORKFLOW.md](../END_TO_END_WORKFLOW.md) | All twelve requested stages, success trace, failure/recovery paths, missing models/history, explicit user-facing semantics and end-to-end provenance |
| [FORECASTING_RESEARCH_PLAN.md](../FORECASTING_RESEARCH_PLAN.md) | Targets, calendar/cadence bridge, granularity, observation gating, candidate admission, baselines/features, held-repository/purged rolling folds, metrics/denominators, quantiles, accepted negative results and future acquisition ceiling |
| [MODEL_EVALUATION_PLAN.md](../MODEL_EVALUATION_PLAN.md) | Independent annotation/identity review, modality-specific classification, retrieval judgments, patch safety/correctness/utility endpoints, ranking utility, matched ablations, contamination and reproducibility |
| [IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md) | M0–M9 each contain objective, tasks, reuse/model/data, I/O, dependencies/effort, tests/evaluation, acceptance and fallback; inactive milestones remain explicit rather than silently blocking base product |
| [PROOF_OF_CONCEPT_PLAN.md](../PROOF_OF_CONCEPT_PLAN.md) | P0–P6 inputs/outputs/gates/budgets; existing read-only commands versus conditional existing collector build/train versus future Qwen/forecaster/harness work; no claim that new adapters exist |

## Candidate and dataset completeness

All requested model groups are present: CodeBERT-Tesoro, GraphCodeBERT-Tesoro, UniXCoder-Tesoro, TechDebtClassifier, BEACon-TD; Chronos-2, Chronos-2-small, TimesFM 2.5, TTM R3, Moirai 2.0, Toto; CodeAid, ModernBERT, CodeRankEmbed, CodeReviewer, SonarSweep and Qwen. The model document reorganizes numbering by modality, but exact checkpoint identities are supplied. BEACon is correctly a collection of binary checkpoints rather than an invented single multiclass model. Unverified licenses/labels remain explicit blockers for optional execution, not omitted research.

Seven resources are inventoried: TDD, NPF, forecaster toolbox, Zenodo 6109615, Zenodo 4534110, Tesoro and SATD repayment effort. Toolbox/replication are not counted as extra independent observations. NPF's 91-day all-quality effort is not conflated with maintainability-only exact90. Tesoro functions/comments and repayment change-count proxies are not interpreted as future labor-minute targets. [Public evidence appendix](../digests/public-datasets.md).

## Quantitative and semantic consistency

V2 counts independently confirmed in the earlier review remain intact: 31 projects, 67,550 analysis records, 66,711 project measures, 1,024,614 issues, 839 blank keys; all 66,711 nonblank records join Git revisions; 66,685 profile-populated measures. Candidate date-pair counts remain **5,840 / 5,356 / 5,513 / 5,694** for 30/60/90/91 days. They are explicitly candidate observed-day pairs, not exact UTC endpoints or effective independent sample counts.

The local target mart remains **1,361 exact-date 90-day rows**, **5,371 at 91 days**, **9,249 at 92 days**, summing to **15,981**; raw same-path candidate pairs are separate. Zero/unchanged/positive counts and stale 738-versus-510 profile distinction are preserved. Original V3 submissions remain attempts, not validated measurements, and recovered server results remain unknown. These distinctions avoid the central data distortions identified earlier. [Quantitative audit](../DATASET_AND_FORECAST_FEASIBILITY.md), [independent recount](review-direction-data.md).

Model granularity is coherent: Tesoro normalized eligible Java functions; diff model cleaned added lines; BEACon issue bodies; CodeAid classes/dependencies; CodeReviewer task-specific edit context; CodeRank retrieval vectors; Qwen generation. No classifier annotation becomes authoritative debt minutes. Repository-level V2 forecasting is first; file-level prior results are secondary, and module history cannot be synthesized from project aggregates.

Exact90 consumes a registered daily UTC grid with a measured selected cutoff state; 13 weekly native steps are explicitly 91 days. Missing grid inputs require supported native handling or a separately evaluated past-only sensitivity. Missing/censored endpoints never receive imputed labels. Reusing a measurement is allowed only for a provably unchanged selected source state. Native context/padding never counts as actual history, and model-specific context/horizon fit remains admission-gated. Architecture and protocol now agree on these contracts.

## Fifteen final questions: answer locations and conclusion

| User question | Answer in the package |
|---|---|
|1 What should the product become?|Evidence-grounded Java debt workbench; architecture/product section|
|2 Most defensible research direction?|Provisional bounded evidence/remediation study; V2 repository thesis can win the early revisit and later outcome gates|
|3 Models actually used?|No mandatory learned detector; candidate Qwen, optional CodeRank; conditional small Chronos/full control/TimesFM; TTM only with exact branch/context fit|
|4 Exact model tasks?|Explanation/patch generation, retrieval, optional typed annotations, numerical forecasting; adapter table|
|5 Required model data?|Exact source/finding/context; judged retrieval corpus; modality-specific labels; compatible observed numerical histories; model/evaluation contracts|
|6 User outputs?|Maintainability estimates, separate security/reliability, provenance/candidates/backlog, precise patch checks; only validated scoped forecasts|
|7 Reliable 90-day feasibility now?|Deployed own-module exact90 unsupported; imported repository feasibility remains unproven but plausible|
|8 Integrate forecasters?|Benchmark conditionally; no operational integration before dataset/runtime/value/calibration gates|
|9 Strongest alternative?|Bounded evidence selection, transparent ranking and independently assessed remediation; safe non-ML fallback|
|10 Cost-effective extra history?|Audit existing V2/small Zenodo first; recover original tasks if possible; small compiled pilot before expensive years-long backfill|
|11 Retained modules?|Collector/export evidence, Git/identity/missingness/dataset/evaluation contracts; optional lexical graphs; audit reuse table|
|12 Complete architecture?|Single-host modular monolith, one API/worker, SQLite/artifacts, sandboxed tools/models and explicit trust/publication seams|
|13 Implementation order?|M0/M1/M4 early gate, M2 trusted evidence, optional M3, M5/M6/M7 studies, thin M8 UI, M9 final evaluation|
|14 Experiments proving value?|Registered classifier/retrieval/patch/ranking comparisons and imported forecast baseline study; P0–P6 plus independent review/ablations|
|15 Limits communicated?|Typed evidence/status, null/reasons, partial verification, calibration level, eligibility/coverage, provenance, drift/expiry and stated claim limits|

The provisional recommendation is decisive about **what to build first and what not to promise**, without pretending the final thesis winner can be known before its proposed experiments. This is consistent with the user's explicit permission to choose a stronger alternative while seriously testing forecasting.

## Nonblocking open experiments

Actual host/deadline/reviewer constraints, checkpoint loading/latency/memory, specialist license/mapping resolution, original operator recovery, V2 eligible cutoff/domain series, source-only versus compiled validity, independently judged patch correctness/utility, and measured gains over strong baselines remain open. Each has a bounded gate or disabled/fallback behavior. They block relevant future execution or scientific promotion, **not completion of a design-only deliverable**.

POC recipes and roadmap commands are explicitly future work; the existing training CLI is identified as training and cannot bypass data gates. New adapter CLIs are honestly absent. No new implementation, experiment result, accuracy winner or deployment is claimed. Source preservation and design-only scope remain intact.

## Post-fix resolution — 2026-10-13

Re-read the current feasibility value gate, roadmap planning envelope, direction revisit contract, [README](../README.md) and [requirements traceability](../REQUIREMENTS_TRACEABILITY.md). Original findings above are retained as the review history.

- **P1 interval mismatch resolved:** feasibility now requires common native central **80%** intervals with **75–85%** coverage and useful width. A proposed central **90%** interval requires a separate validation-only calibration layer and separate coverage/width evaluation. This matches the forecast/evaluation/architecture distinction; no conflicting mandatory 90% promotion predicate remains in the reviewed gate.
- **P2 schedule clarification resolved:** roadmap now states **14–40 elapsed weeks** for the 70–119 person-day base plan at 3–5 contributor-days/week. The early one- to two-week checkpoint is explicitly provisional and restricted to an audit refresh, runtime smoke feasibility and small imported-history subset (**4.5–8 person-days**). Full milestones/model comparisons/M7 repair pilot remain later work. Actual elapsed timing still depends on capacity, as documented.
- **README/traceability reconciled:** README provides all fifteen final answers, states current own-module exact90 unsupported, preserves the V2 thesis opportunity and explicitly separates research/design completion from future runtime/implementation gates. Traceability maps every required capability/deliverable and describes the early gate separately from full milestones. No newly achieved scientific or implementation result is asserted.

**Final handoff result: no unresolved design-coverage blocker from this review.** Remaining licensing, live-recovery, data-admission, resource and efficacy gates are future execution/scientific promotion conditions, not missing design deliverables.
