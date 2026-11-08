# Benchmarked forecasting error summary

Forecasts are continuous debt estimates. MAE and RMSE are in estimated maintainability remediation minutes; lower is better. There is no single classification-style accuracy percentage. Relative skill below means percentage MAE reduction versus persistence, not percentage predictions correct. Negative skill means worse error.

These calculations use existing published aggregate records only. They do not replay models, open raw historical labels, mix synthetic and historical populations, or alter frozen results.

Historical Java: temporal test

| Model | MAE30d | MAE60d | MAE90d | 90d RMSE | 90d MAE reduction vs persistence |
| --- | ---: | ---: | ---: | ---: | ---: |
| Persistence | 50.326 | 98.710 | 148.708 | 193.167 | +0.00% |
| Rolling mean | 52.421 | 100.877 | 150.829 | 194.667 | -1.43% |
| Anchored trend | 82.530 | 149.871 | 189.166 | 223.497 | -27.21% |
| Chronos-2 Small (90 context) | 58.889 | 108.426 | 157.478 | 194.030 | -5.90% |

Historical Java: held-out repositories

| Model | MAE30d | MAE60d | MAE90d | 90d RMSE | 90d MAE reduction vs persistence |
| --- | ---: | ---: | ---: | ---: | ---: |
| Persistence | 179.599 | 327.941 | 470.252 | 680.717 | +0.00% |
| Rolling mean | 186.347 | 332.544 | 474.380 | 675.044 | -0.88% |
| Anchored trend | 280.616 | 520.099 | 775.956 | 981.012 | -65.01% |
| Chronos-2 Small (90 context) | 227.886 | 392.762 | 541.636 | 732.360 | -15.18% |

Synthetic development: Phase6.1B matched36 cases

| Model | MAE30d | MAE60d | MAE90d | 90d RMSE | 90d MAE reduction vs persistence |
| --- | ---: | ---: | ---: | ---: | ---: |
| Persistence | 98.920 | 171.631 | 239.224 | 1251.304 | +0.00% |
| Rolling mean | 120.812 | 193.337 | 261.116 | 1381.137 | -9.15% |
| Anchored trend | 13.466 | 39.552 | 65.551 | 259.360 | +72.60% |
| Chronos-2 Small (512 context) | 22.570 | 34.208 | 54.269 | 188.462 | +77.31% |
| Granite TTM (512 context) | 212.196 | 344.339 | 434.386 | 2377.582 | -81.58% |
| TimesFM 2.5 | unavailable | unavailable | unavailable | unavailable | unavailable |

Historical metrics are repository-macro; synthetic RMSE is pooled across cases. Historical Chronos rows retain its published complete-coverage fallback policy (4 temporal and2 held-out contexts), not a claim that every path was native. Persistence has the lowest historical MAE at all three horizons.

Synthetic rankings depend on the chosen generators and scales. Three mixed-scale cases heavily affect raw errors; normalized and excluding-mixed-scale results remain in the Phase6.1B report. These are not real-world improvement claims.

TimesFM2.5 now has evidence of one low-memory native return, but its full-decile smoke path failed ordering. No36-case TimesFM benchmark was run; do not calculate a comparable accuracy from a rejected single case.

Full machine-readable rows, source hashes and calculation policy: `examples/phase6_1c/benchmark_accuracy_summary.csv` and `accuracy_calculation_receipt.json`.
