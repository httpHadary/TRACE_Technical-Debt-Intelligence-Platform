# Refinement verification and review resolution

Date: 2026-10-13. The five requested revised planning deliverables are present, with fresh model and data digests, a 13-decision BMAD spine and independent review records. This verifies the **design package**, not model loading, experimental accuracy or implemented product behavior.

## Scope and methods

Used installed BMAD deep-recon, architecture and review methods. The user supplied the revised scope and experiment-first decision frame, so the earlier plan was deepened rather than restarted. Project `_bmad` configuration and helper scripts remain absent; no setup, installation or configuration change occurred. Standalone lint, word-metrics, citation and freshness checks without installation were used where applicable; the new output memlog records decisions and assumptions.

Writes are confined to new Markdown documents in this refinement folder. Original code, configuration, old design documents and the old ZIP were preserved. SQLite reads used `mode=ro`. No scans, builds, tests, training, inference, label generation, POC execution or production modifications occurred. New harness commands are explicitly proposed, not existing software. Existing CLI options were source-inspected, not executed.

## Independent review and fixes

| Review | Important resolution |
|---|---|
| [Model strategy](reviews/review-model-strategy.md) | All 11 exact models rechecked; short-context TTM and immutable-class dispatch; classifier label, sigmoid and license semantics; native outputs versus proposed schemas; unmeasured resources |
| [Forecast feasibility](reviews/review-forecast-feasibility.md) | Exact as-of state reuse and censoring; joined timestamps versus eligible cohorts; metadata segments versus Java rule changes; corrected independent counts |
| [Architecture](reviews/review-architecture.md) | Task/dataset-scoped capability grants, feature/label separation, forecast-to-ranking utility gate, owned immutable IDs and policies, learned-only ENGINEERING_CHECKED plus independent outcomes |
| [Experiments](reviews/review-experiments.md) | Separate analyzer-target and learned-only repair denominators and status/verdict axes; untouched final cohorts; matched forecasts and retrieval budgets; precision and future-only commands |
| [Roadmap](reviews/review-roadmap.md) | 38–64-day arithmetic, capacity and contingency assumptions, reviewer hours separately estimated, core A/B studies before primary selection |
| [Final spine](reviews/review-final-spine.md) | AD-5/9/10/13 and five companions reconciled; README, prose and links checked; remaining experimental prerequisites explicit |
| [Research notes](reviews/review-research-notes.md) | Numeric citations reconciled with artifact and upstream sources; historical timestamps and unexecuted experiments explicitly bounded |

Critical seams are closed in the design. Remaining unknown licenses, runtime and cost, gold labels, state eligibility and model outcomes are future prerequisite gates rather than omitted engineering decisions. Reviews preserve their initial findings and correction history.

## Mechanical checks

- Required files: REVISED_ARCHITECTURE, PRETRAINED_MODEL_STRATEGY, FORECASTING_FEASIBILITY, RESEARCH_EXPERIMENTS and REVISED_IMPLEMENTATION_ROADMAP—all populated.
- BMAD spine lint: zero mechanical findings; AD-1 through AD-13 have Binds/Prevents/Rule; stable old IDs retained with explicitly amended or new research rules.
- Research-notes numeric citations match source rows; semantic primary-source model and data checks are documented in digests and independent reviews.
- Research ledger: eight tracked claims, six verified artifact/source/audit contracts and two unverified data-quality/efficacy claims. Verification of contracts does not imply local model performance.
- Freshness review uses the 2026-10-13 retrieval date as a review anchor, not a publication date. Recheck runtime, loader and license compatibility by 2026-11-13, and model-selection assumptions by 2027-01-13, or earlier before execution if upstream changes.
- Local Markdown links and balanced fences checked across the folder; Mermaid diagrams inspected for meaningful workflow and dependencies. No diagram-rendering package installed.
- Source preservation compares 122 captured original source, previous design and selected evidence hashes: zero changed in the final verification pass.
- Output contains Markdown only; the old design and ZIP were not regenerated or overwritten.

## Final recommendation and limits

Architecture: capability-aware pretrained hybrid. Provisional model roles: one GraphCodeBERT/CodeBERT classifier, CodeRank if useful, Qwen 7B and one validated forecast champion. Core comparative controls include Chronos-small/full, eligible TTM branches, TimesFM and conventional baselines. Preserve TechDebtClassifier, CodeAid and SonarSweep as task- and resource-gated extensions rather than treating them as solutions to the same problem.

Repository-level V2 forecasting is a serious candidate; own module 30/60/90-day production readiness remains unsupported. Future as-of reconstruction and measured endpoint states may support more cohorts than exact-date pair counts imply; unmeasured changed states still cannot be filled. V2 analysis `DATE` is a naive imported historical timestamp matching joined Git times, not evidence of actual historical scan execution. TTM short-context branches improve admission but do not prove local forecast accuracy.

Next execution requires separate authorization: resolve prerequisites, register cohorts, load and check contracts, then run A forecasting and B detection and verified repair. Only their evidence selects the primary contribution. Learned-only engineering checks and independent acceptance remain separate from analyzer-target verification. No automatic implementation or `bmad-build` handoff is performed.
