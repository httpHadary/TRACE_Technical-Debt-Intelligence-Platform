# Chronos-2 120M total-principal Kaggle results

Date: 2026-10-29 (Africa/Cairo).

**Execution and artifact audit: PASS. Forecasting improvement over persistence: NOT DEMONSTRATED.** All preregistered alternatives have higher repository-macro MAE than persistence at all three revision-step horizons. Normalized results also favor persistence. No model is promoted from these exposed evaluation outcomes.

Target: native retrospective SonarQube total principal = maintainability + reliability + security estimated remediation effort, in minutes. This is NOT actual developer effort, all technical debt or architectural risk. This is the first completed full Chronos-2 experiment on this target in this research sequence; earlier full/Small results concerned maintainability-only SQALE and must not be pooled.

## Exact population and clock

226 origins across Commons IO (162), Java-WebSocket (21) and Retrofit (43); 678 unique source-state endpoints. All six methods share these cases. 18 method/horizon groups and 54 method/horizon/repository groups were scored, producing 4,068 scored predictions. The origins overlap within repositories and horizons; they are not independent replications. No fitted model, hyperparameter selection or validation-selected promotion was performed.

**Horizons are 3/4/12 distinct measured revisions ahead, NOT days, calendar weeks or consecutive Git commits.** Native commit dates are date-only. The source paper labels are not operational origins. The first supplied measurement per SHA was retained, without selecting based on future outcome. Context contains 12-90 actually measured distinct source states, never padded.

| Revision-step horizon | Origins | Increases | Stable endpoints | Decreases | Elapsed native commit-date days: min / median / max |
|---|---:|---:|---:|---:|---|
| 3 | 226 | 135 | 27 | 64 | 3 / 52.5 / 326 |
| 4 | 226 | 140 | 17 | 69 | 4 / 71 / 348 |
| 12 | 226 | 150 | 2 | 74 | 45 / 236 / 744 |

All projects were already exposed in earlier development research. This is a retrospective diagnostic, not unseen-project confirmation. Eligibility requires future observation coverage through 12 steps and therefore does not represent every operational origin. The two stable 12-step endpoints are both Commons IO.

## Main forecasting comparison

All errors below are equal-repository macro MAE in estimated remediation minutes. Positive skill means lower error than persistence. No configuration was selected or altered after these scores.

| Method | 3-step MAE | Skill | 4-step MAE | Skill | 12-step MAE | Skill |
|---|---:|---:|---:|---:|---:|---:|
| persistence | 104.421 | 0.00% | 135.551 | 0.00% | 384.541 | 0.00% |
| rolling_mean_4 | 128.481 | -23.04% | 157.842 | -16.45% | 398.689 | -3.68% |
| anchored_trend_12 | 138.094 | -32.25% | 180.035 | -32.82% | 409.850 | -6.58% |
| chronos_history | 112.585 | -7.82% | 146.932 | -8.40% | 417.565 | -8.59% |
| chronos_quality | 108.976 | -4.36% | 140.819 | -3.89% | 427.071 | -11.06% |
| chronos_quality_activity | 108.981 | -4.37% | 141.845 | -4.64% | 436.928 | -13.62% |

Quality/coupling covariates improve over debt-only Chronos at 3 and 4 steps, but do not cross the persistence reference. At 12 steps both covariate variants worsen macro MAE relative to debt-only Chronos. Adding activity to quality does not improve macro MAE at any horizon. These are observed ablation results for this checkpoint/domain, not proof that the underlying signals can never help another validated model.

| Chronos variant | Normalized skill, 3 steps | 4 steps | 12 steps |
|---|---:|---:|---:|
| chronos_history | -9.09% | -9.67% | -9.69% |
| chronos_quality | -5.58% | -5.18% | -11.91% |
| chronos_quality_activity | -5.65% | -6.09% | -14.61% |

Normalization uses the origin-known history mean. Zero denominators are omitted/counted, never assigned epsilon. Persistence wins every full-population normalized comparison too.

## Changed and unchanged endpoints

Unlike the protected Combined runs, all Chronos variants predicted nonzero movement for every case. There was no safety gate forcing persistence, no model fallback and no quantile crossing. Thus this negative result is not explained by a gate disabling the model.

| Horizon | Changed n | Persistence changed macro MAE | History | Quality | Quality + activity |
|---|---:|---:|---:|---:|---:|
| 3 | 199 | 111.200 | 118.507 | 114.874 | 115.022 |
| 4 | 209 | 140.788 | 151.506 | 145.057 | 146.184 |
| 12 | 224 | 384.975 | 417.933 | 427.437 | 437.277 |

Every Chronos variant also loses the changed-endpoint macro comparison at every horizon. Predicting movement alone does not establish useful anticipation. Zero missed-change counts are a consequence of always moving, not accurate change detection.

Unchanged-case errors below are POOLED MAE within the subgroup; persistence has zero error. All Chronos variants falsely predict endpoint movement on all 27 / 17 / 2 stable cases. Stable endpoints do not imply no intermediate changes occurred.

| Horizon | Stable n | Persistence | History | Quality | Quality + activity |
|---|---:|---:|---:|---:|---:|
| 3 | 27 | 0.000 | 21.853 | 16.783 | 17.199 |
| 4 | 17 | 0.000 | 29.428 | 27.293 | 28.489 |
| 12 | 2 | 0.000 | 43.686 | 34.542 | 33.959 |

## Direction and large changes

Direction metrics below derive from point forecast signs; they are not calibrated increase/stable/decrease probabilities.

| Variant | Horizon | Increase F1 | Decrease F1 | Stable F1 |
|---|---:|---:|---:|---:|
| chronos_history | 3 | 0.576 | 0.231 | 0.000 |
| chronos_history | 4 | 0.582 | 0.240 | 0.000 |
| chronos_history | 12 | 0.625 | 0.302 | 0.000 |
| chronos_quality | 3 | 0.644 | 0.265 | 0.000 |
| chronos_quality | 4 | 0.633 | 0.270 | 0.000 |
| chronos_quality | 12 | 0.589 | 0.253 | 0.000 |
| chronos_quality_activity | 3 | 0.637 | 0.361 | 0.000 |
| chronos_quality_activity | 4 | 0.602 | 0.295 | 0.000 |
| chronos_quality_activity | 12 | 0.532 | 0.244 | 0.000 |

For the actual-decrease subgroup, every Chronos variant has worse repository-macro error than persistence at every horizon. The following direction-conditioned errors are descriptive post-run diagnostics, not new selection objectives.

| Horizon | Decrease n | Persistence decrease macro MAE | History | Quality | Quality + activity |
|---|---:|---:|---:|---:|---:|
| 3 | 64 | 149.963 | 167.537 | 160.181 | 158.391 |
| 4 | 69 | 160.577 | 186.436 | 174.318 | 172.199 |
| 12 | 74 | 323.990 | 388.622 | 384.632 | 379.642 |

There are favorable increase subgroups, but they do not establish consistent forecasting gains. At 12 steps quality-informed Chronos has 29.11% lower increase-subgroup repository-macro MAE (166.372 vs 234.703). However, Java-WebSocket contributes only ONE increasing endpoint to that equal-repository subgroup: its error falls from 272 to 9.011 minutes, while both other repositories worsen. Pooled increase MAE instead worsens from 158.333 to 175.600. This illustrates why subgroup support and aggregation must be disclosed together.

Large change remains the preregistered 10% of max(1 minute, history mean). No thresholds were altered after observing results.

| Horizon | Large increases n | Persistence macro MAE | Quality macro MAE | Large decreases n | Persistence macro MAE | Quality macro MAE |
|---|---:|---:|---:|---:|---:|---:|
| 3 | 8 | 277.500 | 260.503 | 8 | 588.667 | 593.368 |
| 4 | 12 | 302.250 | 295.469 | 11 | 585.839 | 605.052 |
| 12 | 37 | 383.787 | 330.439 | 26 | 686.994 | 764.082 |

Large-increase macro errors show some favorable results; large-decrease macro errors do not improve. These small, dependent subgroups cannot override the frozen full-population result.

## Per-repository results

| Repository | Horizon | Persistence MAE | History | Quality | Quality + activity |
|---|---:|---:|---:|---:|---:|
| commonsio | 3 | 47.728 | 58.129 | 51.771 | 52.795 |
| commonsio | 4 | 57.679 | 72.376 | 64.017 | 65.583 |
| commonsio | 12 | 104.160 | 132.007 | 122.365 | 117.840 |
| java_websocket | 3 | 183.952 | 180.271 | 179.386 | 177.852 |
| java_websocket | 4 | 244.857 | 240.985 | 236.982 | 235.696 |
| java_websocket | 12 | 752.905 | 766.381 | 810.723 | 827.813 |
| retrofit | 3 | 81.581 | 99.355 | 95.772 | 96.297 |
| retrofit | 4 | 104.116 | 127.435 | 121.458 | 124.255 |
| retrofit | 12 | 296.558 | 354.307 | 348.126 | 365.129 |

Chronos modestly beats persistence on Java-WebSocket at 3 and 4 steps. It loses on the other repositories at those horizons. At 12 steps every Chronos variant loses on every repository. There is no consistent cross-project gain. No confidence interval or real-world significance claim is made from these three exposed families.

## Native prediction intervals

Intervals are native uncalibrated q10/q90, nominal 80%. No test residual calibration or quantile sorting was performed. All 678 native paths have ordered quantiles and all interval endpoints are available.

| Variant | Horizon | Pooled coverage | Repository-macro coverage | Mean width (minutes) | Interval score |
|---|---:|---:|---:|---:|---:|
| chronos_history | 3 | 78.76% | 75.33% | 250.029 | 495.114 |
| chronos_history | 4 | 75.22% | 67.83% | 293.732 | 616.082 |
| chronos_history | 12 | 74.34% | 57.99% | 541.090 | 1444.497 |
| chronos_quality | 3 | 75.66% | 73.89% | 209.703 | 485.451 |
| chronos_quality | 4 | 72.12% | 66.39% | 251.286 | 612.429 |
| chronos_quality | 12 | 66.37% | 50.06% | 514.904 | 1485.498 |
| chronos_quality_activity | 3 | 75.22% | 73.11% | 209.565 | 495.322 |
| chronos_quality_activity | 4 | 73.01% | 66.80% | 253.551 | 623.636 |
| chronos_quality_activity | 12 | 70.35% | 51.34% | 513.257 | 1558.204 |

Pooled coverage can hide repository imbalance: history-only 12-step coverage is 74.34% pooled but only 57.99% equal-repository macro. All variants under-cover the nominal target on both aggregations. Stable cases are covered, but changed-case coverage is poorer. No calibrated reliability claim is warranted.

## Runtime and integrity

- 15 sequential workers, all exit code 0; no resource-limit termination.
- Controller-run wall time: 355.223 seconds (5 minutes 55.223 seconds).
- Sum of recorded worker CPU time: 448.289 seconds.
- Peak observed worker RSS: 970,350,592 bytes / 925.398 MiB.
- Limits stayed at 2 GiB address space, 1.75 GiB RSS guard, two numerical threads and 900 seconds per worker. Notebook/environment installation is outside that worker measurement scope.
- All 15 stderr logs contain the same nonfatal sitecustomize missing-wrapt warning. It was retained, not hidden by changing the environment.
- Archive CRC, 146 manifest-file identities, 226 exact sealed requests, bound source/checkpoint/runtime identities, 15 job populations and every chunk/final seal passed.
- 678 full native paths / 8,136 native quantile steps retained and checked.
- All 4,068 scored records match locally prepared endpoint identities and native labels.
- Independent arithmetic checks reproduce headline, per-repository, direction, subgroup, interval and skill metrics.
- All 1,321 preexisting snapshotted files remain byte-identical; source package identity is unchanged.
- No neural package imported or checkpoint loaded during audit; no local model call, rerun, training, package install, upload or retuning.

Execution receipts and matching source support prediction sealing before target parsing; they are not independent authentication of execution timing. Rights scope is the creator/operator attestation, not an independently authenticated external license review. Source Git ancestry, raw scan/build authenticity and historical operational feature availability remain unverified. All 24 Phase C decisions remain unchanged.

## Conclusion

The first total-principal run completed correctly, but it did not improve full-population forecasts over persistence. It demonstrates actual Chronos movements and limited covariate benefits at shorter revision horizons, alongside worse decrease forecasts, unnecessary movement on stable endpoints, and under-covering intervals. Do not promote the tested variants or reinterpret this as exact-day or unseen-project success. Preserve this negative result before designing any separately registered next study.

Archive SHA256: `523af0b10c6dcf8847699899c1761d0117a19332cd8cc43e27550ebd35df422b`.
Code SHA256: `9fb1c96617e7c7046ec10048c9666625a591aea90c2df0083f9abcaceb131462`.
Registration SHA256: `79d46d682a4cfb28b9e3a2c12240139a1ecc3a2caf4f5b4b45aa21815e71f383`.

Private audit: `/home/hp/tst/research/forecasting_mvp/chronos2_total_principal/2026-10-29/returned-audit-1/`. This holds extracted evidence, audit script, detailed direction analysis and illustrative helpful/harmful cases. Small verification and original aggregate summaries are in `examples/chronos2_total_principal/returned_*`. Raw requests, labels, native paths and private decisions are not copied into Git.
