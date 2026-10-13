# TechDebt360 MVP — Phase 1 implementation report

Date: 2026-10-14, Africa/Cairo. Working project:
`/home/hp/tst/td_pipeline_module_level/td_pipeline`.

**Phase 1 status: PARTIAL for scientific data readiness; implementation and permitted verification pass.** Historical measurements were extracted without changing the DB. Missing/ambiguous histories and imported analyzer limitations are explicit. No future labels, grids, split cohorts, trained models, predictions, scans, API or dashboard were created. Phase 2 was not started.

## Implemented path and changed files

`python3 -m forecasting_mvp ingest-history --config ... --out NEW_DIRECTORY`
opens the source with SQLite `mode=ro`, `query_only=ON`, verifies full integrity
and required schema, then extracts unique Git/analysis/measure joins. It hashes
the source before/after and rejects publication on a change. Artifacts use strict
legacy IO, streaming hashes and an immutable COMPLETE manifest.

| File | Phase 1 change |
|---|---|
| `forecasting_mvp/v2_import.py` | New read-only import/configuration, profile normalization, exact timestamp linkage, graph/first-parent/chronology audit, deterministic CSV/audit/exclusion publication |
| `forecasting_mvp/cli.py` | Add `ingest-history`; keep Phase 0 verification commands and reject all model/later-phase commands |
| `forecasting_mvp/__init__.py`, `forecasting_mvp/README.md` | Correct supported phase scope and reproduction instructions |
| `forecasting_mvp/study.phase1.example.json` | New source/hash/license/output template; Phase 0 config remains unchanged |
| `tests/test_forecasting_mvp_phase1.py` |22 offline integrity/provenance/ancestry/determinism and failure-boundary tests |
| `.gitignore` | Append database/checkpoint/history/private-config/credential patterns while retaining pre-existing entries |
| `README.md` | Add phase-status links without replacing pre-existing text |
| `GITHUB_SYNC.md` | Central repository, independent-history handling and future verified-phase sync procedure |
| `examples/phase1/` | Small attributed sample, full audit, output hashes, raw spot checks, repeatability/test evidence and reproduction README |
| `PHASE_1_IMPLEMENTATION_REPORT.md` | This report |

Existing collectors, module forecasting, dataset/evaluation code and dependency
locks remain unchanged. Pre-existing local README/`.gitignore` modifications and
untracked forecasting work were preserved. Only the listed existing files were
edited for this phase; no cleanup/reset or broad configuration migration occurred.

## Actual source and extraction findings

Source: `/home/hp/TECH_DEBT/td_V2.db`,1,542,533,120 bytes; official
[release 2.0.1](https://github.com/clowee/The-Technical-Debt-Dataset/releases/tag/2.0.1),
CC BY-NC-SA 4.0. Original dataset authors and transformation attribution are in
[the sample README](examples/phase1/README.md).

SHA-256, identical before/after each real ingestion:

```text
8eb329e5e5690b884b98df824c4b94fc7582c5d610fa3bd12784b1e417b2684e
```

| Actual check | Result |
|---|---:|
| SQLite full integrity |`ok` |
| Repository coverage |31 |
| Source Git records |153,994 |
| Source analyses |67,550 |
| Source project measures |66,711 |
| Unique published historical measurements |66,711 |
| Analysis exclusions |839, all blank analysis keys |
| Excluded Git records / orphan measure keys |0 / 0 |
| Missing / invalid published SQALE values |0 / 0 |
| Observed zero debt values |31 |
| Unmeasured Git revisions overall |87,283 |
| Unmeasured revisions within exact measured UTC time spans |19,979 |
| Known profile-metadata rows / missing profile rows |66,685 / 26 |
| Repositories with unique archived graph tip |27 |
| Ambiguous-tip repositories |4 |
| First-parent commits identified in unique-tip graphs |75,713 |
| Published measurement mainline classification |44,003 FIRST_PARENT;4,130 NON_FIRST_PARENT;18,578 UNRESOLVED_MAINLINE |
| Missing parent edges / cyclic nodes in real source |0 / 0 |
| First-parent timestamp inversions |34 |
| Measured historical range |2000-10-11T16:43:11Z–2018-10-15T13:22:16Z |
| Per-repository measured span |533.15–6,408.65 days |

The in-span count uses exact parsed UTC bounds. It differs from the earlier
19,954 day-window diagnostic; those policies are not interchangeable. This phase
does not silently reuse that old count or turn it into an endpoint count.

Ambiguous graph tips: `org.apache:batik`, `org.apache:cocoon`, `org.apache:felix`,
`org.apache:santuario`. No arbitrary tip was selected for them. Inversions occur
in archiva(2),collections(13),hive(12),thrift(6),zookeeper(1). The audit records
their affected first-parent indices; observed domain/chronology segments break at
metadata changes and crossed time inversions. These are **observed metadata
segments**, not full immutable rule/analyzer domains or validated daily grids.

All published analysis dates exactly match the joined aware Git committer time
to the second. The source analysis strings are naive; UTC is assigned only after
that exact match under the recorded import policy. This does not establish actual
scan execution or online branch availability. Full imported scanner/plugin/rule,
build-mode and scope configuration remains unknown. Metadata equality is not
proof of complete analyzer equivalence.

The CSV retains verified record joins even where mainline/profile admission is
unresolved, with explicit status/limitations. `AUDITED_IMPORTED` means linkage,
numeric parsing and timestamp provenance; it is not `VERIFIED_SCAN` or a claim
that every row is fit for forecasting. Source repository IDs are retained, with
stable hash-based MVP IDs to avoid colon-containing legacy IDs conflicting with
the existing safe-ID contract.

## Local artifacts and forecasting-readiness boundary

Final local bundle:
`/home/hp/tst/research/forecasting_mvp/phase1/2026-10-14/run-002/`.

- `historical_debt.csv`:66,711 rows,52,279,826 bytes. Native project SQALE,
  immutable commit/analysis/source IDs, historical/committer timestamps, profile,
  ancestry, chronology and provenance flags. Missing numeric values serialize as
  blank; observed zero remains0.0. No guessed debt or zero substitution.
- `git_history.csv`:153,994 rows,30,283,270 bytes. Includes unmeasured revisions and
  parent/first-parent diagnostics, so later state selection cannot silently skip
  changed but unmeasured commits.
- `historical_data_audit.json`: repository spans, distinct timestamp/gap statistics,
  profile/missingness segments, graph tips/parents/inversions, exclusions, hashes,
  schema and30/60/90-day **span screening only**.
- `excluded_records.json`: explicit excluded analysis identities and reasons.
-12-row sample and complete checksummed manifest.

All horizon records have `eligible_origins=null`, `endpoint_pair_count=null`, and
`NOT_EVALUATED_NO_FUTURE_LABELS`. Long spans alone cannot establish useful context,
independent samples or exact30/60/90 future measurements. Regular/masked context
admission, resolving ambiguous mainlines, conservative analyzer boundaries and
future-state matching remain **Phase 2 prerequisites**, not executed work.
Weekly91-day tasks are not relabeled90-day targets. SQALE remains **estimated
maintainability remediation minutes**, separate from actual developer effort,
reliability/security estimates and classifier scores.

## Verification and reproducible commands

From the working project, using the existing `.venv-forecast`; no dependencies
or model weights were installed:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp ingest-history \
  --config forecasting_mvp/study.phase1.example.json \
  --out /home/hp/tst/research/forecasting_mvp/phase1/2026-10-14/run-002

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m forecasting_mvp verify-bundle \
  --bundle /home/hp/tst/research/forecasting_mvp/phase1/2026-10-14/run-002

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests/test_forecasting_mvp_phase1.py

PYTHONDONTWRITEBYTECODE=1 .venv-forecast/bin/python -m pytest -q -p no:cacheprovider tests \
  -k 'not test_actual_catboost_models_shared_folds_predictions_and_purging'
```

For reproduction, change the output to a **new** directory; existing runs cannot
be overwritten. Exit 2 for the real source indicates PARTIAL audit findings with a
valid COMPLETE bundle. Exit 3 rejects corrupt/schema/hash/config/publication inputs.

Actual verification:

-22 new Phase 1tests cover unique joins/duplicates/missing analyses, zero/null debt,
  SHA/provenance, aware versus naive timestamps, time agreement, mainline versus
  latest timestamp, ambiguous/missing/cyclic graphs, profile normalization,
  chronology segmentation, stable serialization/output, read-only source and
  rejection when the source hash changes before publication.
- Full permitted regression suite: **222 passed,1training test deselected,0 failed**.
  This includes the Phase 0 and legacy tests; no counts are doubled.
- Real repeated ingestion into `run-003`: **all six artifacts byte-identical** to
  `run-002`, including CSVs/audit/manifests; same source/code/config.
-12published sample measurements independently rejoined against raw SQLite SQL:
  **12/12 exact revision and debt-value checks passed**.
- Full output hashes and verification manifest pass; source DB unchanged.

Test and determinism evidence is published under [examples/phase1](examples/phase1/).
These tests/audits do not establish forecast accuracy or sufficient independent
test cohorts. The existing actual-CatBoost training test is deliberately excluded
under the no-model-execution rule.

## GitHub sync and remaining limitations

Destination: [FadyYosry77/TechDebt360-MVP](https://github.com/FadyYosry77/TechDebt360-MVP),
branch `main`. Local legacy history and remote history were inspected before
syncing. GitHub initially ended at `2f2d66a49b3edd007b3ca80c468a4c2bc61c5aae`.
The working project now has the central `origin` and tracking `github-main` ref;
its unrelated original `main` and pre-existing changes are preserved. The clean
central checkout publishes a normal descendant commit, preserving remote `OK`,
architecture packages, ZIPs, Phase 0 evidence and all other remote content. No force
push or unrelated-history merge/reset is used.

Full history CSVs, exclusions, the1.5 GB SQLite DB, caches, environments, private
configs, keys and checkpoints are excluded. Only small attributed samples,
provenance/hashes/schema/audit/tests and reproduction documentation are committed.
The exact publication commit SHA and remote-file verification are reported in the
task completion message; from the central checkout retrieve it with:

```bash
git log -1 --format=%H -- PHASE_1_IMPLEMENTATION_REPORT.md
git ls-remote origin refs/heads/main
```

**Phase 2 readiness: conditional.** The importer and audit provide a reproducible
starting point. Resolve or restrict ambiguous-tip/inversion intervals, admit
known-domain histories, then establish actual contexts/endpoints under the
existing MVP plan. Do not assume87,283unmeasured revisions can be carried forward.
Pretrained runtime packages/resources remain Phase 0 limitations and are not
addressed by history ingestion. No future labels or models have run.

**STOP after Phase 1 verification and GitHub publication. Await authorization
before Phase 2.**
