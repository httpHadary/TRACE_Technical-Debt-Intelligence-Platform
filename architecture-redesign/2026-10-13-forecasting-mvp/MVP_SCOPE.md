# TechDebt360 forecasting MVP scope

Date: 2026-10-13. Status: **proposed implementation plan; no implementation or experiments executed**. Audience: two contributors and the graduation-project supervisor. The team has **20 contributor-hours/week**: two people at 10 hours each. Hardware is unknown.

## Product and research objective

Build a local, single-operator platform that measures repository technical debt, reconstructs audited history, and evaluates **pretrained forecasts of repository maintainability burden at exact 30/60/90-day cutoffs**. The target is SonarQube `SQALE_INDEX` in **estimated remediation minutes**, not developer labor, financial cost or a classifier probability.

Chronos-2 Small is the first pretrained forecaster. Persistence, bounded trend, Ridge and CatBoost are controls; Granite TTM is the compact alternative when its actual context fits the admitted history. LightGBM is a bounded optional comparator, not a second required production model. Pretrained Java classification uses GraphCodeBERT when weight permission, preprocessing, labels and loading pass their gate. Classification remains a separate exploratory output and does not determine the numerical target or inflate it.

This scope supersedes the earlier paired forecasting/remediation thesis-selection rule: the user now selects **forecasting as the primary research objective**. A well-designed negative forecasting result is valid research. It does not authorize claims of useful prediction or invent a successful AI result. Remediation is outside this MVP.

## Mandatory and bounded capabilities

| Capability | Minimum deliverable | Completion boundary |
|---|---|---|
| Repository ingestion | Operator registers an existing local Java Git repository, explicit ref and frozen tip; reads ancestry, dates, tree and trailing activity | One current demonstration repository; public V2 repository registry for research |
| Current Sonar measurement | One completed, revision-bound, paginated export with native project SQALE, raw evidence and analyzer/scope identity | No automatic scanning from browser; build/scan manually controlled |
| Historical dataset | Audited V2 project/Git/measure joins, causal state grid, exact endpoints, eligible IDs and purged splits | Start from already-local DB; six metadata-selected pilot repositories, expand to up to 31 after the policy freezes |
| Pretrained forecasting | Real Chronos-small output for admitted histories, exact endpoint extraction and failures recorded | All three horizons are planned and separately admitted; unsupported horizons are visibly unavailable |
| Evaluation | Actual endpoint SQALE versus predictions, MAE/RMSE, baseline skill, coverage, uncertainty and runtime | Pilot results distinguished from sealed final results; no numerical placeholder portrayed as a result |
| Explainable priorities | Current maintainability findings ordered by documented severity and compatible estimated burden | Forecast comparisons are a separate research watchlist; no arbitrary mixed AI score |
| Pretrained detection | GraphCodeBERT Java annotations with exact four-type contract, source coordinates and coverage | Conditional on license/loadability; otherwise explicit blocked feature, not claimed completion |
| API/dashboard | One local read-only API and static dashboard showing history, predictions, evaluations, findings and provenance | One host, one operator, offline completed artifacts; no job submission endpoint |

The platform must include real pretrained forecast predictions to call the AI-forecasting MVP complete. It may deploy persistence or CatBoost as the default when pretrained models lose; the pretrained research comparison remains visible. A dashboard with synthetic charts alone is not this deliverable. A forecasting study with only 30-day evidence is a **partial-horizon MVP**, not a completed 90-day capability.

## Explicit exclusions

Defer autonomous remediation, patch generation/approval, Qwen/SonarSweep, semantic retrieval, coupling models, graph neural networks, full Chronos/TimesFM, pretrained fine-tuning, model ensembling, module/file forecast deployment, enterprise authentication, tenants, distributed queues, fencing, capability grants/revocation services, Kubernetes, external hosting and automatic retraining. Keep existing module lineage, graphs and datasets intact for later studies. Do not delete historical package copies.

Essential controls remain: local binding, operator-only commands, credential separation, fixed execution arguments, restricted build workspace, exact revision/domain binding, complete exports, bounded resource use, immutable checksummed artifacts, failure states, missingness and label isolation. Simplification does not remove the collector's integrity proofs or allow arbitrary browser commands.

## Evidence and feasibility limits

The [same-date data audit](../2026-10-13-refinement/digests/data-reaudit.md) established 31 V2 projects and 66,711 project measurements; this planning turn rechecked the three table counts. It also found 19,954 unmeasured commits within measured spans. Thus daily grids and exact future labels must be **constructed and validated later**, not inferred from row totals. V2 imported historical timestamps are not proof of historical scan execution or online availability.

Repository-level V2 data is the strongest starting point. No admitted real module cohort was demonstrated by the earlier bounded inventory. NPFDataSet's published labels are 21/28/91-day all-issue effort and its license is unresolved; it is not ready exact-30/60/90 maintainability data. Current scans and imported V2 history remain separate analyzer domains. A current demonstration repository does not inherit V2 accuracy merely because both are Java.

## Success and stop criteria

1. **Data success:** each scored target resolves to an exact reachable state with a compatible measured value; no carried value crosses an unmeasured change. Grid, endpoint, domain and split audits are reproducible. Complete context is preferred; a data-audit-frozen masked90 fallback preserves missing past values and observed endpoints, with narrower claims. Imported-domain unknowns remain explicit.
2. **Engineering success:** all three requested targets have valid forecasts and actual outcomes for an admitted research cohort, or a clear partial/blocked report; every result traces through source, target, dataset, split, checkpoint, runtime and prediction hashes.
3. **Research success:** fair comparisons include persistence and a debt-specific model, with per-horizon/repository MAE/RMSE and failures. No superiority is assumed. Meaningful negative or inconclusive findings count as completed research, subject to supervisor approval of the bounded claim.
4. **Forecast promotion:** select the champion using development/validation only. A proposed useful-effect threshold is 10% macro MAE improvement over the strongest eligible simple baseline; held-out confirmation and clustered uncertainty determine whether superiority is supported. This is a project decision, not an established universal threshold. Low precision yields exploratory results.
5. **Platform success:** one real current analysis plus the audited historical research replay are accessible through the API/dashboard, with explicit domains and unsupported current forecasts. GraphCodeBERT is integrated where admitted, or visibly blocked with the feature and study limitation stated.

If M1 cannot admit enough histories, invoke the fixed acquisition ladder in [forecasting plan](MVP_FORECASTING_PLAN.md), with a maximum 12 additional engineering-hours before reassessing. Long retrospective scan collection or license negotiations are separate work, not silently absorbed into the 4–6-week target. If forecasting remains blocked, the strongest alternative is a bounded pretrained Java debt-type detection study with independent labels, clean/OOD controls and no remediation claim. It requires its own revised scope and authorization; planning it does not execute it.

## Schedule contract

Core plan: **116–166 contributor-hours (14.5–20.75 eight-hour person-days)**. At 20 hours/week this is 5.8–8.3 weeks without reserve, or **about 7–10 weeks with 20% contingency**. The first real forecasting/evaluation package is budgeted at 64–94 hours before the dashboard: approximately 4–6 weeks with contingency. See the [roadmap](MVP_IMPLEMENTATION_ROADMAP.md) for arithmetic and capacity dependencies.

No implementation starts until explicit authorization. All future filenames, commands, tests, scans and model loads in this package describe later work.
