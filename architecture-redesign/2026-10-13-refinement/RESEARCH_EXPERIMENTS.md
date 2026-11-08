# Two early research experiments and selection protocol

Date: 2026-10-13. **Experiment A tests pretrained numerical forecasting; Experiment B tests pretrained detection, evidence retrieval and verified repair. Neither has been executed.** Complete the prerequisite and paired evidence gates before selecting a primary contribution. Architecture preferences, model-card scores and hardware feasibility are not substitutes for outcomes.

This is a proposed reproducible protocol and future harness contract. Existing command references and proposed interfaces are explicitly distinguished. No package installation, training, inference, tests, scans, label generation or candidate patching occurred in this design task.

## Common registration and controls

Create an immutable study manifest before any model outcome:

```text
study_id, research_arm, primary_question, source_license_decision,
source_hashes, repository_registry_hash, domain_policy_hash,
unit_or_target_contract_hash, eligibility_policy_hash,
train_validation_test_manifest_hash, clone_or_lineage_groups,
model_checkpoint_and_code_revisions, environment_lock,
preprocessing_prompt_and_quantization_hashes,
native_context_horizon_quantile_contracts,
seeds, search_budget, generation_or_forecast_budget,
primary_metrics, failure_denominator_policy,
useful_effect_threshold, precision_plan, stopping_rule,
review_rubric_and_blinding_policy, resource_budget
```

Separate phases: prerequisite audit → small feasibility pilot → frozen comparative study → product promotion. `BLOCKED_LICENSE`, `BLOCKED_DATA`, `NOT_ADMITTED_CONTEXT`, `LOAD_FAILED`, `INCONCLUSIVE_PRECISION`, `NO_ADDED_VALUE` and `VALUE_SUPPORTED` are different conclusions. Only the last, plus operational checks, can support product validation; a scientifically sound negative study can still support a thesis.

Pretrained public-repository contamination may be unknowable. Record publisher training cutoffs where available, group clones and related units, exclude future target patches from prompts and retrieval, and disclose residual overlap. Existing NPF sealed outcomes stay unopened; new imported-history studies require their own frozen registry. Source paths, lineages, class balance and clock assumptions must be auditable. Fit scaling, feature selection and imputation on training data; select thresholds and calibration on designated development or validation data, never the final test. Keep outcome-inspected pilot units and repositories out of any test described as untouched.

All resource thresholds are proposed project decisions. Actual team, host, deadline and review capacity must be recorded later. Do not keep extending a losing arm to manufacture a positive result; stop or register a new question with a fresh held-out cohort.

## Experiment A — Pretrained forecasting

### A0: data and horizon admission

Start from the existing V2 repository-level measures. Resolve source, domain and UTC timestamp policy, branch ancestry, and actual state at each origin and at 30/60/90-day cutoffs. A matching measured revision can be reused even when its timestamp precedes the cutoff, provided its domain and complete target coverage match the selected state. An intervening unmeasured change makes an older stock unavailable. Repeated unchanged states remain legitimate inputs but are counted separately from distinct revisions and independent outcomes. Exact-date or exact-second observation pairs are diagnostics, not bounds on this eligible as-of cohort.

Build a registered daily grid using compatible measurements of eligible selected states; preserve gaps and distinguish observed from validly reused states. Do not interpolate test labels. For weekly public series, register 13 steps/91 days as a distinct study; it never validates exact 90 days. NPF's 21/28/91-day all-issue targets remain separate and blocked pending license and provenance. No module label is inferred from repository aggregates.

Required proposed audit output, one row per prospective origin/horizon:

```text
repository_id, origin_id, origin_cutoff, origin_revision,
selected_endpoint_cutoff, selected_endpoint_revision,
origin_analysis_id, endpoint_analysis_id, domain_id,
target_contract_hash, horizon_seconds, grid_interval_seconds,
history_grid_points, observed_points, reused_state_points,
missing_points, distinct_revisions, lineage_state,
label_status, censor_reason, input_manifest_hash
```

The endpoint revision and label are evaluation-side information and never forecast inputs. Feature timestamps must account for as-of availability; reconstructed historical states must disclose any assumed availability rather than imply actual historical scan logs. The exact-calendar target contract fixes stock or delta, quality mode, source population and unit. Standard SQALE and multi-quality maintainability fields are distinct registered measurements; reliability and security remain separate.

Pilot a preregistered, representative subset of six V2 projects chosen from metadata before target outcomes, spanning activity, size and source coverage. Inspect 30/60/90-day readiness separately. Expand to the available 31 projects only after the domain and state policy is stable. For a final study, nominate development, calibration and test repository partitions before outcomes; a 21/5/5 split is a planning example, not a frozen registry or proof of power. Use development-repository leave-one-out and rolling-origin sensitivity, then a final repository cohort not tuned on or inspected for pilot outcomes. Prior-inspected maintenance or classification cohorts cannot be described as entirely unseen data.

Require adequate precision and multiple separated future blocks for each reported horizon. Proposed study floor: at least three non-overlapping horizon blocks per evaluated repository and at least five held-out repositories for a cross-repository claim, subject to development-only precision analysis. These floors do not prove statistical power or independence between repositories. If only shorter-horizon evidence is adequate, keep 90 days unsupported and study 30 days honestly.

### A1: model and baseline design

| Comparison | Inputs and controls | Role |
|---|---|---|
| Persistence / zero delta | Last observed stock / no change | Mandatory difficult baseline |
| Historical mean / bounded trend | Training-only observed values; fixed lookback and slope clipping | Simple numerical control; seasonal naive only with demonstrated repeated seasonality |
| Ridge, CatBoost, LightGBM | Past-only size, process, current TD and trailing TD blocks; identical cohorts | Conventional supervised controls; bounded equal tuning budget |
| Chronos-small | Target-only registered histories; exact SHA and API preprocessing | First pretrained candidate |
| TTM R3 | Explicit fitting branch, class and context; documented masks and output point kind | Efficient pretrained comparator with actual short-context branches |
| Full Chronos / TimesFM 2.5 | Same target and origins; common history, then a separate extended-context comparison | Capacity and independent-publisher controls; not assumed winners |

For each horizon, define a **common eligible benchmark cohort** and disclose wider model-specific coverage separately. Common-context target-only comparison is primary; extended-context and covariate variants are secondary. If TTM requires 512 daily grid points for 90 days, it is not scored on a shorter context merely through padding. Its failure of context admission is not a forecast error. Other models may still be evaluated on a larger shorter-history cohort, but their metrics cannot be directly contrasted with TTM's smaller cohort without matched-origin results. Select the common context and cohort from contracts and availability before comparative outcomes.

TTM native contracts: 90 → 30 for daily 30 days; 180 → 60 for daily 60 days; 512 → 96 cropped to 90 for daily 90 days; 52 → 16 cropped to 13 for weekly 91 days. Preserve actual valid, reused and missing states. Use the explicit decomposed class and SHA, not unsafe bare-SHA dispatch through the substring-based selector. Record tensor shape, output channel and point kind: a 0.5 slot configured as a mean must not be labeled a median or native 0.5 quantile. Evaluate native q0.1/q0.9 intervals only under the documented output contract; masking and LOWESS gap sensitivity are distinct analyses. No recursive extension is needed for the selected branches.

Target-only numerical models receive identical history. Supervised models have additional registered past covariates, so compare them as a separate information-rich family and report ablations. Chronos covariate variants receive the same available feature information; TimesFM XReg is a separate fitted variant, not pure zero-shot. Inspected one-channel TTM checkpoints do not establish working multivariate or exogenous zero-shot capability. A multichannel TTM variant requires a documented configuration/load contract and its own comparison; do not silently initialize new channels then claim unmodified pretrained inference.

Search budget example: at most 12 configurations per supervised family on development and validation data, seeds 0/1/2 for stochastic fits, fixed zero-shot checkpoints, and no test tuning. Save forecasts and failures for every registered origin. Future calendar or release plans qualify as covariates only if truly known as of the origin; future churn, scans, debt and repair actions do not.

### A2: metrics and acceptance

Primary: macro-repository MAE in estimated maintainability minutes, per horizon. Secondary: pooled MAE/RMSE/bias, per-project errors, changing and constant-stock subsets, error versus history and missingness, runtime and coverage. Skill = `1 − MAE_model / MAE_control` only when control MAE > 0; a zero-error control gets absolute differences and undefined relative skill. WAPE requires a positive target denominator; MAPE on zero-heavy stocks is not a primary metric. Delta may be negative; any stock clipping is an explicit evaluated postprocessing variant.

Native uncertainty uses 0.1/0.9 central 80% coverage, width, interval score and compatible pinball endpoints. Genuine medians can be assessed as 0.5 quantile forecasts; do not assume every model's 0.5 slot is one. A central 90% product interval requires a separately fitted validation-only calibration artifact. Report quantile crossing and failure; do not present silent interval repair as native output.

Use paired repository/time-block uncertainty and leave-one-project sensitivity, with the same origin IDs. Overlapping dense windows are descriptive secondary data, not independent confidence samples. Report few-cluster limits and changing-event counts; repeated revisions or seeds do not increase the number of independent repository/time blocks. Preregister the clustering and confidence method after development-only precision assessment. A confidence interval from five repositories is not by itself evidence of reliable external transfer.

Proposed forecast product gate: at least 10% macro MAE gain over the strongest registered simple or conventional control selected on development/validation data; a paired 95% confidence interval above zero; improvement in at least 70% of eligible repositories; useful common 80% coverage approximately 75–85% with nontrivial width relative to a calibrated naive interval; and adequate state/domain coverage and measured cost. Report admitted-origin accuracy and end-to-end forecast availability separately, including registered load, timeout and inference failures. Validate deployment to known repositories and transfer to new repositories as separate claims; a model can serve known eligible repositories without claiming universal transfer.

If baselines tie or win, publish that result. If uncertainty is too wide, state inconclusive. If only one repository passes, scope output to it and do not infer broader accuracy. A larger or fine-tuned forecaster is not an automatic rescue: preregister the additional training-only study and preserve an untouched test.

## Experiment B — Pretrained detection and remediation

### B0: licenses, gold labels and feasibility

Resolve GraphCodeBERT and CodeBERT weight-use permission and checkpoint-specific label mapping before loading. Use upstream Tesoro types as a schema lead; uploaded-fold or checkpoint overlap with its original benchmark means a random new split of the same dataset is not automatically independent. The primary gold sample should include independently adjudicated Java functions from declared held-out repositories, positive types, clean examples, rare types, and out-of-distribution or long inputs. Two reviewers label raw source and context without model scores; a third reviewer adjudicates disputes. Preserve “unknown” rather than forcing a category.

Suggested feasibility sample: 200–300 functions across at least five repositories. Record stratum inclusion probabilities; report prevalence-weighted estimates only when the sampling design supports them, alongside stratum-specific results. Final study size follows development-only precision, per-type counts and review capacity. If a rare type lacks evidence, report it separately or abstain; pooled micro F1 cannot erase that gap. Unsupported overlength functions are excluded from inference but remain in coverage denominators. A test-debt category may need test context; do not claim complete classification from isolated production functions alone. Reserve final held-out repositories before reviewing pilot outcomes.

### B1: detection benchmark

Use the same raw units and labels, the author's lowercase clean-code normalization, 512-token eligibility, and raw-to-normalized line mapping. Four independent sigmoid outputs are required; the author's logit > 0 threshold is an uncalibrated reference, not a production confidence contract. Do not apply softmax across labels or interpret all-zero outputs as confirmed debt absence.

Compare GraphCodeBERT and CodeBERT with declared static, keyword and small supervised feature baselines on independently mapped labels. Sonar rule categories are not inherently the same four debt types; do not manufacture a perfect static-category mapping. Separately test detection and localization utility on reviewed units, including AI-only candidates. Classifiers cannot be evaluated against their own output or only against high-scoring units.

Metrics: per-type, macro and micro precision, recall and F1; PR-AUC/AP; ROC-AUC where both classes exist; false-positive rate; calibration/Brier where probabilities are claimed; abstention and eligible coverage; and held-repository variation. Fit thresholds and calibration on validation only. Proposed annotation gate: a lower 95% precision bound ≥ 0.80 at the chosen review threshold, useful recall and coverage, plus demonstrable utility over a relevant baseline. Account for repository clustering and stratum sampling; rare-type and few-cluster limits remain explicit. The threshold is a project tradeoff, not known achievability. If no model passes, retain experimental results and do not turn its score into measured debt.

TechDebtClassifier is a separate diff experiment: clean added lines, independently reviewed probably-clean/possible-debt labels, project/time grouping, and matched diff baselines. It cannot be ranked against function F1 in one table. If the task forecasts future finding introduction rather than classifies a current diff, obtain real future finding identity labels and maturity splits; name and validate that task separately.

### B2: retrieval ablation

Use at least 50 source, rule and dependency queries from held-out findings or reviewed candidates; two blinded reviewers judge relevance on a 0–2 scale. Compare lexical/symbol lookup and CodeRankEmbed on identical exact-snapshot chunks, k = 1/5/10, and equal context-token budgets. CodeRank uses its query prefix, CLS pooling and pinned reviewed custom code. Exclude actual future fixes and endpoint source from the index. Freeze the query sample without selecting on retrieval scores; group queries from the same finding and repository for uncertainty.

Metrics: Recall@5, MRR/nDCG@K, evidence/citation precision, latency and memory. Proposed retrieval gate: ≥ 10% relative Recall@5 improvement where the baseline denominator is positive, no material citation-precision loss, and actual benefit in B3 under the same generator budget. A zero-recall baseline requires an absolute difference, not undefined relative gain. If embedding helps search but not repair, it can remain a search-only capability with that claim; keep these outcomes separate.

### B3: representative Java repair study

Use 30 prospectively selected finding units across at least five repositories and 3–5 small rule families for the feasibility pilot. Preserve baseline compilation and tests; record exclusions before generation. A final cohort of approximately 100 units across eight repositories is a workload scenario; size and power come from development precision. No earlier pilot unit or outcome-inspected repository enters a test described as untouched. Independently confirmed learned-only candidates form a separate stratum because they may lack a Sonar finding-removal endpoint.

Compare available deterministic quick fixes or rule guidance, Qwen with local context, Qwen with lexical retrieval, and Qwen with CodeRank retrieval. Keep checkpoint, decoding seeds and settings, total prompt/output budget, units and candidate attempts equal; allow at most three candidates per unit. The first-candidate outcome is primary; any-of-three is secondary. Validation feedback and retries supply additional information and form a distinct budget-matched variant. SonarSweep is a later same-task control if a 48 GB+ host and study budget fit; CodeAid is a separate coupling-smell localization study after vocabulary and ground-truth resolution.

Required checks: immutable base, patch and allowed paths; baseline and candidate compilation; the full registered minimum test set; differential checks and same-domain Sonar inventory where required; target finding identity for analyzer-target cases; and audits of new findings, suppression, exclusion and deletion. Two blinded reviewers assess correctness, maintainability and utility without model-arm identity, recording disagreements and any unblinding. Models do not run commands, adjust tests or claim success themselves. Green tests are bounded evidence, not formal equivalence.

Record two independent axes for each candidate:

- **Evidence status:** baseline failure, missing mandatory evidence or timeout → `PARTIALLY_VERIFIED`; candidate regression or a required-check failure from a passing baseline → `FAILED`. For an analyzer-target case, `EVIDENCE_VERIFIED` requires complete passing minimum checks, adjudicated resolution of the registered finding identity, and no prohibited new findings or hiding trick. For a learned-only case without an analyzer-target endpoint, complete passing engineering checks yield `ENGINEERING_CHECKED`, never `EVIDENCE_VERIFIED` merely because tests are green.
- **Independent verdict:** `ACCEPTED`, `REJECTED` or `INCONCLUSIVE` under the preregistered reviewer rubric. A learned-only candidate requires a recorded independent before/after debt or maintainability judgment; no Sonar removal is invented. Human acceptance does not override failed or missing engineering evidence, and passing engineering checks do not imply acceptance.

Freeze eligibility, stratum assignment and denominator policy before generation. Baseline failures detected before generation may be excluded under the registered policy, but remain visible in the full intake funnel. A baseline or evidence problem discovered after assignment remains in the assigned denominator and cannot be removed because an arm failed. Report no-candidate outcomes, abstentions, timeouts, partial evidence and rejections against their assigned units.

| Repair endpoint | Numerator | Denominator and interpretation |
|---|---|---|
| Analyzer-target accepted verified pass@1 | First candidates with `EVIDENCE_VERIFIED` and independent `ACCEPTED` verdict | All prospectively eligible assigned analyzer-target units for that arm, including no-candidate, timeout, failed and partial-evidence outcomes |
| Learned-only accepted engineering-checked pass@1 | First candidates with `ENGINEERING_CHECKED` and independent `ACCEPTED` verdict | All prospectively eligible assigned learned-only units for that arm; this is a separate engineering and human-judgment endpoint, not analyzer-target verification |
| Any-of-three, secondary | At least one qualifying candidate under the respective stratum's evidence status and verdict | The same assigned unit denominator and fixed attempt budget; never three independent cases per unit |

**Do not pool the two strata into a single verified pass rate.** Report their pipeline funnels, baseline exclusions, abstentions, failures, confirmed regressions, reviewer agreement and runtime separately. Test-only and analyzer-only improvements do not automatically count as accepted repair. Use paired repository/rule-cluster uncertainty on the same units, acknowledging few-cluster limits. Proposed useful-effect gate within each stratum: ≥ 10 percentage-point increase over the strongest simpler control selected on development data, with a paired confidence interval above zero and no systemic unsafe acceptance under the registered audit. An inconclusive small pilot does not establish inferiority; it determines final-study feasibility.

## Compare arms before choosing the primary contribution

Do not combine MAE, F1 and patch pass rate into one accuracy score. Each arm has a matched, task-specific useful effect and a separate validity gate. Pilots can guide preregistered resource allocation, but final primary-contribution selection requires the comparative evidence from both arms or a documented blocking condition after the bounded acquisition plan. Use a predefined 0–4 rubric with stored supporting evidence:

| Criterion | Weight | Evidence required |
|---|---:|---|
| Construct, label and provenance validity | 25 | Independent gold, cutoff and domain audit; limitations and censoring |
| Measured incremental utility | 25 | Task-specific paired baseline effect and uncertainty, not publisher results |
| Reproducible generalization | 20 | Held-repository, time and unit performance; failures and contamination limits |
| Feasible compute, data and review cost | 15 | Actual runtime, collection and reviewer hours, hardware limits |
| Graduation scope and contribution | 15 | Bounded deliverable and sourced differences from existing research |

Every score and empirical metric is currently **`PENDING_EXPERIMENT`**. Enter scores only after experiments; invent no ratings or placeholder metrics. Score 0 means unsatisfied or unsupported; 1 exploratory; 2 credible but inconclusive; 3 supported within a limited domain; 4 strongly replicated across declared domains. A critical validity failure overrides the weighted total. A blocked or unrun arm remains `PENDING_EXPERIMENT` with a recorded blocker, rather than receiving an invented empirical score. This rubric guides primary-contribution selection, not debt priority.

Choose A as primary if its data and comparative evidence are strongest and cost fits; B classification if detection adds validated value even when repair fails; B repair if direct verification and acceptance win; or a bounded hybrid if both arms pass and fit the deadline. If one arm is blocked by data or licensing, document and attempt its bounded acquisition or clarification plan before abandonment. If both fail to add value or remain inconclusive, report an honest negative or inconclusive study and avoid claiming a validated AI platform.

## Commands, execution boundary and reproducibility

The existing CLI was source-inspected and supports only `exact90`/`approx91` module construction and M0–M2 CatBoost evaluation. It does not support 30/60 days, V2 repository grids, Hugging Face forecasters or B experiments. This existing-interface reuse example is **future-only**, requires real verified workspaces and new outputs, and has not been executed:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
.venv-forecast/bin/python -m forecasting build \
  --workspace /absolute/verified/workspace \
  --output /absolute/new-study/module-exact90 \
  --horizon exact90 --strategy auto --growth-threshold-minutes 30
.venv-forecast/bin/python -m forecasting evaluate \
  --dataset /absolute/new-study/module-exact90 \
  --output /absolute/new-study/m0-m2 \
  --first-validation-cutoff 2022-01-06T00:00:00Z \
  --validation-weeks 8 --test-weeks 8 --folds 2 --step-weeks 32 \
  --iterations 200 --precision-k 5
```

The date is illustrative; actual boundaries come from the frozen manifest. `evaluate` trains models and must not run in this design session. Exit 2 / `INSUFFICIENT_DATA` is a valid reported prerequisite failure, not permission to split randomly or fabricate targets.

Future harness command contract (**proposed interfaces, not existing or runnable today**):

```text
python -m td360_research audit-history --manifest A.yaml --output NEW_A_AUDIT
python -m td360_research forecast --manifest A.yaml --cohort COHORT_HASH --output NEW_A_RESULTS
python -m td360_research classify --manifest B.yaml --output NEW_B_DETECTION
python -m td360_research retrieve --manifest B.yaml --output NEW_B_RETRIEVAL
python -m td360_research repair --manifest B.yaml --output NEW_B_CANDIDATES
python -m td360_research verify --manifest B.yaml --candidates CANDIDATE_HASH --output NEW_B_VERIFICATION
python -m td360_research compare-arms --a A_RESULT_HASH --b B_RESULT_HASH --output NEW_DECISION
```

A future engineering milestone implements and tests this interface in an isolated research harness; these modules are not claimed to exist. Freeze exact dependencies and rendered commands in the run manifest after load tests. Use documented primary APIs: Hugging Face `AutoModelForSequenceClassification` for Tesoro logits; SentenceTransformer with query prefix and CLS pooling for CodeRank; Qwen chat template for generation; `Chronos2Pipeline` for regular frames; explicit `TinyTimeMixerForDecomposedPrediction` and SHA for R3. No off-the-shelf command already performs the full compilation, Sonar and human-review experiment.

Every future arm writes immutable input/output IDs, actual commands, environment and hardware, duration and peak memory, all predictions, candidates and failures, rubrics and adjudication, and metrics with denominator, split and calibration versions. Reproducibility means another researcher can reconstruct the study without choosing labels, splits, budgets or acceptance after observing outcomes. It does not mean the planned harness is already implemented.

## Next experiments in execution order

1. Resolve classifier weight permission, semantic mapping and original scan access; perform a bounded V2 as-of, domain and coverage audit.
2. Later, perform isolated runtime checks for the classifier, embedding, Qwen, Chronos-small and an eligible TTM branch; fix environments, shapes and masks without an accuracy claim.
3. Preregister A's cohort, horizons and folds, and B's gold and repair cohorts, blinding, budgets and precision targets.
4. Execute A's first baselines plus Chronos-small/TTM, and B's GraphCodeBERT/CodeBERT plus matched Qwen verification pilot under bounded budgets.
5. Expand comparators and the final study only after prerequisites; select the primary contribution from the paired record. No automatically authorized implementation or training follows from this plan.
