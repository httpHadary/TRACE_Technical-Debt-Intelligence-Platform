# TechDebt360 persistence-only MVP plan

Implementation update — 2026-10-30: the persistence input/evidence pipeline,
sealed bundles, evaluator and read-only API/dashboard are implemented in
`forecasting_mvp/persistence_flow.py`, `api.py` and `static/`. See the
[implementation report](../../PERSISTENCE_IMPLEMENTATION_REPORT.md) and
[exact operator commands/schemas](../../forecasting_mvp/PERSISTENCE.md).
A new real current-repository scan/demo and calendar data/evaluation admission
remain separate gates. Earlier future-tense statements below record the approved plan.

Updated: 2026-10-30. Active forecaster: **persistence only**. Start with the [workflow](MVP_FORECASTING_PLAN.md).

The live forecast repeats admitted current debt at registered horizons and predicts zero change. The MVP separately displays measured changes and actual forecast errors when available. Exact elapsed-day and measured-revision horizons retain different contracts and evidence.

| Active document | Purpose |
|---|---|
| [Executive summary](MVP_EXECUTIVE_SUMMARY.md) | Single-model decision and implementation order |
| [Scope](MVP_SCOPE.md) | Required capabilities and honest completion limits |
| [Forecasting workflow](MVP_FORECASTING_PLAN.md) | Persistence formula, data/clock gates, measured change and evaluation |
| [Architecture](MVP_ARCHITECTURE.md) | Immutable single-model bundles and read-only UI |
| [Roadmap](MVP_IMPLEMENTATION_ROADMAP.md) | Persistence bridge, dashboard, current measurement and handoff |
| [Evaluation protocol](MVP_EXPERIMENT_PLAN.md) | Reuse frozen evidence and score deterministic predictions |
| [Verification](VERIFICATION.md) | Checks for this documentation update |

Research history: [Chronos results](../../CHRONOS2_TOTAL_PRINCIPAL_KAGGLE_RESULTS_REPORT.md), [hybrid proposal](MVP_HYBRID_FORECASTING_PLAN.md), [negative hybrid diagnostic](../../HYBRID_PRINCIPAL_DIAGNOSTIC_REPORT.md), older digests/reviews and the [original source-preservation record](SOURCE_PRESERVATION.md). These do not add a model or completion gate to the active workflow. Historical files retain their original execution boundaries.

Next implementation is the persistence-only evidence/bundle bridge. This plan update runs no models, experiments or application stages.
