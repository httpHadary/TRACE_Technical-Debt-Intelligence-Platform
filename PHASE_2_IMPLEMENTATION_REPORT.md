# TechDebt360 MVP — Phase 2 forecasting dataset construction

Date: 2026-10-14, Africa/Cairo. Project:
`/home/hp/tst/td_pipeline_module_level/td_pipeline`.

**Status: PARTIAL overall; implementation/tests and the research data-cohort gate pass.**
Exact 30/60/90-day targets and purged evaluation splits are available. Imported
analyzer/availability limitations remain, and pretrained runtimes are not ready.
No model was trained or run, no forecast generated, and no Phase 3 work begun.

## Created/modified files

- New `forecasting_mvp/targets.py`: monotonic first-parent state selection,
  exact endpoints, measured same-state reuse, metadata barriers, complete/masked
  past contexts and causal feature summaries.
- New `forecasting_mvp/splits.py`: metadata/eligibility-only shared calendar and
  repository-held-out assignments, exact-horizon checks, purging and embargo.
- New `forecasting_mvp/dataset.py`: verified Phase 1 bundle loading, example/context/
  feature/label projections, feasibility/rejection diagnostics, deterministic
  compressed publication and unchanged-input/code checks.
- New `forecasting_mvp/study.phase2.example.json` and
  `tests/test_forecasting_mvp_phase2.py`.
- Updated CLI with `build-forecasting-dataset`, package scope docstring, package/
  root README, `.gitignore` and `GITHUB_SYNC.md`. Existing phase reports, legacy
  collectors/forecasting/evaluation and dependency locks are preserved.
- New report and small attributed evidence under `examples/phase2/`.

The local checkout's pre-existing changes and unrelated history remain intact.
The central GitHub checkout is updated by normal descendant commits; no force
push, reset or unrelated-history rewrite.

## Input and state validation

Reused the checksummed Phase 1 bundle:
`/home/hp/tst/research/forecasting_mvp/phase1/2026-10-14/run-002`.
Its 66,711 measurements and 153,994 Git records preserve source hash:

```text
8eb329e5e5690b884b98df824c4b94fc7582c5d610fa3bd12784b1e417b2684e
```

The original 1.5 GB SQLite source was not modified. Phase2 reads verified artifacts,
validates their checksums/counts/source provenance, and rechecks them before
publishing. Independent raw SQL target spot checks open the database read-only.

Conservative repository isolation:

| Problem | Action |
|---|---|
| Ambiguous tips: batik, cocoon, felix, santuario | Exclude all four from this study; do not choose an arbitrary branch |
|34 first-parent inversions across archiva(2), collections(13), hive(12), thrift(6), zookeeper(1) | Isolate all five affected repositories rather than repairing timestamps or claiming unsafe intervals |
| Missing/cyclic/unresolved ancestry | Reject at bundle/chain admission; no such extra defect in the admitted real chains |
| Unmeasured selected revision | Missing input or rejected origin/endpoint; no previous-measured carry |
| Unknown/changed observed profiles | Reject or split known metadata segments, including sub-day changes/reversions |

This leaves **22 repositories** for context/endpoint audits. Exclusions are not
deletions; Phase 1 evidence remains available for later registered-mainline or
bounded chronology recovery. Full analyzer/rule/scanner/build/scope histories are
unknown. Constant observed profile metadata supplies an **imported research
approximation**, not complete analyzer invariance or historical online evidence.

## Exact target and leakage rules

Origins are Monday 00:00:00UTC. For horizon h, endpoint is exactly
`origin + h*86400 seconds`, h∈{30,60,90}. Select the latest first-parent revision at
or before each cutoff, using chain order for equal timestamps; then require that
exact revision's measured SQALE. Scan time need not equal cutoff time. Never use
nearest dates, interpolated actuals, zero-filled missing debt or old measurements
across changed-but-unmeasured revisions.

An unchanged-state label requires identical selected origin/endpoint revision,
archived chain coverage through the endpoint, measured evidence and compatible
known metadata throughout. It is retrospective unchanged-state evidence; it
does not prove online branch publication timing. Negative observed stock changes
remain signed. The target is native project **estimated maintainability remediation
minutes**, not actual labor or combined reliability/security effort. Weekly 91-day
forecasts are not substituted for exact 90-day targets.

Past features/contexts and endpoint labels are stored separately. Contexts have
only timestamps≤origin, observed/null values, past observation references and
known metadata. Future-value changes cannot change past contexts/features/IDs,
as tested. No scaling, imputation fit, feature selection or model loading occurs.
Later prediction runners must receive a single past-only projected context, not
the combined dataset, label file or all later-origin contexts.

## Actual examples and context feasibility

| Track | Context | Horizon | Eligible examples | Repositories |
|---|---:|---:|---:|---:|
| core90 |90 complete daily points |30 |15,661 |22 |
| core90 |90 complete daily points |60 |15,497 |22 |
| core90 |90 complete daily points |90 |15,348 |22 |
| masked90 |90 daily points,≥80% known |30 |15,706 |22 |
| masked90 |90 daily points,≥80% known |60 |15,540 |22 |
| masked90 |90 daily points,≥80% known |90 |15,386 |22 |
| ttm60 |180 complete daily points |60 |15,008 |22 |
| ttm90 |512 complete daily points |90 |13,423 |21 |

Total: **121,569 example rows and59,819 unique track-context records**. These
include alternative tracks and overlapping weekly origins; do not sum them as
independent observations. Primary `core90` passed the registered data gate, so
masked90 remains a separately labeled sensitivity, not an outcome-selected pivot.
TTM 30 uses the complete90-day/30-day cohort; TTM 60/90 tracks require matched contexts
for every comparator. No foundation model efficacy or loadability follows from
these counts.

Across all eight track/horizon combinations: **167,536 candidate slots;45,967
rejections**. The nine isolated repositories are listed separately and not counted
as attempted origin slots. Rejection reasons:

| Reason | Candidate slots |
|---|---:|
| Unmeasured origin revision |36,384 |
| Insufficient context span |3,763 |
| Context profile-segment crossing |2,320 |
| Unmeasured endpoint revision |1,580 |
| Target profile-segment crossing |998 |
| Missing complete-context state |691 |
| Masked context below 80% |144 |
| Unknown context/origin profile |47 /40 |

Per-repository/horizon rejection counts and example cutoffs, context lengths,
known fractions, daily-state missing rates and eligible counts are in
`forecasting_feasibility.json`. Daily missing fractions range about4.16%–90.43%
over entire audited histories; admitted contexts are a selected subset and retain
that selection limitation. No missing future labels are imputed.

For the full eligible90-day core track:15,348 rows correspond to4,890 distinct
repository/origin revisions and1,198 greedy non-overlapping label windows.
There are2,115 exact same-revision endpoints and5,905 observed zero deltas.
Effective independent sample size remains **unknown**; these are descriptive
proxies, not statistical power guarantees or measured forecast performance.

## Frozen chronological/repository splits

Data-only selection chose **21 repositories**, holding out **six** by the frozen
study/repository hash policy. No held repository enters fitting or validation.
Largest shared eligible calendar interval:2011-08-15–2016-04-25. The registered
minimum630-day overlap and six-repository gate are pragmatic project choices.
No random splits or model-error-driven cohort selection were used.

- Train labels must end strictly before validation start:2014-06-09UTC.
- Validation origins:2014-06-09≤origin<2015-05-18UTC.
- Test origins start2015-08-17UTC, after a 90-day validation/test embargo; all
  validation labels mature before test origin. Test ends 2016-04-25 UTC.

Primary core counts:

| Horizon | Train | Validation | Familiar-repo temporal test | Held-repo test | Purged training labels |
|---:|---:|---:|---:|---:|---:|
|30 |2,145 |735 |555 |222 |60 |
|60 |2,085 |735 |555 |222 |120 |
|90 |2,025 |735 |555 |222 |180 |

The90-day TTM track has1,965 train,735 validation,555 temporal-test and191 held-test
examples; the60-day TTM track has2,073/735/555/222. Compare each model on identical
IDs and information budgets within a track, never different-cohort MAEs. Excluded
calendar rows, embargo and unused held-repository rows remain explicit assignments.
Six held repositories are fewer than the plan's eight-cluster caution threshold;
future cross-project uncertainty must remain exploratory unless additional
evidence justifies a stronger claim. Tests remain untuned; no model has run.

## Deliverables and reproduction

Final local bundle:
`/home/hp/tst/research/forecasting_mvp/phase2/2026-10-14/run-003`.

Required `forecasting_dataset.csv`, `forecasting_splits.json`,
`forecasting_feasibility.json`, plus `forecasting_features.csv`,
`forecasting_labels.csv`, deterministic `forecasting_contexts.jsonl.gz`, sample and
manifest. Full artifacts stay local. GitHub contains feasibility, compact split
summary, original full-output hashes,16-row attributed sample, tests and
reproduction instructions under `examples/phase2/`.

From the working project, change output to a **new** directory on reproduction:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp build-forecasting-dataset \
  --config forecasting_mvp/study.phase2.example.json \
  --out /home/hp/tst/research/forecasting_mvp/phase2/2026-10-14/run-003

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp verify-bundle \
  --bundle /home/hp/tst/research/forecasting_mvp/phase2/2026-10-14/run-003

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests \
  -k 'not test_actual_catboost_models_shared_folds_predictions_and_purging'
```

Exit 2/PARTIAL is the honest imported-provenance status even when the split gate
passes; exit 3rejects configuration/input/code-change/integrity defects. Phase 1
artifacts and source database remain unchanged. Source hashes and implementation
hashes bind reproducibility; configuration path changes intentionally change audits.

## Verification and publication

- **239 tests passed,0 failed; one actual-CatBoost training test excluded** to honor
  the no-training rule. This includes17 new Phase2 tests plus existing tests.
- Tests cover exact horizon/delta, zero/negative target, unmeasured changes,
  unchanged-state/archive boundaries, masks/TTM lengths, profile barriers,
  ancestry/time/tie handling, future mutation invariance, duplicate IDs,
  purged/held splits, insufficient cohorts, input tampering and deterministic
  complete publication. No synthetic result is claimed as forecast accuracy.
-16 published examples were independently joined against32 raw SQLite origin/
  endpoint measurements: **all matched** revisions and SQALE/delta values.
- Repeated frozen real construction into `run-004` verifies byte-identical outputs,
  including compressed contexts; the result is recorded in the published
  determinism evidence. Development smoke runs are not the final source snapshot.

Target publication: normal descendant commit on
[FadyYosry77/TechDebt360-MVP/main](https://github.com/FadyYosry77/TechDebt360-MVP/tree/main).
Remote source/report/sample bytes and exact commit SHA are verified after push
and included in the task completion message. Existing histories, content and
unrelated local changes are preserved; no datasets, checkpoints or credentials
are uploaded. Central sync instructions remain in `GITHUB_SYNC.md`.

## Phase 3 readiness and remaining limits

**Ready for a separately authorized, bounded research comparison**, conditional
on model runtime/package/resource admission. No accuracy claim exists. Maintain
imported-domain labeling, per-track matched cohorts, untouched test choices and
clustered uncertainty. Pretrained packages, model weights, compatibility and
memory/latency remain unverified Phase 0 issues; do not change the working dependency
lock or load models as part of this phase.

Recovery options are later work: obtain verified registered branch-tip evidence
for four excluded mainlines; investigate five inverted histories before admitting
safe causal segments; acquire missing measurements only under a consistent new
domain; recover full analyzer settings or disclose the imported approximation.
Do not patch old-domain time series with modern scans or force ambiguous states.

**STOP after Phase 2 verification and GitHub publication. Phase 3 training and
forecasting require explicit authorization.**
