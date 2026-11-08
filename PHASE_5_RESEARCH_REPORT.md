# Phase 5 — Multi-language and forecasting feature readiness

Date: 2026-10-15. Baseline repository commit: `9e6606cf6fad3ab2e0c92190c10e75d3b86838c2`. Working project: `/home/hp/tst/td_pipeline_module_level/td_pipeline`.

**Phase 5 research/design PASS; multi-language confirmatory forecasting is not yet data-ready.** Extend the platform with versioned, language-neutral observations and past-only Git/process features. Start with persistence, Ridge and a small CPU CatBoost experiment only after separate authorization and data admission. Keep the original Java-project benchmark frozen and use genuinely new repository families for confirmation. Do not infer model superiority from this plan.

The strongest immediate opportunity is **feature enrichment from existing verified snapshot keys**, not another zero-shot model run. Complexity, code size and aggregate issue counts have substantial raw coverage. Churn needs reconciliation: raw change rows contain conflicting values. The shortest engineering pilot is three development repositories, one Java-dominant, one Python-dominant and one genuinely mixed Python+JS/TS project, using imported archives where available and otherwise a separately authorized bounded historical replay. This pilot is not a confirmatory accuracy study.

This phase wrote only four new planning documents. No training, inference, scans, installations, original dataset rebuilding or changes to previous code/reports took place. Read-only SQL counts and source inspection are audits, not constructed model datasets. `VERIFIED` below means the stated local/source observation was checked this run; it does not certify every candidate feature row or source timestamp for online use.

## Decision and deliverables

| Deliverable | Owns |
| --- | --- |
| [FEATURE_AVAILABILITY_MATRIX.md](FEATURE_AVAILABILITY_MATRIX.md) | Raw availability, derivability, missingness and leakage risks; exact proposed primary feature set |
| [MULTILANGUAGE_ARCHITECTURE.md](MULTILANGUAGE_ARCHITECTURE.md) | Versioned contracts, analyzer/language boundaries, state/target proofs, model-facing interfaces |
| [PHASE_5_1_IMPLEMENTATION_PLAN.md](PHASE_5_1_IMPLEMENTATION_PLAN.md) | Small implementation sequence, acceptance gates, files, effort, resource limits and stop boundaries |
| This report | Evidence, dataset comparison, new-cohort evaluation protocol, limitations and verification |

Architecture decisions are **PROPOSED**, ready for the next authorized implementation; none is claimed implemented. Measured local facts, publisher statements, proposals and assumptions are labeled separately.

## Local evidence

**[L1 — verified this run]** `/home/hp/TECH_DEBT/td_V2.db`, SHA-256 `8eb329e5e5690b884b98df824c4b94fc7582c5d610fa3bd12784b1e417b2684e`. Opened through SQLite URI `mode=ro` and `PRAGMA query_only=ON`; temporary grouping used memory. The database has no visible per-file Sonar measurement table: `SONAR_MEASURES` is keyed by project/analysis, without a component path. Existing Phase 1 output retains 66,711 measurements and 153,994 Git records; its chronology/domain limitations remain binding. Source table counts checked this run:

| Table | Rows |
| --- | --- |
| PROJECTS | 31 |
| GIT_COMMITS | 153,994 |
| GIT_COMMITS_CHANGES | 1,142,878 |
| SONAR_MEASURES | 66,711 |
| SONAR_ANALYSIS | 67,550 |
| SONAR_ISSUES | 1,024,614 |
| SONAR_RULES | 1,819 |
| JIRA_ISSUES | 61,402 |
| REFACTORING_MINER | 362,253 |
| SZZ_FAULT_INDUCING_COMMITS | 52,428 |

**[L2 — verified raw coverage]** On the 66,711 source measurement rows, `SQALE_INDEX`, `CODE_SMELLS`, `BUGS` and `VULNERABILITIES` are nonnegative numeric on all rows. NCLOC/lines/files have 26 nulls; cyclomatic and cognitive complexity have 28 nulls. `DUPLICATED_LINES_DENSITY` has 26 nonnumeric entries despite no SQL nulls. All 66,677 numeric coverage entries are zero; that does not prove historical tests were actually run or coverage imported. `TEAM_SIZE` and `BUSINESS_VALUE` have no nonnegative numeric observations. Full numeric/null counts are in the feature matrix.

**[L3 — verified churn quality blocker]** All 1,142,878 change rows have integer-parseable nonnegative additions/removals stored as **text**, and all project/commit keys resolve in `GIT_COMMITS`. There are 1,037,222 distinct `(PROJECT_ID, COMMIT_HASH, FILE)` keys. Of these, 42,113 repeat, producing 105,656 extra rows. **23,321 repeated keys disagree on additions or removals**. The audit did not deduplicate, sum, relabel or repair them. Non-merge examples prove a blanket merge exclusion is insufficient:

| Project | Commit | Path | Raw rows | Additions range | Removals range | MERGE |
| --- | --- | --- | --- | --- | --- | --- |
| org.apache:archiva | 003d5794a823d57b58ec26663fe145f31649ce31 | pom.xml | 4 | 1–33 | 0–5 | False |
| org.apache:archiva | 01666eea895dfa06917f13111bb72e391954f9b4 | pom.xml | 2 | 1–2 | 1–2 | False |
| org.apache:archiva | 023a0b4fe1c22a1af91b4e4dbf9414525cdc7ff2 | pom.xml | 2 | 0–0 | 5–6 | False |

The numbers establish conflicting records, not their cause. Future work must reconcile against a pinned first-parent Git diff or mark affected windows missing. Never use SUM/MAX/MIN as an unverified repair. Raw commit counts can still be derived from unique, admitted Git commit identities without trusting change-row multiplicity.

**[L4 — verified language evidence]** Parsed NCLOC distribution tokens using comma **or** semicolon separators and strict nonnegative integers; 26 missing distributions, no unparsed tokens after normalization. Counts are overlapping project-analysis observations, not independent projects or new forecasting examples:

| Language key | Positive-NCLOC observations | Projects |
| --- | --- | --- |
| css | 13,661 | 8 |
| java | 66,683 | 31 |
| web | 15,599 | 22 |
| xml | 19,822 | 26 |
| js | 11,350 | 5 |
| php | 3,381 | 2 |

No positive NCLOC tokens for Python, Go, C++, C# or TypeScript were found in this archive. Quality-profile metadata contains `cs` on 1,943 rows despite no positive `cs` NCLOC distribution: **profile presence is not evidence of analyzed source coverage**. JavaScript appears in five projects in the existing Java corpus; these already-exposed mixed repositories do not constitute a new JS forecasting holdout. Historical plugin binary versions and complete immutable rule/build domains are not present in the V2 schema. Unknown metadata must remain unknown.

**[L5 — verified implementation reuse]** `forecasting_mvp/v2_import.py` joins analysis IDs/revisions, exports Git ancestry and records provenance, but deliberately does not export new covariates. `prediction_input.py`, `targets.py`, `splits.py`, `io.py` and Phase 3/4 evaluation demonstrate strict boundaries, exact durations, sealing and checksums. Reuse their concepts/pure helpers under new contracts, not their old dataset IDs. `build_module_mart.py:292` mines Git numstats and has window/statistic helpers; `modules.py:24` filters specifically to production `.java` files. Its weekly targets are 3/4/12 weeks, not exact 30/60/90 days. `compute_project_sonar_features.py:130–148` uses nearest history values, substitutes zero for missing quantities and combines three remediation categories; it is **not an admissible historical feature/target adapter**. These observations did not trigger code changes in this documentation-only phase.

**[L6 — additional local artifacts, not certified evidence]** Research outside this checkout contains NPF/CMR marts, repository registries and earlier model reports. `/home/hp/tst/research/npf90_final_validation/NPF90_Final_Gate_Card.md` records unresolved identity and compiled/source-domain gates. These artifacts are quarantined from the new study; their numbers were not imported as Phase 5 forecasting results. Their repository families must be checked for exposure before any new holdout registry is sealed. Existing data are evidence of availability, not scientific validity or authorization to rerun an experiment.

## Additional dataset assessment

| Candidate | Verified evidence this run | Compatibility and decision |
| --- | --- | --- |
| Technical Debt Dataset V2, release 2.0.1 | Local SQLite audit above; publisher describes 31 master-branch projects and research data under CC BY-NC-SA 4.0 | Best development source for repository covariates. Already exposed; not a fresh confirmatory set. Analyzer-domain and numstat quality limitations remain. [Publisher](https://github.com/clowee/The-Technical-Debt-Dataset) |
| NPFDataSet | HF metadata revision `00d1b3865d4b00d9f4a4733af7aaad8f7c90854a`, last modified 2026-09-15; card says Java-file weekly data, lists six repositories; viewer summary exposes four repository classes and seven language values | Card/viewer coverage differs; do not infer a certified multi-language collection. License is `unknown`. Card target mixes bug/vulnerability/code-smell effort and uses 21/28/91-day weekly outcomes; incompatible with native maintainability-only exact 30/60/90 labels. Design inspiration only, pending provenance/license/raw-snapshot audit. No large CSV downloaded. [Card and metadata](https://huggingface.co/datasets/MaramAllah/NPFDataSet) |
| Tsoukalas et al. JSS forecasting archive, Zenodo 4534110 | All 18 local semicolon CSVs match the official file MD5s; 15 OSS histories, two anonymous industrial series and one cross-sectional benchmark. Local Kafka: 150 dated rows; Commons IO: 332; cross-sectional benchmark: 209 rows without dates | Date fields have no commit SHA or analysis ID columns; no certified exact UTC state linkage or immutable analyzer domain. Exploratory series only until provenance is supplied. Official API license is **CC BY-NC-ND 2.0**; do not publish transformed source data without resolving redistribution rights. [Record](https://zenodo.org/records/4534110), [API](https://zenodo.org/api/records/4534110), [license terms](https://creativecommons.org/licenses/by-nc-nd/2.0/) |
| SDK4ED forecaster-toolbox | Publisher provides MIT-licensed forecasting service code; README targets Python 3.6-era environment | Method/reference only. Not pretrained weights or verified multi-language historical state labels. Do not install its environment or copy its old service architecture. [Repository](https://github.com/XAI-toolkit/forecaster-toolbox) |
| Local TDPSN-main/dataset_final.csv | Header has churn/network metrics but no explicit repository, commit SHA, language, UTC date or native SQALE target identity; README is a brief research submission note | Not an admissible forecasting history or confirmatory source. License/row lineage need verification; no training/notebook execution. |
| Existing project/CI Sonar exports | Architecture can accept immutable analysis/revision exports; no additional non-Java archive passed all admission requirements this run | Preferred acquisition route if owners can provide snapshot payloads, analyzer/rule/scope manifests, revision linkage and reuse rights. Public web visibility is not a license or proof of history retention. |
| New historical replay / prospective collection | **PROPOSED**, not executed | Fixed analyzer bundle over pinned historical revisions can produce retrospective counterfactual labels; prospective daily collection can support operational claims later. Scanning belongs to a separately authorized phase. |

Publisher sources were accessed 2026-10-15. Publication dates: TDD paper 2019; Zenodo artifact version 1.0 says publication 2020-08-08 (record created 2021-02-11); NPF metadata date above. Sonar documentation is a live 2026.5/Community Build reference, not evidence about the analyzer used in the older V2 archive. No new independently verified Python/Go/C++/C#/TS forecasting dataset was established by this search; this is a bounded search finding, not a claim that no such dataset exists anywhere.

Dataset licenses and tool/model licenses are separate. TDD research-derived exports retain its attribution/noncommercial/share-alike conditions; do not assume trained-model redistribution rights from a dataset citation. NPF unknown terms block redistribution/use admission pending clarification. SDK4ED MIT does not confer rights on unrelated datasets. Publish project metadata/query recipes and our design, not source databases or third-party transformed data by default.

## Confirmatory evaluation protocol — proposed, not executed

### New cohort and exposure control

1. Treat **all 31 V2 repository families**, original temporal/held-out IDs, NPF card/viewer projects, the 209-name Zenodo cross-sectional benchmark and all previously used local registries/marts as exposed development/quarantine sources. Complete the union by URL/provider ID and fork ancestry in Phase 5.1; this run did not establish an exhaustive exposure inventory. Hash or alias mapping must resolve before new confirmation is possible.
2. Use metadata-only screening of new permissively licensed repository families: fixed language/scope/branch, history availability and analyzer compatibility, never debt magnitudes or model errors. The three engineering-pilot repositories are permanently development. Do not nominate final held-out URLs here: discovery, family-overlap checks and custodian reservation have not occurred.
3. Proposed confirmatory registration: **24 genuinely new families**, 12 development and 12 held-out, with 3 development + 3 held-out in each stratum: Java-dominant, Python-dominant, JS/TS-dominant and mixed. This is a target enrollment, **not current availability**. Classify mixed first: at least two analyzed programming-language families each have >=10% of analyzed production NCLOC. Otherwise classify dominant when one family has >=80%; JS/TS count as one family. The priority makes strata mutually exclusive. Resolve 10–80% cases by fixed `other`/exclude policy before outcomes; no result-based reclassification. Assign the repository stratum from its first registered origin’s language coverage/source inventory before debt outcomes; later composition changes may alter per-origin features, never family role or frozen stratum. C++, C# and Go remain architecture support targets, not claimed evaluated languages.
4. A second contributor acts as label custodian: freeze family/URL mappings, cutoffs, exclusion policy, checksums and model roster before numerical held-out debt is opened to the fitting/selection process. Ordinary separate directories/read permissions and subprocess inputs suffice; no enterprise access service. If a candidate is later revealed as previously exposed, quarantine before any claim and publish a deviation. After outcome access, do not silently replace its family or move another project into test.
5. Use three development-only expanding temporal folds. Exact cutoffs are computed from the verified coverage registry **before numeric labels**, written to a signed-off study manifest, then immutable. Let V be a validation origin boundary. Training rows must satisfy `t0 + h < V − 90 days`; validation's earliest dynamic input is at V−90d. This purges overlapping target and 90-day dynamic-context windows. A 90-day target consequently needs up to 180 days between last training origin and first validation origin. If coverage cannot support three such folds, use two or one preregistered fold and report reduced evidence; no random row split or relaxed purge chosen after scores.
6. For a held-out family the model may receive that family's observed pre-cutoff context at inference, but it gets no fitting/selection/calibration labels from that family. This is repository generalization with historical context, not cold-start with no history. Shared clones/forks always remain one family. Foundation-model pretraining overlap is unknown, so “untouched” means untouched by this project's study/selection, not certified absent from pretraining.

### Estimators and features

Primary target per horizon: measured future native maintainability stock `D(t0+h)` under the same admitted analyzer/scope semantics. Ridge/CatBoost fit signed delta `D(t0+h) − D(t0)` and reconstruct `max(0, D(t0)+delta_hat)`; retain raw delta/stock for audits. This gives persistence delta=0 as an exact baseline. H=30/60/90 are independent direct targets; no 91-day relabeling, sequential pseudo-labels or use of future churn.

- **F0:** current debt + verified past debt/context quality features. **F1:** F0 plus current NCLOC/complexity/aggregate issue categories and unique-commit activity. **F2:** F1 plus reconciled churn, only if its preregistered coverage/consistency gate passes. Groups and column lists are frozen before validation; compare each addition against its predecessor on identical IDs. Missing feature values do not drop rows selectively for the better-looking model.
- **Ridge:** separate h models; train-only numeric median imputation + missing indicators, train-only standard scaling; one-hot encoding for allowed low-cardinality language metadata with unknown category handling. No repository ID, file path, source-project key, outcome availability, test role or target metadata in X. Alpha grid `[0.1, 1, 10, 100, 1000]`, dense one-hot output and deterministic `solver=svd`; choose mean of development-fold repository-macro MAE per horizon. [Ridge definition](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html).
- **CatBoost:** CPU only, 2 threads, seed42, RMSE training loss, learning_rate=.03, fixed500 iterations, depth `[4,6]`, l2_leaf_reg `[3,10]`, no test early stopping. Mean development-fold repository-macro MAE selects among at most four combinations per h; iterations stay500 and no early stopping is used. Native numeric missing handling plus explicit reason/missing flags; categorical unknowns use a fixed `__MISSING__` value. [Missing-value behavior](https://catboost.ai/docs/en/concepts/algorithm-missing-values-processing).
- **Controls:** persistence on every ID. Fixed measured-observation mean over trailing30d and OLS trend over trailing90d are secondary sparse-history controls; use actual UTC elapsed times and distinct analysis/state identities, require >=2 time points for OLS, else an explicitly recorded persistence fallback. These are newly registered sparse-history definitions, not alterations of the original daily Phase 3 baseline artifacts.
- **Optional Chronos:** the existing immutable Small checkpoint only, on a preregistered past-eligible 90-daily-state subcohort. No interpolation of sparse scans to create that context. If eligible contexts do not exist, report NOT APPLICABLE; do not omit hard examples without a separate matched-ID comparison of every model. Original quantile-crossing handling remains typed/whole-path, failed intervals null. Its past negative result is not a new confirmation; no new pretrained candidate/download is required.

F2 is enabled only if at least90% of registered development origins have verified complete churn windows, assessed from past-feature coverage before validation scoring; otherwise keep it disabled. Rank candidate model/feature-group pairs by mean development-fold repository-macro MAE per horizon, with scores within1% preferring persistence, then Ridge, CatBoost and optional Chronos; ties within an estimator prefer F0, then F1, then F2; Ridge ties prefer larger alpha, CatBoost ties prefer smaller depth then larger l2_leaf_reg. Freeze the selected90-day champion for the primary confirmatory claim. No confirmatory scores choose a feature group or fallback.

No model is trained in Phase 5 or the proposed data-readiness Phase 5.1. A later authorized benchmark freezes versions, feature/transform hashes and selection before all confirmatory predictions are generated and sealed. Numerical confirmatory labels are read only after full prediction coverage/status seals exist. Unexpected inference errors abort; no newly invented fallback silently hides failures.

### Metrics, independence and claims

Primary endpoint: 90-day repository-macro MAE; secondary: macro RMSE and paired persistence skill `1 − macro_MAE_model/macro_MAE_persistence`. At zero baseline error, skill is undefined, not infinity or zero; report raw errors/counts. Report all h, per-language stratum, repository, unchanged/changing debt, constant/nonconstant context, missingness/coverage, distinct scans/states/value sequences and overlapping windows. Macro RMSE is mean of repository RMSEs; pooled metrics are separate. Do not pool incompatible analyzer domains as if a minute of tool-defined principal measured an identical latent construct across tools/languages.

Use 2,000 paired **repository-family** bootstrap draws, seed42, percentile95% intervals for MAE/RMSE and absolute MAE gain. Evaluate the validation-selected champion once at the confirmatory 90-day endpoint; the Ridge/CatBoost tables are also reported. Proposed superiority gate: >=5% macro-MAE reduction **and** paired-gain lower CI >0, complete assigned-ID accounting, no material provenance/leakage failure. This is a preregistered practical gate, not a promised result or a power calculation. The 30/60-day and per-stratum comparisons are secondary/descriptive; any additional inferential superiority claims require multiplicity control (e.g. Holm) declared before opening outcomes. With only three held-out families per stratum, within-language bounds are exploratory; broad seven-language generalization cannot be claimed.

Optionally reserve development-only calibration data for intervals in a future explicitly authorized study; no residual fitting or interval recalibration is selected here. Native pretrained q10–q90 coverage/width, when applicable, keeps attempted/native/failure denominators and constant-history collapse diagnostics. Report negative or inconclusive results without expanding cohorts based on outcomes.

## Resources, scope and readiness

Verified host: Ryzen 5 PRO 5650U, 6 cores/12 logical CPUs, 16,036,016,128 bytes RAM, approximately 9.0GB available RAM and 20.9GB free disk at audit time. Existing `.venv-forecast` package metadata: scikit-learn1.8.0, CatBoost1.2.8, NumPy2.4.4, pandas3.0.2. These were **not imported for training or upgraded**. Existing CPU Chronos environment/weights remain unchanged. Ridge is documented under scikit-learn's BSD terms, CatBoost's repository Apache-2.0; deployment versions must be revalidated and frozen at the future study start. [scikit-learn](https://scikit-learn.org/stable/about.html), [CatBoost license](https://github.com/catboost/catboost/blob/master/LICENSE).

No GPU is required for the proposed first tabular pilot. Future fitting cap: one model process, 2 CPU threads, 2GiB RSS and <=30min per candidate/h; stop and record resource failure rather than increase budgets after test outcomes. These are proposed ceilings, not measured training performance. JS/TS scanning recommends at least4GB scanner memory; server/build processes need additional budget. Plan sequential, bounded replay with <=8GiB total monitored job budget or defer to a larger approved machine; C++/C# builds are deferred from the shortest pilot. [JS/TS requirements](https://docs.sonarsource.com/sonarqube-community-build/analyzing-source-code/languages/javascript-typescript-css).

Assumed capacity remains **2 contributors ×10h/week =20 total h/week**. With an 8h person-day, Phase 5.1 core data contracts/adapters/readiness is estimated6–9 person-days (48–72h, 2.4–3.6 elapsed weeks). If small historical replays are separately authorized and needed, add2–4 person-days (16–32h), total64–104h or3.2–5.2weeks. This does not include acquisition delays, a confirmatory corpus, model evaluation or UI. A three-project engineering pilot can use six cutoffs each (`−90, −30, 0, +30, +60, +90` days) for up to18 archived/replayed snapshots and nine endpoint cases; repeated underlying states reduce diversity. It proves data contracts, not accuracy.

For confirmation, one possible sparse schedule has nine fixed30-day-grid states from−90 to+150d and origins0/30/60d, yielding at most9 target cases per family: 24 families would need up to216 snapshots and yield216 cases before exclusions, with only12 independent test clusters. This is a planning count, **not available data or adequate power**. Three purged development folds need substantially more history than that small engineering schedule; extend only the development collection from metadata coverage, before outcomes. Prefer owner-provided archives. Fresh prospective90-day labels require at least90 calendar days after their origins; a4–6week coding schedule cannot create them without retrospective acquisition.

Readiness: (a) existing Java development-feature work is feasible subject to new contracts; (b) churn is conditional on conflict resolution; (c) new non-Java historical target data, complete analyzer metadata, licensing and genuinely new cohort reservation remain acquisition blockers; (d) Phase 5.1 can begin only on separate authorization. Architecture support is not measured language coverage.

## Reproducible local checks

Read-only schema/count recipes below reproduce the load-bearing findings without building forecasting rows. Use the source hash above; values count raw rows, not eligible examples. Parse numstats as strict base10 integer strings as well as native nonnegative numbers; do not equate SQLite `typeof(...)=text` with missing data.

```sql
SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name;
SELECT COUNT(*) FROM GIT_COMMITS_CHANGES;
SELECT TYPE,COUNT(*) FROM SONAR_ISSUES GROUP BY TYPE;
SELECT COUNT(*) total,SUM(NCLOC IS NULL) missing,
       SUM(typeof(NCLOC) IN ('integer','real') AND NCLOC>=0) valid
FROM SONAR_MEASURES;
SELECT COUNT(*) duplicated_keys,SUM(n-1) duplicate_extra_rows,
       SUM(CASE WHEN alo<>ahi OR dlo<>dhi THEN 1 ELSE 0 END) conflicting_keys
FROM (
 SELECT PROJECT_ID,COMMIT_HASH,FILE,COUNT(*) n,
        MIN(CAST(LINES_ADDED AS INTEGER)) alo,MAX(CAST(LINES_ADDED AS INTEGER)) ahi,
        MIN(CAST(LINES_REMOVED AS INTEGER)) dlo,MAX(CAST(LINES_REMOVED AS INTEGER)) dhi
 FROM GIT_COMMITS_CHANGES
 GROUP BY PROJECT_ID,COMMIT_HASH,FILE HAVING COUNT(*)>1
);
SELECT PROJECT_ID,NCLOC_LANGUAGE_DISTRIBUTION FROM SONAR_MEASURES;
```

For language counts: split each nonempty distribution on `[;,]`, match `language=digits`, count positive entries by language and distinct project, record unparsed tokens instead of assuming a Java-only field. Match change-row `(project, SHA)` against the complete Git-key set; this run found no orphan changes. Read `QUALITY_PROFILES` with the existing semicolon-aware JSON parser; do not equate profile languages with positive source measurements. All18 local Zenodo MD5s were checked against `https://zenodo.org/api/records/4534110` file metadata; semicolon CSV parsing is essential.

Audit scratch/provenance on this host: `/home/hp/tst/research/forecasting_mvp/phase5/2026-10-15/` (`local_audit.json`, `raw_sql_evidence.json`, `corrected_language_and_duplicates_audit.json`, conflict examples, NPF/Zenodo metadata and file inventories). An initial semicolon-only distribution probe was superseded by the verified comma-or-semicolon parser; a SQLite numeric-type-only numstat probe was superseded by strict text parsing. Those intermediate probes are not used for conclusions. Scratch files are audit notes, not new training datasets, and are not uploaded. No raw author messages or emails are published in these documents.

## Documentation verification and stop

Acceptance checks: all four required Markdown files exist; cross-links/source links and code-fence/diagram structure checked; numeric claims reconciled to this run's raw SQL/metadata; previous source/config/tests/reports and local frozen bundles/checkpoints remain unchanged; Git staged scope exactly these four new `.md` files, with no credentials/oversized artifacts. No new executable tests were written for a documentation-only change. Prior matching-code regression evidence remains336 passed/1 prohibited CatBoost test excluded from Phase4.2.1; it is **not a new Phase5 test run**.

Safe publication uses a normal descendant commit from central `main`; the working checkout's unrelated legacy history is preserved, with explicit new-document copying and only `github-main` tracking advanced. Remote content must be verified after push. Stop at Phase5 publication: no Phase5.1 implementation, training, scan, dataset reconstruction or dashboard is authorized by this work.

> Phase 5.1 scope correction (2026-10-15): the three engineering development targets are Java-dominant, Python-dominant and genuinely mixed Python+JS/TS. The mixed target is not JS/TS-dominant; no fourth project is included. Original Phase 5 findings remain historical design evidence. Current implementation/data readiness: [Phase 5.1 report](PHASE_5_1_IMPLEMENTATION_REPORT.md).

Phase 5.1 follow-up qualification: all 10 sampled conflicting legacy basename groups map to multiple authoritative full paths, whereas 10 clean controls match unique paths. This does not establish a cause for every one of the 23,321 groups; it establishes that raw `FILE` keys are not reliably full-path identities. No SUM/MAX/MIN repair or F2 promotion is justified.
