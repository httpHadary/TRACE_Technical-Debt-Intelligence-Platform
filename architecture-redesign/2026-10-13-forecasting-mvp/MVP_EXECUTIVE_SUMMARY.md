# TechDebt360 forecasting MVP — executive summary

Date: 2026-10-13. **Planning complete; implementation not started.** Team: two contributors at 10 hours each per week, 20 team-hours/week. Hardware remains unspecified.

Build the research core first: **audited V2 repository history → real Chronos-2 Small forecasts → measured future SQALE comparisons → compact controls → current Sonar evidence → minimal API/dashboard**. Preserve the existing module pipeline for later use. Do not start with enterprise infrastructure or autonomous remediation.

Repository forecasting is the strongest immediate direction because V2 already contains native project measurements across 31 historical projects. The actual eligible daily histories and future cutoffs still need validation. Unmeasured changed commits cannot be filled with older measured debt. Imported V2 results and a current Sonar repository have different measurement domains; the dashboard must make that distinction visible.

Audit complete 90-day grids first. If they cannot admit the preregistered repository/split gate, freeze a limited-data `masked90` primary track before any model outcomes: at least 80% known daily history, a known origin and exact observed future measurements. Chronos and the simple controls use the same admitted cohort and explicit missingness policy. TTM remains a separate complete-context comparator. The default comes from the registered primary track; histories or results from different tracks are never pooled.

Core models: Chronos-small, persistence, trend, Ridge and CatBoost. Evaluate Granite TTM 30 first when 90 daily contexts exist; TTM 60 needs 180 and TTM 90 needs 512 daily past points. Do not require all models in normal runtime. GraphCodeBERT is a separate optional Java debt-type annotation layer, conditional on checkpoint permissions/contracts; it is not a debt-minute estimator. Forecasting remains the primary research feature even if a simple baseline wins.

The implementation order and effort are fixed in the [roadmap](MVP_IMPLEMENTATION_ROADMAP.md):

1. M0 freeze inputs and resources: 4–6 hours.
2. M1 publish audited historical dataset and purged splits: 24–36 hours.
3. M2 obtain real pretrained predictions and validation MAE/RMSE: 16–24 hours.
4. M3 compare debt-specific/TTM controls and execute frozen final evaluation: 20–28 hours.
5. M4 collect current Git/Sonar evidence and feasible GraphCodeBERT annotations: 20–28 hours.
6. M5 build one read-only local API/dashboard: 24–32 hours.
7. M6 verify reproducibility and prepare demonstration/report: 8–12 hours.

Total **116–166 contributor-hours**, 14.5–20.75 eight-hour person-days. With 20% contingency: **139–199 hours, approximately 7–10 weeks** at the stated capacity. First real forecasting results and the comparative core take 64–94 hours before contingency, approximately 4–6 weeks including reserve. A 4–6 week promise for every platform feature is optimistic; those weeks should prioritize measurable research results. These estimates include ordinary peer review; substantial collection/build repair, external permission waits and new hardware add time.

Success is real, reproducible forecasts compared with later measured values, reporting MAE/RMSE, baseline improvement, native 80% interval coverage, failures, independent repository/time counts and limitations. A negative pretrained comparison is a valid research result. Partial horizons or blocked models must be explicitly labeled rather than advertised as a complete 90-day forecaster.

All architecture/data/API/model/milestone contracts are specified in the five companion docs. No production code/configuration/database changed, no model download or experiment ran, and no automatic coding handoff occurs. **Wait for explicit authorization before implementation.**
