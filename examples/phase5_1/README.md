# Phase 5.1 evidence

Real source audits and metadata only. No real pilot measurements, model results
or synthetic real-world evidence are included. Software fixtures live in tests.

- `legacy_source_audit.json`: full raw-table, numeric/missingness and language counts.
- `legacy_identity_audit.json`: exact-join reference coverage; all candidates remain legacy/quarantined.
- `churn_diagnostics.json`: 10 conflicting +10 clean hash-selected keys across three projects, with authoritative existing-object first-parent diffs. Basenames are not automatically full paths. F2 is disabled.
- `pilot_and_source_readiness.json`: bounded local search/exposure counts and the three unfilled development targets. This is not a reserved cohort.
- `verification.json`: final tests, frozen-artifact preservation and reproducibility.
- `manifest.json`: hashes of these small files and the implementing code.

The original Technical Debt Dataset V2 release 2.0.1 was published by its
contributors: https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1
Its research data are licensed
CC BY-NC-SA 4.0: https://creativecommons.org/licenses/by-nc-sa/4.0/ . The three
legacy-derived audit JSONs retain those terms and attribution. These are new
quality/identity audit summaries, not a repackaged database. This notice does not
license or relicense the application's source code or third-party repositories.

Zenodo ND-licensed raw rows and unknown-license NPF data are not distributed.
Only source/availability metadata and exclusions appear in the readiness summary.
No raw emails, credentials, model weights, environments or full datasets appear.

Full reproduction instructions and scope limits:
[implementation report](../../PHASE_5_1_IMPLEMENTATION_REPORT.md) and
[package contract](../../forecasting_multilanguage/README.md).
