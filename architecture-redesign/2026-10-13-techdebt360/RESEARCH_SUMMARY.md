---
type: technical-and-academic-selection
topic: TechDebt360 evidence models and forecasting
decision: bounded evidence/remediation product with early imported forecast gate
source: primary public sources plus separately identified local audit
status: complete
verified_claims: 14
unverified_claims: 2
created: 2026-10-13
updated: 2026-10-13
---

# Research summary

Recommend an evidence-grounded Java debt workbench with a bounded, independently evaluated remediation study. Reliable own-module exact90 forecasting is unsupported today. Preserve an early repository-level forecasting study on the existing V2 corpus; it can replace the primary thesis if its data/value gates pass and patch validation proves impractical. This is a recommended study/design choice, not a measured superiority result. Local facts are documented in [audit](CURRENT_SYSTEM_AUDIT.md) and independently challenged in [reviews](reviews/review-direction-data.md).

## Decision-relevant findings

1. Numerical forecasting resources exist. V2 supplies long project histories and warns specifically about V1 timelines; Zenodo 4534110 supplies weekly and irregular numerical series. Neither certifies an operational exact90 module target. [1] [2]
2. NPFDataSet's `TD_3m` means 13 weeks/91 days and mixes active quality-effort components; license/provenance remain unresolved. Its size does not automatically establish independent usable samples. [3]
3. Tesoro's checkpoints have four multi-label debt-type outputs and function-specific preprocessing, without an explicit no-debt label. Upstream schema supports type semantics but unresolved weight licensing and project-held-out validity keep them optional. [4]
4. Chronos 2 small/full, TimesFM 2.5, TTM-r3, Moirai 2.0 and Toto 1.0 expose downloadable artifacts. They forecast supplied numerical series; this run found no evidence that their pretrained success transfers to these technical-debt targets. TTM has revision-specific context/horizon; Moirai weights are noncommercial. [5]
5. Qwen 7B provides instruction-based code generation, not debt detection or calibrated effort. CodeRankEmbed supplies code retrieval, not proof of debt or duplication. Their minimal conditional roles are justified by task fit and resource estimates, not demonstrated local accuracy. [6] [7]
6. Java static analysis needs compatible compiled context. SonarSource describes limits on reconstructing historical issue inventories. [8] The separate local collector audit establishes the CE/revision/export checks; the recommendation to archive exact outputs immediately is a design inference, not a claim that the transfer notes prove CE binding.
7. Static analysis plus retrieval/generation and SATD repayment have established precedents. Novelty cannot rest on combining those components. Narrow the contribution to provenance/abstention/verification policies and a falsifiable comparative study. [9] [10]

## Cross-dimension implications

Task compatibility, ground truth and input clocks constrain the architecture more than model count. Debt-type predictions, issue-text classifications, estimated remediation minutes, future numerical predictions and verified patch outcomes remain different typed evidence. Imported project measures offer a cheaper forecasting feasibility path than rebuilding years of module scans. A small useful measurement/ranking workflow remains viable even if all learned hypotheses fail.

Model cards/configs establish public artifacts and declared task contracts. They do not independently corroborate runtime correctness, latency, calibration or cross-project predictive performance. This research therefore selects **candidates and gates**, not production accuracy winners. Licenses and unverified label semantics are explicit blockers for optional execution, without blocking the base evidence path.

## Contrary evidence and uncertainty

The strongest counterargument to the pivot is that substantial numerical data already exists while remediation outcomes also need difficult validation. Independent V2 recount strengthens repository-level feasibility; the prior file-density failure cannot prove all forecasting methods fail. The decision allows an early thesis switch. Related-work precedents challenge broad novelty; final claims must identify a specific evaluated difference. No independent production benchmark for the exact requested checkpoint combination was established.

Open questions: original operator recovery state; exact eligible V2 cutoff series and complete historical domains; real host/GPU/runtime bounds; checkpoint licenses for several classifiers; availability of meaningful baseline tests and independent reviewers; model contribution over strongest simple baselines. Each has a bounded experiment or explicit disabled-capability route in the roadmap.

## Source appendix

Every source accessed 2026-10-13. Living documents are marked undated rather than assigned invented publication dates. Confidence applies to the named contract/artifact fact, not downstream accuracy. Multiple pages from one publisher are not independent efficacy corroboration. Detailed asset-level evidence resides in the three source digests.

| Ref | Supports | Publisher and source | Published/updated | Confidence |
|---|---|---|---|---|
|[1]|V2 resource/version/license and V1 warning|[TDD maintainers](https://github.com/clowee/The-Technical-Debt-Dataset)|V2.0.1 release 2021-11-04; living README undated|Medium, publisher contract; local DB independently recounted|
|[2]|Real numerical series/cadence/assets/license|[Tsoukalas et al., Zenodo 4534110](https://zenodo.org/records/4534110)|2020-08-08|Medium, metadata and bounded CSV inspected|
|[3]|NPF target semantics and stated limits|[MaramAllah, Hugging Face](https://huggingface.co/datasets/MaramAllah/NPFDataSet)|Uploaded 2026-09-15|Medium for card; unverified coverage/ground truth|
|[4]|Multi-label checkpoint/type/preprocessing|[NamCyan config](https://huggingface.co/NamCyan/codebert-base-technical-debt-code-tesoro/blob/main/config.json), [upstream Tesoro](https://github.com/NamCyan/tesoro)|Repos created 2024-10-26; living config|Medium, artifact contract; efficacy unverified|
|[5]|Forecast checkpoint availability/contracts|[Amazon](https://huggingface.co/amazon/chronos-2), [AutoGluon](https://huggingface.co/autogluon/chronos-2-small), [Google](https://huggingface.co/google/timesfm-2.5-200m-pytorch), [IBM](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r3), [Salesforce](https://huggingface.co/Salesforce/moirai-2.0-R-small), [Datadog](https://huggingface.co/Datadog/Toto-Open-Base-1.0)|Exact revisions/update dates in digest|Medium, metadata/source inspected; runtime/transfer unverified|
|[6]|Qwen generation/license/template/context|[Qwen card](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)|Last modified 2025-01-12|Medium, primary artifact contract|
|[7]|Retrieval/prefix/pooling/license|[Nomic card](https://huggingface.co/nomic-ai/CodeRankEmbed)|Last modified 2025-06-24|Medium, primary artifact contract|
|[8]|Java binaries and historical issue constraints|[Sonar Java docs](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/languages/java), [Sonar transfer notes](https://github.com/SonarSource/sonar-migration-tool/blob/main/docs/TRANSFER.md)|Living docs undated|Medium, primary contract; local collector corroborates design response|
|[9]|Existing repair precedent|[ACM InferFix](https://doi.org/10.1145/3611643.3613892)|2023-11-30|High for publication existence; not independent TechDebt360 efficacy|
|[10]|Existing SATD repayment precedent|[Elsevier DLRepay](https://www.sciencedirect.com/science/article/pii/S0950584923002318)|March 2024|High for publication existence; different task/domain|

## Staleness map

The standalone BMAD `recon_kit.py staleness` helper computes freshness dates from recorded publication or retrieval-review dates. For living checkpoint/library compatibility claims whose public configuration was re-inspected this run, review anchor is 2026-10-13, explicitly not a publication date. Recheck by 2026-11-13 (1 month). Recheck AI landscape/admission choices by 2027-01-13 (3 months). Static versioned datasets/publications retain fixed provenance, but access/license and metadata should be rechecked before execution. Local mutable workspace facts must be rechecked at the next work session, regardless of calendar window. Generated helper output is recorded in [verification](DELIVERABLE_VERIFICATION.md).

The fastest-aging items are package compatibility, licensing, remote-code/default revision and model API behavior. They are research-gated before future execution; no stale document authorizes installation or implementation.
