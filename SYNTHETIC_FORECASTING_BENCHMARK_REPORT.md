# Synthetic forecasting benchmark — engineering evidence only

**SYNTHETIC_ENGINEERING_TEST.** These results concern designed equations, not
historical technical debt, model selection for production or real-world gains.
All values are simulated estimated-remediation minutes. No analyzer or historical
label was used. Frozen Java results remain in their separate reports.

## Registered population and execution

`synthetic.py` generates14 scenarios ×3 separately seeded cases =42 cases and126
exact endpoints per baseline. Seed is `6000 + scenario_index*100 + replicate`.
Independent random streams do not make these42 real repositories or establish
population-level statistical independence. Origin is2026-01-01T00:00:00Z.
Explicit latent daily truth runs from origin−89 through origin+90; an observation
mask/irregular sampling process is separate. Sparse/missing history is never
converted to a daily measured series, zeros or interpolated evidence.

The14 scenarios are constant, long plateaus, slow increase/decrease, upward/
downward jumps, multiple steps, stationary noise, sparse, irregular, quiet-then-
change, near/at zero, mixed scales and distribution shift. Equations, seeds,
actual past timestamps/masks and population coverage are recorded in the versioned
generator and [population receipt](examples/phase6_0/scenario_population.json).
Signed-change reconstruction, persistence on constant/zero stock, OLS on exact
linear stock and30/60/90 endpoint values have analytical unit tests. Every case's
full generated future is retained privately, outside prediction requests.

Predictions receive only a strict immutable past-only request. Opaque case IDs
replace descriptive scenario IDs; scenario names/mechanisms remain evaluator
metadata. Predictions are written and checksummed before targets are scored.
There is no learning, validation tuning or test-based selection. Fixed baseline
windows are7-day mean and90-day anchored trend. Complete90-day endpoints reuse the
unchanged original baseline implementation. Irregular trend uses actual elapsed
observation days. Rolling windows with fewer than6 observed positions in the last
7 days fail explicitly. Neither a missing origin nor a gap becomes a known zero.

Chronos uses a fixed10-case subset across8 scenarios: constant, increase, decrease,
up/down jumps, stationary noise, two near-zero cases and two mixed-scale cases.
It intentionally does not cover the full42-case population, and refuses sparse/
irregular contexts without filling. It ran twice per selected case in each worker.
No alternative case was selected after observing an error.

## Numerical results

Equal-weight synthetic-case macro MAE, in simulated minutes:

| Population | Model | Successful cases / attempts | 30-day MAE | 60-day MAE | 90-day MAE |
| --- | --- | ---: | ---: | ---: | ---: |
| Full baseline population | Persistence | 42/42 | 76.471 | 213.761 | 305.549 |
| Full baseline population | Trend | 42/42 | 49.056 | 32.189 | 54.196 |
| All-baseline success-matched population | Persistence | 36/36 | 88.551 | 248.134 | 354.755 |
| All-baseline success-matched population | Rolling mean | 36/36 | 112.800 | 272.524 | 378.985 |
| All-baseline success-matched population | Trend | 36/36 | 57.010 | 37.373 | 63.048 |
| Fixed Chronos population | Persistence | 10/10 | 276.375 | 811.061 | 1167.066 |
| Fixed Chronos population | Native Chronos q50 | 10/10 | 68.484 | 24.872 | 138.504 |

Rolling mean failed6/42 cases (three sparse and three irregular); failure rate
14.29%, with no fallback or silent omission. Its matched metrics must not be
compared against42-case persistence. Chronos native failures were0/10 in the
release worker (20/20 successful calls including repeats), with no fallback.
It did not attempt32 other cases. Aggregate skill on its matched population was
75.22%/96.93%/88.13%, **not a real technical-debt improvement**. Mixed-scale cases
include stocks scaled by1000, so unnormalized absolute MAE can be dominated by
those designer-chosen cases even under equal case weighting. Per-scenario errors
and all failure/population counts remain visible; no difficult scenario is hidden
or removed based on its performance.

The full [numerical summaries](examples/phase6_0/numerical_results.json) include
macro/pooled MAE and RMSE, median absolute error, pooled signed bias, unchanged/
changing/large-change errors, skill, failure rates, collapsed intervals and
case-bootstrap paired gain bounds. Large change was fixed as
`abs(delta) >= max(10, 0.2*current)`. Each case has one endpoint per horizon, so
within-horizon case-macro RMSE equals case-macro MAE here; pooled RMSE remains
different. This is expected, not a copied historical statistic.500 seeded
case-cluster bootstrap draws exercise the arithmetic; their intervals do not
establish real repository generalization or meaningful coverage of all generators.

## Native quantiles, zeros and runtime

Release native q10–q90 empirical coverage on10 synthetic cases was90%/70%/80%
at30/60/90 days, with macro widths274.055/529.166/805.485 minutes. These small-
sample ranges are uncalibrated engineering observations. The positive constant
case produced raw q10=q50=q90=100, zero width at each selected endpoint. The
zero-stock case produced tiny signed raw values (for example90-day raw median
−7.787789968460856e−9); its scored stock was clipped to0. Raw quantiles remain
preserved, and clipping is not quantile sorting. No native path crossed in these
cases. Mock-engine tests prove crossing rejection; this does not remove or explain
away the12 original historical failures.

Release checkpoint/config/runtime identities are in the
[registration](examples/phase6_0/chronos_registration.json).
Actual release measurements:

- CPU-only float32; two Torch intra-op/one inter-op threads, affinity to two CPUs;
  no CUDA, model acquisition or runtime installation.
- Whole supervisor wall time6.111s; worker `ru_maxrss`491,237,376 bytes (~468.5MiB),
  sampled peak492,843,008 bytes (~470.0MiB), below2GiB.
- Linux x86_64 seccomp denied socket creation and was verified inside the worker;
  offline library settings and local-files-only loading were also active.
- Limits:900s wall/CPU,2GiB sampled RSS, bounded16MiB individual outputs/logs.
  The20ms RSS monitor is not a hard cgroup quota; a transient overshoot cannot be
  ruled out by sampling. No observed run approached the bound.
- All10 pairs repeated exactly. Five preserved successful engineering workers
  made100 calls total on the **same10 unique contexts**, not100 independent cases.
  Numerical path hashes matched across all workers, including the final opaque-ID
  release. Development changes tightened failure reporting, response identity and
  scenario-ID isolation; they did not tune model parameters, input values or
  case selection using outcomes. Earlier receipts were retained, not overwritten.

[Resources](examples/phase6_0/chronos_resources.json),
[supervision](examples/phase6_0/chronos_supervisor.json) and
[repeatability](examples/phase6_0/reproducibility.json) contain actual values.
Wall time and memory are not byte-deterministic. Software tests separately cover
real child-process timeout, nonzero worker exit, missing environment, seccomp
network denial, wrong identities, malformed/missing/nonfinite values and native
crossing rejection. No timeout or RSS breach occurred during actual model inference.

## Interpretation and replay

A linear process gives extrapolation a structural advantage; a long constant past
followed by an unobservable future jump exposes an information limit. Synthetic
rankings therefore depend on the authored generator. They validate plumbing,
contracts, scoring and resources, **not H1–H7 on real technical debt**. Persistence
remains the real-study reference and original validation-selected default.

Run commands and interfaces are in the
[package README](forecasting_research/phase6_0/README.md). Full requests, latent
truth, daily paths, logs, seals and manifests remain under
`/home/hp/tst/research/forecasting_mvp/phase6_0/2026-10-19/` in fresh task directories.
Git contains only original code, small generated samples and sanitized summaries.
No real dataset, frozen result, model or rights decision was changed.
