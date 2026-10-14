# Phase 2.1 frozen-dataset validation evidence

Source: The Technical Debt Dataset V2, release 2.0.1; Valentina Lenarduzzi,
Nyyti Saarimäki and Davide Taibi (2019):
https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1

The transformed sample and derived diagnostics retain source attribution and
CC BY-NC-SA 4.0 terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: deterministic stratified validation and descriptive independence counts
on the existing frozen Phase 2 archive-state dataset. No predictions or new labels.

- `dataset_validation.json`: all structural checks, original hashes, implementation
  hashes, 559 independent raw-SQL checks, sample coverage and readiness limits.
- `raw_sql_validation_sample.csv`: all 559 selected audit examples, with original
  unchanged labels/IDs/split groups. Stratified audit sample, not a new test cohort.
- `dataset_quality.json`: all 64 track/horizon/split and 870 per-repository cells,
  unchanged/changing-debt statistics, distinct measures/context diversity, overlap
  and cross-split reuse. Effective independent sample size is unknown.
- `manifest.json`: COMPLETE checksummed evidence bundle for the three data files.
  README, test XML and determinism receipt are supplementary, outside its manifest.
- `regression_tests.xml`: 268 passing tests, one actual-training test deselected.
- `working_regression_tests.xml`: the same passing suite in the original project.
- `determinism.json`: byte equality of the final two full audits of frozen inputs.

Read [the report](../../PHASE_2_1_VALIDATION_REPORT.md) for commands, interpretation,
source limitations and the strict model-input admission boundary. Original full
Phase 2 artifacts and the 1.5 GB SQLite database are excluded from GitHub.

Phase 2.1 integrity PASS does not establish model efficacy or complete historical
analyzer invariance. Phase 3 readiness is PARTIAL; no models ran in this phase.
