# Phase 6.3 — Phase 6.2 failure-mode audit

Prepared and published before Phase 6.3 experiment design or fitting.
**SYNTHETIC_ENGINEERING_TEST; read-only audit PASS.**

The Phase 6.2 sealed private artifact inventory rehashes exactly. Three published
main-test references reproduce from the small aggregate CSV: persistence versus
selected MAE is1942.398/688.603 at30d,3311.420/595.005 at60d,5393.460/459.493 at90d.
These are simulated remediation minutes, not measured software debt. Only summary
records were interpreted; old numerical target files were opaque-hashed, not opened
as labels. No Phase 6.2 fitting, prediction or scored experiment was rerun.
Exact source and artifact identities: examples/phase6_3/phase6_2_audit.json.

Observed limitations and interpretation:

- The selected90d method was anchored trend. The evidence does not establish
  uniform superiority of the learned two-stage architecture over strong baselines.
- Selected large-decrease skill was−6.88% at30d and−7.10% at90d. Signed-delta
  correctness and strong classification F1 did not establish safe magnitude errors.
- Selected raw OOD30d MAE33.715 versus persistence28.853 is16.85% worse. The
  normalized ranking differed; aggregate scale can reverse conclusions.
- Selected nominal80% OOD interval coverage was50.00/58.33/54.17% at30/60/90d.
  Calibration had used a shared normalized absolute residual radius. Residual-law,
  scale, conditional-direction and change-frequency shifts are plausible causes;
  this audit does not claim a measured causal decomposition or optimal remedy.
- All48 OOD endpoints changed at each horizon. Negative-class discrimination,
  unchanged-case forecasting and conditional coverage could not be assessed there.
- Some useful30d gating results coexist with long-horizon false movements and
  missed changes. Future endpoint class is a scoring/training label, never an
  inference-time feature. Returns to origin must count as unchanged endpoints.
- Cases share mechanisms and one deterministic generator implementation. Synthetic
  resampling intervals are not evidence about independent real repositories.

Code inspection confirms training-only preprocessing, separate train/validation/
calibration roles and prediction-before-test seals. Features preserve nulls, use
actual timestamps and mark gap-censored observed transitions; they do not prove
absence of hidden changes. The working empirical mixture assumes a shared
normalized changed-training residual law. Its finite CDF is defined; its adequacy
under shift is unproven. Native pretrained intervals were not available.

Research motivations, not findings about an unrun successor: test cautious trend
shrinkage, separate direction/magnitude estimates, explicit unchanged/large-decrease
safety and bounded interval-quality criteria. A genuinely new registration is
required before fitting. Exposed Phase 6.2 outcomes may motivate questions but may
not select successor hyperparameters or serve as fresh test evidence.

The historical Java reference remains persistence148.708 versus Chronos157.478
at90d temporal MAE and470.252 versus541.636 on exposed held-out repositories.
Those cohorts remain frozen. All24 Phase C decisions remain NOT_APPROVED. No
historical data access, pretrained loading, scanning, Maven, services or dataset
admission occurred. This audit grants no new rights or subsequent-phase permission.
