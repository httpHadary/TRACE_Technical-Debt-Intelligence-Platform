# Phase 5.1 — Multi-language data foundation

Date: **2026-10-15**. Publication base: `e4dabcfef3f39f676a3bfa9e4f6bb4efef87b97d`.
Working project: `/home/hp/tst/td_pipeline_module_level/td_pipeline`.
Central repository: https://github.com/FadyYosry77/TechDebt360-MVP (`main`).

**Overall: PARTIAL / BLOCKED_NONJAVA_DATA. Software foundation: PASS.** The isolated
schema-v2 package, read-only adapters, F0/F1 features, independent exact-horizon
target-status builder and leakage-protected input interface are implemented and
verified. **No new real pilot history passed strict admission.** All three pilot
slots remain unfilled; no real schema-v2 feature vectors or labels are claimed.
The existing schema1 Java benchmark and its published results remain unchanged.

No model fitting, pretrained inference, SonarQube scans, new archive/model
downloads, dependency changes, backend or dashboard development occurred. The
regression suite uses software fixtures/mocks; it did not rerun a real benchmark.

## Scope correction and implemented work

The three development targets are **Java-dominant, Python-dominant and genuinely
mixed Python+JS/TS**. The mixed project is not JS/TS-dominant. No fourth project
was added. The four Phase5 documents now make this explicit, retaining the
original research findings and adding the new Git-path qualification below.

| Component | Implemented behavior |
| --- | --- |
| `forecasting_multilanguage/contracts.py` | Schema2 identity, finite typed measures/null reasons, UTC clocks, exact horizons, analyzer-domain and observation contracts; native estimated minutes remain distinct from actual effort |
| `registry.py` | Separate code/data rights, source/family exposure, fixed production scope, seven language groups, mixed-first classification; JS+TS are one programming family |
| `git_events.py` | Existing-object-only first-parent Git adapter; immutable tip/tree/ref identities, no shallow/inverted history admission, literal paths, pinned Myers/no-renames diffs, merge/root handling; no checkout/fetch/hooks/textconv |
| `adapters/v2.py` | Read-only/query-only SQLite audit, exact project+analysis joins, raw reference/date preservation, typed candidate metrics in `LEGACY_DOMAIN_UNVERIFIED`, deterministic churn diagnostics |
| `adapters/sonar_archive.py` | Hashes and parses the same archived bytes; binds native revision/analysis/project, inventory and complete coverage; rejects partial/unsupported scope and preserves invalid numeric values |
| `admission.py` | Domain/scope/repository/tree/lineage binding, actual Git production-inventory comparison, declared language/plugin/positive-NCLOC coverage, duplicate and contradictory-state rejection |
| `features.py` | All **7 F0 + 15 F1** columns with past evidence/missingness; no F2; no learned transformations or model imports |
| `targets.py` | Independent endpoint resolution at exactly 30/60/90×86400 seconds; stable input-derived forecast/context identities, separate actuals/status/reasons; unknown remains null |
| `cohorts.py` | Exposed/alias/family-role rejection and strict 90-day-context interval purging, without changing old cohorts |
| `inventory.py` | Bounded, explicit-local-root search, metadata-only exposure union, unresolved-name/fork reporting; discovery cannot certify admission |
| `io.py`, `cli.py`, `__main__.py` | Deterministic atomic new-directory publication, source/code hashes, COMPLETE integrity verification; `audit-legacy`, `inventory-local`, development-only `build-archive`; no model/scanner command |

The [package README](forecasting_multilanguage/README.md) specifies exact archive,
registry, coverage, inventory and feature interfaces. The quarantined
[template](forecasting_multilanguage/study.schema2.example.json) is not a real
repository registration. No new package or infrastructure was introduced.

Strict archive output includes `analysis_snapshots.csv`, `measurements.csv`,
`language_coverage.csv`, `git_events.csv`, `features.csv`,
`feature_evidence.jsonl`, `forecast_origins.csv`, `forecast_labels.csv`,
`origin_admission.json`, registry/domain/source/cohort/readiness records and a
schema2 manifest. These outputs are demonstrated by **synthetic software
integration tests**, not presented as real historical measurements.

Missing origins stay in the attempted-cutoff ledger. Missing future endpoints
retain null values and typed reasons. Software/integrity failures abort; they do
not silently become zero, persistence or successful partial analyses.

## Verified source and feature availability

Source: `/home/hp/TECH_DEBT/td_V2.db`, SHA256:
`8eb329e5e5690b884b98df824c4b94fc7582c5d610fa3bd12784b1e417b2684e`.
It was opened with SQLite URI `mode=ro`, `query_only=ON` and memory temporary
storage; its hash was checked before and after each audit. It was not modified.

| Finding | Actual result |
| --- | ---: |
| Projects | 31 |
| Git commits | 153,994 |
| Raw change rows | 1,142,878 |
| Sonar analyses | 67,550 |
| Sonar measure rows / exact-join legacy candidates | 66,711 |
| Missing or malformed joined revision identities | 0 |
| Invalid nonnegative integer numstat rows | 0 |
| Orphan project/commit change keys | 0 |
| Strict admitted new observations | **0** |

The ordered exact source-reference digest is
`777f09bd98c4c3e234dd353ed08cdefe477f1d71053cbfed3d9b6848a718883e`.
All candidates retain their real raw project/analysis/revision/date references;
raw naive dates are not silently promoted to UTC. Complete immutable analyzer,
rule, runtime/build and scope provenance is absent from V2, so candidates remain
quarantined for the new strict-domain study. This does not retroactively alter
the original benchmark's documented schema1 admission policy or results.

Full reproducible counts are in the [source audit](examples/phase5_1/legacy_source_audit.json)
and [identity audit](examples/phase5_1/legacy_identity_audit.json). Examples:

- SQALE, smell, bug and vulnerability counts: 66,711 numeric observations each;
  SQALE has 31 observed zeros, retained as real zeros.
- NCLOC/files/lines: 66,685 valid values and 26 SQL nulls. Complexity and cognitive
  complexity: 66,683 valid values and 28 SQL nulls.
- Duplication density: 66,685 numeric values plus 26 blank/nonnumeric missing
  cells despite **zero SQL nulls**. Missingness is not a null-only SQL check.
- Every one of the 66,677 numeric coverage values is zero; historical test
  instrumentation remains unverified and is excluded from F1. Team size and
  business value have no numeric observations.
- Positive language measurements reproduce Java 66,683/31 projects; JS
  11,350/5; PHP 3,381/2; CSS 13,661/8; web 15,599/22; XML 19,822/26.
  There are 26 missing distributions and no unparsed tokens. No positive
  Python, TS, Go, C++ or C# distribution was established in this source.

Raw availability is distinct from strict feature eligibility. F0/F1 implementations
are tested, but no real strict feature vector is fabricated to bypass the missing
domain data. Legacy covariates can be inspected through the candidate adapter;
they are not admitted directly to the model-facing interface.

## Churn and full-path identity audit

The full source audit reproduced **1,037,222 unique raw keys**, **42,113 repeated
keys**, **105,656 extra rows** and **23,321 groups with disagreeing additions or
removals**. Numstats are parseable nonnegative integer **text**, not missing values.

The deterministic sample chooses the smallest SHA256 keys per available project,
then round-robins projects: **10 conflicting + 10 clean groups**, across
`org.apache:codec`, `org.apache:commons-cli` and `org.apache:commons-io`.
Existing objects allowed all **20/20 authoritative first-parent diffs** to be read.
No network acquisition occurred.

| Stratum | Actual result |
| --- | --- |
| 10 conflicting groups | **10 ambiguous basenames**, each matching multiple actual changed full paths |
| 10 clean groups | **10 unique-path matches** to the stored numeric variant |
| Full included-window reconciliation/coverage proof | **Not available** |
| F2 | **DISABLED** |

For example, the conflicting `package.html` key at codec commit
`5839ea5ccc2d4d9dcf541744fb3fd295d8c88dd4` maps to five full paths with distinct
diffs. A basename is not a stable production-file identity. This sample supports
a path-collision explanation for its 10 conflicting groups; it does **not** prove
the cause of all 23,321 groups or justify summing/deduplicating them.

An intermediate exact-path-only diagnostic incorrectly treated some basenames as
root paths. It was superseded before publication by full-diff basename resolution;
its provisional mismatches are not evidence. The final [20-case evidence](examples/phase5_1/churn_diagnostics.json)
contains source pairs, complete matching paths, first-parent identities and raw
diff hashes. No legacy rows or churn totals were repaired.

F1 uses deduplicated authoritative Git commits and full production paths; raw V2
`FILE` alone is not adequate for distinct-source-path features. F2 needs a future
full-path reconciliation and per-window binary/missing/coverage proof, not merely
a passing sample.

## Pilot and local acquisition readiness

The approved local search examined **12,588 files** at depth ≤8 across:

```text
/home/hp/TECH_DEBT
/home/hp/tst/research
/home/hp/tst/td360_v3_real_operator_v0100/workspace/repos
/home/hp/tst/td360_v3_real_operator_v0100/workspace/admission_raw
```

Frozen/model/current-output roots under `research/forecasting_mvp` were explicitly
excluded from discovery to avoid outcome parsing and self-contaminating inventory
counts. This is a **bounded search**, with depth truncation and 18 inaccessible or
unresolved Git-worktree directories recorded, not proof of universal absence.

It found 105 existing Git checkout locations representing 32 distinct URLs, 56
unregistered raw measure components/payloads and 30 exposure-registry files.
Those measure payloads lacked usable language-distribution evidence in the
inventory. Inspected older raw metadata includes controlled Java semantics-probe
scenarios; these are not independent new longitudinal pilot histories. An inspected
caffeine admission result was FAIL. Version/image fields in old metadata alone
do not establish the new study's full state/scope/license/domain admission.

Exposure inventory combines the 31 V2 source identities, six cached NPF-card
identities, 209 local Zenodo cross-sectional names, local Git metadata and prior
registry identities. It yields **294 conservative exposure keys**: 69 normalized
URL-alias keys and 225 unresolved names. Fork-family certification is still
incomplete; all are excluded from any claim of a genuinely new held-out cohort.
No future confirmatory families were enrolled or numerical held-out outcomes
opened for selection. Raw identities/roles, not model outcomes, drove discovery.

Additional sources were assessed without downloads:

| Source | Current disposition |
| --- | --- |
| 18 local Zenodo 4534110 files | SHA256s still match the prior verified inventory. Missing exact revision/analysis/domain linkage; CC-BY-NC-ND-2.0 restrictions remain. No transformed source rows published |
| Cached NPF metadata/card | Revision `00d1b3865d4b00d9f4a4733af7aaad8f7c90854a`; unknown license, combined/weekly target semantics and incomplete native provenance remain blockers. No large CSV fetched |
| Local TDPSN wide CSV | No verified repository/commit/time/native-target identity; not substituted for archived Sonar states |
| Old NPF/CMR and source/compiled probe artifacts | Exposure/quarantine metadata only; not new confirmatory or non-Java pilot data |

The [readiness evidence](examples/phase5_1/pilot_and_source_readiness.json) records
**zero admitted states and zero eligible 30/60/90 endpoints in each of the three
new strict pilot slots**. Even the Java development slot requires complete new
schema2 provenance; the existing Java schema1 dataset remains separately frozen.
No synthetic test fixtures are counted as acquired pilot data.

## Leakage, chronology and target controls

- Origin state is selected through complete, monotonic first-parent ancestry,
  not nearest timestamp or sorted dates alone. Ties follow ancestry; shallow,
  missing-parent and inverted histories cannot prove a strict context.
- The native Git commit timestamp is `state_utc`; prediction cutoff is
  `origin_utc`. Execution, source availability and retrieval clocks are separate.
  Retrospective-fixed-analyzer mode makes no historical-online-availability claim.
  Operational mode requires contemporaneous branch and input availability; Git
  activity without such proof stays missing.
- Snapshot metrics join by admitted identity only. Git windows are open-left
  `(t0−30d,t0]` / `(t0−90d,t0]`. Trends require three distinct measured states and
  timestamps and use elapsed days. Missing lag/current-state evidence is not
  interpolated or carried over an unmeasured revision.
- Model X exposes only 22 allowlisted features plus past missing indicators.
  Raw IDs, paths, split roles, endpoint IDs, `actual_*`, `TD_*` and label statuses
  are rejected. Tests mutate future measurements and prove X and forecast IDs
  unchanged, while independently constructed labels change.
- A same active unchanged revision can have a valid endpoint with exact state,
  domain and scope proof. A different unmeasured revision, even with a familiar
  tree or nearby analysis, remains unknown. Targets are exact UTC durations;
  91 days is rejected under a 90-day contract.
- Existing frozen cohorts are untouched. The new purging utility requires
  `training_origin + horizon < validation_origin − 90d`, and checks duplicate IDs
  and family/alias exposure separately from X. No new modeling split was chosen.

## Tests, deterministic proof and preservation

**Final full regression results: central checkout 404 passed / 1 deselected;
working project 404 passed / 1 deselected.** The one excluded test is
`test_actual_catboost_models_shared_folds_predictions_and_purging`, which actually
fits CatBoost and is prohibited here. The new suite contains **68 passing cases**.
It covers serialization/zero/null/NaN/boolean handling, exact horizons and missing
targets, same-state proofs, chronology/shallow/identity/scope errors, language
classification, incomplete/incompatible domains, operational missingness,
future-value/label rejection, deterministic source sampling, first-parent/root
diffs, ambiguous basenames, fatal-versus-missing Git errors, family purging,
read-only SQLite, immutable publication and source-byte preservation.

Two independent final-code legacy audit bundles are **byte-identical including
their manifests**. The two final-code local inventory bundles are also byte-identical including manifests.
The synthetic archive integration test independently verifies byte-identical full
strict bundles, including feature and label files, and unchanged source bytes.
Empty/unmeasured-origin integration retains exclusions and emits no invented labels.

Preservation verification rechecked **56 frozen bundles / 322 artifacts**, **303
protected central files**, **214 protected existing working-project files**, and
the pinned Chronos weight/config hashes. Source/dependency locks, original data,
splits, forecasts, baselines, model configuration, numerical metrics and Phase0–4.2.1
reports remain unchanged. The working project's unrelated original `main` HEAD
`2e7999ea436d49449652e6c52e9066ef2e514419` is preserved.

Small [verification evidence](examples/phase5_1/verification.json) records these
checks. Full local logs, manifests and inventories are outside Git:
`/home/hp/tst/research/forecasting_mvp/phase5_1/2026-10-15/`.

Reproduce checks on this host, using **new output directories**:

```bash
cd /home/hp/tst/td_pipeline_module_level/td_pipeline
TD51_PY="$PWD/.venv-forecast/bin/python"
PYTHONDONTWRITEBYTECODE=1 "$TD51_PY" -m pytest -q -p no:cacheprovider \
  tests/test_multilanguage_foundation.py
PYTHONDONTWRITEBYTECODE=1 "$TD51_PY" -m pytest -q -p no:cacheprovider tests \
  -k 'not test_actual_catboost_models_shared_folds_predictions_and_purging'

TD51_ROOT=/home/hp/tst/research/forecasting_mvp/phase5_1/2026-10-15
PYTHONDONTWRITEBYTECODE=1 "$TD51_PY" -m forecasting_multilanguage audit-legacy \
  --db /home/hp/TECH_DEBT/td_V2.db \
  --sha256 8eb329e5e5690b884b98df824c4b94fc7582c5d610fa3bd12784b1e417b2684e \
  --git-sources "$TD51_ROOT/git_sources.local.json" \
  --output "$TD51_ROOT/reproduce-legacy-new"
PYTHONDONTWRITEBYTECODE=1 "$TD51_PY" -m forecasting_multilanguage inventory-local \
  --root /home/hp/TECH_DEBT --root /home/hp/tst/research \
  --root /home/hp/tst/td360_v3_real_operator_v0100/workspace/repos \
  --root /home/hp/tst/td360_v3_real_operator_v0100/workspace/admission_raw \
  --exclude /home/hp/tst/research/forecasting_mvp \
  --exposure-records "$TD51_ROOT/exposure_records.local.json" \
  --output "$TD51_ROOT/reproduce-inventory-new"
```

The local JSON inputs are retained with audit receipts. On another host, construct
them from available licensed source metadata using the documented map/record
schemas; matching Git objects are a prerequisite, not implicitly downloaded.
Checksums and counts are portable, absolute audit paths are host-specific.

## Files and publication

Added: the 15 Python modules under `forecasting_multilanguage/`, its README and
quarantined template, `tests/test_multilanguage_foundation.py`, this report and
small attributed `examples/phase5_1/` evidence. Modified only the four Phase5
documents for pilot/path qualifications, root README and `GITHUB_SYNC.md` for the
new phase boundary. No old production module or lock was edited.

Publication uses a normal descendant of the inspected remote `main`; no unrelated
remote content or working-project history is overwritten. Full databases,
environments, checkpoints, raw private exports and large data artifacts are
excluded. The post-push commit/content receipt is recorded outside Git to avoid
self-referential commit hashes; the completion response identifies the published
commit. Original-project synchronization copies only explicit reviewed files and
advances only `github-main` tracking, never its unrelated local `main`.

## Unresolved acquisition requirements and stop

1. Obtain owner-authorized, immutable Python-dominant and genuine Python+JS/TS
   archives, plus a Java development archive with complete matching schema2
   provenance. Require raw native SQALE measurements, revision/analysis/tree
   linkage, whole declared scope/language coverage, full analyzer/rule/build
   domain and separately documented data reuse rights.
2. Supply complete first-parent objects/ref evidence and independently resolvable
   origin and exact 30/60/90-day endpoint states; unknown endpoints must remain
   unknown. The planned three-family/six-cutoff pilot is an engineering check,
   not a training corpus or evidence of forecasting accuracy.
3. Resolve exposure aliases/forks before enrolling genuinely new held-out families.
   Unresolved Zenodo/registry names must not silently pass the exposure gate.
4. Keep F2 disabled until full-path reconciliation and included-window coverage
   are demonstrated. The sampled basename ambiguity is not a repair algorithm.
5. If archives cannot supply this evidence, historical replay/scans or archive
   acquisition require **separate authorization**. This phase did not take that
   fallback automatically or create artificial observations.

**STOP at Phase5.1 verification and publication.** No Ridge/CatBoost training,
Chronos rerun, scanning, backend, dashboard or next phase has been started.
