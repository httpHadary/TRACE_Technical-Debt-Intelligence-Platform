# Persistence + Chronos-2 hybrid: fixed-grid diagnostic results

Date: 2026-10-30, Africa/Cairo.

**Decision: do not adopt the hybrid as the MVP default.** None of the three registered interior blends beats persistence on the primary repository-macro MAE at any of the three horizons. Keep persistence as the default reference and Chronos-2 as the standalone research comparison.

## Population and evidence role

Reused the sealed full history-only Chronos-2 and persistence forecasts from the completed total-principal experiment. There are 226 origins from Commons IO (162), Java-WebSocket (21) and Retrofit (43), with 678 paired endpoints. Forecast horizons are 3/4/12 distinct measured revisions, not days. Target: native maintainability + reliability + security estimated remediation minutes.

This is **EXPOSED_RETROSPECTIVE_DEVELOPMENT_ONLY**, not fresh validation or untouched confirmation. The origins overlap within repositories. No confidence or unseen-project superiority claim is made from three previously exposed families. The diagnostic can reject adoption of these tested candidates; it cannot prove no other hybrid could ever help.

## Registered comparison

Formula: `P + alpha * (C - P)`, where `P` is origin-stock persistence and `C` is the admitted nonnegative Chronos q50. Frozen weights: 0, 0.25, 0.50, 0.75, 1. Endpoints are the two standalone controls. No continuous search, per-project weighting, learned gate, new covariates, fine-tuning or checkpoint change was added.

The protocol was saved and all 3,390 candidate/control endpoint records were sealed before numerical actuals were opened by the scoring process. Earlier exposure is explicitly retained; sealing does not restore an untouched evaluation population.

## Primary result

All figures below are equal-repository macro MAE in estimated remediation minutes. Smaller is better. All five rows at each horizon use the exact same 226 origins.

| Chronos weight | Persistence weight | 3 revisions | 4 revisions | 12 revisions |
|---|---|---:|---:|---:|
| 0% | 100% | 104.420724 | 135.550811 | 384.541132 |
| 25% | 75% | 104.421082 | 135.864219 | 386.324597 |
| 50% | 50% | 106.164367 | 137.641740 | 394.452557 |
| 75% | 25% | 109.028210 | 141.810245 | 405.221322 |
| 100% | 0% | 112.585056 | 146.932124 | 417.565178 |

The best interior blend on these exposed data is 25% Chronos at every horizon. It reduces error relative to standalone Chronos, but not relative to persistence:

| Horizon | 25% blend minus persistence MAE | Change in error vs persistence |
|---|---:|---:|
| 3 revisions | +0.000358 minutes | +0.000343% |
| 4 revisions | +0.313408 minutes | +0.231210% |
| 12 revisions | +1.783465 minutes | +0.463790% |

The 3-step difference is only 0.000358 minutes in macro MAE, effectively a numerical near-tie in practical terms, not a demonstrated improvement. Persistence has the smallest grid MAE and is also the smallest weight within the preregistered 1% tie band at every horizon. Alpha zero is persistence, not a successful hybrid. No interior weight approaches the proposed 10% improvement over both bases.

## Why the blend did not win

Chronos helps some cases, but its gains do not offset errors elsewhere under the frozen objective. The following are paired per-origin comparisons, not independent replication counts:

| Horizon | Chronos lower absolute error | Chronos higher absolute error | Actual strictly between the two points |
|---|---:|---:|---:|
| 3 revisions | 75 / 226 | 151 / 226 | 34 / 226 |
| 4 revisions | 76 / 226 | 150 / 226 | 36 / 226 |
| 12 revisions | 79 / 226 | 147 / 226 | 54 / 226 |

The 25% blend improves macro error on actual-increase subgroups but worsens it on actual-decrease subgroups at all three horizons. It falsely moves on every stable endpoint (27/17/2 cases), where persistence is exactly correct. The two 12-step stable cases belong to Commons IO and provide very limited subgroup support.

Per-repository effects vary: the 25% blend improves Java-WebSocket MAE at 3/4 steps but worsens both other repositories; at 12 steps it modestly improves Commons IO while worsening the other two. These descriptive exceptions cannot override the frozen full-population objective or justify selecting a project-specific weight after scoring.

Detailed pooled MAE/RMSE, normalized error, bias, per-repository and changed/stable/increase/decrease/large-change summaries are retained in the local run. No hybrid interval was manufactured. All source Chronos paths succeeded; there are zero runtime fallbacks, so the negative outcome is not a fallback disabling cooperation.

## Verification and adoption gates

- All 146 files listed by the original artifact manifest and the original request/prediction seals match. The original result archive identity matches its previous audit.
- All 678 persistence/Chronos identities, origin stocks, scales and endpoint memberships match.
- Both standalone endpoint MAEs reproduce the six original method/horizon metrics.
- A separate arithmetic implementation and the unchanged pure numerical helper agree on 90 metric checks across 15 grid/horizon groups.
- The scoring run preserved 147 source files and all 1,550 snapshotted repository files; later publication intentionally adds this report/evidence and updates status documents.
- No neural package, checkpoint, new inference, model training, installation, cloud upload, rescan or consumed-run replay was used.

No fresh validation/confirmation was performed. Promotion is disallowed both because the registered interior candidates do not improve the primary objective and because the fresh-evidence gates are unmet. This is sufficient to stop this bounded diagnostic without expanding its weight grid or opening another model study.

## MVP action

Retain persistence as the MVP default; retain Chronos-2 as a visible independent comparison. Preserve the proposed hybrid and this negative diagnostic as research evidence, without integrating a hybrid deployment policy. Resume the evidence bridge/read-only MVP work under the existing plan. A different future hybrid would require a new hypothesis, separate registration and fresh evidence; it is not authorized or implemented by this result.

Public-size receipts are in `examples/hybrid_principal/`. The local reproducible scripts, sealed candidate predictions, complete metrics, source/repository preservation snapshots and decisions are under `/home/hp/tst/research/forecasting_mvp/hybrid_principal/2026-10-30/`. Raw per-origin data remain in that local research directory, outside the small published evidence folder.
