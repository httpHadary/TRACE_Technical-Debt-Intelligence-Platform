# Persistence: frozen evidence and research limits

This is interpretation of the **published Phase 3/4.2 Java study**, not a new
real-data experiment. The Phase 6 auditor recalculated 216 macro/pooled arithmetic
checks from two small published summary CSVs. It opened no numerical label file,
prediction export or historical context store. The receipt identifies both source
hashes. Reproducing summary arithmetic is not rerunning the benchmark.

Units are estimated maintainability remediation minutes, **not developer labor**.
The primary statistic averages per-repository MAE equally. Pooled MAE weights rows;
macro RMSE averages per-repository RMSE, rather than taking the square root of
macro MSE. Do not row-weight stratum macro values to reconstruct overall macro MAE.

| Frozen test | Days | Persistence macro MAE | Chronos policy macro MAE | Chronos skill | Unchanged endpoints / total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Temporal | 30 | 50.326 | 58.889 | −17.01% | 410/555 (73.87%) |
| Temporal | 60 | 98.710 | 108.426 | −9.84% | 330/555 (59.46%) |
| Temporal | 90 | 148.708 | 157.478 | −5.90% | 287/555 (51.71%) |
| Held-out repositories | 30 | 179.599 | 227.886 | −26.89% | 130/222 (58.56%) |
| Held-out repositories | 60 | 327.941 | 392.762 | −19.77% | 98/222 (44.14%) |
| Held-out repositories | 90 | 470.252 | 541.636 | −15.18% | 82/222 (36.94%) |

These frozen Chronos policy numbers include explicitly labeled persistence
fallbacks on invalid native paths. Skill is `1 − model_MAE / persistence_MAE`.
Selection used validation only and retained persistence at every horizon. On the
90-day native-success-matched populations, temporal Chronos/persistence MAEs were
157.010/148.140; held-out MAEs were 547.006/474.753. Failure removal does not reverse
the observed ranking; it changes the estimand and must be labeled separately.

Persistence has exactly zero error on unchanged endpoints. Its errors are entirely
on changing endpoints. Chronos both introduces movement error on unchanged cases
and misses changes: temporal 90-day changing-case macro MAE was 266.093 versus
261.422 for persistence; held-out was 795.377 versus 717.061. Temporal unchanged
Chronos MAE was 50.698; held-out was 31.062. Thus change-aware methods have a clear
failure mode to investigate, but **the existing evidence does not show pretrained
superiority even after selecting changing cases**. Future changes are a scoring
stratum, never information available to a predictor.

## Constant history, native errors and uncertainty

The configuration used 90 past daily positions and one native 90-step path,
selecting indices 29/59/89. It did not test all context lengths or all pretrained
models. Daily positions are not independent scans: temporal histories had median
3 distinct measurements, held-out histories median 8; there were 286/131 distinct
past value sequences across 555/222 contexts respectively. Origins and horizons
overlap. Repository bootstrap handles clustering partially, not source ambiguity
or all temporal dependence. Only six held-out families make its CIs exploratory.

All 740 constant-history contexts (360 validation, 286 temporal, 94 held-out)
had raw and clipped zero-width selected intervals. Constant past did not guarantee
constant future. Native nominal-80% macro coverage fell from 79.32% to 62.37% between
30/90 days on temporal tests, and 78.59% to 60.90% on held-out repositories. Widths
increased while coverage deteriorated; these intervals were not calibrated.
Constant/nonconstant diagnostics and failure denominators are in the original
interval summaries. An interval collapse is not evidence that future risk is zero.

Twelve of 1,512 contexts failed strict full-path quantile ordering (36 endpoints
fell back, with null intervals). Phase 4.2.1 observed 14 crossed steps, at days
1/17/18/19/64, with maximum inversions 0.000244140625–2.8369140625 minutes. All 36
selected endpoints were ordered. All failures were nonconstant histories; all
repeated identically in that diagnostic. The full-path rejection was conservative
relative to selected endpoints, but remains the frozen policy. No sorting,
tolerance, endpoint-only exception or metric revision is authorized here.

**Established mechanism:** native returned quantiles crossed. **Unproven causes:**
training objective, finite precision, scale, sparse-state patterns and domain
mismatch. The largest crossings cannot all be dismissed as single-ULP noise.
Likewise, persistence's advantage is consistent with persistent debt stock and
penalties for unnecessary movement; the existing observational study does not
identify a unique causal explanation. Longer context, process signals, residual
models and calibration remain hypotheses.

References: [Phase 3](PHASE_3_IMPLEMENTATION_REPORT.md),
[Phase 4.2](PHASE_4_2_IMPLEMENTATION_REPORT.md),
[diagnostics](PHASE_4_2_1_DIAGNOSTIC_REPORT.md), and
[summary-only recomputation](examples/phase6_0/summary_audit.json).
