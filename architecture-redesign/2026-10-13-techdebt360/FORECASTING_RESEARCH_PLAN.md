# Conditional forecasting research plan

Date: 2026-10-13. This is a proposed experiment protocol, not a deployed forecasting subsystem. No new labels, training, inference, scans or experiments were executed. Current conclusion: own module exact90 forecasting is unsupported; imported repository-level forecasting merits an early bounded audit.

## Research question and unit

Can pretrained numerical forecasters improve measured future maintainability remediation estimates over persistence and conventional feature-based models, under stable analyzer semantics, matched information and repository/time-aware validation?

Begin at **repository level** on the existing Technical Debt Dataset V2. Benefits: actual project measure schema, less lineage ambiguity, long histories. Limits: few independent domains, old analyzer semantics, aggregate scope changes and reduced localization. Use Zenodo 4534110 as an external historical replication namespace with weekly/irregular frequencies preserved. Keep its related replication package separate from independently collected observations. NPFDataSet remains quarantined until license and provenance are resolved; its all-issue effort and 91-day target cannot be combined with maintainability-only exact90.

Module evaluation follows only after verified own module histories exist. File-level studies remain secondary because persistence dominates and repeated files exaggerate sample size. Imported project aggregates never become synthetic modules.

## Target contracts

An immutable `TargetContract` contains: outcome name/unit, quality scope, aggregation population policy, origin/endpoint policy, duration in seconds, cadence/model-step policy, compatible domain policy, lineage version, missingness/censoring rules, feature availability, eligibility and label provenance. Hash this record; all datasets, models, capabilities and predictions refer to it.

| Target | Definition | Interpretation |
|---|---|---|
|Current TD|sum active eligible maintainability issue estimates at cutoff, or separately named compatible SQALE measure|Tool remediation estimate, not actual labor|
|TD at horizon|`TD(state at t+H)`|Future measured stock under the specified population/domain|
|Delta TD|future minus current stock|Growth/reduction estimate; population decomposition required|
|Growth event|`delta > threshold_minutes`, threshold fixed before test|A chosen material-change event, not universal business risk|
|New finding endpoint|at least one adjudicated compatible finding absent at origin and present at endpoint|Does not cover issues introduced and repaid between endpoints|
|New finding during interval|at least one verified introduction anywhere in interval|Needs intermediate scans or reliable lifecycle evidence; endpoint-only data cannot provide this label|

H = 30/60/90 days means 30/60/90 × 24 h in UTC. A 13-week target is 91 days and a three-calendar-month target has varying duration. These are separate contracts and separate results. `TD at cutoff` uses the last **reachable and available** branch state at or before the cutoff; it does not require a commit at the exact instant. A measured export for that exact selected commit/tree/domain can be reused. A previous nearby scan of a different state is not the endpoint. Never label by arbitrary nearest-date choice or interpolate ground truth.

For modules, primary target uses origin module membership carried by unambiguous file lineage to endpoint. Report retained-file delta, added-file debt and removed-file debt separately. A scope-changing whole-module stock is a separate target. Deletion and ambiguous split/merge censor the target; deletion is not automatic zero. Repository targets use declared source policy at each endpoint and disclose scope/population change; sensitivity evaluates stable retained source populations.

## Imported-history audit before model choice

V2 has 67,550 analysis records, 66,711 project measures and 31 domains. Nonblank analyses join Git revisions; profile fields are mostly available. Validate full timestamps/timezones, branch coverage, commit ancestry, analysis-to-measure uniqueness, quality profile content, rule/remediation domain changes and SQALE units. Distinct-day 90-day pairs (5,513) are candidate evidence, not a final eligible cohort. Determine eligibility by selected cutoff state and actually measured revisions.

For each repository report: eligible unique commits and cutoffs; span/cadence; missing runs; analyzer-domain segments; constant/changing target fraction; raw-minute distribution; duplicates; usable context; eligible horizon endpoints; non-overlapping evaluation blocks; domain-level effective sample limits. Profile/revision linkage strengthens this study but cannot certify missing plugin/settings metadata. If enough metadata is unavailable, name the imported historical domain and limit claims rather than falsely call it current-domain validation.

## Cadence-to-model adapter

Foundation forecasters consume observation steps. Fix this bridge before execution:

1. Define a regular calendar grid and select the actual branch state at each grid cutoff using only as-of available commits. Populate a grid point only when the selected state has a compatible measured analysis. Reusing a measured unchanged state is allowed when Git reachability/source identity proves it is the same state; record `REUSED_SAME_STATE`. No invented new measurement is claimed.
2. Preserve unavailable grid points as missing with reasons. Use only documented native model missingness support or an explicitly evaluated, past-only input treatment. Input imputation is a separate sensitivity and never creates evaluation labels. Baseline cohorts remain identical.
3. For weekly histories, native 13 steps represent 91 days. Benchmark this as 91 days. Exact90 may be studied with a **daily** grid when measured selected states actually cover the needed input/endpoint; never map 90 days to 12 or 13 weekly steps and rename it.
4. For irregular commit series, the initial step-based experiment has a separately named `next-k-observations` target with elapsed-time distribution. It cannot appear in the product as a calendar-day forecast. Prefer a justified regular-grid experiment for deployment semantics; no “event time” equal-spacing assumption is hidden.
5. Store `requested_duration_seconds`, `grid_interval_seconds`, `native_horizon_steps`, `input_grid_hash`, origin/endpoint snapshot/analysis IDs and native output timestamps. Noninteger duration/grid combinations are rejected unless a separately registered adapter has independent validation; MVP has no interpolated-output exact90 adapter.

Weekly imported Zenodo results provide a 91-day comparator, not evidence of exact90 success. Daily V2 reconstruction is conditional on observed state coverage, not on whether the model accepts a long array.

## Models and baselines

All models use the same eligible origin IDs, target values, information cutoff and observed history. Common-history comparisons are primary; extended-context results are separate. Candidate admission is based on task/cadence/context fit, not marketing accuracy.

| Order | Candidate | Role and constraint |
|---|---|---|
|0|last value; zero delta; training historical mean; bounded drift/trend|Mandatory strong simple controls; seasonal naive only with justified repeated seasonality|
|1|Ridge/ElasticNet, CatBoost, LightGBM, Random Forest|Size/process then current TD then trailing trend/graph ablations; select tuned model on validation only|
|2|Chronos-2-small|First zero-shot target-only probabilistic candidate; same observed history and horizon|
|3|full Chronos-2|Capacity control; separate covariate-aware variant using genuinely available inputs|
|4|TimesFM 2.5|Target-only challenger; XReg is a separately fitted variant and cannot be counted as equivalent native zero-shot input|
|5|Granite TTM-r3|Revision-specific contextual/horizon fit; main is 512→30; a verified 512→96 branch exists; context of 512 observations cannot be manufactured by padding|
|6|Toto 1.0, Moirai 2.0|Budget-gated challengers; Toto sample count fixed; Moirai checkpoint NC license and independent-univariate limitation|

See [checkpoint evidence](PRETRAINED_MODEL_RESEARCH.md) for immutable revisions, licenses, inputs/outputs and package conflicts. TTM is evaluated only when sufficient actual context and a fitting branch exist. It may be `NOT_ADMITTED_CONTEXT`, not scored as a failed model. Chronos small/full/TimesFM are also not automatically appropriate merely because they accept short histories.

Feature registry: trailing 30/90/180-day Git commits/churn/authors; current source size/complexity; current compatible remediation measures/finding counts; trailing TD trend and count of actual observed points; module membership/coverage; optional causal graph metrics and business context known at origin. Exclude future churn/modification, endpoint metrics, future path mapping, post-origin labels/statuses, whole-corpus normalizers and hindsight-selected issue links. Distinguish commit timestamp from branch availability; imported histories lacking availability logs have explicit retrospective assumptions.

Unknown future repository activity is not a known-future covariate. Calendar fields may qualify. A planned release can qualify only with a versioned plan demonstrably known at origin. Feature importance/SHAP is model association, not a causal explanation or proof the model “understands debt.”

## Splits and tuning

Two axes: rolling-origin within known repositories; whole-repository holdout with temporal constraints. Freeze repository registry before model outcomes. Imported-domain group splits do not borrow old NPF sealed outcomes. Reserve a final never-tuned cohort; report potential pretrained data contamination for old public repositories because model training overlap may be unknowable.

Train labels must mature before validation begins; validation labels must mature before test begins. Purge every origin whose endpoint crosses the next partition; include as-of availability timestamps. Group duplicate source states, repeated entities and clones to prevent cross-split shortcuts. Use non-overlapping horizon blocks for primary uncertainty, retaining dense rolling origins as secondary descriptive analysis. Cluster uncertainty by repository and time blocks; with 31 repositories report leave-one-project sensitivity and few-cluster limitations.

Prespecify equal search budgets, fixed seeds 0/1/2 for stochastic models, bounded parameters and no tuning on the sealed test. Fit scaling/imputation/feature selection/calibration only on train or validation as appropriate. No native quantile calibration on test.

## Metrics and uncertainty

Primary point metric: macro-repository MAE in remediation minutes; secondary pooled MAE, RMSE, bias, per-horizon and changing/constant-series errors. Skill = `1−MAE_model/MAE_baseline` when baseline MAE > 0; zero-error baseline yields skill undefined with absolute differences reported. WAPE requires positive sum absolute observed targets; report undefined on all-zero cohorts. MASE/RMSSE require a nonzero training-only scale. No MAPE on zero-heavy targets. Directional accuracy excludes a preregistered indifference band and reports eligible prevalence.

Common probabilistic comparison uses quantiles 0.1/0.5/0.9: **central 80% intervals**, quantile pinball loss, coverage/width and interval score. The decile-only models cannot natively supply central 90% intervals. A 90% deployment interval requires a documented validation-only conformal/residual calibration layer and adequate calibration blocks; report it separately. Proposed common 80% coverage gate is 75–85%, with width compared to a calibrated naive control. Marginal coverage is not per-repository conditional calibration; report both as far as data permits. Unchanged histories can yield narrow intervals with high coverage and still miss rare growth events.

Negative forecasts are retained in raw outputs and assessed. A nonnegative-clipped stock is a registered postprocessing variant; clipping invalidates untested interval semantics. Delta may legitimately be negative. Report failure/abstention and eligible coverage alongside accuracy; no dropping a hard repository to win an aggregate.

## Gates and branch decisions

Feasibility is not a universal snapshot count. Require adequate observed context for the specific adapter, multiple separated evaluation blocks, changing outcomes, compatible measured endpoints and enough repository/block precision to test a chosen useful effect. Preregister a development-only sample/precision assessment. Proposed minimum operational study shape is three non-overlapping horizon blocks per evaluated repository plus held-repository tests; this is a project governance floor, not proof of power.

Promotion criteria: ≥10% macro-MAE improvement over the strongest registered baseline; paired repository/block 95% CI above zero; benefit in ≥70% of eligible repositories; no unacceptable changing-subset failure; common 80% interval coverage of 75–85% with useful width; measured resource/coverage and license compliance. If these fail, retain negative results as research and do not enable normal-mode forecasts. If only a subset passes, scope capability to that subset and target/domain; never claim universal transfer.

If zero-shot forecasters lose but CatBoost wins, select the conventional predictor. If precise-minute forecasts lose, a growth-direction/new-finding target is a **new preregistered study**, not a post hoc relabeling of the same test. Interval introduction needs stronger lifecycle evidence than endpoint appearance. If all predictions fail, keep measured history and the primary evidence/remediation direction.

Early study effort ceiling: one week of imported-data audit, one bounded benchmark week after data/runtime gates in a later authorized phase. Fresh weekly backfill is secondary and requires the acquisition pilot/cost gate in [feasibility](DATASET_AND_FORECAST_FEASIBILITY.md). No forecast is operational today, and no model integration is authorized by this plan.
