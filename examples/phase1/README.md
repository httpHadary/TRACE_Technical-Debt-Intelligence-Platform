# Phase 1 historical import evidence

Source: **The Technical Debt Dataset, Version 2**, release 2.0.1, Valentina
Lenarduzzi, Nyyti Saarimäki and Davide Taibi, 2019. Original release:
https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1

The small measurement sample and derived dataset audit are attributed research
artifacts under the source's **CC BY-NC-SA 4.0** license:
https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: unique SQLite analysis/measure/revision joins, UTC normalization after
exact Git-time agreement, stable identity/profile hashes and explicit quality
flags. These are imported proxy measurements, not actual developer labor or
newly verified historical scan executions. No future labels were constructed.

Included:

- `historical_debt_sample.csv`:12 measurements, first valid historical row from
  each of the first12 sorted source projects. Not a random/evaluation cohort.
- `historical_data_audit.json`: full source/schema/coverage/ancestry/provenance
  statistics, exclusions and narrow30/60/90-day span screening.
- `full_output_hashes.json`: original full local bundle manifest for reproduction
  byte hashes. It references deliberately unuploaded large files; it is not a
  self-contained portable bundle manifest.
- `raw_spot_checks.json`:12 exact sample-to-raw-SQL checks.
- `determinism.json`: six real output artifacts repeated byte-for-byte.
- `compatibility_tests.xml`: permitted regression tests; training test excluded.

Reproduce full outputs locally from the already acquired source DB. Edit a copy
of `forecasting_mvp/study.phase1.example.json` to an ignored local configuration,
retaining the registered release source hash. From the project root:

```bash
python3 -m forecasting_mvp ingest-history \
  --config forecasting_mvp/study.phase1.local.json --out /absolute/registered-output/new-run
python3 -m forecasting_mvp verify-bundle --bundle /absolute/registered-output/new-run
```

Use a new output directory. Exit 2/PARTIAL is expected for the source's documented
blank analysis keys and chronology/provenance gaps; inspect the audit. Exit 3 is a
source/config/publication error. No data are downloaded by these commands.

The full `historical_debt.csv`, `git_history.csv`, exclusion details and1.5 GB DB
stay local and are ignored by Git. Do not compare audit byte hashes after changing
configuration paths, source bytes or implementation hashes; CSV rows are stable
for the same source/code policy, but the audit intentionally records configuration.

See [Phase 1 report](../../PHASE_1_IMPLEMENTATION_REPORT.md). Phase 2 readiness is
conditional on a later exact-context/endpoint audit; no accuracy is established.
