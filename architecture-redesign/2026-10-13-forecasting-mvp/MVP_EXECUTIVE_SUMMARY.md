# TechDebt360 MVP: persistence-only workflow

Implementation update — 2026-10-30: the persistence input/evidence pipeline,
sealed bundles, evaluator and read-only API/dashboard are implemented in
`forecasting_mvp/persistence_flow.py`, `api.py` and `static/`. See the
[implementation report](../../PERSISTENCE_IMPLEMENTATION_REPORT.md) and
[exact operator commands/schemas](../../forecasting_mvp/PERSISTENCE.md).
A new real current-repository scan/demo and calendar data/evaluation admission
remain separate gates. Earlier future-tense statements below record the approved plan.

Updated: 2026-10-30. **Persistence is the only active MVP forecaster.** Its prediction repeats current measured debt at every registered horizon; projected change is zero and no forecast interval is supplied.

The MVP continues to measure repository total principal (maintainability + reliability + security estimated remediation minutes), show historical and newly measured changes, and evaluate persistence against actual endpoints. Persistence does not anticipate increases or decreases; measured change and projected change must be displayed separately.

Implementation order: validate existing persistence evidence → publish a persistence-only bundle → build the read-only local dashboard → demonstrate a current repository measurement and compatible measured change → hand off with explicit horizon/provenance limits. Exact 30/60/90-day total-principal evaluation retains its own admission gate; 3/4/12-revision evidence cannot replace it.

Chronos-2 and the hybrid are removed from active execution, live forecast UI and completion requirements. Their original code, model artifacts, reports and negative results are preserved as research history. The fixed-grid hybrid did not beat persistence; no hybrid policy is adopted. No future comparison or model experiment runs automatically.

The [workflow](MVP_FORECASTING_PLAN.md), [scope](MVP_SCOPE.md), [architecture](MVP_ARCHITECTURE.md), [roadmap](MVP_IMPLEMENTATION_ROADMAP.md) and [evaluation protocol](MVP_EXPERIMENT_PLAN.md) form the active plan. This update changes planning documents only; application implementation remains future work.
