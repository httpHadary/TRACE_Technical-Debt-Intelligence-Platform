# TechDebt360 MVP scope: persistence only

Implementation update — 2026-10-30: the persistence input/evidence pipeline,
sealed bundles, evaluator and read-only API/dashboard are implemented in
`forecasting_mvp/persistence_flow.py`, `api.py` and `static/`. See the
[implementation report](../../PERSISTENCE_IMPLEMENTATION_REPORT.md) and
[exact operator commands/schemas](../../forecasting_mvp/PERSISTENCE.md).
A new real current-repository scan/demo and calendar data/evaluation admission
remain separate gates. Earlier future-tense statements below record the approved plan.

Updated: 2026-10-30. The [active workflow](MVP_FORECASTING_PLAN.md) uses **persistence as the only forecaster**. Chronos-2 and the hybrid are excluded from active inference, model selection, UI forecast requirements and the implementation critical path. Preserve their existing code and research results.

| Capability | Required MVP behavior | Evidence |
|---|---|---|
| Register/audit source | Bind repository, revision, target, scope/domain and clock | Valid source identities and permissions |
| Current measurement | Show compatible components and total principal | Complete revision-bound observations; unknown stays unknown |
| Forecast | Repeat admitted origin stock at each registered horizon | Versioned persistence formula, zero predicted change, null interval |
| Measured change | Show increases/decreases between compatible observations | Signed measured delta; comparability breaks explicit |
| Evaluation | Compare persistence with actual endpoints when available | MAE/RMSE, subgroup support, coverage and provenance |
| Local application | Read-only history, single-model forecast, actual/error and findings views | Completed immutable artifacts; unavailable/pending states |
| Calendar objective | Exact total-principal 30/60/90-day track when admitted | Separate target-specific source-state/evaluation gate |

The target remains estimated remediation minutes. The forecast assumes unchanged debt and cannot claim reliable advance detection of changes. Current finding priorities remain based on measured severity/minutes; architectural risk and actual labor remain separate quantities.

No Chronos dependency installation, checkpoint load, model worker, ensemble weight, neural training, automatic retraining, multi-model deployment or model promotion is required. Earlier adaptive/direct work stays paused. Existing optional GraphCodeBERT annotations remain separate from numerical forecasting and outside this critical path; the forecasting workflow does not require them. Remediation, enterprise infrastructure and remote hosting remain excluded.

Done means an operator can inspect real measured history, persistence points with explicit horizon units, measured changes, actual/error availability and provenance. Current-domain admission and calendar availability must be truthful. A missing prior observation cannot yield a fabricated measured change. A missing endpoint cannot yield a fabricated error. AI forecasting and comparison panels are not completion gates.
