# Red-team review: direction and data

Date/accessed: 2026-10-13. Reviewed `CURRENT_SYSTEM_AUDIT.md`, `DATASET_AND_FORECAST_FEASIBILITY.md`, and `digests/public-datasets.md`. Independent read-only SQLite recount used `/home/hp/TECH_DEBT/td_V2.db` with `mode=ro`. No model, scanner, test, experiment or implementation was run. This review adds recommendations only and changes none of the reviewed documents.

## Verdict and strongest counterargument

**Keep the rejection of a presently validated exact90 module forecaster. Make the primary pivot conditional, and preserve a real opportunity for V2 repository forecasting to become the main scientific study.** The strongest counterargument is asymmetric proof: V2 already contains substantial numerical observations with revision/Git links and profile metadata, whereas the proposed prioritization/remediation service and outcome benchmark are not implemented or validated. Poor results on a short source-only file-density corpus do not establish poor results on V2 project-level raw debt, nor establish that new remediation data will be easier to validate. [Current audit](../CURRENT_SYSTEM_AUDIT.md), [feasibility document](../DATASET_AND_FORECAST_FEASIBILITY.md), [V2 database](/home/hp/TECH_DEBT/td_V2.db).

A reasonable decision is to nominate evidence-grounded prioritization and bounded patch assessment as the **provisional product direction**, while reserving the documented one-week imported-data audit before freezing the **primary thesis contribution**. This is a planning inference, not proof that V2 will forecast well or that remediation will succeed.

## Concrete corrections

### P1 — Primary pivot is proposed, not demonstrated superior research feasibility

The “Strongest alternative” implies remediation avoids the difficult ground truth by avoiding 90-day labels. It avoids temporal forecasting labels, but introduces another unresolved target: whether a patch safely repays a meaningful debt item and whether a ranking helps a maintainer. The current audit explicitly finds no complete patch-verification service, no measured runtime adapters and uncompleted human identity review. These risks are not resolved by having a code generator. [Current audit, implementation assessment and gaps](../CURRENT_SYSTEM_AUDIT.md), [feasibility document, strongest alternative](../DATASET_AND_FORECAST_FEASIBILITY.md).

**Correction:** describe the pivot as a hypothesis with a small independently adjudicated outcome cohort and an explicit stop condition. Define repair validity independently of detector score; separate analyzer finding removal, regression-test outcomes, blinded patch correctness and maintainer utility. Tests/analyzer improvements are observable evidence, not proof of behavioral equivalence or realized human labor savings. Prioritization requires comparative ranking judgments or another justified utility endpoint; raw severity/remediation minutes alone do not supply business-priority ground truth. [Dataset semantics](../digests/public-datasets.md), [repayment manuscript §2.4](https://arxiv.org/html/2309.06020v3) (authors/arXiv, 2026-04-26 preprint).

### P1 — Understate neither V2 provenance nor its ability to challenge the pivot

Independent recount confirms **31 projects; 67,550 analyses; 66,711 measure rows; 1,024,614 issue rows; 839 blank analysis keys; no missing SQALE_INDEX; 31 zero values**. Distinct observed-day candidate pair totals are exactly **5,840 / 5,356 / 5,513 / 5,694 at 30 / 60 / 90 / 91 days**, each covering all 31 projects. No numerical correction is required for those claims. [Local V2 database](/home/hp/TECH_DEBT/td_V2.db), [reported audit counts](../DATASET_AND_FORECAST_FEASIBILITY.md).

Additional positive evidence: **all 66,711 nonblank-key/revision analysis rows join to a Git commit by `(PROJECT_ID, REVISION=COMMIT_HASH)`**. Analysis date’s first ten characters equal both author and committer date’s first ten characters for every joined row. **66,685/66,711 measure rows contain QUALITY_PROFILES**, leaving 26 blank. This field includes language/profile keys and rule-update timestamps in sampled rows. The draft’s repeated absence of a “current-domain guarantee” is correct, but should not obscure substantial available historical provenance. [Actual tables SONAR_ANALYSIS, SONAR_MEASURES, GIT_COMMITS](/home/hp/TECH_DEBT/td_V2.db).

**Correction:** add these positive audit results and prioritize a measured-origin eligibility audit over new scanning. The day equality is not a full timestamp/timezone check, profile content is not a complete analyzer/rule-parameter manifest, and candidate pairs are not independent backtests. Keep those qualifications. The maintainer warns about **v1**, while v2 deliberately restricts analysis to master; do not transfer v1 timeline defects to v2 as an established fact. [Maintainer README](https://github.com/clowee/The-Technical-Debt-Dataset) (GitHub, date unspecified), [public version evidence](../digests/public-datasets.md).

### P1 — Novelty of static analysis + retrieval + LLM repair is not established

This combination already has primary research precedents: **InferFix**, FSE 2023, combines a static analyzer, retrieval and generation with candidate patch validation; **DLRepay**, *Information and Software Technology* 167, March 2024, studies direct SATD repayment from comment/code input and releases a repayment corpus. These precedents refute novelty based solely on assembling the components. They do not prove the entire remediation field is saturated or establish performance for this project’s Sonar maintainability domain. [Microsoft Research publication page, December 2023](https://www.microsoft.com/en-us/research/?p=984972), [Elsevier DLRepay article, March 2024](https://www.sciencedirect.com/science/article/pii/S0950584923002318).

**Correction:** narrow the proposed contribution to a falsifiable difference, for example evidence/provenance-based admission and abstention, independently judged patch correctness under a resource budget, or prioritization utility. State that distinction against existing work before declaring it the stronger thesis. Do not promise a novel repair model or infer detector accuracy from patch success. These are reviewer recommendations, not established novelty claims.

### P2 — Exact90 must name a cutoff policy, not demand a commit exactly 90 days later

The feasibility document correctly distinguishes date-pair candidates from exact timestamp endpoints. Nevertheless, a repository state **at a fixed 90-day cutoff** can be defined as the last reachable commit at or before that cutoff. There need not be a commit at the exact instant. An already scanned selected state could supply the observation after coverage/branch/clock checks; arbitrary nearest-day interpolation cannot. [Public dataset digest, backfill conditions](../digests/public-datasets.md), [V2 master-branch design](https://github.com/clowee/The-Technical-Debt-Dataset).

**Correction:** preregister calendar convention, branch reachability, source-state availability and cutoff-state selection. Then recount eligible measured origins under that policy rather than treating 5,513 day-equal pairs as either the complete eligible cohort or proven exact90 labels. This does not rescue unobserved module measurements.

### P2 — Attribution and artifact wording need repair

- NPF is described as “Spreadsheet histories” in the resource table, but the accessible asset is `combined_td_mart.csv`, a derived regression mart. Its horizon definition is correctly reported as 91 days. **Correction:** say CSV file-level regression mart. [Actual Hugging Face tree](https://huggingface.co/api/datasets/MaramAllah/NPFDataSet/tree/main) (MaramAllah, uploaded 2026-09-15).
- `CURRENT_SYSTEM_AUDIT.md` points to `digests/local-audit.md`, which was absent from the output inventory during this pass. **Correction:** provide the referenced digest or remove/change the link before delivery. The V2 recount above independently verifies only the specified V2 numbers, not every file-data count in the current audit. [Current audit](../CURRENT_SYSTEM_AUDIT.md).
- “NC-restricted model weights” cannot be inferred automatically from NC dataset metadata. **Correction:** describe data-license restrictions separately from model-weight licensing and leave derived-weight obligations unresolved unless a specific license/source establishes them. [Dataset license records](../digests/public-datasets.md).

## What survives the critique

The proposed split between exact90 **module** deployment and bounded historical **repository** research is sound. Existing data do not directly establish module labels, source-only file results are highly persistent, SATD classes/change counts are not labor minutes, and a downloaded forecaster is not predictive evidence. A negative V2 baseline result would still be scientifically reportable if the study is properly framed; passing the selected 10% utility gate is necessary for a deployment claim, not for the existence of a worthwhile research contribution. Conversely, a repair pipeline can be product-useful without establishing scientific novelty. [Audited distinctions and selected gates](../DATASET_AND_FORECAST_FEASIBILITY.md), [public resource evidence](../digests/public-datasets.md).

No critical arithmetic error was found in independently recounted V2 figures. The most material corrections concern comparative feasibility, recognizing existing provenance, and defining the independent correctness/utility target for the pivot.
