# TechDebt360 — forecasting MVP plan

2026-10-13. Planning only. This package narrows the previous design to a local, repository-first forecasting MVP for two contributors at 10 hours/week each. Forecasting and pretrained AI remain central; real datasets and evaluation precede the dashboard.

Complete-context `core90` is audited first. A failing data-only cohort gate activates the preregistered `masked90` fallback before model outcomes, preserving known origins and exact observed future labels. The primary track is frozen and reported explicitly; TTM complete-context comparisons remain separate.

| Document | Purpose |
|---|---|
| [MVP_EXECUTIVE_SUMMARY.md](MVP_EXECUTIVE_SUMMARY.md) | Implementation order, estimate and conditions |
| [MVP_SCOPE.md](MVP_SCOPE.md) | Mandatory/excluded capabilities, evidence and success gates |
| [MVP_ARCHITECTURE.md](MVP_ARCHITECTURE.md) | Simplified components, contracts, APIs, diagrams and essential controls |
| [MVP_FORECASTING_PLAN.md](MVP_FORECASTING_PLAN.md) | Datasets, exact targets, model/cohort/split policies, metrics and acquisition ladder |
| [MVP_IMPLEMENTATION_ROADMAP.md](MVP_IMPLEMENTATION_ROADMAP.md) | M0–M6 tasks, files, dependencies, effort, tests and fallbacks |
| [MVP_EXPERIMENT_PLAN.md](MVP_EXPERIMENT_PLAN.md) | Future reproducible commands and real-result reporting protocol |

Evidence: [existing-code reuse](digests/code-reuse.md), [prior-plan reconciliation](digests/prior-plan-reconciliation.md), [fresh model/data verification](digests/research-check.md). [Verification](VERIFICATION.md) records document checks; [source preservation](SOURCE_PRESERVATION.md) records unchanged captured originals.

This is a new output package; previous designs and ZIPs remain unchanged. Future commands/package names describe software to implement after authorization. They are not existing implementations or achieved results.
