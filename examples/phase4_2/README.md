# Phase 4.2: complete frozen-cohort Chronos evaluation evidence

Data: The Technical Debt Dataset V2, release 2.0.1, Valentina Lenarduzzi,
Nyyti Saarimäki and Davide Taibi (2019):
https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1
Derived sample/results retain attribution and CC BY-NC-SA 4.0 terms:
https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: frozen historical states, past-only native Chronos inference and paired evaluation.
Model-card license: Apache-2.0; no weights redistributed.

Overall PARTIAL: all registered IDs covered with explicit persistence fallback;
12/1512 native contexts rejected. Persistence remains validation-selected default.
See [actual report](../../PHASE_4_2_IMPLEMENTATION_REPORT.md).

- Complete aggregate/per-repository/stratified comparison CSVs and native-success-only paired controls.
- Native interval diagnostics, including attempted/native/fallback denominators and collapse.
- Comparison PNG and deterministic 45-row sample; no full context data or full predictions.
- Study, validation selection, stage prediction seals, failure/resource summaries and environment pins.
- `determinism.json`: complete run-004/run-005 deterministic file SHA-256 comparisons.
- `preservation.json`: unchanged source/requirements/frozen-bundle receipts.
- Regression XML for both checkouts; actual CatBoost training test intentionally deselected.
- `full_local_output_hashes.json` and stage `full_local_worker_hashes.json` are receipts
  referring to local full artifacts, **not** standalone published bundles.
- Root `manifest.json` verifies only published small evidence.

Replay commands and exact model/source hashes appear in the report. Paths identify
this machine; runtimes, checkpoints and full input bundles remain local. Resource
measurements differ across repeats; deterministic predictions and metrics do not.
