# TRACE
### Technical Debt Intelligence

**Every problem leaves a trace.**

Detect. Predict. Prioritize. Remediate.

## Project Description

TRACE is an AI-powered Technical Debt Intelligence Platform designed to help software engineering teams understand, manage, and reduce technical debt throughout the software development lifecycle.

Unlike conventional static analysis tools that provide isolated snapshots of code quality, TRACE combines repository mining, static analysis, machine learning, natural language processing, and large language models to deliver a comprehensive view of a software system's technical health.

The platform goes beyond identifying existing code quality issues by analyzing software evolution, predicting future debt accumulation, assessing architectural risks, and providing actionable, data-driven remediation recommendations.

TRACE aims to transform technical debt management from a reactive maintenance activity into a proactive, measurable, and intelligent engineering process.

## Integrated MVP

This migration branch integrates the complete `TechDebt360-MVP` implementation and its source history into TRACE. The migration preserves the source repository's existing layout, tests, research evidence, and documentation so the team can review and evolve it without breaking its Python module paths.

See [`docs/TECHDEBT360_MVP_MIGRATION.md`](docs/TECHDEBT360_MVP_MIGRATION.md) for the exact source revision, branch/base details, repository map, and verification notes.

## Project Scope

TRACE covers the technical debt lifecycle through the following capabilities:

- **Technical Debt Detection:** Identify and classify code, design, architecture, and test debt using static analysis and custom detection techniques.
- **Self-Admitted Technical Debt Detection:** Extract and classify technical debt explicitly acknowledged in source code comments using NLP techniques.
- **Repository Mining:** Analyze Git history, commits, pull requests, contributors, and code evolution to understand development patterns and their relationship with technical debt.
- **Technical Debt Prediction:** Apply machine learning to forecast future debt accumulation, maintainability degradation, and file-level risk.
- **Architecture Analysis:** Detect architectural and design smells, dependency issues, and structural weaknesses across software modules.
- **Debt Prioritization:** Rank identified debt items based on severity, change frequency, defect probability, business criticality, remediation effort, and architectural impact.
- **AI-Assisted Remediation:** Generate refactoring recommendations and code improvements using large language models.
- **Remediation Impact Tracking:** Measure changes in code quality, maintainability, and technical debt before and after remediation.
- **Return on Investment Estimation:** Estimate the expected benefits and effort associated with resolving individual debt items.
- **Explainable AI:** Provide transparent explanations of machine learning predictions and prioritization decisions.
- **Analytics and Visualization:** Present technical debt insights, risk assessments, architectural dependencies, and remediation progress through interactive dashboards.

## TechDebt360 MVP: current implementation

The persistence-only flow is implemented. See [run instructions](forecasting_mvp/PERSISTENCE.md)
and the [implementation/verification report](PERSISTENCE_IMPLEMENTATION_REPORT.md).
Use `persistence-build`, `persistence-import`, `persistence-verify` and `persistence-serve`
for the active MVP; older multi-model commands below retain their research-only scope.

For the current MVP direction, use the
[persistence-only workflow](architecture-redesign/2026-10-13-forecasting-mvp/MVP_FORECASTING_PLAN.md)
and [repository index](MVP_REPOSITORY_INDEX.md), updated 2026-10-30.
Chronos-2 and hybrid studies remain archived research; they are not active forecast
stages. The phase entries below retain their historical execution boundaries.

Start with [MODULE_LEVEL_README.md](MODULE_LEVEL_README.md) for the corrected missing-value,
evidence, calendar, output and compatibility contracts.

- [REPAIR_REPORT.md](REPAIR_REPORT.md): repair coverage and validation limits.
- [CHANGES.md](CHANGES.md): current repair and historical changelog.
- [TESTED_ENVIRONMENT.txt](TESTED_ENVIRONMENT.txt): tested dependencies.
- `tests/`: offline regression and end-to-end checks.
- [FORECASTING.md](FORECASTING.md): additive 90/91-day forecasting datasets,
  historical graphs, and reproducible M0–M2 evaluation commands.
- [M3_M4_DESIGN.md](M3_M4_DESIGN.md): causal TCN and GraphSAGE–TCN data interfaces.
- [MILESTONE1_REPORT.md](MILESTONE1_REPORT.md): implementation evidence and remaining gates.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Missing values remain missing. Offline software PASS is not scientific approval or permission
to rescan, train, or execute the separate TechDebt360 V3 experiment.

## MVP phase status

Phase 0 verification, Phase 1 ingestion and Phase 2 exact-target construction are available in
[`forecasting_mvp/`](forecasting_mvp/README.md). See
[`PHASE_2_IMPLEMENTATION_REPORT.md`](PHASE_2_IMPLEMENTATION_REPORT.md) for dataset
statistics, limitations and test evidence.
[`GITHUB_SYNC.md`](GITHUB_SYNC.md) documents the central repository and safe sync.

Phase 2.1 adds raw-SQL validation, independence diagnostics and a strict past-only
input boundary. See [PHASE_2_1_VALIDATION_REPORT.md](PHASE_2_1_VALIDATION_REPORT.md)
and [small evidence files](examples/phase2_1/README.md). The Phase 2 dataset and
splits remain frozen.

Phase 3 statistical baselines have been implemented and evaluated on those
frozen cohorts. See [PHASE_3_IMPLEMENTATION_REPORT.md](PHASE_3_IMPLEMENTATION_REPORT.md)
and [results](examples/phase3/README.md). Persistence, rolling mean and linear trend
are available through the offline `run-baselines` command. Full pretrained
benchmarks, CatBoost and dashboards remain outside this implementation.

Phase 4.1 now admits a separate CPU Chronos-2 Small runtime and a six-context
training/validation smoke test. See [PHASE_4_1_IMPLEMENTATION_REPORT.md](PHASE_4_1_IMPLEMENTATION_REPORT.md)
and [smoke evidence](examples/phase4_1/README.md). Phase 4.1 stopped at that
boundary; its separately authorized evaluation follows below.

Phase 4.2 evaluates the pinned Chronos model against the original baselines on
the unchanged validation, temporal-test and held-repository cohorts. See
[PHASE_4_2_IMPLEMENTATION_REPORT.md](PHASE_4_2_IMPLEMENTATION_REPORT.md) and
[comparison evidence](examples/phase4_2/README.md) for coverage, failure handling,
point/interval metrics and limitations. Later phases remain unauthorized.

Phase 4.2.1 hardens typed inference recovery and audits only the 12 previously
failed contexts. The original experiment remains frozen. See the
[diagnostic report](PHASE_4_2_1_DIAGNOSTIC_REPORT.md) and
[diagnostic evidence](examples/phase4_2_1/README.md). No benchmark was rerun.

Phase 5.1 adds an isolated [schema-v2 data foundation](forecasting_multilanguage/README.md): read-only source adapters, F0/F1 features, exact target-status construction and a strict past-only input boundary. [Implementation/data-readiness report](PHASE_5_1_IMPLEMENTATION_REPORT.md). F2 and the real non-Java pilot remain blocked; no training, inference or scans were run. Earlier experiments stay frozen.

Phase 5.2 pins three real development sources and their historical code states.
See the [preflight report](PHASE_5_2_PREFLIGHT_REPORT.md),
[candidate decision](REAL_PILOT_REPOSITORY_CANDIDATES.md),
[future collection plan](HISTORICAL_SCAN_EXECUTION_PLAN.md) and
[small metadata evidence](examples/phase5_2/README.md).
Collection remains blocked by explicit scope, live-domain, build/runtime and
resource gates. The new `forecasting_multilanguage.preflight` command only
inspects Git source metadata; it cannot run a build, scanner or model.

## Repository map

- `forecasting_mvp/` — active persistence MVP and serving flow.
- `forecasting_multilanguage/` — multi-language ingestion and readiness contracts.
- `forecasting/` and `forecasting_research/` — forecasting foundations and archived studies.
- `tests/` — regression, integration, and validation tests.
- `examples/` — reproducible evidence and phase artifacts.
- `architecture-redesign/` — architecture plans and design decisions.
- `research/` — research inputs and experiment records.
- `tools/` — build, recovery, inspection, and verification utilities.
- `.github/` — TRACE repository governance files retained from the destination branch.
