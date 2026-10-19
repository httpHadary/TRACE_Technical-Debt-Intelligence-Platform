# Phase 6.2 — synthetic-only change-aware research

Every result is `SYNTHETIC_ENGINEERING_TEST`, in simulated estimated maintainability
remediation minutes. There is no real-data loader, pretrained runner, server, API,
dependency installer or permission setter. The existing studies remain frozen.

Run from the project root with the existing `.venv-forecast` (Python 3.12.3,
NumPy 2.4.4). No dependency installation or network is needed:

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
.venv-forecast/bin/python -m forecasting_research.phase6_2 prepare \
  /home/hp/tst/research/forecasting_mvp/phase6_2/YYYY-MM-DD/new-study
.venv-forecast/bin/python -m forecasting_research.phase6_2 run \
  /home/hp/tst/research/forecasting_mvp/phase6_2/YYYY-MM-DD/new-study
.venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_phase6_2_change_aware.py
```

The completed registered study must never be reused as writable output. An
exclusive attempt receipt prevents a second execution. A later scientific
experiment needs separate authorization and a new registration; this README
does not authorize follow-up experiments.

`prepare` generates histories/targets, validates unique history/parameter hashes,
records partitions, installed NumPy RECORD hashes, source hashes and the fixed
search policy **before fitting**. Model parameters and preprocessing use training
only; selection uses validation only; residual radii use calibration only.
Test and OOD forecasts are complete and sealed against requests, models,
selection and calibration before numerical test targets can be opened for scoring.
The label boundary is a role/file/contract boundary, not an OS security boundary
against deliberately hostile Python code. Generator code itself can generate
truth; it is excluded from predictor dependencies.

`models.predict(Request, state, config, horizon)` receives only immutable past
observations, a fitted state, a frozen config and exact horizon. Its request has
no split, scenario, generator parameters or future change flag. Models never
receive the actual test change indicator. The origin must be measured.

Features use actual timestamps and observed values. Explicit nulls stay null;
imputation applies to **feature columns**, fitted on training only, with missing
indicators. No history is filled, padded, interpolated or carried forward.
Observed endpoint transitions across gaps are censored observations, not actual
event rates. Plateau duration is the contiguous daily observed lower bound.

The change label is endpoint inequality at day 30/60/90. It is **not** the label
"any change occurred at any interim time": a change followed by reversal can
have a zero endpoint delta. All generators and labels are original synthetic data.

Both logistic and ridge models are deterministic float64 NumPy models. This is
not a change to existing CPU float32 pretrained adapters. Logistic uses unweighted
binary cross-entropy with L2 regularization and 40 fixed half-step Newton updates;
ridge uses squared error with L2 regularization, intercept unpenalized. Penalties
are 1 or 10. Single-class classification is explicitly marked ineligible for a
logistic fit; its empirical constant probability is retained as a diagnostic.
Insufficient conditional-change support is an explicit failure, never a fake fit.

Two scales are distinct. The model/validation objective uses `max(1 minute,
mean(abs(observed history)))`, an explicit one-minute unit floor. Reported
normalized metrics use the unfloored historical mean; zero denominators are null,
excluded and counted. No epsilon is silently assigned to zero-history metrics.

The mixture method forms a probability mass at zero plus a conditional ridge
location and empirical changed-training residual distribution in normalized delta
units. Quantiles are calculated from that finite CDF. Sorting CDF support is not
repairing unordered native quantiles. Its distributional assumptions are research
assumptions; no native pretrained intervals are involved. Probability-weighted
residuals are a point heuristic, not an MAE-optimal median claim.

Derived calibrated intervals use the separate calibration partition's empirical
80th percentile of absolute normalized forecast residuals, then nonnegative stock
clipping. These are symmetric residual intervals, not distribution-free conformal
guarantees or verified native model uncertainty. Raw deltas and raw mixture
quantiles are retained separately. All point methods share the same cases.

The controller permits one sequential CPU worker, at most two numerical threads,
900 seconds, 2 GiB RSS, bounded logs/output and owned-process termination. It uses
sampled `/proc` RSS/HWM plus final `ru_maxrss`, not a hard cgroup quota. Worker
socket connections are rejected in Python; this is not network-namespace isolation.
Ordinary exceptions retain resource/failure receipts through `finally`; abrupt
kills leave available supervisor evidence and missing worker fields unavailable.

Chronos is `NOT_EXECUTED_NO_SEPARATE_APPROVAL`; TTM and TimesFM are not executed.
All 24 Phase C decisions remain NOT_APPROVED. A synthetic gain is neither a
real-world accuracy claim nor authorization to use analyzer-derived measurements.
