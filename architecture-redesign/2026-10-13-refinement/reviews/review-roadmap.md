# Roadmap feasibility and prose review

Reviewed 2026-10-13: [REVISED_IMPLEMENTATION_ROADMAP.md](../REVISED_IMPLEMENTATION_ROADMAP.md). Scope: effort arithmetic, model/study sequencing, verification outcomes and readable prose. Changes were applied only to the newly authored roadmap; this review record is the only other artifact written. No existing source, code, configuration or other design document changed. No installation, scan, model load, experiment or runtime test ran.

## Repairs applied

| Location | Finding | Applied repair |
|---|---|---|
| Minimum scope and budget | Joined numbers obscured effort and calendar assumptions. | Recorded the nine milestone sums explicitly: 38 minimum and 64 maximum contributor-days. Preserved 5–13 weeks at 5–8 effective contributor-days/week and 8–22 weeks at 3–5, both before contingency. A 20% reserve raises effort to 45.6–76.8 days. |
| Reviewer budget; R4/R5/R8 | Gold labeling, retrieval judging and patch review could be counted again when referenced in milestones. | Added one pilot labor table: function labels ~27–80 hours; patch outcomes 15–30; retrieval ~3–5; total ~45–115 before adjudication. Made these excluded from the contributor-day estimate and referenced once in R4/R5. Expanded final annotation remains separately budgeted. Shared personnel reduce effective implementation capacity. |
| Dependencies; R1/R6 | Prerequisite blocks could be confused with model failure, and preliminary feasibility could appear to select a contribution. | Separated license/data/runtime admission from efficacy. A load failure is a runtime result, not an accuracy result. Kept independent work possible while an arm is blocked, without declaring that arm complete. Primary selection remains R6 after A/B evidence. |
| R1/R3 | TTM needed actual short-context branch admission rather than an implicit family minimum. | Added weekly 52→16 cropped to 13, daily 90→30, 180→60 and 512→96 cropped to 90, with a link to exact branch revisions. Required real context and future evaluation observations. Weekly 91-day and daily 90-day tasks remain distinct. |
| R1 | Loading/output details were too compressed for an execution plan. | Preserved future checks for immutable-SHA class dispatch, default mapping, masks, axes, native cropping, inconsistent classifier labels and `mq_q50_type="mean"`; no assumed median or completed load test. |
| R5 | `ENGINEERING_CHECKED` incorrectly required independent semantic acceptance, merging technical verification and human outcome. | Defined engineering verification through all mandatory engineering, safety, differential and applicable analyzer checks. Kept independent semantic `ACCEPTED` / `REJECTED` / `INCONCLUSIVE` separate, without an ability to change or upgrade verification. |
| R5 | Analyzer-backed target resolution and learned-only acceptance risked sharing a “verified” success denominator. | Restricted `EVIDENCE_VERIFIED` to registered analyzer-target resolution plus minimum checks. Human acceptance stays separate. Learned-only checked/accepted outcomes remain a separate cohort and cannot claim analyzer debt removal. |
| R3/R4/R5/R6 | A repair-first contribution could be implied by implementation sequence. | Kept pretrained forecasting and detection/retrieval/remediation central to the studies; treated generators and controls as provisional. R6 may select forecasting, detection, explanation, repair or a bounded hybrid according to measured validity/value. |
| Entire document | Ordinary words, quantities and abbreviations were joined throughout milestone and acceptance text. | Rewrote readable prose and tables; preserved model/code identifiers, Mermaid node identifiers and branch literals. All commands, checks and workflow steps are explicitly future-only. |

## Remaining constraints

- Contributor-days are estimates, not a deadline commitment. They exclude major build recovery, full backfill, reviewer labor, waiting and expanded final annotation. Host, capacity and reviewer access still need confirmation.
- Unknown classifier licenses remain weight-execution/adoption blocks, not blanket rejection or poor-performance evidence.
- No model, package lock, adapter or native output contract has been executed. Research evidence supports candidate admission, not local efficacy.
- TTM branch availability does not establish software-debt forecasting accuracy. Actual context, native horizon, missingness and cadence still constrain eligible cohorts.
- Static findings cannot automatically serve as Tesoro gold labels. Function labels, retrieval judgments and patch outcomes require distinct independent rubrics and adjudication.
- Pilot precision may be insufficient for proposed benefit thresholds or generalization claims. The final held-out study must remain untouched by pilot tuning.
- Expanded data collection and reviewer work can exceed the base estimate. Independent engineering checks and human acceptance must remain separately recorded throughout integration.
- Future execution still requires a separately authorized task; this planning review triggers no build, scan, inference or operational workflow execution.

## Text and arithmetic checks

Verified the sums 38–64; capacity extrema 4.75–12.8 weeks and 7.6–21.33 weeks, conservatively rounded to the stated ranges; contingency effort 45.6–76.8 days; and pilot reviewer workload 45–115 hours under the stated assumptions. Confirmed representative joined-prose defects were removed. These are document checks, not runtime validation.
