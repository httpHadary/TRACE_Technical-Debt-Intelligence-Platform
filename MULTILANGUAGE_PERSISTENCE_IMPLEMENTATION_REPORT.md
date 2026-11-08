# Multi-language persistence implementation — 2026-11-03

The MVP can ingest complete offline native Sonar project exports for Python,
Java, JavaScript/TypeScript and mixed repositories, then use the existing
persistence engine, read-only API and dashboard. This is **software-validated**.
It is not a claim of real Click measurements or multi-language forecast accuracy.

| Area | Implemented and verified | Real-world validation remaining |
| --- | --- | --- |
| Python first | Synthetic Python Git history and native-project envelopes pass ingestion, persistence, API and CLI tests. | `pallets/click` has source-only local evidence, no completed native export found in the bounded audit. |
| Java | Same additive ingestion path; Java-containing projects require a `java_compiled` domain. Existing historical principal import still works. | Fresh native archive needs actual build/scanner/domain evidence; a build-mode claim alone does not certify compilation. |
| JS/TS and mixed | JS, JSX, TS, TSX and Python/Java/JS/TS mixtures are covered. One JavaScript analyzer can support JS and TS. Ancillary language coverage is retained separately. | Authorized representative JS/TS and mixed native exports; matching runtime/settings and complete scope evidence. Other suffixes/languages need explicit extension. |
| Native metrics | Require native project (`TRK`) aggregate, exact project/analysis/revision/tree identity, hash-bound raw envelopes, scanner/CE success, Git inventory and complete analyzed coverage. | Exporter must preserve real native responses and evidence when constructing the documented normalized envelopes. No automatic live collector was added. |
| Targets | Separate target-qualified bundles for maintainability-only SQALE and total principal. | No real non-Java accuracy benchmark is available. |
| Workflow and UI | Existing formulas, prediction seals, semantic replay, API routes and dashboard; selected target, language NCLOC, scope/domain and provenance are visible. | Browser rendering was not checked; the live HTTP and actual JavaScript logic smoke passed using a minimal DOM harness. |

## Metric and missingness contract

`native_sqale_index_minutes` selects `sqale_index` only.
`native_total_principal_minutes` sums `sqale_index`,
`reliability_remediation_effort`, and `security_remediation_effort` only when
all three are observed. These are estimated remediation minutes in Standard
mode. See [Sonar metric definitions](https://docs.sonarsource.com/sonarqube-server/user-guide/code-metrics/metrics-definition).
MQR mode is rejected rather than silently converting metric names or assuming
that its quality categories are disjoint; see [Sonar mode semantics](https://docs.sonarsource.com/sonarqube-server/2025.3/user-guide/code-metrics/changing-modes).

Absent/null effort stays null with typed missingness. Missing security or
reliability does not prevent a valid SQALE forecast; it makes total principal
unavailable. A missing latest stock never falls back to an older stock. Native
language NCLOC describes coverage and never allocates project debt by language.
Comparable measured stock changes remain separate from persistence's zero
projected change. Intervals remain null.

The additive formats are `persistence.observations.v2` and
`persistence.presentation.v2`. Each bundle contains one target. Old v1 defaults,
contracts and historical adapters remain intact. API route version stays
`/api/mvp/v1`; bundle manifests identify their presentation version.

## Verification

The final focused batch passed **421 tests**, including **46 new native tests**:

```bash
python3 -m pytest -q \
  tests/test_native_project_persistence.py \
  tests/test_multilanguage_foundation.py tests/test_multilanguage_preflight.py \
  tests/test_production_scope_readiness.py \
  tests/test_persistence_flow.py tests/test_persistence_api.py \
  tests/test_forecasting_mvp_phase0.py tests/test_forecasting_mvp_phase1.py \
  tests/test_forecasting_mvp_phase2.py tests/test_forecasting_mvp_phase2_1.py \
  tests/test_forecasting_mvp_phase3.py
```

Tests exercise all requested language families, both targets, missing values,
actuals isolation and chronology, unmeasured changed revisions, target-specific
IDs, seal-before-actual parsing, tampering, duplicate JSON/metrics, invalid
numbers/units, file-vs-project values, incomplete scans, missing analyzers,
scope/language mismatches, Java build mode, Git symlinks/submodules and
cross-project actuals on the same Git lineage.

Independent compatibility checks reproduced the original v1 example bundle
byte-for-byte: ID
`6b0071f359ea1e371ada66e53fc5d467247ef4c0704ada11946962dff08fea78`,
12 forecasts and all seven artifact hashes unchanged. Importing the existing
sealed historical Java principal archive still produces 678 persistence
endpoints; macro MAE at revision horizons 3/4/12 remains
104.42072378764885 / 135.55081142419644 / 384.541131755602 minutes.
Those historical results do not validate Python, JS/TS or mixed forecasts.

A live loopback server and the actual dashboard JavaScript passed a logic smoke
for synthetic Python/JS/TS/XML bundles: SQALE 12 minutes, unavailable total
principal when security is missing, native language coverage, ancillary labels,
provenance and all six horizon selections. This is not rendered-browser QA.
The original v1 dashboard logic smoke also passed. JavaScript syntax and
whitespace checks passed. Review reproduced and fixed two admission defects:
actuals must retain the sealed native project identity, and scoped Git entries
without a recognized suffix cannot hide a submodule. Both have regression tests.

## Click evidence and remaining blockers

The unchanged [Phase 5.2 readiness manifest](examples/phase5_2/readiness_manifest.json)
and [Phase 5.2.1 readiness manifest](examples/phase5_2_1/readiness_manifest.json)
both record zero actual scans, native measurements and targets. The
[selected source plans](examples/phase5_2/selected_source_plans.json) retain
six planned Click cutoffs, empty native analysis IDs and null native debt.
Source inventories/text proportions are not Sonar NCLOC or debt measurements.
The [Phase 6.6 readiness receipt](examples/phase6_6/readiness_receipt.json)
still does not admit real data. Existing capability work supersedes historical
software-only scope blockers; it does not create native scanner evidence or
approve the existing rights decisions.

Real validation needs an existing authorized completed export, explicit source
reuse/content review, full analyzer/rules/runtime/settings/dependency/suppression
domain evidence, complete production scope, successful scanner/CE evidence and
project-level native measurements. The [archive contract and commands](forecasting_multilanguage/NATIVE_PROJECT.md)
describe precisely what to provide. Then ingest Click separately for SQALE and,
only if all components exist, total principal; inspect the resulting dashboard
and supply independently archived future actuals before reporting accuracy.
Use the same admission process for representative JS/TS and mixed repositories.

Known limits are explicit: two measured commits sharing a UTC second are blocked
by the existing observation clock, with no altered timestamps; unsupported/MQR
domains are blocked; source authenticity, rights and Java build claims remain
operator assertions. Self-contained replay checks supplied raw bytes and
recorded Git bindings; it does not independently authenticate those claims.
Actuals must select the exact Git state at the cutoff and cannot reuse a stale
measurement across an unmeasured changed revision. Archived retrospective
measurements do not establish historical operational availability.

No scans, live Sonar requests, downloads, new forecasting models or frozen
experiment changes were performed. Persistence remains the only MVP forecaster.
