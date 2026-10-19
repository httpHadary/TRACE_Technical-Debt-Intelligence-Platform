# Phase 6.2 research handoff — no execution authorization

Read the final Phase 6.1C report and receipts before choosing a new research task.
The new loader changes checkpoint materialization only. It does not change the
TimesFM architecture, float32 tensors, native forecasting or quantile policy.
Static tests alone never establish native memory feasibility.

Actual Phase6.1C result is **PARTIAL**: one approved low-memory model load and
native smoke return completed below the retained guard; all90 steps had native
adjacent-decile crossings. The selected endpoint q10/q50/q90 trios were ordered,
but all-nine-decile ordering failed. The remaining35 cases were not executed.
No accepted TimesFM accuracy or coverage score is available. Do not reinterpret
that rejected smoke case as a completed benchmark or repair the previous receipt.
The smoke exception occurred before final inference timing, kernel ru_maxrss
and post-inference in-memory hashes were published. Before any new authorization,
a separately versioned worker should retain those measurements on ordinary
exceptions as well as success. Do not backfill the existing receipt or rerun
the consumed attempt to obtain missing values.

The separately approved Phase 6.1C scope is one TimesFM CPU worker, one model
load, an initial 512→90 synthetic smoke forecast, then at most the other 35
Phase 6.1B cases if the smoke succeeds. No retry, higher limit, new dependency,
alternative checkpoint, model training or unrelated model replay follows it.

If actual loading or inference fails, preserve the earliest failure, all
available resource measurements and raw invalid paths. A new attempt needs
separate authorization and a reviewed explanation; do not loosen the 1.75 GiB
guard or 2 GiB ceiling automatically. Missing measurements remain unavailable.

If native prediction succeeds, distinguish CPU feasibility from point accuracy,
interval validity and uncertainty calibration. Compare only identical successful
case IDs and retain every registered failure. The reused 36 synthetic cases
were already exposed during Phase 6.1B and remain development evidence. A later
synthetic replication needs new preregistration and seeds; it still cannot
demonstrate real technical-debt forecasting improvement.

Potential research questions include interval undercoverage, plateau/change
behavior, scale sensitivity and validation-selected change-aware combinations.
Do not select thresholds or settings from this exposed population and call the
same cases a fresh confirmatory test. Persistence remains mandatory; no model
is promoted automatically.

All original Java experiments, Phase 6.0/6.1A/6.1B results, six compilation
archives and Phase C decisions stay frozen. All 24 analyzer/data permission
decisions remain NOT_APPROVED. Real measurements require independent rights,
provenance, runtime and collection admission, plus an actually new held-out cohort.
No SonarQube, Maven, historical scan, dataset admission, backend or dashboard
activity is authorized by this handoff.
