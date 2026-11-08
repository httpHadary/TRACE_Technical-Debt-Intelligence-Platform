# Phase 6.3 — Adaptive Persistence robustness

This package fits original synthetic data only. Every result is
`SYNTHETIC_ENGINEERING_TEST`, in simulated estimated maintainability remediation
minutes. There is no real-data, pretrained, service, scanner or installation route.
The separately published Phase 6.3 failure audit precedes this experiment design.

The primary model at **every** horizon is `adaptive_persistence`. It anchors on
the observed origin stock; estimates unchanged/increase/decrease direction scores;
predicts separate signed magnitudes; then confidence-gates and shrinks an adjustment.
Weak evidence defaults to persistence. Its protected zero-adjustment option is
chosen by validation if more active adjustments do not earn an advantage. The
`comparison_champion` is a separately labelled alias, never a replacement for the
primary research candidate. Simpler baselines can legitimately win.

Reproduction uses the already available Python3.12.3 / NumPy2.4.4 environment:

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
.venv-forecast/bin/python -m forecasting_research.phase6_3 prepare \
  /home/hp/tst/research/forecasting_mvp/phase6_3/YYYY-MM-DD/new-study
.venv-forecast/bin/python -m forecasting_research.phase6_3 run \
  /home/hp/tst/research/forecasting_mvp/phase6_3/YYYY-MM-DD/new-study
.venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_phase6_3_robustness.py
```

A completed directory/attempt cannot be reused. The frozen original Phase6.2
private state, selected configs, calibration and history-hash metadata must be
present and match registered hashes. Missing transfer evidence blocks execution;
there is no substituted or silently retrained transfer model. The original state
is applied only to new requests; no old experiment workload is rerun. A separate
binary architecture is explicitly fitted to NEW Phase6.3 training data.

Features reuse the24 past-only definitions from Phase6.2. Nulls and timestamps
remain intact; training-only feature medians and missing indicators never create
observed zeros. Across-gap transitions are censored, and plateau duration is a
contiguous observed lower bound. `predict(request,state,config,horizon)` accepts
no labels, split, family, generator parameters or future direction. Cached feature
copies are immutable. Origin stock must be measured.

New synthetic root seed63020261020; independent SHA-derived case/partition streams.
Counts:384 training,192 validation,192 calibration,256 test,160 OOD. The16 training
families and eight wholly held-out mechanisms are fixed before fitting. Each OOD
family has stable, interim-return, upward-change and downward-change branches,
giving10 unchanged/5 increased/5 decreased endpoints per20 cases at each horizon.
No post-outcome filtering/deduplication is permitted. History/parameter hashes
are unique, and old Phase6.2 histories are excluded by hash before fitting.
Identical families across development splits still imply shared mechanism dependence,
not independent software repositories. A return to origin is an unchanged endpoint
even if generated debt changes at intermediate times.

The primary architecture uses normalized one-vs-rest direction scores (three ridge-
regularized logistic fits), with none/balanced training class weights. They are
not claimed calibrated posterior probabilities. Separate positive/negative signed
ridge heads retain raw values before sign projection. L2 penalties1/10, intercepts
unpenalized,40 deterministic half-step Newton updates, no stochastic training.
Insufficient class support is explicit and blocks a three-way claim.

Adaptive confidence thresholds are0.75/0.9. A predicted magnitude must exceed
`max(0.02 or 0.1, 0.25*past normalized volatility)`. The adjustment is multiplied
by0.25/0.5 and by `1/(1+maximum observed gap days/30)`. The protected zero-adjustment
config is first in tie order. Thresholds and shrinkage are selected on validation
only. Stock clipping at zero, direction sign projection and deliberate shrinkage
are separately recorded. Probability-weighted signed expectations are an ablation,
not an MAE-optimal median claim.

Selection minimizes equal-family validation MAE divided by the model scale
`max(1 minute,mean(abs(observed past)))`, subject to unchanged and large-decrease
safety. Reported normalized metrics use the **unfloored** historical mean;
zero denominators are excluded/count reported, never silently given epsilon.
All groups/cases and raw MAE/RMSE are retained. Within1% of the best eligible
validation error, prefer first registered configuration/method. Adaptive Persistence
stays primary even if the comparison champion is persistence or another baseline.

Interval choices are separately preregistered: shared symmetric residuals, global
signed residual quantiles, and predicted-direction-stratified signed residuals.
Training residual prototypes are used only for validation interval selection;
the final chosen algorithm is recalibrated on the independent calibration partition.
Sparse bins (<12) explicitly reuse the global residual distribution and record the
fallback. True future direction never chooses a bin. Widening is bounded to1/1.25.
Asymmetric interval median can differ from the unchanged point forecast; point
predictions are not recalibrated. Quantiles are derived, not native pretrained
outputs. There is no sorting repair or distribution-free guarantee.

The fixed protocol contains all hypotheses,73 candidates per horizon, tolerances,
scale policies and failure handling. Complete test/OOD predictions, model state,
selection, calibration and requests are sealed before target access. This is a
logical role/file/pure-function boundary, not an adversarial OS sandbox.

One sequential CPU worker:2GiB RSS, two numerical threads,900seconds,8MiB logs,
64MiB total outputs. Monitoring uses10ms `/proc` RSS/HWM plus final kernel ru_maxrss,
not a hard cgroup quota. Python socket connections are denied, not network-namespace
isolation. Finally receipts survive ordinary exceptions; abrupt-kill evidence is
limited to supervisor observations. No worker retry or resource increase is automatic.

All prior studies, model/checkpoint files, compilation receipts and rights decisions
remain frozen. All24 Phase C permissions remain NOT_APPROVED. No further phase is
authorized by these reproduction instructions or by synthetic improvements.

## Recorded run status: PARTIAL; do not silently reuse this selector

The first registered run found a protocol defect: with only3 large-decrease
validation cases at30d, no candidate was safety-admitted, but the generic selector
chose an active AP adjustment instead of the registered protected zero-adjustment
fallback. The main30d test also had0 large-decrease cases. The original code, state,
selection, predictions and metrics are retained unchanged as historical evidence.
The30d AP results are descriptive and not a compliant safe-selection result.
Do not treat the reproduction commands above as approval for another run or use
this selector for a new scientific claim until a separately versioned correction
and adequate new preregistration are authorized. No corrected predictions or new
cohort were generated. See the implementation report and protocol_audit.json.
