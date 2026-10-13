# Milestone-by-milestone MVP implementation roadmap

Date: 2026-10-13. **Future work only; no coding authorization is implied.** Capacity confirmed by user: two contributors, 10 hours/person/week = 20 team-hours/week. An eight-hour person-day is only an effort unit; neither person is assumed full-time. Hardware, Sonar access and a deadline were not supplied.

## Estimate and critical path

| Milestone | Contributor-hours | Eight-hour person-days | Dependency | Owner and concrete artifact |
|---|---:|---:|---|---|
| M0 freeze inputs/setup |4–6|0.5–0.75|Explicit authorization|A/B: source/resource/license registry |
| M1 verified historical dataset |24–36|3–4.5|M0|A leads, B reviews: audited import, grids, labels, splits |
| M2 first pretrained predictions and actual-error comparison |16–24|2–3|M1|B leads, A validates joins: Chronos/persistence validation report |
| M3 debt-specific controls and frozen final study |20–28|2.5–3.5|M2|B models, A integrity: final MAE/RMSE/uncertainty bundle |
| M4 current Git/Sonar and GraphCodeBERT evidence |20–28|2.5–3.5|M3 recommended; limited prep may parallel M1|A scan/export, B classifier: current evidence bundle |
| M5 read-only API/dashboard |24–32|3–4|M3, M4|B UI, A routes/schema: local end-to-end application |
| M6 reproducibility and handoff |8–12|1–1.5|M5|A/B: replay checks, demo, report and limitations |
| **Total** |**116–166**|**14.5–20.75**| |All MVP capabilities subject to data/license gates |
| **20% reserve** |**23.2–33.2**|**2.9–4.15**| |Data/runtime/integration uncertainty |
| **Total with reserve** |**139.2–199.2**|**17.4–24.9**| |**7–10 calendar weeks at 20 hours/week** |

Critical path: M0→M1→M2→M3→M4→M5→M6. Parallel code reading, schema work and UI mockups do not remove the serial data/real-result gates. Estimates are total team effort including ordinary peer review and documentation. The optional 12-hour acquisition ladder consumes reserve, not a free extra team. Major rebuilds, GPU procurement, license waits, broader labeling, long scan collection and supervisor scheduling are outside the estimate and add wall time. Machine-hours are not person-hours but shared hardware can create waiting.

The first major deliverable is M1, followed by M2 predictions versus **validation ground truth**, before dashboard work. M0–M3 total 64–94 hours, or 76.8–112.8 hours with reserve: approximately 4–6 weeks. The complete MVP cannot responsibly be promised in 4–6 weeks at the stated capacity. A 4-week hard limit would require narrowing the research core; its upper estimate does not fit that limit.

Unless a repository-relative path is shown, implementation module filenames below are relative to the new `forecasting_mvp/` package. Research artifacts belong under `research/forecasting_mvp/`; existing source paths are reuse references, not instructions to overwrite them.

## M0 — Freeze resources and inputs

**Tasks/files:** create additive `forecasting_mvp/contracts.py`, `io.py`, `cli.py`, `__init__.py`, `__main__.py` and `research/forecasting_mvp/studies/study-001/study.json` in the future implementation. Source root is `/home/hp/tst/td_pipeline_module_level/td_pipeline`. Record old Git state/pre-existing modifications; do not clean them. Inspect legacy dependency lock and preserve it. Prepare separate pinned research/model environments, retaining Python 3.12 seed where supported. Small dependency/weight installs occur only during later authorized execution, not this planning task.

**Inputs→outputs:** V2 DB/release, exact model revisions, local Git/Sonar paths, capacity/hardware inventory → input hashes, scope/target policies, license decisions and reproducibility registry. Include RAM/CPU/GPU, free disk and Sonar availability; checkpoint/source/runtime versions are distinct pins.

**Dependencies/models:** already-local V2; Chronos-small Apache-2.0; CatBoost existing dependency. GraphCodeBERT license unresolved. Use small metadata/source checks before any weights. Publish TTM conditional admission rather than requiring it for M0 completion.

**Acceptance/tests:** schema round-trip preserves UTC/null/signed delta; path traversal rejected; wrong/partial bundles rejected; unknown-source licenses marked blocked; SHA verification can detect a deliberately altered test artifact. These are future software tests, not evidence of forecast accuracy. Freeze a 15-minute/model smoke budget and 8-machine-hour pilot budget. Hardware shortage yields explicit resource block, not a fabricated GPU assumption.

**Risk/fallback:** impossible runtime compatibility → isolated supported environment; no hardware fit → smoke smaller batch on supported CPU and measure, otherwise keep preload blocked and revise budget. Do not substitute full Chronos/Qwen or install into legacy environment.

## M1 — First major milestone: audited historical dataset

**Tasks/files:** implement `v2_import.py`, `observations.py`, `git_state.py`, `targets.py`, `splits.py`, `features.py`. Reuse strict scalar parsing/hashing/publication patterns in legacy `contracts.py` and Git ancestry concepts in `forecasting/git.py`; avoid blindly importing modules with workspace-global configuration. Implement exact joins and complete mainline-state selection as [specified](MVP_FORECASTING_PLAN.md). Audit all 31 metadata histories, freeze up to six pilot repositories by metadata-only policy, and expand later without changing target semantics.

**Inputs→outputs:** read-only V2 tables/parents/profiles + exact 30/60/90 target policy → `repositories.json`, `observations.csv`, `past_grid.csv`, `features.csv`, evaluator-only `labels.csv`, `targets.json`, `splits.json`, `dataset_audit.json`, COMPLETE manifest. Every future endpoint has a raw measurement ID/revision or null/reason. Keep source/time/domain limitations.

**Dependencies/models:** M0; no model inference/training required. Label construction uses actual raw project measurements, not model-generated values. Publish linkage quality `AUDITED_IMPORTED` distinct from own-scan status.

**Acceptance/tests:** hand-check 12 pilot states/endpoints; detect blank/duplicate joins and mismatched revisions; preserve observed zero versus missing; unchanged revision reuse works; unmeasured changed state remains null; backwards/missing-parent chains censored; no cross-domain target; exact 30/60/90 elapsed-day cutoffs versus a 91-day target; endpoint outside archived history unavailable; features after origin rejected; training-label windows crossing validation purged; held repositories absent from fit/tune lists; hashes before/after DB identical. Tests include adversarial fixtures and real raw-record spot checks, with separate reports.

**Measurable gate:** six admitted pilot repositories, two untouched repository tests, nonempty purged phases and reported non-overlapping windows is the target. If unavailable, publish truthful insufficiency/case-study status. No row-count-based sufficiency declaration. M2 cannot invent a cohort to get past this gate.

**Risk/fallback:** incomplete dense context → report coverage and metadata-only wider V2 selection; if core90 fails the data-cohort gate, freeze masked90 as the primary limited-data track before any model output, with the exact 80%/known-origin/observed-endpoint policy in the forecasting plan. Never pool tracks or choose by outcome. Invoke at most 12 extra engineering-hours acquisition/recovery ladder only after these audits, charged to reserve. Current scans cannot fill V2's old analyzer domain.

## M2 — Actual pretrained predictions before the dashboard

**Tasks/files:** implement `adapters/chronos.py`, target-only request/response validator, persistence/trend controls in `adapters/tabular.py`, initial `evaluate.py`; add proposed isolated runner environments under `research/forecasting_mvp/environments/`. Pin Chronos-small checkpoint plus upstream code/environment. Run one real validation-series smoke case; verify timestamps/axes/native q50/deciles and no label columns in inputs. Then predict the frozen pilot validation origins.

**Inputs→outputs:** registered primary-track 90-day historical grids + validation split IDs → 90 native forecast steps/origin, endpoint 30/60/90 predictions, raw quantiles, failures/runtime/memory; evaluator joins actual validation endpoints → first real `predictions.csv`, `evaluation.json`, `FORECAST_VALIDATION_REPORT.md` and plot. Complete or masked context is explicitly labeled. Data bounds or failure should be explicit, never replaced with synthetic numerical results.

**Dependencies/models:** M1, licensed/downloadable Chronos-small and controlled runtime; persistence/trend. Train nothing neural. Model loading and prediction occur only after later coding/execution authorization.

**Acceptance/tests:** indices 29/59/89 match the target UTC timestamps; ID alignment survives reordered adapter output; q0.1/q0.5/q0.9 levels and point semantics not mislabeled; bad frequency, wrong shape and label-column injection rejected; failure coverage emitted; arithmetic MAE/RMSE checked against a hand-computable fixture; actual measurement IDs visible in real report. A real forecast and real later measurement for each admitted horizon is mandatory. If a horizon lacks data, report partial scope.

**Risk/fallback:** latency/OOM → serial batch 1, supported CPU/GPU measured without changing model semantics; one bounded retry; still failing → report a runtime block, do not claim a completed pretrained MVP. No dashboard milestone can bypass M2. Validation errors are exploratory, not sealed test superiority.

## M3 — Comparative evidence and frozen default

**Tasks/files:** finish `adapters/tabular.py`, `evaluate.py`, model-card/decision output, implement `adapters/ttm.py` only after context/resource admission. Fit Ridge/CatBoost per horizon on past-only features. Check TTM 30 first, then 60/90 if their native 180/512 contexts and complete matched cohorts exist. LightGBM only within its 4-hour optional cap. Record lack of context as `NOT_ADMITTED_CONTEXT`, distinct from poor accuracy. Freeze choices before opening test labels.

**Inputs→outputs:** immutable train/validation manifests + model candidates → fitted controls/checkpoint contracts, validation-selected primary-track default per horizon, separately labeled matched-track comparator results, locked final predictions and joined real test errors; `MODEL_COMPARISON.md`, model registry, environment locks and final limitations.

**Dependencies/models:** M2; CatBoost and Ridge mandatory; TTM conditional independent comparator. No requirement to install every forecaster. Keep normal runtime to one selected predictor; research controls remain artifact outputs.

**Acceptance/tests:** all models share exact cohort/context in each track; supervised preprocessing/tuning never reads tests; altered labels do not alter a frozen past-only request hash; mismatched IDs/checkpoint/target rejected; TTM branch and class selected explicitly with SHA, quantile axes and mean-slot preserved; context padding and 91→90 substitution rejected. Report per-repo/horizon MAE/RMSE, macro/pooled values, persistence skill with zero-denominator handling, native 80% coverage/width/pinball, failure counts, constant/changing cases and runtime. Pair uncertainty at repository level; small cluster counts remain exploratory.

**Decision:** validation selects defaults; test can invalidate superiority but does not tune a new winner on test. A losing pretrained model remains a documented comparator. If all sophisticated models lose, persistence serves as default and the thesis reports the negative result. Sparse tests do not authorize production claims.

**Risk/fallback:** 512-point context unavailable → defer TTM 90, continue Chronos 90; no TTM runtime → document the block; too few unseen repositories → temporal case study with narrowed claims. Extra ablations/full models/neural fine-tuning are outside the estimate.

## M4 — Current repository analysis and optional pretrained annotations

**Tasks/files:** add `ingest.py`, `sonar_project.py`, `java_units.py`, `graphcodebert.py`, `prioritize.py`; wrap the existing collector/scan/export behind explicit operator inputs. Use the architecture's pinned Tree-sitter method/constructor extraction and byte/line-coordinate contract. Change legacy source only if a narrow additive project-export hook is necessary, documented in a separate commit; do not rewrite scanner/evidence protocol. Preserve existing scan proofs and locks. Registry takes local path/ref/frozen-tip; source reads use immutable objects, not mutable working-tree files.

**Inputs→outputs:** one registered current Java repo + operator-controlled compatible Sonar analysis → native project maintainability stock, complete issue export, severity/minutes priorities and raw manifest. Source functions + licensed pinned GraphCodeBERT → four exploratory type scores, original coordinates, preprocessing/coverage and blocked reasons. Current evidence uses own domain, separate from imported V2 results.

**Dependencies/models:** M3 to keep results first; functioning Sonar/scanner/build environment. GraphCodeBERT exact checkpoint/license/label/preprocessing confirmation. Resolve permission before fetching weights. No CodeRank/Qwen/remediation integration.

**Acceptance/tests:** completed CE and exact analysis/revision binding, full project metric/issue pagination, native scope identifier; empty/missing project metrics are not zero. Current totals cannot silently equal production-Java sums. Failed export stays incomplete; retry resumes evidence rather than resubmitting blindly. No scanner token in untrusted build, API or artifacts. Basic Git ancestry/churn output traced to origin. Classifier smoke checks 20 Java functions across two repositories when admitted, explicit 512-token overlength abstention, four independent sigmoid labels with mapping hash, all-zero is not proven clean. Manually check source coordinates and meaningful annotation display; this is a contract/demo pilot, not a robust detection-accuracy claim.

**Risk/fallback:** original V3 recovery inaccessible → one new controlled scan only after future access/setup, with original evidence preserved; incompatible MQR metric mapping → explicit domain adapter or block. GraphCodeBERT permission unresolved → disabled blocked card and recorded partial feature; missing Sonar proof → platform current-analysis requirement remains unmet. No unconditional “MVP complete” when a mandatory ungated feature is absent.

## M5 — Minimal platform

**Tasks/files:** `api.py`, `static/index.html`, `static/app.js`, `static/style.css`, CLI `serve`; implement only routes in [architecture](MVP_ARCHITECTURE.md). File-bundle registry is authoritative; no SQLite ORM/new database/queue/service. Serve static assets with the local API and plain JS/SVG charts. Browser observes completed runs; operators run explicit foreground CLI stages.

**Inputs→outputs:** M3 final study and M4 current evidence → local UI with imported history, exact endpoint forecasts, real error comparison, current priorities, optional annotations and provenance. Show research-only/current unsupported outcomes.

**Acceptance/tests:** API response-schema checks, 404 for unknown bundle, 409 for partial/corrupt bundle, 422 for invalid horizon, and 200 with null for an unsupported forecast; path traversal and source XSS tests; no POST/job/command endpoint. Dashboard selects repository/horizon, separates datasets/domains, plots gaps as gaps, labels the 80% interval and stock minutes, and exposes persistence comparison and measured actual values. One scripted UI smoke journey plus manual current-repo/research-replay trace is enough; avoid a new enterprise E2E framework.

**Risk/fallback:** if UI budget grows, retain one static page and downloadable Markdown/CSV reports; visual polish is deferred. Remote hosting requires separate security scope, not opening localhost API to the network.

## M6 — Reproducibility, demonstration and graduation report

**Tasks/files:** future `research/forecasting_mvp/README.md`, `reports/FINAL_MVP_REPORT.md`, `REPRODUCIBILITY.md`, tests and exact command logs; document licenses/export restrictions, hardware/runtime, split/data/checkpoint hashes and honest negative results. Re-run a bounded subset from frozen artifacts and compare numerical outputs at recorded dtype tolerance; full model re-execution only if unresolved mismatch justifies it.

**Inputs→outputs:** completed artifacts/application → reproduce-one-origin instructions, final metrics table, research-claim limitations, current demo and handoff. Original code/data/license evidence and older results stay retained.

**Acceptance/tests:** source hashes/artifact restore, deterministic non-model stages, recorded model tolerance and checkpoint locks, failure/partial scope pathways, end-to-end trace from repo/revision to actual 90-day label where admitted. Synthetic tests clearly separate from real metrics. Report invalid/ineligible/failed unit denominators. Do not publish data beyond permissions. Completion document lists every blocked horizon/feature.

**Risk/fallback:** insufficient precision → descriptive case/negative feasibility report; no fabricated sample power. Supervisor report acceptance is external scheduling, not a technical test.

## Existing component disposition

The [full source-backed component table](digests/code-reuse.md) is part of this roadmap and gives exact files/line anchors. Reuse Git reads, scalar/IO integrity, collector complete proofs and purged-baseline ideas; simplify foreground operator execution/current-priority display; modify native project export and explicit configuration wrappers; replace nearest-date matching, missing-to-zero targets and row-shift target building in this new track; preserve the legacy module pipeline; defer neural graph interfaces, CMR-90/NPF remediation experiments, the V3 large fixed protocol and historical package copies. No existing component is deleted by this plan.

## Execution authorization and progress rule

After explicit authorization, Codex executes M0, then gates each milestone using its tests/artifacts. Data/hardware/permission failures choose the listed bounded fallback and produce a stop report; they do not require new architecture decisions or allow extra scope. Only a change exceeding the acquisition/resource/capacity budget requires replanning. Current task ends with these documents; no `bmad-build`, scans, training, code generation or deployments follow automatically.
