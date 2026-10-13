# Technology and forecasting review

Reviewed 2026-10-13: **only** `MVP_FORECASTING_PLAN.md` and `MVP_ARCHITECTURE.md`, against [fresh research digest](../digests/research-check.md) and its explicitly named same-date verified import. Planning-only review; no application/model/dataset execution or document edits. This review does not independently repeat the local DB/code audit.

Review lenses: binding contract consistency, scientific input/evaluation reconciliation, technical-source verification and narrow local input boundaries. Findings below are concrete gaps; no additional service, distributed infrastructure or large collection is requested.

## Findings

### 1. Supervised training labels are prohibited by the inference boundary

- **Location:** `MVP_ARCHITECTURE.md` AD-4, lines59–63; `labels.csv`, line112; runner rejection, line118. `MVP_FORECASTING_PLAN.md` splits, lines53–57; Ridge/CatBoost, lines67–68.
- **Trigger:** All runners receive only past grids/features and labels are evaluator-only, yet mandatory Ridge/CatBoost must fit direct future-delta labels. Validation labels are described as the only permitted label reads after sealing.
- **Consequence:** Either supervised controls cannot be trained, or implementation must silently bypass the very boundary intended to prevent test leakage.
- **Guard:** Separate `fit` and `predict` manifests. Fitting gets only purged development TRAIN labels and train features; validation evaluator gets only VALIDATION labels for parameter/default selection; inference gets no labels; temporal/repository TEST labels remain evaluator-only until choices freeze and predictions publish. Persist model/transform hashes, fitted forecast-ID set and fit cutoff. Explicitly state that retrospective supervised learning uses future outcomes from training origins whose label window ends before validation.
- **Evidence:** The contradictory requirements are in the two reviewed documents. CatBoost officially exposes supervised fit/training and prediction as different operations. [CatBoostRegressor](https://catboost.ai/docs/en/concepts/python-reference_catboostregressor), accessed2026-10-13.

### 2. Stored prediction contract cannot support promised quantile/path/clipping checks

- **Location:** `MVP_ARCHITECTURE.md` shared contracts, line114; AD-5, line69. `MVP_FORECASTING_PLAN.md` lines37,79,87.
- **Trigger:** Plan requires native forecast paths, decile mean loss, crossed-quantile checks and unclipped values/clipping rates; required `predictions.csv` stores only endpoint point, q10 and q90.
- **Consequence:** A conforming implementation cannot reconstruct q20–q80 scores, full-path charts or raw-versus-clipped diagnostics. The decile axis becomes an undocumented in-memory convention lost at publication.
- **Guard:** Add one hashed long-format `forecast_path.csv` (forecast/model/target/step/timestamp, point, point_kind, quantile_level, quantile_value, raw values or a corresponding raw artifact), or define equivalent full decile fields. Keep endpoint summary rows for UI convenience. Record exact axis conversion from Chronos `(variates,Q,H)` and TTM native output; verify point and quantile time-axis cropping before publication. Point-only baselines have quantile metrics `UNSUPPORTED`, not manufactured deciles.
- **Evidence:** Current Chronos-small includes all native deciles and its APIs return the axes recorded in [research-check](../digests/research-check.md). The reviewed plan promises information absent from the shared file schema.

### 3. The published grid cannot represent planned missing states

- **Location:** `MVP_ARCHITECTURE.md` `past_grid.csv`, line109; history route, line129; AD-1, line45. `MVP_FORECASTING_PLAN.md` lines33,35,47.
- **Trigger:** Grid enum allows only `MEASURED/REUSED_SAME_STATE`, but state construction emits `MISSING_STATE`, the history route exposes missing flags, and the sensitivity track requires genuine missing targets.
- **Consequence:** Missing states must be dropped, serialized as an invalid enum, or misrepresented as observed/reused. Dropping rows destroys the regular grid needed by Chronos.
- **Guard:** Allow `MISSING_STATE` and an exclusion reason, nullable observation ID/value, and selected revision when known. Keep serialization as CSV blank/JSON null; only the runner adapter translates null to masked NaN. Register strict/sensitivity track and missingness policy in forecast/cohort identity. Nonfinite observed values remain rejected.
- **Evidence:** Chronos requires regular timestamp rows and supports numeric missing-target masks; [research-check](../digests/research-check.md). The contradiction is in the reviewed enum, route and sensitivity protocol.

### 4. Constant training deltas need an explicit supervised-control outcome

- **Location:** `MVP_FORECASTING_PLAN.md` lines43,67–68,85,89.
- **Trigger:** A per-horizon TRAIN slice has constant deltas, including all-zero debt changes; this is possible in the deliberately retained unchanged-state population. CatBoost defaults `allow_const_label=False`.
- **Consequence:** A scientifically valid constant cohort can fail the mandatory control's fitting for an unregistered algorithmic reason, or trigger an undocumented parameter change/replacement.
- **Guard:** Preregister constant-label handling before fitting: either explicitly enable supported constant-label training or publish a distinct `CONSTANT_TRAIN_TARGET`/constant-control result, preserving original model identity and full-cohort failure/fallback reporting. Do not alter cohort membership to create target variance. Also reject empty per-horizon TRAIN labels before model launch.
- **Evidence:** CatBoost documents the constant-label option and default. [Common training parameters, allow_const_label](https://catboost.ai/docs/en/references/training-parameters/common#allow_const_label), accessed2026-10-13. This is a conditional edge case, not a claim that the new cohort is already constant.

### 5. A restricted working copy does not define the untrusted-build boundary

- **Location:** `MVP_ARCHITECTURE.md` AD-6, line75; `MVP_FORECASTING_PLAN.md` current collection/fallback, lines96–100.
- **Trigger:** An untrusted repository's Maven/Gradle/build hooks run from a copied directory in an ordinary operator process. Copying files and using argv prevents neither reading the operator's home/environment nor modifying files outside the copy. Credentialed scanning can also consume repository-controlled scanner/project settings unless overrides are enforced.
- **Consequence:** The stated boundary is not reviewable: absence of credentials in the copy does not establish absence of inherited secrets/host access or controlled scanner destination.
- **Guard:** Keep the MVP narrow: admit only explicitly reviewed local build recipes, or require a defined restricted runner with sanitized environment and disposable HOME, bounded filesystem access and an operator-fixed scanner server/project/arguments. Repository config cannot redirect credentialed scanning. If the existing wrapper lacks these guarantees, current build/scan collection stays blocked; imported V2 forecasting continues. Do not introduce a remote build service.
- **Evidence:** This is a threat-model deduction from the missing process boundary in AD-6, not an observed exploit or a claim about an existing adapter. The document itself already requires collection to block when that boundary cannot be honored; specify the minimum admission checks so that condition can be assessed.

## Checks with no finding

- Daily origins and exact30/60/90-day endpoints use UTC and86400-second spacing; 90-point inclusive context and Chronos indices29/59/89 are internally consistent. Endpoint-only scoring does not require fabricated intermediate outcomes. First-parent/committer-time retrospective availability is explicitly qualified rather than called historically online.
- Split purging,90-day validation/test embargo, separate held repositories and no random re-splitting are coherent. `T=E+90days` can erase the test phase on a short common interval, but nonempty-phase gates explicitly handle that as feasibility failure. Selection/completeness bias is disclosed.
- TTM branch SHAs,90/180/512 contexts, native30/60/96 horizons, explicit decomposed loader and mean-slot convention match freshly verified source/config evidence. Complete contexts and matched longer-context cohorts avoid the earlier padding/cohort comparison errors.
- Chronos-small's revision, native horizon, q50 convention, deciles and mask support match the digest. The16GBCPU assumption, smoke/total budgets and80% exploratory threshold are proposed operator/protocol choices, not verified resource minima or efficacy claims.
- NPF unknown licensing,21/28/91-day horizons and broader effort target are correctly separated. V2 CC BY-NC-SA4.0 and release2.0.1 metadata match primary-source verification.
- FastAPI's official static-file documentation supports the simple static dashboard. Fresh CatBoost docs support the proposed regression parameters, CPU threading and numeric NaN modes; fresh LightGBM docs expose the planned tree/leaf/learning-rate/thread controls. These API checks do not prove the legacy package lock or a new environment works. [FastAPI](https://fastapi.tiangolo.com/tutorial/static-files/), [CatBoost](https://catboost.ai/docs/en/concepts/python-reference_catboostregressor), [CatBoost NaNs](https://catboost.ai/docs/en/concepts/algorithm-missing-values-processing), [LightGBM](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMRegressor.html), accessed2026-10-13.

No imported or current-domain forecast efficacy, calibration, package-load success, hardware sufficiency, cohort sufficiency or production readiness was verified by this review. Exact local data/code/declared version claims remain attributed to the root's named audits; they were not independently reread outside the requested scope.

## Corrective recheck — 2026-10-13

Rechecked the edited binding sections of the same two documents, without expanding research or modifying them. **All five original findings are resolved at the design-contract level.** No new meaningful binding contradiction was found in this limited corrective pass.

| Original finding | Resolution verified |
|---|---|
|1 — supervised labels prohibited | AD-4 and shared label contract now distinguish phase-filtered fitting labels, validation evaluation and sealed final-test labels. Prediction subprocesses receive a past-only projected folder without the complete dataset root; trainer requests admit only hashed training-label projections. The existing purge/split rules still constrain that training set. |
|2 — incomplete prediction artifacts | `predictions.csv` now includes raw/clipped points and all deciles; `forecast_path.csv` supplies step/timestamp/raw/decile data. Endpoint quantile evaluation is explicitly independent of intermediate actual availability. Optional native path storage does not manufacture missing ground truth. |
|3 — missing states unrepresentable | `past_grid.csv` now allows `MISSING_STATE`, nullable selected revision/observation/value and reason. The strict cohort still rejects missing historical states; null serialization remains separate from the adapter's masked-NaN representation. |
|4 — constant supervised training | Forecast plan preregisters explicit constant-target and constant-feature fallbacks with retained assigned cohort, instead of dropping records or silently changing CatBoost options. These statuses keep fallback behavior distinguishable from ordinary model fitting. |
|5 — untrusted-build boundary undefined | AD-6 now specifies a pinned rootless/non-root restricted build runner, read-only source/private output/cache, no host-home/socket mounts or inherited secrets, disabled build networking and resource limits. Credential-free dependency fetch is separate; trusted scanner settings force destination/project/revision/scope and token-bearing phases prohibit source-controlled commands. Unsupported local execution remains blocked. |

The added deterministic target/forecast/request/split/model identities preserve endpoint horizon identity while grouping a shared core90 model request. Tree-sitter Java extraction is a source-only syntactic choice with pinned grammar/API, immutable blob coordinates and error/encoding/token-limit abstention; it does not claim GraphCodeBERT weight permission, validated label mapping, compiler correctness or a semantic graph. The root reports checking its linked official documentation; this corrective pass checks contract reconciliation and does not independently repeat that new web read.

Resolution means the proposed specification now states the required behavior. File projections, schemas, missingness conversion, fallbacks, restricted execution and parser outputs still require future implementation/verification; no runtime security or forecasting efficacy claim is added.

## Final data-only masked-fallback check — 2026-10-13

The new masked90 fallback in AD-5/AD-7 and the forecasting plan is scientifically coherent as a proposed limited-data study: choose the primary track from data availability before inspecting model outputs, reapply G2, retain exact observed endpoint labels, use one regular90-point calendar grid, keep masks/nulls, compare controls on the same cohort and do not pool complete/masked/TTM tracks. TTM remains restricted to complete contexts. The80% known-history/window and24-of30 trend thresholds are explicitly proposed/preregistered; upstream mask support does **not** validate those cutoffs, accuracy or interval coverage. Shared-state reuse counts as known state but not independent measurements, and the existing distinct-revision reporting preserves that qualification.

Two small cross-document seams remain in this snapshot:

1. The forecast plan's fixed-feature paragraph still states globally that “complete target context remains required.” Scope that clause to core90 and TTM, with the explicit masked90 rules as its exception, so an adapter does not reject the newly admitted primary fallback.
2. The architecture's required `features.csv` projection omits the masked plan's known-grid fraction and feature-availability flags. Add those track-specific fields, or reference a hashed/versioned feature schema carrying them, so the stored runner request reproduces the registered masked baseline information budget.

No additional research or document edits were performed. This is a specification consistency check, not an executed feasibility/model test.

Roadmap spot-check: `MVP_IMPLEMENTATION_ROADMAP.md` M1 fallback and M2 inputs reflect the same data-only masked-primary decision; M3 keeps TTM on complete native matched cohorts. No contradictory roadmap fallback was found.

## Final author reconciliation

Both remaining masked-track seams were corrected: the complete-context requirement is explicitly limited to core90/TTM, and the architecture feature contract includes track/policy hashes plus masked known-grid fraction and availability flags. This records the applied author fixes; it does not claim new model execution or an independent runtime check.
