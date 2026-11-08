# Persistence-only local flow

This flow consumes operator-provided observations. It does not collect scans, load a neural model, train, upload, or establish predictive accuracy. Native total principal is the sum of compatible maintainability, reliability, and security estimated remediation minutes. Source permission and provenance remain operator claims; importing JSON grants no rights. The examples are **SOFTWARE_VALIDATION_ONLY**, with invented revisions and measurements.

From the repository root, using the existing Python requirements:

```bash
registry=$(mktemp -d)
python3 -m forecasting_mvp persistence-build --source examples/persistence_only/observations.json --out "$registry/pending"
python3 -m forecasting_mvp persistence-build --source examples/persistence_only/observations.json --actuals examples/persistence_only/actuals.json --out "$registry/measured"
python3 -m forecasting_mvp persistence-verify --bundle "$registry/measured"
python3 -m forecasting_mvp persistence-serve --registry "$registry" --port 8765
```

Open `http://127.0.0.1:8765`. The example includes increases, decreases, observed zero, domain/scope breaks, a latest observation with a missing component, measured endpoints, unchanged selected calendar states, and pending endpoints. The server binds only to `127.0.0.1`; keep incomplete outputs outside a serving registry until repaired or removed by the operator. A corrupt or incomplete visible entry makes registry reads fail closed with HTTP 409.

All commands require explicit inputs and a new output directory. Existing outputs are never overwritten. Input validation fails before output creation where possible. Evaluator failures retain origin artifacts and prediction seals for inspection, without a COMPLETE manifest; choose a new output for retry. CLI validation errors print a JSON `BLOCKED` result and exit 3. Successful bundles return `COMPLETE` and exit 0. Stop the server with Ctrl-C.

## Observation source contract

`examples/persistence_only/observations.json` is a complete input. JSON objects require exactly the documented fields. Duplicate JSON keys, unknown fields, invalid IDs, duplicate observation identities, nonfinite values, and contradictory revision/time ordering are rejected.

Top-level object:

| Field | Contract |
| --- | --- |
| `version` | Literal `persistence.observations.v1` |
| `source` | Provenance object below |
| `horizons` | One or both entries: `"revision_step": [3,4,12]`, `"elapsed_day": [30,60,90]`. Each registered list must be exact. |
| `observations` | Nonempty array of observation objects below |

Every source/projection provenance object has exactly `source_id`, `kind`, `description`, `permission`, and `provenance`. `source_id` is a safe identifier; `kind` is `SYNTHETIC` or `OPERATOR_PROVIDED`; the other fields are nonblank strings describing source identity, permission claims, and measurement provenance. Synthetic inputs are always labeled SOFTWARE_VALIDATION_ONLY. Operator inputs remain unvalidated.

Each observation has exactly:

| Field | Contract |
| --- | --- |
| `observation_id`, `repository_id`, `domain_id`, `scope_id` | Identifiers matching `[A-Za-z0-9][A-Za-z0-9_.-]*`. Domain identifies compatible analyzer/rules/measurement semantics; scope identifies the measured source population. |
| `revision` | Full lowercase 40- or 64-hex revision hash |
| `revision_index` | Nonnegative integer, increasing within each repository; defines the selected revision sequence, not a calendar duration |
| `observed_utc` | Exact valid `YYYY-MM-DDTHH:MM:SSZ`, increasing with revision index |
| `components` | Exactly `maintainability`, `reliability`, `security`, each a finite nonnegative JSON number or `null` |

Observation IDs are globally unique. Revision hashes, indices, and observation times are unique within each repository. Boolean/string numbers are rejected. Zero is observed zero; null is missing. A missing component makes the total unavailable. The latest observation supplies the origin even if incomplete: the flow never borrows an older or another-domain stock. Signed measured change is current total minus the immediately preceding total only when both are complete and domain/scope match. Otherwise its value is null with an explicit status.

For each repository and registered horizon, an available forecast repeats the origin stock, predicts zero change, and carries null interval bounds. An unavailable origin yields null prediction/change and an explicit reason. Forecast IDs hash source identity, origin contents, target, clock and horizon; refreshing the origin produces new IDs. Revision-step targets are origin index plus 3/4/12. Calendar targets are the exact origin UTC plus 30/60/90 elapsed days. The clocks are separate contracts.

## Optional evaluator-only actual projection

`examples/persistence_only/actuals.json` is a complete example. Actuals are opened and parsed only after origin-only predictions and `prediction_seal.json` have been written. Changing actuals cannot change a forecast ID or prediction.

Top-level object has exactly `version` (literal `persistence.actuals.v1`), `source` (the same provenance schema), and `actuals` (an array, possibly empty). Each actual row has exactly:

- `forecast_id`: ID copied from the sealed forecast.
- `target`: literal `native_total_principal_minutes`.
- `repository_id`, `origin_observation_id`, `domain_id`, `scope_id`, `horizon_unit`, `horizon`: exact typed matches to that forecast.
- `endpoint_revision`: full lowercase 40/64-hex selected endpoint revision.
- `endpoint_revision_index`: nonnegative integer identifying that revision in the same repository sequence.
- `observed_utc`: valid canonical UTC later than origin. Calendar actuals must match the forecast's exact `endpoint_utc`; revision-step actuals must have the exact forecast `endpoint_revision_index` and a new revision.
- `components`: the same three component fields, all measured finite nonnegative numbers.

For a calendar horizon, an unchanged selected revision may retain the origin revision/index and identical component measurements at the later evaluation instant. Repeated selected revisions must retain consistent indices, domain/scope and components; two revisions cannot claim the same endpoint index. Wrong/duplicate targets, clock/domain mismatches, backward endpoints and inconsistent measurements fail validation. Actual selected-state indices must also remain nondecreasing across later evaluation times and agree at the same instant, across all supplied horizons/clocks. Missing actual rows stay PENDING. An unavailable forecast remains UNAVAILABLE even if a measured actual is supplied. Error is prediction minus actual; actual change is actual minus origin.

## Historical principal bridge

```bash
python3 -m forecasting_mvp persistence-import --bundle /operator/path/to/sealed-principal-bundle --out "$registry/archived"
python3 -m forecasting_mvp persistence-verify --bundle "$registry/archived"
```

The bridge is restricted to the original principal contract and exactly 678 persistence endpoints (226 per registered revision horizon). It verifies all artifact-manifest file hashes/sizes, request and prediction seals, context membership, origin identities, persistence formulas, scored prediction membership, and endpoint measurement consistency, and requested revision-step distance wherever explicit context edges establish it. Separate context chains do not create a proven distance through their display/date ordering. Unsafe paths and symlinks are rejected. Other archived methods remain in the source archive and are excluded from the active projection. No research/model module is imported.

The bridge preserves original forecast/context/repository/revision IDs, original source-file hashes, source registration, commit dates and measured elapsed commit-date exposure. Those date-only values are not converted to invented UTC timestamps or calendar horizons. Original component breakdowns are unavailable and stay null. History merges explicit consecutive context edges independently of request ordering; disconnected chains do not gain invented changes. Origin/prediction projections are sealed before scored outcomes are parsed. Source rights and provenance are retained as claims, with no permission upgrade.

## Bundle and evaluation reports

The additive namespace is `persistence.presentation.v1`; existing research schemas and CLI commands retain their behavior. A COMPLETE manifest is published atomically last, includes exact artifact hashes and a content-derived bundle ID, and is reverified on every API bundle read. Verification recomputes predictions, history, evaluations and summaries from their inputs, checks prediction seals, and rejects unexpected/missing files and provenance/semantic tampering. Hashes provide integrity within the bundle, not external authentication of operator claims.

`evaluation_summary.json` reports each clock/horizon's forecast count, available/measured/pending/unavailable counts, and measured coverage among available forecasts (null if none are available). For all measured endpoints and the changed/stable/increase/decrease subsets, it includes per-repository counts, MAE/RMSE, repository-macro MAE/RMSE, and pooled MAE/RMSE. Macro metrics average repository metrics with equal repository weight; pooled metrics weight endpoints equally. Empty subsets have null metrics. Subset membership uses signed measured actual change, not predicted change. These are descriptive source results; current accuracy remains UNVALIDATED, including when the evidence is synthetic.

## Read-only API

All routes below use prefix `/api/mvp/v1`:

| GET route | Result |
| --- | --- |
| `/health` | Local service identity and unvalidated status |
| `/bundles` | Deterministically ordered verified manifests |
| `/bundles/{bundle_id}` | One manifest |
| `/bundles/{bundle_id}/repositories` | Sorted repository IDs |
| `/bundles/{bundle_id}/repositories/{repository_id}/history` | Observation history |
| `/bundles/{bundle_id}/repositories/{repository_id}/forecasts?horizon_unit=revision_step&horizon=3` | Matching persistence rows |
| `/bundles/{bundle_id}/repositories/{repository_id}/evaluations?horizon_unit=revision_step&horizon=3` | Matching evaluator rows |
| Same evaluations route with `&summary=true` | Bundle-wide summary for that clock/horizon, across all repositories |

Forecast/evaluation requests require explicit `horizon_unit` and `horizon`; optional `model=persistence` is the only accepted model. Unknown IDs/routes return 404. Corrupt/incomplete bundles return 409. Invalid, duplicate, unknown, or unsupported model/clock/horizon query values return 422. A registered clock/horizon absent from a particular bundle returns HTTP 200 with `{"status":"UNSUPPORTED_DATA","data":null,"reason":"..."}`. Mutation methods return 405. Host headers must identify localhost. Only fixed local HTML/CSS/JS assets are served; source text is inserted with `textContent`, and no remote fonts or dependencies are used.

Focused software checks:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_persistence_flow.py tests/test_persistence_api.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_forecasting_mvp_phase0.py tests/test_forecasting_mvp_phase1.py tests/test_forecasting_mvp_phase2.py tests/test_forecasting_mvp_phase2_1.py tests/test_forecasting_mvp_phase3.py
```
