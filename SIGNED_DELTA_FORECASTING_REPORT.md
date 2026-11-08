# Signed delta forecasting — Phase 6.2

**SYNTHETIC_ENGINEERING_TEST.** A separate ridge head at each30/60/90-day endpoint
learns normalized signed delta. Direct heads use all384 training cases; conditional
heads use only cases with nonzero synthetic endpoint change. Future change is a
training label, never an inference feature. Exact changed-training counts and
coefficients are in [models.json](examples/phase6_2/models.json).

The normalized target is `(future_stock-current)/max(1,mean(abs(observed past)))`.
The explicit one-minute floor stabilizes model training on zeros/sub-minute values;
it is **not** the denominator used for reported normalized error. Preprocessing is
fitted on training only. Ridge solves squared-error normal equations with L2
penalties1/10, intercept unpenalized. It estimates a working conditional **mean**,
not an automatically MAE-optimal median. Negative predictions remain valid signed
deltas. Raw signed delta/raw stock are retained; final stock is `max(0,current+delta)`.
No historical POM, model checkpoint or previous forecasting implementation changed.

Methods: direct delta; hard-gated conditional delta; probability-weighted conditional
delta; finite-mixture median; and a bounded validation-selected direct-delta blend
with persistence. Probability multiplication is a point heuristic, not a conditional
median claim. The blend weights selected are0.75/1/1 at30/60/90d.

The mixture has probability mass1-p at zero plus p spread uniformly across each
changed-training normalized residual added to the conditional ridge location.
Finite support/probability mass and quantile order are verified. Lower CDF quantiles
at0.1/0.5/0.9 define the derived mixture outputs. This is a fully specified empirical
working distribution, with a shared normalized residual-law assumption; it is not
certified as the true feature-conditional distribution. Its test coverage/collapse
are measured rather than assumed. Sorting CDF support is necessary distribution
calculation, not sorting invalid native quantiles. There are no native quantiles
or pretrained calls in this phase. The empirical CDF assumptions need further
independent validation before any real-world claim.

| Method | 30d MAE | 60d MAE | 90d MAE | 30d normalized skill | 60d normalized skill | 90d normalized skill |
| --- | --- | --- | --- | --- | --- | --- |
| persistence | 1,942.398 | 3,311.420 | 5,393.460 | +0.00% | +0.00% | +0.00% |
| rolling_mean | 2,092.514 | 3,461.232 | 5,543.109 | -29.71% | -14.10% | -11.03% |
| anchored_trend | 504.666 | 132.787 | 459.493 | +11.26% | +56.79% | +64.94% |
| direct_delta | 882.398 | 780.400 | 1,268.018 | +8.52% | +59.89% | +60.27% |
| hard_gate | 688.603 | 564.238 | 1,245.053 | +37.43% | +62.41% | +60.32% |
| probability_weighted | 687.818 | 514.970 | 1,272.038 | +30.79% | +60.48% | +60.67% |
| mixture_median | 710.706 | 595.005 | 981.150 | +36.96% | +62.90% | +61.38% |
| blend | 373.800 | 780.400 | 1,268.018 | +14.33% | +59.89% | +60.27% |
| selected | 688.603 | 595.005 | 459.493 | +37.43% | +62.90% | +64.94% |

All192 cases and exact horizons match across methods. Selected is an alias for the
validation-selected candidate, not an independently fitted ninth predictor. Raw
errors are scale-dominated; use the comparison report and normalized columns.
The direct regression's unchanged-case MAEs are23.528/27.869/14.231, versus
hard-gate0/30.776/13.803. Thus gating reduces false movements, but does not uniformly
reduce the size of unchanged-case errors at every horizon.

| Days | Unchanged N / MAE | Changed N / MAE | Large increases N / MAE / skill | Large decreases N / MAE / skill |
| --- | --- | --- | --- | --- |
| 30 | 54 / 0.000 | 138 / 958.056 | 38 / 58.731 / +51.88% | 5 / 89.401 / -6.88% |
| 60 | 30 / 28.046 | 162 / 699.997 | 61 / 338.642 / +92.84% | 14 / 58.483 / +31.11% |
| 90 | 15 / 9.572 | 177 / 497.621 | 78 / 1,075.002 / +91.87% | 24 / 96.333 / -7.10% |

The selected forecast's30d and90d large-decrease skill is negative. Negative delta
support and nonnegative stock reconstruction are mechanically correct; that does
not guarantee good debt-reduction predictions. Unobservable future changes after
constant histories cannot be recovered from unavailable future information.
No test-informed parameter change or retry was made.
