# Research direction decision

Date: 2026-10-13. **Provisionally select a bounded evidence and verified-remediation workbench as the primary product direction. Run an imported repository-level forecasting feasibility study as an early, conditional research branch.** Do not make exact 90-day module forecasts the graduation promise today. This is a design recommendation under uncertainty, not a finding that remediation models outperform forecasters.

## Why the direction changes

The current module pipeline has no discovered verified real dataset. Old file-level continuous results failed persistence/zero-change baselines; horizons mix 90/91/92 days. NPF labels depend on uncompleted human identity and compiled-domain audits. The CMR replacement has rare events and zero human-validated edges; current TD did not add consistent value over process features. [Local audit](CURRENT_SYSTEM_AUDIT.md) and [feasibility](DATASET_AND_FORECAST_FEASIBILITY.md) give counts and exact artifact links.

Conversely, public V2 has real, extensive numerical histories. Independent read-only review confirmed 66,711 nonblank analysis records join Git revisions, with analysis dates matching both author/committer days, and 66,685 measure rows populated with profile metadata. This is affirmative evidence for a bounded imported-domain forecasting experiment. It does not certify module labels, exact UTC endpoints or stable measurement semantics. Do not discard it because a fresh module corpus is unavailable. See [independent data review](reviews/review-direction-data.md).

The listed pretrained specialists solve different tasks and have substantial semantic, licensing or validation gaps. There is no basis for stacking them all into a stronger debt model. A small generator can be assessed with direct before/after outcomes, but those outcomes also need adequate tests and independent review.

## Selection matrix

Scores 1–5 are architectural judgments of feasibility/fit under the observed constraints. They are **not measured expected model accuracy**. Weights total 100; hard gates below override weighted scores. Validity and ground truth dominate because a graduation project needs defensible evidence. Developer value, reproducibility and scope favor a small useful system. Performance evidence is deliberately low where no local results exist.

| Criterion | Weight | A1 own-module forecasting | A2 imported repo forecast study | B prevention prediction | C broad detection/remediation | D unrestricted hybrid | E bounded evidence/remediation | F CMR risk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|Scientific validity|18|2|4|3|3|3|4|3|
|Ground-truth availability|16|2|4|2|3|3|4|3|
|Developer value|12|4|3|4|4|5|4|3|
|Reproducible evaluation|10|2|4|3|3|3|4|4|
|Pretrained applicability|8|4|4|3|4|4|4|2|
|Performance evidence|8|2|2|2|3|3|3|3|
|Defensible contribution|8|4|3|3|3|4|3|3|
|Hardware feasibility|5|3|4|4|2|2|4|5|
|Implementation simplicity|5|2|4|3|2|1|4|4|
|Reuse|5|5|4|4|4|4|5|5|
|Graduation scope|5|2|4|3|2|1|4|3|
|Weighted total /5|100|2.76|3.64|2.98|3.10|3.20|3.89|3.27|

Formula: `sum(weight × score)/100`; scores and weights are editable judgments. A1 refers to promising a fresh own-module platform, A2 to a narrower imported-domain scientific study. C includes the broader learned architectural smell/detection stack requested as a candidate; E intentionally bounds that scope. D's value is high but its validation and integration burden is too large.

Hard gates: observed legitimate ground truth; no synthetic predictive claims; task-compatible models; resolved execution licenses; no uncalibrated displayed probability; matched temporal/repository evaluation; reproducible measurement domain; no main-branch automated remediation. A1 presently fails history gates. B/F fail label-quality promotion gates. C/D fail minimal-model and scope gates. E still needs scan/runtime/tests/reviewer gates. A2 needs domain/clock/cadence audit and actual baseline comparison.

### Sensitivity and runner-up

The top gap E versus A2 is only 0.25. If E's validity and ground-truth scores each fall by one point after the patch/test pilot, it loses 0.34 and A2 wins. If no GPU or trustworthy test harness is available, A2 can become the primary thesis. If the bounded V2 audit yields adequate stable series and forecasters beat persistence with grouped uncertainty, prefer a forecasting thesis rather than force the pivot. If neither ML branch passes, ship an evidence/prioritization demonstration and an honest negative-results evaluation; do not claim successful AI repair or accurate predictions.

## What TechDebt360 should become

Primary scope: Java production sources, compiled static analysis, source/issue provenance, file/module inventory, transparent maintainability backlog, optional source-grounded explanation, bounded patch candidates and precise verification outcomes. Preserve reliability/security separately. Support imported public histories as a research namespace. Forecasts are repository/domain-specific capabilities, enabled only after accuracy/calibration gates. Module forecasting needs actual own module history; public project aggregates cannot fill that gap.

The minimal learned stack is Qwen2.5-Coder-7B-Instruct as a **candidate** explanation/patch generator; CodeRankEmbed only if retrieval adds measurable value. A licensed, verified Tesoro classifier may later annotate debt types for eligible Java functions; it does not declare the rest of a repository debt-free. Chronos-2-small/full and TimesFM 2.5 are conditional forecast benchmarks, with TTM-r3 where its exact revision and context fit. No model wins production selection from a model card.

## Academic contribution and questions

The system composition is not itself novel. [InferFix, ESEC/FSE 2023](https://doi.org/10.1145/3611643.3613892) provides a static-analysis/LLM repair precedent. [DLRepay](https://www.sciencedirect.com/science/article/pii/S0950584923002318) addresses SATD repayment; its labels/task differ from verified Sonar maintainability. See the independent review for exact accessible source corrections. These precedents invalidate a claim that combining analysis, retrieval and LLMs is a new invention.

Proposed narrower contribution: a reproducible evaluation of **provenance-bound evidence selection, abstention and verification** on Java maintainability candidates, with contamination controls, matched baselines, per-rule/per-project negative results and measured runtime. Thesis title candidate: “Evidence-Grounded Technical Debt Assessment and Verified Remediation in Java Repositories.” Do not promise all technical debt, actual repayment labor or causal business benefit.

Research questions:

1. Does semantic retrieval improve relevant evidence and independently verified patch success over lexical/symbol context under the same generator/token budget?
2. Do type annotations improve blinded developer assessment or useful localization beyond static findings without excessive false positives?
3. How often do analyzer-reduced candidates fail tests, differential checks, suppression checks or human review?
4. Does transparent ranking improve fixed-budget reviewer utility over severity-only and burden-only orderings?
5. On eligible imported repository histories, do small foundation forecasters improve future remediation estimates over persistence and tabular controls under identical horizons/cohorts?

No positive answer is assumed. A2 can supply an academically useful negative forecasting result, but precision and artifact lineage must be adequate to interpret it.

## Main objections and responses

**Forecasting data exists.** Agreed: V2 and Zenodo warrant early inspection and benchmarking. The rejection concerns an unsupported deployed own-module exact 90-day promise, not a lack of all numerical data.

**Remediation validation is difficult and saturated.** Agreed: compilation/tests are incomplete behavioral evidence. Restrict rule families, forbid suppression/deletion, use blinded review and compare strong deterministic/static/generator baselines. Novelty must come from the evaluation and specific evidence policy, not model count. If these gates fail, reduce the claim or let A2 become primary.

**A platform could still be too large.** The base workflow must run with no GPU, no history and no learned detectors. Postpone neural graphs, full issue-text suite, SonarSweep, CodeAid, autonomous merge, multi-tenancy infrastructure and distributed services. API/UI renders already validated outputs; it must not become the research critical path.

## Decision and revisit contract

Approve the **design recommendation**, not implementation or achieved ML performance. In a later authorized early feasibility study, audit a small V2 clock/domain/series subset and assess runtime/scan/patch harness availability. A one- to two-week checkpoint is provisional and limited; full model comparison and the M7 repair pilot occur later under their roadmap estimates. Select primary thesis at that gate: E if direct outcome validation is feasible and the bounded generator hypothesis survives; A2 if existing histories are strong and repair infrastructure is unsuitable; neither if prerequisites fail. Preserve interfaces so this switch changes the evaluation target and model adapter, not evidence semantics.

The full operational architecture remains useful in all three outcomes. The [roadmap](IMPLEMENTATION_ROADMAP.md) has explicit branch acceptance and stop conditions; the [POC plan](PROOF_OF_CONCEPT_PLAN.md) lists only future experiments. No implementation permission or model claim is inferred from this document.
