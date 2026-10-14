# Phase 4.1: bounded real Chronos CPU smoke evidence

Data source: The Technical Debt Dataset V2, release 2.0.1; Valentina Lenarduzzi,
Nyyti Saarimäki and Davide Taibi (2019):
https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1

The six transformed past-context samples and derived outputs retain attribution
and CC BY-NC-SA 4.0 terms: https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: past-only training/validation selection and native Chronos smoke inference.
Model-card license: Apache-2.0; pinned model weights are not redistributed here.

- `requests/`: COMPLETE six-context past-only request bundle. No label values;
  all three exact horizon identities in each training/validation context.
- `results/`: COMPLETE final worker bundle with 18 q50 endpoint predictions,
  540 daily q10/q50/q90 path rows, raw/clipped outputs and runtime/determinism report.
- `checkpoint_admission.json`: immutable model/config/card hashes and license evidence.
- `runtime_admission.json`, `pip_check.txt`: isolated CPU package versions/admission.
- `smoke_resources.json`, `worker_log.txt`: bounded final successful run and resource data.
- `preservation_and_resources.json`: old-lock/Phase 3 integrity and host capacity.
- `determinism.json`: exact two-repeat paths, fresh-worker CSV equality and
  byte-identical repeated preparation; timings are not claimed reproducible bytes.
- `regression_tests.xml`, `working_regression_tests.xml`: allowed regression suites
  in both checkouts; the actual CatBoost training test is excluded.
- Root `manifest.json`: checksums of published small evidence only.

[Implementation report](../../PHASE_4_1_IMPLEMENTATION_REPORT.md) contains actual
resource use, corrected UTC DataFrame compatibility, install/download/replay
commands and limitations. Only six train/validation contexts were inferred.
No test-cohort inference, accuracy evaluation, tuning or final benchmark occurred.
