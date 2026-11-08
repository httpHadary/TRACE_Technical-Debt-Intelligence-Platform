# Phase 2 dataset and split evidence

Source: The Technical Debt Dataset, Version 2, release 2.0.1; Valentina
Lenarduzzi, Nyyti Saarimäki and Davide Taibi (2019):
https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1

The transformed measurement sample and derived data audit retain source
attribution and **CC BY-NC-SA 4.0** terms:
https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: exact archived first-parent state selection at UTC cutoffs, conservative
chronology/profile exclusions, measured 30/60/90-day stock/delta labels,
complete/masked context diagnostics and purged calendar/repository assignments.

- `forecasting_dataset_sample.csv`: 16 deterministic illustrative examples,
  two earliest rows per track/horizon. Not a random or evaluation cohort.
- `forecasting_feasibility.json`: full per-repository/horizon admission,
  rejection/missingness/independence diagnostics and recorded policies.
- `forecasting_splits_summary.json`: frozen boundaries/repository IDs/counts;
  large per-example assignments are omitted with their count and full-file hash.
- `full_output_hashes.json`: hashes of the original full local bundle, whose
  large files are deliberately unuploaded. It is not a portable COMPLETE bundle.
- `determinism.json`: eight frozen real output artifacts repeated byte-identically.
- `target_spot_checks.json`: 16 sample labels checked against 32 raw SQL measures.
- `serialized_context_checks.json`: every serialized context checked for length,
  past-only timestamps, masks and strict-track completeness.
- `compatibility_tests.xml`: tests permitted under the no-model-execution rule.

Reproduce locally with an already acquired V2 database and verified Phase 1
bundle. No download is performed. Copy the Phase 2 config to an ignored local
file and set its absolute input/output paths, then:

```bash
python3 -m forecasting_mvp build-forecasting-dataset \
  --config forecasting_mvp/study.phase2.local.json --out /absolute/registered-root/new-run
python3 -m forecasting_mvp verify-bundle --bundle /absolute/registered-root/new-run
```

The output must be new. Full dataset, per-example splits, separate labels/features
and compressed past contexts remain local and ignored. Exit 2 indicates imported
scientific limitations even when usable research cohorts exist. No training or
inference commands are implemented. Byte comparisons require identical code,
input bytes and configuration; absolute-path configuration changes affect audits.

The sample is research data, not model predictions. Future model runners must
receive an origin-filtered past projection, never the combined dataset or label
files. Targets are rule-estimated maintainability minutes, not actual repair
labor. Imported metadata and retrospective timing remain limitations.

See [Phase 2 report](../../PHASE_2_IMPLEMENTATION_REPORT.md). Stop before Phase 3
until explicit authorization.
