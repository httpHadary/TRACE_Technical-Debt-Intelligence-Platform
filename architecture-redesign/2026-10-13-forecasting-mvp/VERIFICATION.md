# Planning package verification

2026-10-13. This verifies the **documents**, not software behavior or model performance.

## Evidence collected

Reviewed 33 prior primary architecture/research/planning documents and digests, with a [document inventory and supersession matrix](digests/prior-plan-reconciliation.md). Re-inspected actual source/CLI contracts and recorded the [component reuse table](digests/code-reuse.md). Rechecked V2 table schemas/counts through SQLite `mode=ro`; detailed same-date data integrity evidence is explicitly imported from the earlier audit. Independently reread small primary model/config/source and dataset metadata resources in the [research check](digests/research-check.md). No large dataset/model downloads or experiments were performed.

Latest scope supersedes enterprise and paired-remediation requirements for this MVP. No prior architecture file or ZIP was updated. Two contributors at 10 hours each supply 20 hours/week; no hardware was assumed to exist.

## Independent review and resolutions

| Review | Resolved contract issues |
|---|---|
| [Scope/roadmap structure and prose](reviews/review-scope-roadmap.md) | 116–166 hour arithmetic, core 64–94 hours, 20% reserve, 4-week limit, all milestone files/contracts/dependencies/acceptance/fallbacks |
| [Technology and forecasting](reviews/review-technology-forecasting.md) | phase-filtered train labels, label-free prediction projections, native deciles/path/raw prediction records, missing-state fields, constant-target fallback, restricted builds/scanner credentials |
| [Rubric and adversarial seams](reviews/review-seams.md) | deterministic ID ownership, grouped paths versus endpoint IDs, fitted-setting IDs, Java unit extraction, complete future CLI stages, per-track selection, bounded masked-data fallback |

Data-only primary-track selection happens before model outcomes: complete core90 first, masked90 only when its cohort gate fails and the limited-input gate passes. Exact future labels are always measured; TTM never uses masked/fabricated context. Longer-context research scores cannot select a global default by an incompatible smaller-cohort MAE. Runtime, license, data precision and actual forecast performance remain future gates.

## Document checks

- All six requested documents populated; local Markdown links and balanced code fences checked.
- Architecture has seven ordered ADs with Binds/Prevents/Rule. BMAD lint reports no missing/duplicate AD or unresolved design marker; six low-severity `{id}` detections are intentional API path parameters, manually resolved as false positives.
- Mermaid workflow and gate diagrams inspected; no renderer/package installed, and diagram rendering was not tested.
- Budget sums 116–166 hours; 20% reserve gives 139.2–199.2 hours; at 20 hours/week this is 6.96–9.96 weeks. First research core is 64–94 hours, 76.8–112.8 with reserve; upper bound exceeds 4 weeks.
- Source-preservation baseline captures 7,888 selected original source/design/evidence/ZIP files. Final hash comparison found zero changes. This is a bounded captured inventory, not a hash of every file on the machine.
- New output contains Markdown only. No production code, configuration, database mutation, packages, weight downloads, training, model inference, build, Sonar scan or proof-of-concept execution.

## Future checks and handoff

Recheck checkpoint/code/package/license contracts before authorized model execution, especially TTM loader/class/runtime and GraphCodeBERT weight permission. Small-card/source availability does not prove successful loading, sufficient memory, calibration or debt forecasting efficacy. The earliest runtime/license review date is 2026-11-13, or before execution if earlier; data/checkpoint/policy changes invalidate the matching study assumptions.

The proposed `forecasting_mvp` module/CLI does not exist now. Its filenames, parser arguments, tests and examples are future implementation contracts. Implementation begins only on explicit user authorization, starting at M0, with the M1 data and M2 real-forecast gates before the dashboard. Unsupported horizons/features remain partial or blocked; no fabricated metrics or automatic `bmad-build` handoff.
