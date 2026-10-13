# TechDebt360 MVP — Phase 0 implementation report

Date: 2026-10-13, Africa/Cairo. Project: `/home/hp/tst/td_pipeline_module_level/td_pipeline`.

**Status: PARTIAL — the minimal foundation and dataset/software checks pass; pretrained runtime installation/loading remains unverified. Phase 1 data preparation is ready for explicit authorization. Phase 1 was not started.**

No model weights or datasets were downloaded, no model was trained, no forecasts were generated, no real scans were submitted, and no API/dashboard was implemented. Only small public model configurations and runtime source manifests were retrieved. The existing model-training test was deliberately excluded. Offline legacy collector tests use fake Sonar/Docker fixtures, not real scans.

## Completed work and new files

All changes are additive. No existing tracked or untracked source was edited. The checkout started at `2e7999ea436d49449652e6c52e9066ef2e514419`, with existing README/`.gitignore` modifications and untracked module forecasting work. A pre-change hash baseline of 68 original source/document/dependency files was captured; final comparison found **zero changed originals**. No dependency lock or package installation was changed.

| New file | Implemented Phase 0 responsibility |
|---|---|
| `forecasting_mvp/__init__.py` | Separate MVP schema namespace, version 1 |
| `forecasting_mvp/contracts.py` | Exact elapsed UTC 30/60/90-day native-project SQALE target contracts; observation identity, null/zero distinction, finite signed deltas; no scan-certification shortcut |
| `forecasting_mvp/config.py` | Validated Phase 0-only study/model configuration, immutable checkpoint revisions, source/license/path/resource contracts and config hash |
| `forecasting_mvp/io.py` | Reused strict legacy JSON/atomic publication/path checks; streaming SHA-256; COMPLETE bundle validation; tampering, traversal, symlink/schema/serializer rejection |
| `forecasting_mvp/verification.py` | Read-only SQLite integrity/schema/repository/measurement verification; installed package and hardware-resource metadata; no model imports or dataset construction |
| `forecasting_mvp/cli.py`, `forecasting_mvp/__main__.py` | Verification-only CLI: `validate-config`, `audit-v2`, `environment`, `verify-bundle`; later workflow commands are absent |
| `forecasting_mvp/study.phase0.json` | Actual source/output locations, research-use license, exact forecast horizons and pinned Chronos/TTM candidates; future 900-second smoke and 28,800-second pilot budgets |
| `forecasting_mvp/README.md` | Usage and Phase 0 boundary |
| `tests/test_forecasting_mvp_phase0.py` |35 offline foundation tests without training/inference/scans |
| `PHASE_0_IMPLEMENTATION_REPORT.md` | This report |

Evidence is stored in [the Phase 0 directory](/home/hp/tst/research/forecasting_mvp/phase0/2026-10-13): source baseline/preservation, V2 audit, additional dataset inventories/hashes, environment records, model/source metadata, test logs/JUnit and a checksummed manifest. These are verification artifacts, not training datasets or forecasting results.

The Phase 0 CLI adds small setup-verification commands; the architecture's future `audit-v2` dataset workflow is not implemented by this audit command. It currently produces a JSON audit file. No importer, grid/label builder, model adapter, split builder, evaluator or serving feature was created.

## Existing-code audit and reuse decisions

The MVP architecture/roadmap, forecasting/experiment plans and source-backed reuse digest were consulted, then the relevant source/functions were re-inspected.

| Existing source | Decision and caveat |
|---|---|
| [contracts.py](contracts.py:13) | **Reused directly:** numeric validation, strict duplicate-key JSON, stable digest, safe IDs/relative paths, atomic JSON/CSV writes. Large dataset hashes use a new streaming wrapper rather than reading 1.5GB into RAM. |
| [forecasting/git.py](forecasting/git.py:10), [compute_project_git_features.py](compute_project_git_features.py:52) | Preserve/reuse later: immutable Git reads and ancestral activity concepts; no new Git miner implemented in Phase 0. |
| [scan_snapshot.py](scan_snapshot.py:112), [sonar_evidence.py](sonar_evidence.py:151) | Preserve collector locks, exact CE/analysis/revision proofs, paginated export and completion markers. No real server call or scanner execution occurred. |
| [compute_project_sonar_features.py](compute_project_sonar_features.py:98) | Replace matching in the future MVP track: absolute-nearest timestamps, missing-to-zero conversion and mixed SQALE/reliability/security effort are unsuitable exact-calendar ground truth. |
| [build_project_dataset.py](build_project_dataset.py:19) | Preserve legacy behavior; future MVP labels must replace row shifts with exact calendar state cutoffs. |
| [forecasting/schema.py](forecasting/schema.py:54), module dataset/identity/graphs | Preserve existing module exact 90/approx 91,26-week context and source/population contracts; do not relabel them repository 30/60/90. |
| [forecasting/evaluation.py](forecasting/evaluation.py:88) | Reuse purging/cohort/baseline/metric concepts later; unchanged now. Existing CatBoost model-fitting test excluded under the user's no-training restriction. |
| CMR90 SQLite/experiments and local NPF/file marts | Retain as prior research. Corrective-event classification, all-issue effort, file proxies and native maintainability stock are different targets. |

The broader [component disposition inventory](/home/hp/tst/architecture-redesign/2026-10-13-forecasting-mvp/digests/code-reuse.md) remains applicable. No collector behavior, legacy horizon, existing configuration or dataset was modified.

## Verified dataset availability

### Technical Debt Dataset V2

Local file: `/home/hp/TECH_DEBT/td_V2.db`,1,542,533,120 bytes. Source: [official release 2.0.1](https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1); local official README inspected. Dataset license: CC BY-NC-SA 4.0, recorded for research use and future attribution/export constraints.

SHA-256:

```text
8eb329e5e5690b884b98df824c4b94fc7582c5d610fa3bd12784b1e417b2684e
```

The audit used SQLite URI `mode=ro`, `query_only=ON`, full `PRAGMA integrity_check`, required-column checks and streamed hashes before/after. **Integrity result: `ok`; hashes identical.**

| Check | Actual result |
|---|---:|
| Repositories with project measurements |31 |
| `GIT_COMMITS` |153,994 |
| `SONAR_ANALYSIS` |67,550 |
| `SONAR_MEASURES` |66,711 |
| Joined analysis/measure/Git records |66,711 |
| Blank analysis keys |839 |
| Duplicate measure/Git/nonblank-analysis key groups |0/0/0 |
| Valid finite nonnegative `SQALE_INDEX` measurements |66,711 |
| Missing/invalid SQALE values |0/0 |
| Observed zero values |31 |
| SQALE range in estimated remediation minutes |0–701,914 |

Required schemas, all repository IDs and per-repository counts/time ranges are in [v2_audit.json](/home/hp/tst/research/forecasting_mvp/phase0/2026-10-13/v2_audit.json). The 839 blank-key analyses cannot serve as measured joins. Integrity/measurement checks **do not establish** enough independent origins, valid mainline availability, compatible analyzer history or future 30/60/90 labels. These remain Phase 1 work. Historical dataset dates are not verified execution/online availability. SQALE minutes remain rule-estimated maintainability effort, not actual developer labor.

### Other local sources

All listed CSVs were streamed for headers/row counts and SHA-256; none were rewritten. These are inventory findings, not target admission.

| Source | Verified local availability | Limits |
|---|---|---|
| `/home/hp/tst/combined_td_mart.csv` |1,327 rows;1repository,`nltk`;1,228,238 bytes; consistent row widths | A local NPF-style subset, not evidence of the complete public [NPFDataSet](https://huggingface.co/datasets/MaramAllah/NPFDataSet). Public source/reuse permission and subset provenance unresolved. Its weekly-named TD fields do not establish exact durations, units or independent future measurements; this is not an admitted Java repository SQALE cohort. |
| `/home/hp/TECH_DEBT/4534110/*.csv` |18 CSV files,2,240total rows, including 209benchmark repository rows; correct semicolon parsing | Date-based series/benchmark records need cadence, source, scope and license admission; do not count benchmark rows as independent histories. File-level schemas/hashes recorded. |
| `TDPSN-main/dataset_final.csv` |16,907 rows with process/code/network features | No repository/time identity in inspected header; not ready calendar forecast labels. |
| `Same_Data_Target_Mart.csv` |15,981 rows across 10repositories | File proxy mart; prior audit found mixed 90/91/92-day endpoints and repeated states. No new forecast labels created. |
| Kafka `npf90_features.csv` / `npf90_labels.csv` |3,718feature and 3,736label rows | One retained case; finding-introduction labels differ from stock forecasts and clocks require audit. |
| `cmr90_mart.sqlite` |Full integrity `ok`; origins 110,977, features 110,977, splits 664,134 | Existing corrective-event study, not future SQALE stock. |
| `cmr90_history.sqlite` |Full integrity `ok`; commits 11,169, changes 56,807, path_periods 7,758 | Prior Git/file-history evidence; not a repository forecast mart. |

Both derived SQLite files also retained identical before/after hashes. See [additional_datasets.json](/home/hp/tst/research/forecasting_mvp/phase0/2026-10-13/additional_datasets.json) for exact paths, sizes, schemas and hashes. No sealed prediction/evaluation outcomes were opened.

## Environment and model compatibility

| Resource/check | Measured finding |
|---|---|
| Python / SQLite |Python 3.12.3 / SQLite 3.45.1 |
| CPU |AMD Ryzen 5PRO5650U,6 cores/12 logical CPUs, x 86_64 |
| RAM |16,036,028,416 bytes total (~14.94GiB); latest recorded available 4,376,580,096 bytes (~4.08GiB) |
| Swap |4GiB total, almost exhausted at capture (~36MiB free); concurrent memory pressure is material |
| Free disk |29,991,505,920 bytes (~27.93GiB) on project filesystem at capture |
| CUDA/NVIDIA |No `nvidia-smi`, no `/dev/nvidia*`; system Torch reports CUDA unavailable,0 devices, no CUDA/HIP build |
| GPU |AMD integrated graphics devices exist; no usable ML accelerator demonstrated |
| Existing forecast environment |`.venv-forecast`; pytest 9.0.3, requests 2.32.5, pandas 3.0.2, numpy 2.4.4, scikit-learn 1.8.0, CatBoost 1.2.8, networkx 3.6.1 |
| Git / Java / Docker CLI |Git 2.43.0, OpenJDK 17.0.20.1, Docker 29.6.2; daemon and Sonar server not queried |
| Dependency check |`pip check`: “No broken requirements found.” |
| Pretrained packages in forecast venv |Torch,Transformers,Accelerate,Chronos,Granite TSFM,einops absent |
| System Torch |2.11.0+cpu exists separately; not copied into the forecast venv |

Resource values are snapshots, not performance or minimum-memory guarantees. [Environment records](/home/hp/tst/research/forecasting_mvp/phase0/2026-10-13/environment_forecast.json) preserve actual bytes/package versions and the absence of visible cgroup limit files; system and Torch records are separate. No CUDA inference or model loading was attempted.

Small pinned HF configurations were successfully retrieved for Chronos-small and TTM 30/60/90; config byte hashes are recorded. Candidate weights remain unloaded. Chronos checkpoint `ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a` permits native 90 steps by configuration; the study context is 90 daily points, not the model's 8192 maximum. TTM contexts are 90/180/512 daily for 30/60/90targets; the 90day branch produces 96 native steps for later cropping. This verifies metadata, not callable runtime contracts or local accuracy.

Fresh source manifests were recorded at Chronos source commit `1224fafa91e1ecd6674f5204066b159e40b5e4a1` and TTM source commit `3d92535ca4138648b9d1e2f3f1421b5dec4dc3aa`, with exact byte hashes. [Chronos requirements](https://github.com/amazon-science/chronos-forecasting/blob/1224fafa91e1ecd6674f5204066b159e40b5e4a1/pyproject.toml) admit this Python/pandas/numpy metadata. [TTM requirements](https://github.com/ibm-granite/granite-tsfm/blob/3d92535ca4138648b9d1e2f3f1421b5dec4dc3aa/pyproject.toml) require `scikit-learn<1.8`, which **conflicts with the existing 1.8.0 lock**. Both need missing pretrained packages; TTM also requires Torch>=2.10,<2.12 and Transformers>=4.57.6,<6.

Therefore keep legacy requirements unchanged and prepare an isolated model environment during a later authorized phase. Model package resolution, loadability, RAM and latency remain unverified. No Phase 0 package/weight installation was necessary for the standard-library foundation.

## Tests and reproducible commands

Run from the project root. Existing `.venv-forecast` was reused; no install commands were run.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_forecasting_mvp_phase0.py

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests \
  -k 'not test_actual_catboost_models_shared_folds_predictions_and_purging'

.venv-forecast/bin/python -m pip check

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp validate-config \
  --config forecasting_mvp/study.phase0.json

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp environment --disk-path /home/hp/tst

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp audit-v2 \
  --config forecasting_mvp/study.phase0.json \
  --output /home/hp/tst/research/forecasting_mvp/phase0/2026-10-13/v2_audit-recheck.json
```

The recheck output must not already exist. Tests are offline and use temporary fixtures. Actual results:

- New foundation: **35 passed**, 0 failed, 0.17 seconds.
- Final combined compatibility suite: **200 passed, 1 deselected**, 0 failed, 21.71 seconds. This includes 165 legacy tests and 35 new tests; counts are not added twice.
- Intentionally excluded: `test_actual_catboost_models_shared_folds_predictions_and_purging`, because it trains/predicts. No regression claim is made for that excluded test.
- Config validation: PASS; config hash `d043f48d50370525724b27b4d0e162ea0fb196f37d5046f051fe32f37cc99431`.
- Tests cover UTC/naive rejection, exact horizons, null/zero/signed values, duplicate JSON keys, config gates, immutable checkpoint IDs, path containment/symlinks, schema/serializer/status checks, bundle round-trip/tampering, read-only SQLite, missing schemas and absence of later CLI stages.

[JUnit](/home/hp/tst/research/forecasting_mvp/phase0/2026-10-13/compatibility_tests.xml) and [test log](/home/hp/tst/research/forecasting_mvp/phase0/2026-10-13/compatibility_tests.log) record final results. These tests establish software compatibility, not forecast performance or historical scientific validity.

## Problems, blockers and readiness

1. **Pretrained runtime not ready:** packages/weights absent in the selected venv; TTM conflicts with scikit-learn 1.8.0. Isolated runtime resolution and bounded loading belong to later authorized model integration; do not mutate the working legacy environment.
2. **Hardware pressure:** CPU-only execution, limited currently available RAM/swap and disk. Free resources and measure memory/latency before future model loads; no CPU speed or fit guarantee is claimed.
3. **Historical target readiness unknown:** Phase 1 must audit causal mainline states, unmeasured revisions, domains, regular/masked contexts, exact endpoints and independent purged cohorts. Measurement count is not proof of 90-day feasibility.
4. **Secondary-source limitations:** local NPF subset provenance/license and target semantics need separate admission. Source-only/file/CMR targets must not be mixed with V2 native project SQALE.
5. **BMAD project helper absent:** installed build launcher points to missing `_bmad/scripts/render_skill.py`. No setup/install was performed; this authorized Phase 0 was executed directly and narrowly. No later BMAD workflow was invoked.

**Readiness for Phase 1: YES, for read-only historical data preparation after explicit authorization**, using the verified V2 source and passing foundation. This does not authorize model loading/training, predictions or production scan admission. Phase 0 remains PARTIAL specifically for unprepared/unverified pretrained runtimes, while foundation, local integrity audit and permitted tests pass.

**STOP: Phase 0 only completed. Await explicit authorization before Phase 1.**
