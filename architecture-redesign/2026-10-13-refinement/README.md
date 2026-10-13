# TechDebt360 pretrained-AI architecture refinement

Date: 2026-10-13. **Recommendation: a capability-aware pretrained hybrid platform. Forecasting and detection/remediation are core research tracks; the primary thesis is selected after paired experiments.** This revision replaces the earlier remediation-first preference without asserting a forecasting or repair winner.

| Document | Contents |
|---|---|
|[REVISED_ARCHITECTURE.md](REVISED_ARCHITECTURE.md)|Integrated workflow, model roles, typed contracts, APIs, ranking, verification, storage and deployment|
|[PRETRAINED_MODEL_STRATEGY.md](PRETRAINED_MODEL_STRATEGY.md)|Fresh checks of all 11 requested models, exact revisions, task/license/resource limits and smallest complementary stack|
|[FORECASTING_FEASIBILITY.md](FORECASTING_FEASIBILITY.md)|Fresh historical audit, 30/60/90-day readiness, as-of endpoint corrections, short-context TTM and acquisition/fallback|
|[RESEARCH_EXPERIMENTS.md](RESEARCH_EXPERIMENTS.md)|Experiment A and B, preregistration, baselines, metrics, independent review, gates and future commands|
|[REVISED_IMPLEMENTATION_ROADMAP.md](REVISED_IMPLEMENTATION_ROADMAP.md)|Dependencies, existing-code reuse, 38–64 contributor-day scenario, acceptance/stop rules and separate reviewer cost|

Start with the revised architecture and experiments. The short [BMAD spine](2026-10-13-refinement.md) fixes shared invariants. [Verification and review resolution](VERIFICATION.md) records design checks and remaining experimental unknowns. Fresh source evidence is in [model digest](digests/model-reverification.md) and [data digest](digests/data-reaudit.md).

Key corrections: TTM R3 has genuine short-context branches; exact-date pair counts do not bound all as-of forecast labels; V2 timestamps/revisions match to the second but selected unmeasured states still need censoring/backfill; metadata profile segments are not automatically rule changes. Learned-only repairs have engineering checks plus independent outcome reviews and cannot invent Sonar finding removal.

Provisional successful active roles: one GraphCodeBERT/CodeBERT category winner, CodeRankEmbed retrieval if useful, Qwen7B generation and a validated numerical model if adequate histories and measured value exist. Comparators are research controls. Unknown licensing/data/load prerequisites are not “poor accuracy.” Published benchmarks are not local results. User-visible model candidates, measured minutes, forecasts and verified outcomes remain distinct.

No production code, previous design file, package, configuration or database was changed. No inference, training, tests, builds, scans or POC experiments were run. Future runtime/harness commands in the experiment plan are explicitly future-only; the new research harness does not exist today. The prior design package/ZIP remains unchanged. No automatic implementation follows.
