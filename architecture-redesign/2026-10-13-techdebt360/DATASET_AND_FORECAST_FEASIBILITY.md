# Dataset and forecasting feasibility

Date: 2026-10-13. **Decision: reliable deployed exact 90-day module debt forecasting is currently unsupported. Repository-level forecasting on public V2 histories merits a bounded feasibility study; it is not ruled out.** Current file data is marginal, short, correlated and contains mixed horizons; predictive value has not cleared baselines. A provisional primary pivot is justified without declaring forecasting scientifically impossible; revisit it at the early imported-data and patch-harness gates.

## Definitions and evidence levels

An inventory record is not a verified observation. A verified own scan requires commit/tree/source manifest, intended observation cutoff, actual scan timestamp, CE task and analysis ID, exact revision/project/scope binding, full exports, analyzer-domain metadata and checksums. Public historical records are `IMPORTED_PUBLIC`, with their available provenance and limitations; do not fabricate missing scanner proofs or reclassify them as locally verified scans.

`TD(t)` is applicable active maintainability remediation estimates in minutes under one frozen measurement domain. Actual engineer labor, reliability/security effort, debt-category probabilities and business priority are separate quantities. Raw `sqale_index` and summed eligible issue estimates are separately recorded and reconciled with explicit discrepancy flags. Unknown effort remains missing, not zero. A module lineage transition can change the population without representing improvement.

## Quantitative local audit

| Evidence population | Independent domains and coverage | Observation span/cadence | Usable status |
|---|---|---|---|
| Module forecast collector | 0 discovered real generation/completion markers; real modules/files unknown | No proven real weekly sequence | 0 certified module labels at every horizon in the audited workspace |
| V3 operator submissions | Reported 36 manifest rows × two modes = 72 attempts | Three slots per selected repository; actual server results unavailable | Verified recovered analyses unknown; operational submission count is not sample count |
| Kafka download | One inferred repository, 8 manifest entries, 3,718/3,752 measured paths | All analysis timestamps same execution day; actual cutoffs unresolved | No certified horizon labels; 3,736 retained NPF rows are provisional |
| Source-only target selection | 10 repositories × 18 snapshots = 180; 1,374 file clusters; 15,981 origins | Monthly Jan 2023–Jun 2024; roughly 17 months between endpoints | Research exports exist; compiled validity and human issue identity unresolved |
| V2 DB, inspected directly | 31 projects; 67,550 analysis rows, 66,711 nonblank analysis keys and associated project measure rows; 1,024,614 issue rows | Nonblank-key dates range 2000-10-11–2018-10-15 across projects; irregular commit analyses | Large imported research corpus; no direct module measure schema or current-domain guarantee |
| CMR derived mart | 5 repositories; 110,977 origins; 1,509 artifact clusters; 639 repo timestamp origins; 461 positive rows | Sparse selected historical origins over project-specific long histories | Corrective-maintenance target, not future debt; 0 human-validated event edges in retained coverage table |
| Netty sample workbook | 138 package rows, 1,133 dependency rows | Single named snapshot, 2017-09-15 | Architecture-schema sample; 0 proven temporal debt labels |

Counts were recomputed, not copied from an old recommendation. V2 has 839 blank analysis-key records (1.24%). Every `SONAR_MEASURES.SQALE_INDEX` cell is populated in the visible DB; 31 explicitly equal zero. Independent recount also found all 66,711 nonblank analysis records linked to Git revisions and 66,685 measure rows with profile metadata. Analysis date matches author and committer day in those joined records. This is substantial usable provenance. It does **not** prove full timestamp/UTC-cutoff validity, complete coverage, stable rule/remediation settings, valid human-effort estimates or complete issue lifecycles. Report analysis duplicates, missing project/date points and lifecycle-key mismatches per project before forecasting.

### Exact horizons: three different counts

| Horizon | Raw target-selection repo snapshot pairs at exact date separation | Same-path raw file pairs (no lineage certification) | Existing retained mart rows / repo-origin clusters |
|---:|---:|---:|---:|
| 30 days |60|7,972| 0 / 0 |
| 60 days |20|2,719| 0 / 0 |
| 90 days |10|1,361| 1,361 / 10 |
| 91 days |50|6,651| 5,371 / 40 |

The mart also contains 9,249 rows at **92 days**. Its 90/91/92 total is 15,981; it is a three-calendar-month endpoint dataset, not one exact 90-day dataset. Raw same-path matches are candidates only: no claims about identity, compatible domains or independent evaluation follow from path intersections. No new labels were constructed during this audit.

V2 date-level candidate repository pairs are 5,840 / 5,356 / 5,513 / 5,694 at 30 / 60 / 90 / 91 days, covering all 31 projects. These were counted by distinct observed date with nonblank key/revision. They do **not** count exact timestamp endpoints, independent origins, valid module labels, compatible rule domains, or runtime-verified scans. Multiple commits on a date require a preregistered deterministic choice; never select the most favorable target after inspecting debt.

The retained target mart has 8,470 zero T0 debt rows (53.0%); 15,425 unchanged raw-debt pairs (96.52%); 510 NPF positives (3.19%). The old profile's 738 positives describes an earlier version. This version mismatch is material. Raw-minute unchanged fraction differs from density unchanged fraction because LOC can change. Heavy skew and persistence make mean-error and high R² insufficient evidence of useful future prediction.

### Missingness and identity

The Kafka measures contain blanks and include non-Java/test files. The source-only target mart reports complete targets after its own filtering, which does not establish unbiased source coverage. CMR labels exclude 288 known-open future-work rows; a null primary label must never become a negative. File deletions/splits/merges, missing source scope, missing analyzers, censored endpoints, reset issue keys and contradictory fingerprint matches have distinct reasons.

The final NPF evidence shows 1,503 / 39,939 automated matching disagreements (3.763%); both 200-case reviewer forms remain uncompleted. Automated disagreement is not identity-error probability. Compiled/source comparison covers only three Maven pairs, not the proposed diverse 30-pair gate. Old NPF sealed repository outcomes were not opened for this redesign.

## Public resources

See [public dataset digest](digests/public-datasets.md) for asset-level sources and schema inspection, incorporated as the detailed evidence appendix to this document.

| Resource | Access and actual relevance | Admission decision |
|---|---|---|
|[Technical Debt Dataset V2](https://github.com/clowee/The-Technical-Debt-Dataset)|Downloadable SQLite; local copy verified; historical project measures, issue lifecycles, Git/Jira; CC BY-NC-SA 4.0; V1 timeline warning|Primary low-cost imported forecasting feasibility source; research-only licensed corpus, separate domain |
|[NPFDataSet](https://huggingface.co/datasets/MaramAllah/NPFDataSet)|CSV file-level regression mart and derived numerical labels; `TD_3m` is 13 weeks / 91 days and `TD_1m` is 4 weeks; repository package uploaded 2026-09-15; unknown dataset license|Quarantine pending license/provenance audit; exact 90-day labels cannot be asserted; disabled counters are not identity ground truth |
|[SDK4ED forecaster toolbox](https://github.com/XAI-toolkit/forecaster-toolbox)|Forecasting code/toolbox, not an independent population of debt labels|Reference baseline methodology; no sample-count addition |
|[Zenodo 6109615](https://zenodo.org/records/6109615)|Replication artifacts for debt prediction research reuse forecasting dataset|External replication reference; do not count as independent of 4534110 |
|[Zenodo 4534110](https://zenodo.org/records/4534110)|Concrete CSV forecasting assets with date/debt fields; small project cohort|Imported repository-level external study only; verify record license/date/units and errors before use |
|[Tesoro](https://github.com/NamCyan/tesoro)|Java code units with debt-type labels and checkpoints; not longitudinal debt-minute targets|External code-category benchmark, with project/clone grouping and manually checked negative/OOD samples |
|[SATD repayment effort](https://github.com/yikun-li/satd-repayment-effort)|Message text, SATD classes and changed-code/file counts; exported header lacks repository/date; labor minutes not supplied|Text/debt-repayment scope reference, not numerical future-debt or human-work-hour ground truth |

Publication or successful download does not certify temporal semantics. Unknown/NC licenses prevent unrestricted product redistribution. A research study can use an appropriately licensed corpus without shipping its rows. Dataset terms and checkpoint-weight terms must be checked separately; NC data metadata does not automatically establish derived-weight licensing. Moirai checkpoint weights have their own explicit noncommercial restriction.

## Feasibility gate

Evaluate each repository × domain × granularity × horizon independently. Four outcomes: `UNSUPPORTED_DATA`, `RESEARCH_ONLY`, `VALIDATED`, `REVOKED_DRIFT`. Model-load ability is a separate attribute.

1. **Measurement gate:** compatible domain, complete archived evidence, correct cutoff/revision and observed endpoint. No unobserved future value is a label.
2. **Series gate:** actual cadence, usable context, missing masks and native horizon supported by the exact model revision. No universal snapshot threshold. Chronos accepts short contexts; this does not create independent backtests. A 512-point TTM context means 512 observations—roughly 9.8 years at weekly cadence. Padding to 512 does not establish 512 measurements.
3. **Validation gate:** enough repository domains, non-overlapping evaluation blocks and changing-target events for useful uncertainty. Preregister a power/precision simulation from development data only; require at least three separated horizon blocks per evaluated repository and a held-repository cohort before generalization claims. If this cannot be met, remain research-only.
4. **Value gate:** on the same origins, beat persistence and strongest conventional model materially; report macro and per-project errors, changing/constant subsets, coverage and failures. Proposed acceptance: ≥10% macro-MAE reduction, paired repository/block CI above 0, benefit in ≥70% eligible repositories, common native central 80% intervals with coverage 75–85% and useful width. A separate validation-only calibration layer is required for a proposed central 90% interval; evaluate its coverage and width separately. These are chosen study gates, not universal scientific laws; revisit sample precision before final preregistration.
5. **Deployment gate:** measured compute/cost, license, versioned adapter, deterministic provenance, failure/abstention paths, and capability expiry.

**Current gate result:** own module history fails 1–3; exact 90-day file history cannot provide multiple independent origins per repository; previously learned density models fail 4. Imported V2 could pass enough of 1–3 for a carefully bounded repository-level study after domain and clock audits. None of the six foundation forecasters has been run on these histories, so no accuracy winner exists.

## Can more history be acquired cost-effectively?

Yes, a staged path is plausible. Start with the existing 1.5 GB V2 DB and small Zenodo assets: no historical builds required for that imported-domain study. Audit revision/date/profile coverage, measured regular points and changes, then obtain an origin list. Do not map project aggregates to invented modules or merge historical 7.x / current 26.x measurements.

For a fresh own-domain cohort, first recover/export already submitted operator tasks on the original environment. Recovery may save scans but cannot yield long histories from three slots. Next propose a bounded compiled pilot: 12 representative Java repositories × 3 historical commits, including Maven/Gradle/library/application variation. Estimate per scan after observing a later authorized pilot. At an assumed 5–20 minutes per build + scan + export, 36 snapshots cost 3–12 sequential machine-hours, excluding dependency failures and setup. Require ≥90% usable compatible scans and document failures by repository.

If pilot passes, a three-year weekly corpus is 12 × 157 ≈ 1,884 scheduled cutoffs before exact 90-day supplemental endpoints. Exact 90-day endpoints may require up to a similar number of extra cutoffs; deduplicate identical commits only with proof. At the assumed 5–20 minutes this is 157–628 sequential hours for the weekly portion; four workers offer an ideal 39–157 hours before contention/retries. This is likely more expensive than imported-data research. Monthly 12 × 37 = 444 snapshots is cheaper (37–148 sequential hours under the same assumption) but supplies far fewer exact 90-day dates; use calendar-month horizons or add actual endpoint scans. Actual CPU/RAM/disk/bandwidth costs remain unknown. A 32 GB workstation and 100 GB free disk are planning reservations, not measured minima.

Freeze budget: spend at most one study week auditing imports and one week piloting recovery/backfill in a future authorized phase. Stop if reproducible coverage, historical builds, sample precision or baseline skill fail. Do not commit the graduation critical path to 1,884 scans before the small pilot.

## Strongest alternative

Provisionally select an evidence-grounded Java debt assessment, prioritization and verified remediation study, subject to the early V2 and patch-harness revisit gate. Static findings establish measurements; a small code LLM proposes bounded patches; source retrieval is retained only if it improves patch success/evidence relevance. Debt-type classifiers add candidate annotations only after task semantics and external validation. Compare static-only, generation-without-retrieval, retrieval-assisted generation and deterministic fixes. Evaluate compile/tests/finding changes and blinded reviewer judgments; no 90-day labels are required for the primary study.

CMR-90 and debt-introduction prediction are secondary possibilities, not automatic rescue targets: the local CMR study has rare events and no human-validated edges; current debt did not improve process-only baselines. Forecasting remains a real research track with the staged acquisition plan above and [conditional protocol](FORECASTING_RESEARCH_PLAN.md).
