# Phase 3: real baseline forecasting results

Source: The Technical Debt Dataset V2, release 2.0.1; Valentina Lenarduzzi,
Nyyti Saarimäki and Davide Taibi (2019):
https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1

Transformed measurements and derived results retain attribution and CC BY-NC-SA
4.0 terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: statistical baseline predictions and evaluation on the unchanged Phase 2
primary cohort. All inputs, models, exact horizons and seals are recorded.

- `baseline_metrics.csv`: all 1,485 actual paired metric rows, including per-repo,
  split and changed/unchanged cases. Macro and pooled errors are separate.
- `baseline_comparison.png`: test macro MAE/RMSE and 95% repository-bootstrap bands.
- `baseline_predictions_sample.csv`: 108 selected real predictions; first three
  forecast hashes per phase/horizon, all three models. Not a new test cohort.
- `selected_parameters.json`: validation-only search scores, selected windows,
  validation IDs and frozen persistence champions.
- `study.json`, `run_audit.json`: registered protocol/environment/input/code hashes
  and ordered leakage-prevention events with full cohort coverage.
- `candidate_seal.json`, `prediction_seal.json`: original local seal receipts.
  Full prediction files referenced by these seals are deliberately not uploaded.
- `full_output_hashes.json`: original full local COMPLETE manifest, not a portable
  full-run bundle. Reproduce its large predictions locally using the report.
- `determinism.json`: all eleven final/repeated result files are byte-identical.
- `regression_tests.xml`, `working_regression_tests.xml`: permitted compatibility
  checks in both checkouts; actual CatBoost training test excluded.
- `repeat_resources.txt`: measured 17.65-second CPU replay, about 257 MiB peak RSS.
- `manifest.json`: checksums of the published small artifacts only.

Read [the implementation report](../../PHASE_3_IMPLEMENTATION_REPORT.md) for
numerical results, reproduction commands, independence/provenance limits and
Phase 4 readiness. No pretrained models, CatBoost or dashboard ran in Phase 3.
