# Persistence-only replay and evaluation protocol

Implementation update — 2026-10-30: the persistence input/evidence pipeline,
sealed bundles, evaluator and read-only API/dashboard are implemented in
`forecasting_mvp/persistence_flow.py`, `api.py` and `static/`. See the
[implementation report](../../PERSISTENCE_IMPLEMENTATION_REPORT.md) and
[exact operator commands/schemas](../../forecasting_mvp/PERSISTENCE.md).
A new real current-repository scan/demo and calendar data/evaluation admission
remain separate gates. Earlier future-tense statements below record the approved plan.

Updated: 2026-10-30. The only active forecast method is persistence. See the [workflow](MVP_FORECASTING_PLAN.md). No weight tuning, model-selection stage, checkpoint/runtime setup, native-quantile evaluation or neural prediction is required.

## Reuse completed evidence

Reuse the persistence rows and original measurements from `chronos2-total-principal-mart-v1` without rerunning its notebook or changing its six-method registration. The [returned audit](../../examples/chronos2_total_principal/returned_verification.json) and [aggregate metrics](../../examples/chronos2_total_principal/returned_summary.csv) retain the original identities. A persistence-only presentation view has 678 endpoint rows from 226 origins at three horizons; it is a filtered view of frozen evidence, not a newly run study.

Per-origin display requires authorized full artifacts; aggregate files alone support only aggregate display. The [Chronos report](../../CHRONOS2_TOTAL_PRINCIPAL_KAGGLE_RESULTS_REPORT.md) and [hybrid diagnostic](../../HYBRID_PRINCIPAL_DIAGNOSTIC_REPORT.md) remain research records outside the active forecast execution. Do not rerun either study or modify their results to match the simplified product.

## New persistence predictions

1. Register source/revision/domain, total-principal component definitions, target/unit, horizon value/unit, origin-selection policy and allowed evidence use. A new retrospective population must be frozen before scoring and retain honest exposure/eligibility metadata.
2. Project only the valid origin measurement and registered forecast identities to the deterministic predictor. Future numerical labels are absent.
3. Copy origin stock to every registered horizon. Save point, zero predicted delta, null interval, formula/policy and source identity. No fitting or additional model is involved.
4. Validate and seal output, then allow the evaluator to open the matched actual endpoints. Missing/pending actuals stay null; they do not prevent a valid current forecast.
5. Publish immutable output plus actual/error availability, MAE/RMSE and subgroup/coverage reports. Do not select a new model or promote a hybrid from the results.

For elapsed-day evaluation, require the selected reachable source state and its compatible measurement at the exact UTC cutoff. Do not carry an older stock across an unmeasured change. New current domains need their own data admission; old SQALE and revision cohorts remain separate from total-principal calendar studies.

## Measures and assertions

Check `prediction = origin_stock` and `predicted_delta = 0` for all admitted points, including zero stock. Evaluate repository-macro and pooled MAE/RMSE, bias, actual coverage, changed/stable/increase/decrease cases and source counts. Preserve repeated/overlapping-state dependence. Do not interpret zero projected change as proof of stability or compute an improvement against the same persistence method.

Measured change between comparable observations is reported separately from forecast change. A changed domain produces an incomparable reason; absent prior data produce an unavailable measured delta. There is no statistical forecast interval or change probability in this protocol.

Existing commands are study-specific; inspect their help before reuse and avoid any command that implicitly launches Chronos or other models. Planned bridge/API commands are not implemented yet, so no new runnable command is invented here. This update changes documentation only.
