# Review of MVP scope and roadmap

Date: 2026-10-13. Reviewed only [MVP_SCOPE.md](../MVP_SCOPE.md) and [MVP_IMPLEMENTATION_ROADMAP.md](../MVP_IMPLEMENTATION_ROADMAP.md). Applied the installed BMAD review **structure**, then **prose** lenses, using the Microsoft Writing Style Guide baseline. The parent architecture workflow explicitly authorized this review and small editorial fixes. Project `_bmad` setup remains absent; no configuration or installation was attempted. The standalone word-metrics helper ran through the existing Python interpreter.

These documents help two part-time contributors understand the reduced MVP scope, execute its milestones in dependency order, and distinguish real forecast evaluation from incomplete platform features. Structure models: **Strategic/Context** for scope; **Tutorial/Guide** with a consistent milestone reference schema for roadmap.

## Editorial findings and accepted fixes

| Pass | Original text or section | Revised text or disposition | Changes |
|---|---|---|---|
| structure | Scope: mandatory capability table, explicit exclusions and success/stop criteria | PRESERVE | These distinguish mandatory forecasting from conditional classifier execution and prevent partial-horizon or blocked-feature work being labeled complete. No reduction. |
| structure | Roadmap: estimate table and M0–M6 sequence | PRESERVE | Capacity/critical path precede tasks; each milestone includes files, inputs/outputs, dependencies/models, acceptance/tests and risk/fallback. No reduction. |
| structure | Roadmap: milestone module filenames without repeated package prefixes | Clarify once before M0 that filenames are relative to `forecasting_mvp/` and research artifacts to `research/forecasting_mvp/` | Removes path ambiguity without repeating full paths or changing package design. Existing-source references remain reuse evidence. |
| prose | Roadmap throughout: `two contributors,10hours/person/week =20teamhours/week`, `M3finalstudy`, `context512unavailable`, and similar joined prose | `two contributors, 10 hours/person/week = 20 team-hours/week`, `M3 final study`, `512-point context unavailable`, etc. | Repaired spacing in prose and units; preserved filenames, contract IDs and registered statuses. Consolidated repeated instances into this row. |
| prose | M2: “four-decile semantics not mislabeled” | “q0.1/q0.5/q0.9 levels and point semantics not mislabeled” | Names the planned shared quantile levels accurately; does not invent a four-decile checkpoint contract. |
| prose | Estimate section: “A4week hard limit should fund the research core” | “A 4-week hard limit would require narrowing the research core; its upper estimate does not fit that limit.” | Avoids implying the entire core is guaranteed within four weeks when its reserved upper estimate is 112.8 hours. |
| prose | M5: browser “observes completed jobs” | Browser “observes completed runs” | Keeps vocabulary consistent with the foreground artifact workflow and deferred job infrastructure. |

No scope rewrite or deletion was required. Scope text was already readable and remained unchanged. Roadmap word metrics changed from **1,900 to 2,165 words**; most of the increase reflects restoring word boundaries in joined prose. The path clarification adds context, not implementation scope. Scope remains **1,111 words**. Reduction: **0 words / 0%**; no comprehension aids or acceptance criteria were cut.

## Arithmetic and coverage verification

Recomputed effort from the milestone table:

- M0–M6: **116–166 contributor-hours** = **14.5–20.75 eight-hour person-days**.
- Twenty-percent reserve: **23.2–33.2 hours**; total **139.2–199.2 hours**.
- At **20 total team-hours/week**, reserved elapsed effort is **6.96–9.96 weeks**, consistently rounded to **7–10 weeks**.
- M0–M3: **64–94 hours**; with reserve **76.8–112.8 hours**, or **3.84–5.64 weeks**, rounded to **4–6 weeks**.
- The two contributors' capacity is already combined; no additional parallelism multiplier appears.
- Optional acquisition is capped at twelve engineering-hours charged to reserve; optional LightGBM is capped at four hours. External waits, long backfill and major build repair are explicitly excluded rather than silently absorbed.

M1 produces the audited historical dataset, M2 produces actual pretrained predictions against validation measurements, and M3 performs the frozen comparative study before M5 dashboard work. Every milestone lists future module/files, input/output artifacts, dependency/model conditions, tests or measurable gates, and fallback behavior. M4 includes current Git/Sonar evidence and conditional GraphCodeBERT annotations; inability to obtain current scan proof or pretrained forecast output cannot be reported as a completed full platform. GraphCodeBERT license blocking is distinct from poor accuracy, and partial-horizon results remain explicit.

All local Markdown links resolve in these two documents, and fenced blocks are balanced. No production files, previous planning packages, databases or configuration were changed. No builds, tests, scans, training, inference or implementation experiments were executed. This review verifies the planning artifacts, not the feasibility gates or model performance.

Remaining uncertainty is properly assigned to execution gates: usable exact-cutoff cohorts, actual runtime/hardware, current Sonar access, classifier permission and statistical precision. The 7–10-week estimate is a scenario conditional on those prerequisites; it is not a promised completion date.
