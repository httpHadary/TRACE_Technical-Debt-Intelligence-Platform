# Model evaluation and scientific validation

Date: 2026-10-13. Proposed protocol. No evaluation was executed in this task. All thresholds below are project choices to preregister, not universal scientific rules. The primary direction remains a testable bet; negative results are acceptable research outcomes.

## Claims, populations and independence

Evaluate five distinct capabilities: measured finding integrity, optional classification, retrieval, assisted remediation, and conditional forecasting. Do not average them into platform “accuracy.” The authoritative debt construct is the analyzer's maintainability remediation estimate. It does not measure all debt, actual labor, causality, business cost or functional correctness.

Use three data namespaces:

- **Software fixtures:** contract/failure-path verification only, excluded from predictive metrics.
- **Imported research:** licensed V2/Zenodo/Tesoro resources, documented historical domains and potential public pretraining contamination.
- **Own repository study:** frozen Java repositories/commits, source scope, compiled domain, identity policy and independent review. Existing source-only/NPF outcomes remain prior evidence, not an untouched test.

Freeze repository registry, target contracts, candidate selection, split manifests, metrics, budgets and stop rules before outcome inspection. For classification, group by repository and near-duplicate function/comment lineage. For patches, group related findings and identical base context; split by repository/rule as feasible. For temporal prediction, purge crossing label intervals and hold out repositories. Old NPF sealed repositories remain unopened unless a separately authorized study explicitly unlocks them after choices freeze.

Public foundation-model pretraining overlap is generally unverifiable. Record checkpoint training cutoffs when documented, exclude retrieved target fixes and future source, use fresh/unpublished held-out examples when obtainable, and disclose residual contamination. Do not claim a benchmark is uncontaminated solely because local training was not run.

## Ground-truth integrity study

Take a stratified independent sample of own findings and identity matches across rule, severity, no-line, rename/move, duplicate fingerprints, high-impact and disagreement strata. Preserve sampling probabilities. Two independent reviewers label evidence before seeing model scores; adjudicate disagreements with a third reviewer. Report agreement, Cohen's kappa where meaningful, positive/negative precision/recall, unresolved fraction and per-stratum results. Do not infer population error from the intentionally oversampled 200-case NPF set without weighting or a representative sample.

Compiled/source comparison must match exact source inventory and frozen rules; report coverage, finding overlap, minutes, rule families and identity errors by repository/build type. The historical three-pair Maven sample cannot validate a broader compiled/source claim. Prefer compiled primary evidence; source-only remains a labeled sensitivity domain. Any representation disagreement remains explicit in downstream study data.

## Classification experiment

Evaluate at most one shortlisted specialist per modality after license/label/preprocessing checks. Tesoro code models use four independent debt-type indicators on eligible normalized Java functions. A zero vector is not established debt absence. Include manually adjudicated clean and out-of-domain functions, not just SATD-derived positive examples. TechDebtClassifier inputs cleaned added diff lines; BEACon inputs issue text. No head-to-head table compares unrelated tasks as if they had common labels.

Baselines: majority/prevalence, transparent keyword rules where appropriate, static-only finding evidence; code-family comparison on identical eligible units. Metrics: per-label and macro/micro precision, recall, F1, PR-AUC/AP, ROC-AUC where both classes exist, specificity/false-positive rate, calibration plots/Brier/ECE for probability claims, and eligibility/abstention coverage. For multicategory binary outputs use independent sigmoid thresholds; no softmax normalization across Tesoro types. Tune thresholds only on validation. Calibration is a separate fitted artifact.

Initial study size is constrained by positive class counts and reviewer effort. Reserve at least five repository domains where possible and enough positive/negative examples per reported category for interval precision; estimate that precision from development data before a claim. A suggested pilot is 300 independently reviewed functions/diffs across at least five repositories, with class counts reported. It establishes feasibility, not universal deployment power. Proposed annotation promotion: precision lower confidence bound at least 0.80 at the selected threshold and acceptable recall under the intended review budget; otherwise keep experimental annotations hidden from normal backlog ranking. This target may be impossible for a rare type; abstain or reduce the claim instead of pooling it away.

## Retrieval experiment

Construct at least 50 blinded queries from held-out findings, spanning source localization, supporting dependency context, similar prior changes and rule guidance. Two reviewers judge candidate chunks for relevance/usefulness with a frozen 0–2 rubric. Gold relevance is independent of the embedding score and generator output. Exclude the actual held-out target patch or later commit from the index.

Compare symbol/path search, lexical BM25-style search and CodeRankEmbed using identical snapshot/access filters, chunk corpus and k = 1/5/10. Record Recall@K, MRR and nDCG@K, judged coverage, source-citation precision, p50/p95 latency and peak RAM. Query prefix, pooling and chunk boundaries follow the exact checkpoint contract. Useful evidence need not be semantically similar; dependency/rule context remains a deterministic retrieval source.

Proposed admission: at least 10% relative Recall@5 improvement, no material loss in source-citation precision, acceptable measured latency, and evidence of better patch outcomes under the same generator/token budget. If embedding retrieval fails to improve the downstream result, use lexical/symbol retrieval. No vector database is required for this pilot.

## Remediation outcome study

The evaluated unit is one eligible finding or tightly related finding cluster at an immutable base commit. Select a reproducible prospective sample before generation. Restrict an initial cohort to three to five rule families with small, reviewable edits, preserved public APIs and available compile/test harnesses. Avoid broad architectural rewrites and projects without meaningful test evidence. Record exclusions rather than cherry-pick only successful candidates.

Suggested feasibility pilot: 30 candidates across at least five repositories. Final study: approximately 100 eligible units across at least eight repositories, revised by development-only precision assessment. These are workload estimates; report effective clusters and do not treat repeated variants of one finding as independent examples.

Compare, under fixed budgets:

1. Static rule guidance and available deterministic quick fixes.
2. Qwen with finding + local symbol context.
3. Qwen with lexical retrieval.
4. Qwen with CodeRankEmbed retrieval, only after retrieval admission.
5. Optional type annotations added to the best evidence policy, only after classification admission.

Retrieval/evidence ablations use the same checkpoint, generation settings, context token budget, eligible units and at most three candidates per unit. A separately registered newer-generator comparison may test one fitting challenger (for example Qwen3.5-9B) under the same total budget; it must not confound the retrieval ablation. Keep one final generator selected by verified outcomes. Report pass@1 as primary and bounded any-of-three success separately. A validation-retry loop is an explicit additional variant; equalize its total tokens/candidates and compute. Do not let one model have unlimited retries or manual repair.

Verification has several separate endpoints:

| Endpoint | Measurement | Permitted claim |
|---|---|---|
|Patch validity|parse/apply, allowed paths, base/tree binding|Candidate is syntactically applicable|
|Compilation|baseline and candidate compile results, exit codes/logs|Candidate compiles in recorded environment|
|Tests|baseline/candidate same full policy; counts, failures, skipped/timeouts|No observed regression in those tests|
|Differential checks|selected behavior/API/invariant tests with recorded coverage|No observed regression in those checks|
|Analyzer change|compatible before/after findings, minutes, new problems|Measured issue changed under one domain|
|Suppression/scope checks|annotation/config/exclusion/deletion diffs|Finding did not disappear solely by hiding code/rules|
|Blinded correctness|two reviewers, model identity hidden, behavioral/maintainability rubric|Independent reviewer assessment; still not formal equivalence|
|Utility/acceptance|developer decision with rationale, review time if timed|Observed usefulness in this sample; not general labor savings|

`EVIDENCE_VERIFIED` requires baseline and candidate compilation, mandatory tests and differential checks passing, targeted finding resolved with identity support, no new prohibited findings, no suppression/deletion trick and complete provenance. Missing tests, baseline failure, unresolved identity, timeout or partial analyzer coverage yield `PARTIALLY_VERIFIED`; a confirmed regression yields `FAILED`. This label is evidence under a bounded policy, not proof of all behavior. Human approval is separate from the scientific label.

Primary comparative outcome: proportion of all eligible units yielding an independently accepted, evidence-verified pass@1 patch. Report pipeline pass rates and denominator at every stage, analyzer-only reductions, regressions, abstentions, uncertainty and runtime separately. Blind reviewers to model arm; adjudicate disagreements. Use paired repository-cluster bootstrap/permutation for variant comparisons, repository/rule sensitivity and Wilson intervals as descriptive unit-level results. Few clusters limit inference; do not substitute naive row p-values.

Proposed continuation gate after the 30-unit pilot: at least half the units support complete baseline/verification evidence; no systematic unsafe acceptance; generation produces enough assessable candidates for a comparative final study. Proposed useful effect gate: at least 10 percentage points improvement in independent accepted verified pass@1 over the strongest simpler baseline, with paired clustered CI above zero. If power is too low, report an exploratory effect and stop the deployment/novelty claim. Zero confirmed regressions among accepted candidates is necessary but not proof that future regressions are impossible.

## Prioritization utility

Ranking ground truth is not inferred from debt minutes. Run blinded fixed-budget comparisons of severity-only, remediation-burden-only, trailing-churn-only and the published factor policy. At least five developers/technical leads review matched queues from multiple repositories and identify useful/actionable findings under a fixed time or top-K budget. Counterbalance order; record knowledge of the repository. Outcomes: relevant/actionable items found, reviewer agreement, effort spent reviewing, reasons for rejection and uncertainty. User criticality remains a preference, not a causal label.

If the combined ranking does not improve utility, preserve simple filterable factors rather than claim an optimal learned priority. Do not fit a learning-to-rank model without sufficient independent judgments and a held-out utility study.

## Forecasting and regression

Use the [conditional forecasting protocol](FORECASTING_RESEARCH_PLAN.md) for exact target/cadence contracts, baselines, rolling/held-repository splits, common 80% intervals and promotion gates. Report 30/60/90/91 horizons separately, repository macro/pool metrics, nonzero-baseline denominators, failures and changing/constant target subsets. Naive performance is a first-class result. No interpolation creates a test label; input treatment is a separately reported sensitivity.

## Required ablations and interpretation

| Comparison | Question answered | Claim limit |
|---|---|---|
|Static only vs specialist annotation|Does the classifier add useful localization/types?|No remediation or forecast accuracy inferred|
|Git/size only vs current TD vs trailing TD|Does debt evidence add prediction signal?|No causal debt-interest claim|
|Local context vs lexical vs embedding retrieval|Does retrieval add evidence and verified repair value?|No new debt ground truth from similarity|
|Generation vs generation + independent verification|How many plausible outputs fail real checks?|Verification is not a generation accuracy improvement|
|Simple rank factors vs combined policy|Does the backlog help a fixed-budget reviewer?|No universal business priority|
|Persistence/tabular vs zero-shot forecast|Does a model add numerical future value?|Domain-specific numerical result only|
|History only vs graph features|Do graph features add beyond cheap evidence?|Lexical graph coverage must be reported|

Do not require an ablation for an inactive subsystem. If no forecast dataset passes the gate, record `NOT_EVALUABLE_DATA` with reasons; do not synthesize its performance. Choose primary/secondary hypotheses before analysis and control multiple-comparison claims with a limited declared comparison family; report exploratory comparisons as such.

## Reproducibility and monitoring

Each run archives repository URLs/licenses and immutable commits; source/analysis/domain/identity/target hashes; complete raw export manifests; model/runtime/preprocessing/quantization revisions; input/output IDs; seeds and budgets; split and calibration manifests; metrics with units/denominators; error/abstention logs; annotation rubrics and adjudication; candidate diffs and exact test/analyzer artifacts; wall time/peak memory/hardware description. Redact credentials and personal identifiers. Redistributable artifacts follow their own source/data/model licenses.

Report model-card comparisons as publisher evidence, local software results as contract validation and held-out study outcomes as scientific evidence. New analyzer/model/target/code versions invalidate affected capability grants. Monitor coverage, calibration, runtime and rejection rates; trigger a new frozen evaluation rather than automatic retraining. Final thesis includes negative results, unresolved constructs, contamination risks and dataset-specific generalization limits.
