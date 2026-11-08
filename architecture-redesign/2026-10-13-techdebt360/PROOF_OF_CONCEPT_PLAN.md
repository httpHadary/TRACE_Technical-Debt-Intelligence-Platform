# Minimal proof-of-concept plan

Date: 2026-10-13. **No commands in this document were executed as experiments.** They describe a later, explicitly authorized validation phase. They may create isolated environments, download artifacts, scan or train; those activities are outside the present design-only task. Existing project paths are source references. Every future run uses new output paths and preserves original evidence.

## Smallest experiment set

| Experiment | Decision | Required inputs → expected output | Pass/fail |
|---|---|---|---|
|P0 Read-only imported history audit|Is V2 a defensible primary/secondary forecast corpus?|V2 DB + revision/profile schema → inventory/eligible origin/domain/cadence/precision reports|Pass if measured states and valid split blocks can be defined; otherwise unsupported or narrower step-based study|
|P1 Exact own observation collection|Can trusted Java evidence be collected/recovered?|Registered three representative repos × two commits, compiled domain → complete scan/export manifests|Exact task/revision/domain/scope/export checks for every included observation; incomplete results excluded, never zero|
|P2 Qwen runtime/output|Can one generator fit the real budget and produce bounded assessable outputs?|Pinned Qwen revision + five source-bound Java cases → typed samples/runtime report|Load/output/hash contract works, no arbitrary tool action, resource limits measured; efficacy not claimed|
|P3 Retrieval ablation|Does embedding add enough value?|50 blinded held-out queries, same snapshot/chunks → lexical/CodeRank rank lists/relevance metrics|Declared recall/precision/runtime gate and later patch benefit; otherwise lexical only|
|P4 Optional specialist semantics|Does a requested classifier add usable evidence?|Resolved license/label mapping + reviewed positives/negatives → per type/modality/coverage/calibration results|Independent validation gate; no debt absence or effort claim; unresolved license blocks execution|
|P5 Conditional forecast benchmark|Does numerical forecasting beat naive fairly?|P0 eligible grid/target/fold manifest + pinned models → common cohort predictions/metrics|Target/cadence gate then baseline/value/calibration gate; negative outcome retained|
|P6 Bounded remediation pilot|Is evidence-grounded repair a feasible primary thesis?|30 eligible finding units/five repos, same generator/budget, meaningful tests → candidates/verification/reviewer labels|Adequate complete baseline evidence, no unsafe acceptance; final comparative claim needs a larger preregistered study|

Run P0 and P1 feasibility before expensive model comparisons. P2 cannot prove repair efficacy; P3 cannot prove debt detection; P5 cannot use fixture data for accuracy; P6 cannot call test-passing patches formally equivalent.

## Reproducible read-only commands already supported

These standard-library reads need no new packages and print structural data, not private source/text. They can be reused later; the design audit used equivalent read-only inspections. Exact study eligibility is more than a row count.

```bash
cd /home/hp/tst
git -C td_pipeline_module_level/td_pipeline rev-parse HEAD
git -C td_pipeline_module_level/td_pipeline status --short
python3 - <<'PY'
import sqlite3
con = sqlite3.connect('file:/home/hp/TECH_DEBT/td_V2.db?mode=ro', uri=True)
con.execute('PRAGMA query_only=ON')
for table in ('SONAR_ANALYSIS', 'SONAR_MEASURES', 'SONAR_ISSUES'):
    count = con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    columns = [r[1] for r in con.execute(f'PRAGMA table_info({table})')]
    print(table, count, columns)
con.close()
PY
```

Output schema: table name, integer row count, ordered column names. Later P0 audit must additionally produce `repository_id, origin_cutoff, origin_revision, endpoint_cutoff, endpoint_revision, domain_segment, grid_interval_seconds, horizon_steps, label_status, reason, source_hash` with no fabricated endpoints. Source-date/revision joins, as-of cutoff and profile validation logic will require future development; it is not implemented by the count command.

## Existing collector forecast commands: conditional reuse

The installed source supports these interfaces in [FORECASTING.md](/home/hp/tst/td_pipeline_module_level/td_pipeline/FORECASTING.md) and [CLI](/home/hp/tst/td_pipeline_module_level/td_pipeline/forecasting/__main__.py). They are **not runnable on a verified real module dataset today**, because such a workspace was not found. Provide a separately verified collector workspace and new output directory first. The example variables must be set from the frozen study manifest; no example date is silently adopted.

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
# Set these to independently verified inputs and a new future-run output path.
td360_workspace=/absolute/verified/collector-workspace
td360_dataset=/absolute/new-study/dataset-exact90
td360_evaluation=/absolute/new-study/evaluation-001
td360_validation_cutoff=2022-01-06T00:00:00Z
.venv-forecast/bin/python -m forecasting build \
  --workspace "$td360_workspace" --output "$td360_dataset" \
  --horizon exact90 --strategy auto --growth-threshold-minutes 30
.venv-forecast/bin/python -m forecasting evaluate \
  --dataset "$td360_dataset" --output "$td360_evaluation" \
  --first-validation-cutoff "$td360_validation_cutoff" \
  --validation-weeks 8 --test-weeks 8 --folds 2 --step-weeks 32 \
  --iterations 200 --precision-k 5
```

`build` reads collector evidence and constructs datasets; `evaluate` **trains CatBoost**, so it is future-only. Exit 2/INSUFFICIENT_DATA is a valid failed feasibility result, not permission to random-split. Legacy all-issue effort features and existing 26-week fixed interfaces require the new measurement/target adapters in the roadmap; existing command output cannot bypass new scientific gates. The existing module evaluator targets delta/growth, not the entire proposed forecaster comparison.

Expected existing files include `module_weekly_state.csv`, `module_labels.csv`, sequence arrays, identity/membership/graphs, immutable manifest, per-fold models/predictions/metrics. Required future comparison output extends them with exact TargetContract hash, native horizon steps/grid, model revision, common cohort and failure coverage. Names for new forecast adapters are design contracts, not existing CLI claims.

## Checkpoint loading recipes for a future isolated environment

Acquire dependencies only in a separately approved later phase, with exact package versions locked after compatibility checks. Never share all forecasters' conflicting Torch/NumPy requirements. Artifact revisions were verified in the research digests; current main must not replace pinned SHA silently. The following is a documented future Qwen inference pattern, derived from the [official card](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct). It may download weights and run inference.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = 'Qwen/Qwen2.5-Coder-7B-Instruct'
revision = 'c03e6d358207e414f1eca0bb1891e29f1db0e242'
tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
model = AutoModelForCausalLM.from_pretrained(
    model_id, revision=revision, torch_dtype='auto', device_map='auto'
)
# messages must come from the frozen source/evidence case manifest.
messages = [{'role': 'user', 'content': 'Explain the supplied finding using its source evidence.'}]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer([text], return_tensors='pt').to(model.device)
generated = model.generate(**inputs, max_new_tokens=256, do_sample=False)
answer = tokenizer.batch_decode(generated[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
```

This smoke example establishes loading/format only; it deliberately has no actual finding/source and cannot produce a verified explanation. P2 cases must supply exact context and cited IDs. Capture elapsed time, peak memory, tokenizer revision, hashes and raw answer; parser failure becomes FAILED, not unreviewed valid JSON. Quantization is a separate variant; theoretical 4-bit weight payload is not proof a quantized runtime fits or preserves outcomes.

For Chronos, the public API documents `Chronos2Pipeline.from_pretrained` and `predict_df` with ID/timestamp/target columns and optional future covariate frame. Validate a pinned `chronos-forecasting` environment and record checkpoint SHA from [model digest](digests/forecast-models.md). Future minimal input is `series_id,timestamp,target` plus separately allowed past/future covariates; output must include `origin_id,target_contract_hash,native_horizon_steps,output_timestamp,point_kind,point,q0.1,q0.5,q0.9,model_version,status`.

TimesFM/TTM/Toto/Moirai recipes depend on their exact package/revision config and cadence gate. Do not write fictional “one command loads all” examples. Their adapter runner CLI does not exist today; a future engineering task must implement the ports in the architecture and freeze the runnable command/environment in its verification manifest. The current proof plan provides input/output and pass/fail specifications, not an implemented experimental harness.

## P6 verification sequence and budget

For every registered unit: verify base/source/domain hashes; generate at most three candidates under a fixed token budget; validate allowed paths/unified diff; apply only to an isolated copy; run baseline and candidate compile; full declared tests and differential policy; frozen before/after analyzer exports; new finding/suppression/deletion audit; independent blinded review. Build/test commands are fixed per repository in `VerificationPolicy`, checked against the project's build definition; models never supply the command. No scan/test is launched in this design session.

Expected artifact contract: `case_id, base_snapshot_id, analysis_id, domain_id, recommendation_id, candidate_id, patch_hash, verification_policy_hash, baseline_results, candidate_results, before_after_finding_ids, status, reviewer_decisions, runtime, limitations`. Report all 30 eligible units, including no-candidate and timeout cases. No manual repair of unsuccessful patches inside one arm. Independent reviewers decide correctness/utility separately from the model's own explanation.

Budget reservation: P0 ≤ one week; P1 six snapshots before 36-snapshot expansion; P2 five cases; P3 fifty queries; P6 thirty units. Full benchmark/review size is determined from pilot precision, not from a desired positive headline. If hardware, baseline evidence, licensing or sample precision fails, stop dependent experiments and retain an honest narrower design.

## POC completion record

Each future experiment ends with `decision=PASS/FAIL/NOT_EVALUABLE`, input/output manifest hashes, actual commands/environment, measured resources, metric denominators, uncertainties and next dependency. It must state what was not proved. The present project has research designs and retained software validation—not newly executed POC results.
