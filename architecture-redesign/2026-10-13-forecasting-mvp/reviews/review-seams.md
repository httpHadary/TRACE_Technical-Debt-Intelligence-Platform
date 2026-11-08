# BMAD rubric walker and adversarial seam review

Date: 2026-10-13. Reviewed all six requested MVP documents plus README and source-backed reuse evidence. This is an independent final-gate design review, not implementation verification. The requested lens constructs two independently built components that each obey the written plan but could disagree at a shared boundary. No models, tests, scanners or production commands ran.

**Verdict:** the simplified forecasting-first plan is coherent after the clear corrections below. The architecture binds the completed CLI contracts and data-audit-frozen primary-track default rule. Final root reconciliation applies that same rule to all six deliverables. Data, license and hardware gates remain execution prerequisites, not silent design omissions or achieved research results.

## Good-spine rubric

| Dimension | Assessment |
|---|---|
| Real divergence points | Artifact ownership, canonical IDs, source/domain/scope, clocks, target durations, past-only requests, phases, failures, publication and current ranking are bound. |
| Enforceable ADs | AD-1–7 have Binds/Prevents/Rule and practical artifact/test enforcement. Phase projections and restricted execution are concrete implementation checks rather than broad assurances. |
| Brownfield reconciliation | Existing module schema/CLI, synthetic outputs, CMR90 labels and V3 recovery are accurately bounded. New repository/HF/API modules are explicitly proposed. |
| Required capabilities | Historical dataset and real pretrained errors precede UI; exact 30/60/90, current Git/Sonar, conditional GraphCodeBERT, explainable priorities and minimal API/dashboard are covered. |
| Deferred boundaries | Multitenant/distributed/remediation features are excluded from this local operating model; essential credential, integrity and failure protections remain. |
| Environment and operations | One operator, localhost GET API, immutable files, serial isolated model runtimes, bounded CPU/memory/time and current build/scanner isolation are stated. Hardware remains an explicit budget assumption. |
| Parent continuity | This is a newly scoped MVP, not an edit weakening the preserved earlier initiative. Earlier data/model/provenance principles remain; experiment-first A/B contribution selection is explicitly superseded by the user's forecasting-first request. |
| Technology evidence | Named HF contracts and dataset evidence are source-verified in research-check; no local efficacy or CPU speed is assumed. Backend/parser/runtime versions are setup admission pins. |
| Effort and completion | 116–166 team-hours sums correctly; 20% reserve gives 139.2–199.2 hours. At stated 20 team-hours/week, complete platform is about 7–10 weeks, research core about 4–6. Conditional/partial completion is explicit. |
| No hidden next-stage implementation | CLI commands and tests are contracts for later authorization, not commands executed here. |

## Constructed divergent pairs and fixes

### 1. Training labels versus evaluator-only labels

- **Location:** Architecture AD-4/shared labels and Experiment Step 5.
- **Trigger:** trainer obeys a blanket “evaluator-only labels” rule and cannot fit CatBoost; another trainer reads the full label file because fitting obviously requires labels.
- **Guard:** publish distinct train/validation/test label projections; trainer gets train only, validation evaluator supports tuning, final evaluator opens test only after freeze. Prediction subprocess receives a projected past-only folder, never the whole dataset.
- **Consequence:** either implementation is blocked or future outcomes leak into fitted/zero-shot predictions.
- **Disposition:** corrected in architecture and owned experiment prose. The foreground CLI's dataset path is an orchestration input, not a model-process mount.

### 2. Three endpoint IDs versus one native path

- **Location:** Architecture AD-1 and prediction contracts; Experiment Steps 3–4.
- **Trigger:** one runner treats a 90-step request as one forecast ID; evaluator expects different 30/60/90 target identities.
- **Guard:** target/horizon/track/context/source policy belong in endpoint `forecast_id`; `request_id` groups one core90 model path. Endpoint extraction uses native indices 29/59/89. Canonical split/model IDs are owned and hashed consistently.
- **Consequence:** prediction overwrites, horizon collisions or incorrect actual joins.
- **Disposition:** corrected by explicit ID bindings in AD-1. Endpoint records remain one per registered target.

### 3. Quantile and raw-value retention versus endpoint-only CSV

- **Location:** Architecture shared files and forecasting metrics.
- **Trigger:** runner saves only q10/q90 and clipped point; evaluator must calculate native decile pinball and clipping analysis.
- **Guard:** retain raw/clipped point and decile endpoint values, point semantics and optional native `forecast_path.csv`; evaluate endpoint deciles against real endpoint labels only.
- **Consequence:** missing required evidence, invented intervals or a full-path score against unobserved intermediate outcomes.
- **Disposition:** corrected in shared artifact contracts. MAE/RMSE and signed derived delta remain stock-consistent.

### 4. Strict history versus masked sensitivity

- **Location:** Architecture past_grid and forecasting missingness tracks.
- **Trigger:** schema allows only MEASURED/REUSED states but a second implementation emits missing grid points for the explicitly permitted masked sensitivity study.
- **Guard:** explicit `MISSING_STATE`, nullable revision/observation/value and reason; `core90` rejects it. A data-only G2 failure may activate a preregistered `masked90` primary before model outcomes, with at least 80% known context, known origin and exact observed endpoints. Track/threshold are frozen and never pooled with TTM complete contexts.
- **Consequence:** invalid files or historical padding silently entering the primary cohort.
- **Disposition:** corrected in shared schema. Forecast coverage and repeated-state counts remain reported separately from independent temporal units.

### 5. Current Java units versus arbitrary function extraction

- **Location:** M4, model annotations, architecture module ownership.
- **Trigger:** one developer uses regex snippets and another full methods; both claim GraphCodeBERT Java inputs with original coordinates.
- **Guard:** pinned compatible Tree-sitter Java/Python parser; method/constructor nodes only, UTF-8 immutable blobs, parser-error abstention, byte/line ranges and extractor hash before exact author normalization. Overlength and mapping/license gates remain separate.
- **Consequence:** incomparable predictions and misleading line evidence.
- **Disposition:** corrected with `java_units.py` contract. Twenty-function smoke pilot checks engineering contracts, not detection F1 or debt absence.

### 6. Build sandbox versus credentialed scanner destination

- **Location:** AD-6/current collection.
- **Trigger:** one wrapper isolates build credentials but still lets repository scanner settings redirect the credentialed scanner; another mounts the user's home/cache to obtain dependencies.
- **Guard:** non-root restricted rootless build, approved mounts and fixed limits; prior credential-free dependency acquisition; trusted generated scanner configuration forces approved server/project/revision/scope, with no source-controlled scanner commands or secret destinations.
- **Consequence:** host or credential exposure despite both wrappers claiming isolated execution.
- **Disposition:** corrected in AD-6. Unavailable local runtime blocks collection rather than authorizing unrestricted host builds.

### 7. Track champion versus one horizon default

- **Location:** Experiment Step 5, architecture AD-7, roadmap M3.
- **Trigger:** one app picks the registered primary-track champion; another chooses lower MAE from TTM90's selected 512-day-context cohort. Both obey “one best predictor per horizon.”
- **Guard:** the data-audit-frozen primary track (`core90` or `masked90`) supplies the per-horizon default research replay; optional complete-context track champions are distinct comparator records. No cross-track raw MAE ranking, no transferred current-domain serving claim.
- **Consequence:** the dashboard advertises a winner selected on easier/different data.
- **Disposition:** experiment corrected to the registered primary track. Root applies the same bounded clarification across architecture, forecasting, scope and roadmap.

### 8. Complete scientific runner versus incomplete application CLI

- **Location:** Experiment command contracts and M4–M5.
- **Trigger:** one developer adds arbitrary scanner/serve flags; another omits current evidence/assembly because the experiment names only audit/build/split/predict/evaluate.
- **Guard:** fixed proposed foreground contracts for fit, register, collect-current, annotate, prioritize, assemble and serve; immutable input manifests, fresh output paths, localhost-only GET API. Fitted candidate IDs carry setting hashes; no arbitrary shell/SQL arguments.
- **Consequence:** implementation requires unplanned architecture choices or cannot complete repository-to-dashboard flow.
- **Disposition:** experiment includes exact required argument contracts and outputs; architecture now binds the complete enum. Evaluator owns validation decisions/setting-specific model registry; assembly only validates/packages immutable completed bundles. No services added.

## Other seams checked without findings

Current maintainability finding rank stays separate from forecasting/research watchlists and classifier annotations. Estimated minutes are never converted to developer labor. Imported native project stock is separate from production-Java aggregates and current analyzer domain. Unknown endpoints do not become zero; unmeasured changed states cannot use earlier measured stock. Source-end censorship and 90-versus-91 distinctions are explicit. Nonempty purged phases and held-repository blocks are execution gates; small cluster intervals remain exploratory. Negative pretrained results can complete the research comparison but absent pretrained predictions cannot complete its AI feature.

## Final bounded data-feasibility clarification

A strict-only complete 90-day grid can unnecessarily block a model whose native contract supports missing-value masking. Conversely, selecting a masked track after seeing errors can become outcome-driven cohort tuning. The agreed guard audits `core90` first, then permits `masked90` as primary only if the strict data-only gate cannot provide six eligible projects, two untouched repository tests and nonempty purged phases. Require at least 80% known past daily values, known origin and exact observed future endpoints; freeze track/threshold/selection/splits/features before model outcomes. Missing historical states remain missing, supervised mask/coverage summaries and training-only transforms are explicit, and future labels are never imputed. TTM comparisons retain complete native contexts and separate cohorts. Report limited-data findings as limited-data findings, not complete-history claims. This expands feasible admission without increasing infrastructure, inventing data or modifying the scientific question after results.

## Editorial changes in assigned files

Polished joined prose only in MVP_EXPERIMENT_PLAN, MVP_EXECUTIVE_SUMMARY and README, preserving code paths, identifiers, commands and numerical facts. Added phase-projection explanation, fitted-control commands and bounded current/platform CLI contracts to resolve concrete execution seams. Root-owned architecture/forecast files and other-agent scope/roadmap files were not edited by this reviewer.
