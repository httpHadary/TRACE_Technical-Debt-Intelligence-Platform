# Adaptive Persistence uncertainty and identifiability

SYNTHETIC_ENGINEERING_TEST. Derived calibration-only intervals, not native model
quantiles. Point selection is frozen before180 calibration cases per replication
are opened. The80th empirical quantile of normalized absolute error sets symmetric
radii; final stock interval is truncated atzero. No test residual widens intervals.
The independent auditor verifies every radius/point-derived endpoint and seal.
The nominal80% diagnostic target is75–85% coverage with normalized mean width<=1.
This target is NOT met consistently. No coverage guarantee is asserted.

Ranges below cover all three seeds and three horizons in each cell.

| Population | Policy | Coverage range | Normalized mean width range |
| --- | --- | --- | --- |
| test | adaptive_local | 72.50–80.83% | 0.211–0.329 |
| test | adaptive_stress | 70.83–81.25% | 0.315–0.740 |
| unseen | adaptive_local | 72.92–80.83% | 0.211–0.329 |
| unseen | adaptive_stress | 72.08–82.92% | 0.315–0.740 |
| hidden | adaptive_local | 44.58–60.42% | 0.211–0.329 |
| hidden | adaptive_stress | 64.58–82.92% | 0.315–0.740 |
| reversed | adaptive_local | 49.17–69.58% | 0.211–0.329 |
| reversed | adaptive_stress | 70.83–81.25% | 0.315–0.740 |
| delayed | adaptive_local | 52.50–79.17% | 0.211–0.329 |
| delayed | adaptive_stress | 70.83–81.25% | 0.315–0.740 |

The delayed-signal policy correctly abstains, but its residual calibration remains
based on origin-available calibration signals. Coverage therefore deteriorates
under the missing-information intervention. That mismatch is a useful failure,
not a reason to recalibrate using final labels. A future conditional missingness
calibration study needs its own development evidence and registration.

Hidden/reversed mappings break local AP's point relationship and residual law.
Stress-selected persistence has wider intervals in this construction, but still
misses the target in some cells. Coverage must be reported together with widths,
interval scores, conditional changed/unchanged coverage and collapsed counts.
See intervals.json for all methods/horizons/seeds and these diagnostics.

## What can and cannot be predicted

The mathematical control shows a bound for specified finite worlds: current debt
minimizes total absolute error for balanced identical-history outcomes c−a,c,c+a.
A reflected future relationship can share EXACTLY the same request with an opposite
optimal action. The auditor verified34,560 equal forecast pairs across hidden and
reversed worlds. No origin-only algorithm can choose different predictions for
indistinguishable inputs, so an invisible first shift cannot be guaranteed safe.
This does not prove universal unpredictability or make persistence always optimal.
The signed channel improves under its constructed stable relationship, confirming
that additional information can matter when the assumptions actually hold.

Predicting event probability can still be useful when persistence is the optimal
point median. Event-before-h and endpoint-change differ when stock returns to its
origin. This study estimates endpoint-direction frequencies only. Calibration,
drift detection, and model uncertainty cannot manufacture a missing leading signal.
Online updates must wait for each horizon's genuinely available realized label.

Literature context: [Gneiting2011](https://www.bundesbank.de/resource/blob/635562/7d3de0f3fc003e5b4864828143f268cf/mL/2012-06-01-eltville-11-gneiting-paper-data.pdf)
aligns medians with absolute loss; [Gibbs/Candès2021](https://arxiv.org/abs/2106.00170v3)
studies online long-run coverage adaptation. Neither supplies real feature validity,
immediate conditional coverage, or permission to use restricted analyzer outputs.
