# Persistence-only MVP continuation roadmap

Implementation update — 2026-10-30: the persistence input/evidence pipeline,
sealed bundles, evaluator and read-only API/dashboard are implemented in
`forecasting_mvp/persistence_flow.py`, `api.py` and `static/`. See the
[implementation report](../../PERSISTENCE_IMPLEMENTATION_REPORT.md) and
[exact operator commands/schemas](../../forecasting_mvp/PERSISTENCE.md).
A new real current-repository scan/demo and calendar data/evaluation admission
remain separate gates. Earlier future-tense statements below record the approved plan.

Updated: 2026-10-30. The user selected persistence as the only active forecaster. Follow the [active workflow](MVP_FORECASTING_PLAN.md). Chronos/hybrid results and code remain archived; H1–H3 hybrid work, neural inference, fitting and model-selection stages are removed from the active roadmap.

Existing ingestion, targets/splits, persistence and research evidence already exist. Continue integration rather than rerunning completed studies. Paths below are relative to `TechDebt360-MVP/`; all additions remain planned. A owns data/integrity and B owns presentation/integration, under the prior two-person capacity assumption. No new deadline is asserted.

| Package | Action/files | Dependency | Acceptance |
|---|---|---|---|
| P0: bind persistence evidence | Audit original principal source/target/clock and persistence rows in authorized frozen results | Start | Original identities/hashes and 678 endpoints reconcile; no neural imports or rerun |
| P1: persistence bundle bridge | Add `forecasting_mvp/comparison_bundle.py`, focused `tests/test_mvp_comparison_bundle.py`; reuse existing persistence/IO helpers | P0 | Only persistence forecast rows; exact origin stock at every horizon; zero delta/null interval; reject wrong target/clock, missing origin and tampered evidence; preserve original artifacts |
| P2: read-only dashboard | Add `forecasting_mvp/api.py`, `static/index.html`, `static/app.js`, `static/style.css` and focused API checks | P1 | Select repository/horizon; see persistence, history, measured change, actual/error or pending status; no model chooser/job endpoint; malformed units/models fail |
| P3: current measurement/change | Reuse collector/registration and compatible component exports; narrow additive mapping only if needed | P1; UI uses P2 | Revision-bound native total; signed change between compatible observations; new origin uses new measured stock; missing/changed domain stays unavailable/incomparable |
| P4: handoff | Add `reports/MVP_PERSISTENCE_HANDOFF.md` and reproducibility instructions | P2 and P3 | Trace origin → persistence → measured endpoint/error; show failure/pending/calendar limits; no claim of anticipating change |
| C1: calendar readiness | Audit exact-state total-principal endpoints/domain coverage in existing targets/import sources; register persistence-only contract and any new population | May inspect alongside P1 | Genuine exact 30/60/90-day target identity/evaluation coverage or explicit insufficiency; do not relabel revision steps |
| C2: calendar persistence | Publish deterministic persistence forecasts/evaluation on the admitted calendar contract | C1 | Same formula, exact UTC cutoff/measurement joins, sealed outputs before actuals, truthful coverage/exposure |

P1 is the next implementation slice. It does not depend on a pretrained runtime or a hybrid module. Historical replay can ship with explicit partial calendar scope. Current measurement can ship before enough history exists for measured change. Current forecasts can await future actuals without fabricating evaluation.

## Verification and stop conditions

Use meaningful fixtures for observed zero versus missing, signed measured changes, formula identity at multiple horizons, revision/day separation, pending actuals, domain transitions, future-label isolation and corrupted hashes. Check every exported historical persistence value/metric against its frozen source. The API needs focused containment/schema/escaping/read-only checks and one operator journey; no new enterprise test framework.

Invalid origins, unclear source scope/permissions or corrupt evidence stop the affected package and produce a reason. Do not replace missing values or reopen past cohorts. Unavailable per-origin data permit only aggregate research display. Preserve prior reports, approvals, pause decisions and artifacts. No automatic rescan, new model experiment or heavyweight runtime setup belongs to these packages.

Completion requires the persistence display and current measurement demonstration, with each advertised calendar horizon admitted or explicitly partial/unavailable. Forecasting future changes and pretrained AI comparisons are not current completion requirements.
