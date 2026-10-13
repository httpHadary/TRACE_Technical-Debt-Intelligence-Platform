# Local evidence digest

Accessed 2026-10-13. Evidence class: own source/retained experimental artifacts, not external model efficacy. Confidence high for counted rows/source behavior; low or unknown for unreproduced real-world integration/accuracy. No scans, training, inference, builds or package installs occurred.

## Repository identity

`/home/hp/tst` has no root Git metadata. The current source Git checkout is `td_pipeline_module_level/td_pipeline`, HEAD `2e7999e` (2026-10-10), with preceding baseline `cf726ca`. No remote appeared. Existing working changes include README/.gitignore modifications and untracked forecasting code/docs/dependencies/test file. Latest separate V3 package metadata is `td360-v3` 0.15.2. Historical subject-repository mirrors and extracted package copies are excluded from application identification.

## Read-only recounts

| Population | Result | Source |
|---|---|---|
|Source-only raw snapshots|180; 10 repositories; 18 dates each|`research/td_target_selection/raw/*/*/snapshot.json`|
|Retained target mart|15,981 rows; 1,374 repository/file clusters; 120 repo-origin clusters|`research/td_target_selection/outputs/Same_Data_Target_Mart.csv`|
|Retained horizon distribution|90 days: 1,361; 91 days: 5,371; 92 days: 9,249|date subtraction on origin_date/endpoint_date in same mart|
|NPF positives|510; stale profile JSON says 738|mart vs `Same_Data_Target_Profile.json` and final NPF repair report|
|Raw-minute persistence|15,425 pairs unchanged; 8,470 zero T0 values|td0_raw_minutes_proxy/td90_raw_minutes_proxy|
|Exact raw 30/60/90/91 pairs|60/20/10/50 repository pairs; 7,972/2,719/1,361/6,651 same-path file intersections|raw snapshots, date separation; research candidates only|
|Current real module proof markers|0 discovered outside excluded runtime/vendor/test areas|non-mutating filesystem walk; matches existing Milestone 1 report|
|V2 source DB|31 projects; 67,550 analyses; 66,711 measure rows; 1,024,614 issues|read-only `/home/hp/TECH_DEBT/td_V2.db`|
|V2 missingness|839 blank analysis keys; no missing SQALE_INDEX; 31 explicit zero values|actual table reads, distinguishing 0 from null|
|V2 date-pair candidates|30/60/90/91 days: 5,840/5,356/5,513/5,694; all 31 projects|distinct observed dates with nonblank key/revision; not final valid labels|
|CMR origins|110,977; 5 repos; 1,509 repo/artifact clusters; 639 repo-origin timestamps; 461 positive rows|read-only `cmr90_mart.sqlite.origins`|
|CMR label validation|0 human-validated edges; 288 known-open future-work exclusions in summary|`label_coverage.csv`, `cmr90_dataset_summary.csv`|
|Netty workbook|138 package metrics; 1,133 dependency rows; one named snapshot; no parse-error rows listed|XLSX XML read-only, sheets PackageMetrics/Dependencies/ParseErrors|

The V2 join/profile findings were independently corroborated in [data review](../reviews/review-direction-data.md): all 66,711 nonblank analyses match Git revisions; date matches author/committer day; 66,685 measure rows have QUALITY_PROFILES. Same-day equality does not prove full timestamp/timezone or immutable branch availability semantics. Public historical analysis records are imported evidence, not newly runtime-verified own scans.

## Source reality checks

- Collector `sonar_evidence.py` validates pagination totals/IDs, exact task/project/analysis/revision, frozen profile metadata and source inventory before complete marker publication. It queries current analysis before/after export; historical issue inventories cannot be assumed.
- V3 `scan_recovery.py` binds original evidence and external CE tasks. `Live_Recovery_Availability.json` states missing original environment and 0 real CE queries; actual recovered analyses unknown.
- `forecasting/schema.py` explicitly distinguishes exact90/approx91, keeps combined effort separate, requires domain metadata and UTC cutoffs. `dataset.py` builds masked 26-week history and future label contracts; `evaluation.py` fits CatBoost under purged/grouped folds. These are implemented source routines, not validated real predictive outcomes.
- `MILESTONE1_REPORT.md` reports 166 tests on synthetic software validation, no real Sonar/training and no verified collector generation available. This audit did not rerun these tests.
- `graphs.py` is lexical source/build extraction plus co-change/contributor relations. Full compiler/Gradle resolution is not present; coverage/unresolved status is material.
- Prior continuous metrics are file-density targets, not raw-minute repository/module claims. Cross-repository persistence MAE: 3.0952; best reported learned current-Sonar ElasticNet MAE: 6.7500. CMR process-only mean AP: 0.04457 vs process + TD: 0.03634; no stronger TD signal proven.

## Audit limits

No private operator server/task state was queried. No original source/config was modified. No API/frontend implementation was found in the project-owned source inventory; absence is scoped to this workspace, not all possible external repositories. Full runtime hardware/latency and package compatibility are unmeasured. See [source hashes](../imports/LOCAL_SOURCE_HASHES.md) for preserved reads; source copies/subject mirrors are not independent cohorts.
