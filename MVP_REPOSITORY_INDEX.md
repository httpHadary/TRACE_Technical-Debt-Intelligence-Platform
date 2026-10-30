# TechDebt360 MVP repository

Updated: 2026-10-30. Active forecaster: **persistence only**. Use the
[workflow](architecture-redesign/2026-10-13-forecasting-mvp/MVP_FORECASTING_PLAN.md)
and [roadmap](architecture-redesign/2026-10-13-forecasting-mvp/MVP_IMPLEMENTATION_ROADMAP.md).

The product repeats admitted current debt at registered horizons. Measured changes,
actual/error availability, target/clock and provenance remain explicit. Chronos-2
and the hybrid are archived research and are not active forecast stages or required
live series. The persistence bridge/API/dashboard are implemented; see the report below.

- [Persistence implementation and checks](PERSISTENCE_IMPLEMENTATION_REPORT.md)
- [Operator schemas and commands](forecasting_mvp/PERSISTENCE.md)
- [Active direction](RESEARCH_DIRECTION_STATUS.md)
- [MVP plan package](architecture-redesign/2026-10-13-forecasting-mvp/README.md)
- [Existing forecasting implementation and historical boundaries](forecasting_mvp/README.md)
- [Original persistence aggregate evidence](examples/chronos2_total_principal/returned_summary.csv)
- [Source experiment audit](examples/chronos2_total_principal/returned_verification.json)
- [Archived Chronos principal results](CHRONOS2_TOTAL_PRINCIPAL_KAGGLE_RESULTS_REPORT.md)
- [Archived hybrid diagnostic: no adoption](HYBRID_PRINCIPAL_DIAGNOSTIC_REPORT.md)
- [Phase 2 dataset report](PHASE_2_IMPLEMENTATION_REPORT.md)
- [Phase 3 baseline report](PHASE_3_IMPLEMENTATION_REPORT.md)
- [Pipeline documentation](README.md)
- [GitHub sync instructions](GITHUB_SYNC.md)

Revision-step results do not establish total-principal 30/60/90-day accuracy.
Historical SQALE targets stay separate. Current repositories need their own
measurement admission. Private data/reviews, model weights and raw returned
artifacts remain outside the presentation export. Local paths in historical
reports remain provenance records.
